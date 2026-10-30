"""Shared, cached AI prose on top of immutable Bazi/Mai Hoa/Liu Yao snapshots."""
from datetime import datetime, timezone
from collections import OrderedDict
from hashlib import sha256
import json
import logging
import re
import time
from typing import Literal
from uuid import UUID
from threading import Lock, Thread

from pydantic import Field, model_validator

from research_tools.interpretation_prompt import Context, Response, build_messages, validate_response, PACK
from .ai_client import AIConfig, CompatibleAIClient
from .ai_jobs import ReadingJob
from .ai_context import natal_context, maihoa_context, liuyao_context
from .date_ai_context import DateReadingContext, date_context
from research_tools.date_interpretation_prompt import build_date_messages, DATE_PACK
from .bazi_models import BaziReadingSnapshot
from .engine import EngineError
from .liuyao_analysis import digest
from .liuyao_models import AnalysisContext
from .models import StrictModel
from .reading_display import (UnreadableReading, VerboseReading, JargonReading, validate_reading_prose,
                             validate_reading_brevity, validate_liuyao_language)
from .snapshots import SignedSnapshot
from .bazi_pipeline import (LifeReading, PipelineProvenance, prepare_analyst,
                            interpreter_messages, validate_analysis, validate_life_reading, validate_life_display,
                            ANALYST_MAX_TOKENS, INTERPRETER_MAX_TOKENS, LifeReadingIssues)


class AIReadingRequest(StrictModel):
    method: Literal["BAZI", "MAIHOA", "LIUYAO", "DATE"]
    consultation_id: UUID
    consultation: SignedSnapshot
    bazi_reading: SignedSnapshot | None = None
    analysis: SignedSnapshot | None = None
    bazi_reading_id: UUID | None = None
    analysis_context: AnalysisContext | None = None
    analysis_rules_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def matching_options(self):
        if self.method != "BAZI" and self.bazi_reading_id is not None:
            raise ValueError("Bazi reading ID requires the Bazi method")
        if self.method != "BAZI" and self.bazi_reading is not None:
            raise ValueError("Unexpected Bazi reading")
        if self.method != "LIUYAO" and self.analysis is not None:
            raise ValueError("Unexpected Liu Yao analysis")
        if self.method == "LIUYAO":
            if self.analysis_context is None or self.analysis_rules_sha256 is None:
                raise ValueError("Liu Yao requires the exact saved analysis context and rule hash")
        elif self.analysis_context is not None or self.analysis_rules_sha256 is not None:
            raise ValueError("Analysis options require the Liu Yao method")
        return self


class AIReadingResult(StrictModel):
    schema_version: Literal["ai-reading-v1"] = "ai-reading-v1"
    reading_id: str
    consultation_id: UUID
    method: Literal["BAZI", "MAIHOA", "LIUYAO", "DATE"]
    created_at: datetime
    model_requested: str
    model_returned: str
    provider_host: str
    prompt_version: str
    case_ids: list[str]
    context_sha256: str
    model_called: Literal[True] = True
    validation: Literal["SCHEMA_AND_REFERENCES_CHECKED"] = "SCHEMA_AND_REFERENCES_CHECKED"
    usage: dict[str, int]
    generation_passes: int = Field(default=1, ge=1, le=4)
    pipeline: PipelineProvenance | None = None
    context: Context | DateReadingContext
    reading: Response | LifeReading = Field(discriminator="schema_version")

    @model_validator(mode="after")
    def bind(self):
        if isinstance(self.reading, LifeReading):
            validate_life_display(self.reading)
            if (self.method != "BAZI" or self.pipeline is None
                    or self.reading.context_id != self.context.context_id
                    or self.reading.analysis_sha256 != self.pipeline.analysis_sha256
                    or self.generation_passes != self.pipeline.analyst_passes + self.pipeline.interpreter_passes):
                raise ValueError("Bazi pipeline provenance does not match the reading")
        else:
            validate_response(self.reading, self.context)
            validate_reading_prose(self.reading)
            if self.pipeline is not None:
                raise ValueError("Unexpected pipeline provenance")
        if (self.method == "DATE") != (self.context.method == "DATE_SELECTION"):
            raise ValueError("Date reading method does not match its context")
        if str(self.consultation_id) != self.context.context_id or digest(self.context.model_dump(mode="json")) != self.context_sha256:
            raise ValueError("AI response is not bound to the saved consultation")
        return self


class PlainReadingIssues(ValueError):
    def __init__(self, issues, draft):
        self.issues, self.draft = issues, draft
        super().__init__("Reading needs editorial repair")


def validate_liuyao_candidate(raw, context):
    """Report all repairable issues together, rather than fixing one per paid pass."""
    reading = Response.model_validate(raw)
    issues = []
    try:
        validate_response(reading, context)
    except ValueError:
        issues.append({"type":"CONTEXT_OR_REFERENCE_MISMATCH"})
    for validator, kind in ((validate_reading_prose,"PROSE_CONTAINS_INTERNAL_NOTATION"),
                            (validate_liuyao_language,"LIUYAO_TOO_MUCH_JARGON"),
                            (lambda r:validate_reading_brevity(r,section_limit_factor=1.5),"READING_TOO_LONG")):
        try:
            validator(reading)
        except ValueError as error:
            issues.extend({"type":kind, **field} for field in getattr(error,"fields",[{}]))
    if issues:
        raise PlainReadingIssues(issues, reading)
    return reading


class AIReadingService:
    def __init__(self, app_state, config=None, client=None):
        self.state = app_state
        self.config = config if config is not None else AIConfig.load()
        self.client = client if client is not None else CompatibleAIClient(self.config)
        self._cache = OrderedDict()
        self._pending = set()
        self._jobs = OrderedDict()
        self._lock = Lock()
        # Counts are reserved for every actual outbound attempt, including retries.
        if isinstance(self.client, CompatibleAIClient):
            self.client.before_request = self.state.ai_budget.reserve

    def context_for(self, request):
        key = str(request.consultation_id)
        kind = {"BAZI": "BAZI", "MAIHOA": "MAIHOA", "LIUYAO": "COINS", "DATE": "DATE"}[request.method]
        saved = self.state.signer.verify(request.consultation, kind)
        if saved.get("request_id") != key:
            raise EngineError("SNAPSHOT_INVALID", "Kết quả không khớp phiên đang mở.", 422)
        if request.method == "DATE":
            return date_context(saved)
        if request.method == "BAZI":
            reading = None
            if request.bazi_reading_id and str(request.bazi_reading_id) != key:
                data = self.state.signer.verify(request.bazi_reading, "BAZI_READING") if request.bazi_reading else None
                if (not data or data.get("consultation_id") != key or data.get("reading_id") != str(request.bazi_reading_id)
                        or data.get("chart_sha256") != digest(saved["chart"])):
                    raise EngineError("BAZI_READING_NOT_FOUND", "Không tìm thấy bài luận của lá số đang mở.", 404)
                reading = BaziReadingSnapshot.model_validate(data).reading
            return natal_context(saved, reading)
        if request.method == "MAIHOA":
            return maihoa_context(saved)
        wanted = request.analysis_context.model_dump(mode="json")
        analysis = self.state.signer.verify(request.analysis, "LIUYAO") if request.analysis else None
        if (analysis and analysis.get("session_id") == key and analysis["context"] == wanted
                and analysis["rules_sha256"] == request.analysis_rules_sha256
                and analysis.get("snapshot_sha256") == digest(saved)):
            return liuyao_context(saved, analysis)
        raise EngineError("LIUYAO_ANALYSIS_NOT_FOUND", "Hãy tải bài luận Lục Hào trước khi đọc phần diễn giải AI.", 409)

    def prepare(self, request):
        try:
            context = self.context_for(request)
        except ValueError:
            raise EngineError("AI_CONTEXT_INVALID", "Dữ kiện của phiên chưa đủ để nối phần luận AI. Hãy mở lại phần phân tích.", 409) from None
        prepared = (prepare_analyst(context) if request.method == "BAZI" else
                    build_date_messages(context, limit=2) if request.method == "DATE" else build_messages(context, limit=2))
        pack = DATE_PACK if request.method == "DATE" else PACK
        key = digest({"context": context.model_dump(mode="json"), "model": self.config.model, "endpoint": self.config.base_url,
                      "reasoning_effort": self.config.reasoning_effort,
                      "pack_sha256": prepared.get("pack_sha256") or sha256((pack / "manifest.json").read_bytes()).hexdigest(), "case_ids": prepared["case_ids"],
                      "messages_sha256": prepared["messages_sha256"], "ai_service": "ai-reading-v1"})
        return context, prepared, key

    @staticmethod
    def decode_cached(raw):
        payload = json.loads(raw)
        if "bazi_analysis" in payload:
            result = AIReadingResult.model_validate(payload["result"])
            if not isinstance(result.reading, LifeReading):
                raise ValueError("Unexpected intermediate analysis")
            analysis = validate_analysis(payload["bazi_analysis"], result.context)
            validate_life_reading(result.reading, analysis)
            return result.model_dump(mode="json")
        result = AIReadingResult.model_validate(payload)
        if isinstance(result.reading, LifeReading):
            raise ValueError("Bazi intermediate analysis is missing from cache")
        return result.model_dump(mode="json")

    def execute_bazi(self, context, prepared, key, request, *, progress=lambda stage: None, stream=False, deadline=None):
        total_usage = {}

        def stage(messages, validator, name, max_tokens):
            for attempt in range(1, 3):
                progress("ANALYZING" if name == "ANALYST" else "WRITING")
                if not isinstance(self.client, CompatibleAIClient):
                    self.state.ai_budget.reserve()
                raw, metadata = (self.client.complete(messages, max_tokens=max_tokens, stream=stream, deadline=deadline) if isinstance(self.client, CompatibleAIClient)
                                 else self.client.complete(messages))
                for token, count in metadata["usage"].items():
                    total_usage[token] = total_usage.get(token, 0) + count
                try:
                    progress("CHECKING")
                    return validator(raw), metadata, attempt
                except ValueError as error:
                    types = [row.get("type", "VALIDATION_ERROR") for row in error.errors()] if hasattr(error, "errors") else [type(error).__name__]
                    safe_types = sorted({code if isinstance(code, str) and re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", code)
                                         else "VALIDATION_ERROR" for code in types})
                    logging.getLogger("arcana.ai").warning("Bazi validation: stage=%s pass=%d types=%s", name, attempt, ",".join(safe_types))
                    if attempt == 2:
                        raise EngineError("AI_RESPONSE_UNBOUND", "Bài luận Bát Tự chưa đạt kiểm tra căn cứ và phạm vi; bạn có thể thử lại.", 502) from None
                    # Never feed rejected model prose back as authoritative evidence.
                    issues = (error.issues if isinstance(error,LifeReadingIssues) else [{"field": list(e["loc"]), "type": e["type"]} for e in error.errors()]
                              if hasattr(error, "errors") else [{"type": str(error)[:100]}])
                    if name == "ANALYST":
                        issues.append({"type": "ALLOWED_REFERENCE_CATALOG",
                            "fact_refs": [f.id for f in context.facts],
                            "evidence_refs": [e.id for e in context.evidence]})
                    messages = [dict(message) for message in messages]
                    messages[0]["content"] += ("\nLƯỢT KIỂM TRA LẠI CỦA " + name +
                        ": viết lại từ cùng dữ liệu đã kiểm tra, không tạo ID hoặc luận điểm ngoài phạm vi được cấp. "
                        "Giữ đầy đủ điều kiện và giới hạn; không xuất JSON/ID trong lời văn dành cho người đọc. Lỗi: " +
                        json.dumps(issues, ensure_ascii=False))

        analysis, analyst_meta, analyst_passes = stage(prepared["messages"], lambda raw: validate_analysis(raw, context,
            require_portrait=prepared.get("reading_scope") == "WHOLE_LIFE"), "ANALYST", ANALYST_MAX_TOKENS)
        reading, interpreter_meta, interpreter_passes = stage(interpreter_messages(analysis, prepared["interpreter_prompt"]), lambda raw: validate_life_reading(raw, analysis,
            prose_only=analysis.whole_life is not None), "LIFE INTERPRETER", INTERPRETER_MAX_TOKENS)
        provenance = PipelineProvenance(analysis_sha256=digest(analysis.model_dump(mode="json")),
            analyst_passes=analyst_passes, interpreter_passes=interpreter_passes,
            analyst_model=analyst_meta["model"], interpreter_model=interpreter_meta["model"])
        result = AIReadingResult(reading_id=key, consultation_id=request.consultation_id, method="BAZI",
            created_at=datetime.now(timezone.utc), model_requested=self.config.model, model_returned=interpreter_meta["model"],
            provider_host=self.config.public_status()["provider_host"], prompt_version=prepared["pack_version"], case_ids=[],
            context_sha256=digest(context.model_dump(mode="json")), usage=total_usage,
            generation_passes=analyst_passes + interpreter_passes, pipeline=provenance, context=context, reading=reading).model_dump(mode="json")
        # Full technical content is cached privately to revalidate every replay.
        return result, {"result": result, "bazi_analysis": analysis.model_dump(mode="json")}

    def lookup(self, request):
        _, _, key = self.prepare(request)
        with self._lock:
            row = self._cache.get(key)
        if row and row[0] > time.monotonic():
            try:
                return self.decode_cached(row[1])
            except (ValueError, TypeError, KeyError):
                # Old cached prose containing machine notation must not reach the UI.
                return None
        return None

    def _cached_locked(self, key):
        now = time.monotonic()
        for expired in [k for k, v in self._cache.items() if v[0] <= now]:
            del self._cache[expired]
        for expired in [k for k, job in self._jobs.items()
                        if job.finished_at is not None and job.finished_at + 900 <= now]:
            del self._jobs[expired]
        row = self._cache.get(key)
        if row:
            try:
                return self.decode_cached(row[1])
            except (ValueError, TypeError, KeyError):
                del self._cache[key]
        return None

    def _reserve_job_locked(self, key):
        if len(self._pending) >= self.state.security.ai_concurrency:
            raise EngineError("AI_RATE_LIMITED", "Phần luận AI đang bận. Hãy thử lại sau.", 429)
        if not self.config.configured:
            raise EngineError("AI_NOT_CONFIGURED", "Chưa cấu hình dịch vụ luận giải AI ở máy chủ.", 503)
        # Never evict active workers; completed jobs have the cache's 15-minute TTL.
        while len(self._jobs) >= 32:
            old = next((k for k, job in self._jobs.items() if job.finished_at is not None), None)
            if old is None:
                raise EngineError("AI_RATE_LIMITED", "Phần luận AI đang bận. Hãy thử lại sau.", 429)
            del self._jobs[old]
        job = ReadingJob()
        self._jobs[key] = job
        self._pending.add(key)
        return job

    def subscribe(self, request, *, generate=False):
        context, prepared, key = self.prepare(request)  # Always verify the signed snapshot, including reattachment.
        with self._lock:
            cached = self._cached_locked(key)
            if cached is not None:
                job = ReadingJob()
                job.finish(result=cached)
                return job
            job = self._jobs.get(key)
            if job is not None:
                if job.finished_at is None or (job.error is not None and not generate):
                    return job
                # Success without a valid cache must not bypass replay validation.
                if not generate:
                    return None
            if not generate:
                return None
            job = self._reserve_job_locked(key)
            worker = Thread(target=self._run_job, args=(context, prepared, key, request, job),
                            kwargs={"stream": True}, name="arcana-reading", daemon=True)
            try:
                worker.start()
            except RuntimeError:
                self._pending.discard(key)
                self._jobs.pop(key, None)
                raise EngineError("AI_RATE_LIMITED", "Phần luận AI đang bận. Hãy thử lại sau.", 429) from None
            return job

    def _run_job(self, context, prepared, key, request, job, *, stream=True, propagate_errors=False):
        try:
            result = self._execute_reserved(context, prepared, key, request,
                progress=job.progress, stream=stream, deadline=job.deadline)
        except EngineError as error:
            logging.getLogger("arcana.ai").warning("AI reading failed: method=%s code=%s stream=%s",
                                                   request.method, error.code, stream)
            job.finish(error={"code": error.code, "message": str(error)})
            if propagate_errors:
                raise
        else:
            job.finish(result=result)
            return result

    def execute(self, request):
        context, prepared, key = self.prepare(request)
        with self._lock:
            cached = self._cached_locked(key)
            if cached is not None:
                return cached
            if key in self._pending:
                raise EngineError("AI_BUSY", "Bài luận này đang được viết. Bạn có thể đợi rồi mở lại.", 409)
            job = self._reserve_job_locked(key)
        # Both public entry points consume the upstream stream. This endpoint
        # still returns one validated JSON article to older clients.
        return self._run_job(context, prepared, key, request, job, stream=True, propagate_errors=True)

    def _execute_reserved(self, context, prepared, key, request, *, progress, stream, deadline):
        try:
            if request.method == "BAZI":
                result, cached = self.execute_bazi(context, prepared, key, request, progress=progress, stream=stream, deadline=deadline)
                with self._lock:
                    self._cache[key] = (time.monotonic() + 900, json.dumps(cached, ensure_ascii=False))
                    while len(self._cache) > 32:
                        self._cache.popitem(last=False)
                return result
            # HTTP happens after committing the short reservation transaction.
            messages=prepared["messages"]
            total_usage={}
            for generation_pass in range(1,3):
                progress("WRITING")
                if not isinstance(self.client, CompatibleAIClient):
                    self.state.ai_budget.reserve()
                raw, metadata = (self.client.complete(messages, stream=stream, deadline=deadline)
                                 if isinstance(self.client, CompatibleAIClient) else self.client.complete(messages))
                for token,value in metadata["usage"].items(): total_usage[token]=total_usage.get(token,0)+value
                try:
                    progress("CHECKING")
                    if request.method == "LIUYAO":
                        reading = validate_liuyao_candidate(raw, context)
                    else:
                        reading = validate_reading_prose(validate_response(raw, context))
                        validate_reading_brevity(reading)
                    break
                except ValueError as error:
                    safe_type = (",".join(sorted({i["type"] for i in error.issues})) if isinstance(error, PlainReadingIssues) else
                                 "READING_TOO_LONG" if isinstance(error, VerboseReading) else
                                 "LIUYAO_TOO_MUCH_JARGON" if isinstance(error, JargonReading) else
                                 "UNREADABLE_PROSE" if isinstance(error, UnreadableReading) else
                                 "SCHEMA_OR_REFERENCE_MISMATCH")
                    logging.getLogger("arcana.ai").warning("AI reading validation: method=%s pass=%d type=%s",
                                                           request.method, generation_pass, safe_type)
                    if isinstance(error, VerboseReading):
                        logging.getLogger("arcana.ai").warning("AI reading length: %s", json.dumps(error.fields))
                    elif isinstance(error, PlainReadingIssues):
                        counts = [i for i in error.issues if i["type"] == "READING_TOO_LONG"]
                        if counts:
                            logging.getLogger("arcana.ai").warning("AI reading length: %s", json.dumps(counts))
                    if generation_pass==2:
                        raise EngineError("AI_RESPONSE_UNBOUND", "Bài luận AI chưa đạt kiểm tra định dạng và dẫn chiếu; chưa được hiển thị.", 502) from None
                    # A single fresh pass gets machine-generated validation hints.
                    # Invalid prose is neither displayed nor treated as new facts.
                    issues=(error.issues if isinstance(error, PlainReadingIssues) else
                            [{"type":"READING_TOO_LONG", **issue} for issue in error.fields] if isinstance(error, VerboseReading) else
                            [{"type":"LIUYAO_TOO_MUCH_JARGON", **issue} for issue in error.fields] if isinstance(error, JargonReading) else
                            [{"type":"PROSE_CONTAINS_INTERNAL_NOTATION"}] if isinstance(error, UnreadableReading) else
                            [{"field":list(e["loc"]),"type":e["type"]} for e in error.errors()] if hasattr(error,"errors") else
                            [{"type":"CONTEXT_OR_REFERENCE_MISMATCH"}])
                    hints={"issues":issues,"context_id":context.context_id,"allowed_fact_refs":[f.id for f in context.facts],
                           "allowed_evidence_refs":[e.id for e in context.evidence]}
                    messages=[dict(m) for m in prepared["messages"]]
                    if isinstance(error, PlainReadingIssues) and error.draft.context_id == context.context_id:
                        reading = error.draft
                    if isinstance(error, VerboseReading) or (isinstance(error, PlainReadingIssues) and error.draft.context_id == context.context_id):
                        # Edit the rejected draft with all validation hints at
                        # once. It stays untrusted user data, never source facts;
                        # the edited article must pass every check again.
                        messages=[messages[0], {"role":"user", "content":json.dumps({
                            "editorial_draft":reading.model_dump(mode="json"),
                            "editing_goal":"SHORTEN_WITHOUT_CHANGING_CONDITIONS_OR_REFERENCES"},ensure_ascii=False)},
                            prepared["messages"][-1]]
                    messages[0]["content"] += ("\nLƯỢT KIỂM TRA LẠI: Bản trước chưa đạt định dạng/dẫn chiếu. Viết lại từ cùng context cuối; "
                        "chỉ dùng ID trong danh sách dưới đây, không lấy ID từ các ví dụ. "
                        "Các trường lời luận và giới hạn phải là văn xuôi tiếng Việt: không chèn JSON, khối code, tên trường, mã trạng thái hoặc ID vào câu văn. "
                        "Viết ngắn, không cắt mất điều kiện: summary tối đa 50 từ; đúng 2 đoạn analysis, mỗi đoạn tối đa 70 từ; "
                        "mỗi practical_options tối đa 35 từ; mỗi limits tối đa 30 từ; cả bài tối đa 300 từ, đếm bằng khoảng trắng. "
                        "Lượt này nhắm summary 25–35 từ, mỗi analysis 35–45 từ, chỉ một practical_options 15–25 từ và 1–2 limits ngắn; "
                        "cả bài khoảng 150–190 từ để có khoảng dư dưới giới hạn. "
                        "Nếu có editorial_draft, đó là bản nháp cần rút gọn, không phải nguồn dữ kiện: giữ đúng kết luận, chủ thể, điều kiện và dẫn chiếu; "
                        "gộp ý trùng, bỏ lời giải thích lặp và tuyệt đối không cắt bỏ giới hạn quan trọng để đủ số từ. "
                        "Thông tin kiểm tra của ứng dụng: "+json.dumps(hints,ensure_ascii=False))
            try:
                result = AIReadingResult(reading_id=key, consultation_id=request.consultation_id, method=request.method,
                    created_at=datetime.now(timezone.utc), model_requested=self.config.model, model_returned=metadata["model"],
                    provider_host=self.config.public_status()["provider_host"], prompt_version=prepared["pack_version"],
                    case_ids=prepared["case_ids"], context_sha256=digest(context.model_dump(mode="json")), usage=total_usage,generation_passes=generation_pass,
                    context=context, reading=reading).model_dump(mode="json")
            except (ValueError, TypeError, KeyError):
                raise EngineError("AI_RESPONSE_UNBOUND", "Bài luận AI chưa đạt kiểm tra định dạng và dẫn chiếu; chưa được hiển thị.", 502) from None
            with self._lock:
                self._cache[key] = (time.monotonic() + 900, json.dumps(result, ensure_ascii=False))
                while len(self._cache) > 32:
                    self._cache.popitem(last=False)
            return result
        except Exception as exc:
            if isinstance(exc, EngineError):
                raise
            raise EngineError("AI_FAILED", "Chưa hoàn tất phần luận AI. Dữ liệu của phiên vẫn được giữ.", 502) from None
        finally:
            with self._lock:
                self._pending.discard(key)
