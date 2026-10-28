"""Shared, cached AI prose on top of immutable Bazi/Mai Hoa/Liu Yao snapshots."""
from datetime import datetime, timezone
from collections import OrderedDict
from hashlib import sha256
import json
import time
from typing import Literal
from uuid import UUID
from threading import Lock

from pydantic import Field, model_validator

from research_tools.interpretation_prompt import Context, Response, build_messages, validate_response, PACK
from .ai_client import AIConfig, CompatibleAIClient
from .ai_context import natal_context, maihoa_context, liuyao_context
from .date_ai_context import DateReadingContext, date_context
from research_tools.date_interpretation_prompt import build_date_messages, DATE_PACK
from .bazi_models import BaziReadingSnapshot
from .engine import EngineError
from .liuyao_analysis import digest
from .liuyao_models import AnalysisContext
from .models import StrictModel
from .reading_display import UnreadableReading, validate_reading_prose
from .snapshots import SignedSnapshot


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
    generation_passes: int = Field(default=1, ge=1, le=2)
    context: Context | DateReadingContext
    reading: Response

    @model_validator(mode="after")
    def bind(self):
        validate_response(self.reading, self.context)
        validate_reading_prose(self.reading)
        if (self.method == "DATE") != (self.context.method == "DATE_SELECTION"):
            raise ValueError("Date reading method does not match its context")
        if str(self.consultation_id) != self.context.context_id or digest(self.context.model_dump(mode="json")) != self.context_sha256:
            raise ValueError("AI response is not bound to the saved consultation")
        return self


class AIReadingService:
    def __init__(self, app_state, config=None, client=None):
        self.state = app_state
        self.config = config if config is not None else AIConfig.load()
        self.client = client if client is not None else CompatibleAIClient(self.config)
        self._cache = OrderedDict()
        self._pending = set()
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
        prepared = build_date_messages(context, limit=2) if request.method == "DATE" else build_messages(context, limit=2)
        pack = DATE_PACK if request.method == "DATE" else PACK
        key = digest({"context": context.model_dump(mode="json"), "model": self.config.model, "endpoint": self.config.base_url,
                      "pack_sha256": sha256((pack / "manifest.json").read_bytes()).hexdigest(), "case_ids": prepared["case_ids"],
                      "messages_sha256": prepared["messages_sha256"], "ai_service": "ai-reading-v1"})
        return context, prepared, key

    def lookup(self, request):
        _, _, key = self.prepare(request)
        with self._lock:
            row = self._cache.get(key)
        if row and row[0] > time.monotonic():
            try:
                return AIReadingResult.model_validate_json(row[1]).model_dump(mode="json")
            except ValueError:
                # Old cached prose containing machine notation must not reach the UI.
                return None
        return None

    def execute(self, request):
        context, prepared, key = self.prepare(request)
        with self._lock:
            now = time.monotonic()
            for expired in [k for k, v in self._cache.items() if v[0] <= now]:
                del self._cache[expired]
            row = self._cache.get(key)
            if row:
                try:
                    return AIReadingResult.model_validate_json(row[1]).model_dump(mode="json")
                except ValueError:
                    pass  # A user-requested retry can replace unreadable legacy prose.
            if key in self._pending:
                raise EngineError("AI_BUSY", "Bài luận này đang được viết. Bạn có thể đợi rồi mở lại.", 409)
            if len(self._pending) >= self.state.security.ai_concurrency:
                raise EngineError("AI_RATE_LIMITED", "Phần luận AI đang bận. Hãy thử lại sau.", 429)
            if not self.config.configured:
                raise EngineError("AI_NOT_CONFIGURED", "Chưa cấu hình dịch vụ luận giải AI ở máy chủ.", 503)
            self._pending.add(key)
        try:
            # HTTP happens after committing the short reservation transaction.
            messages=prepared["messages"]
            total_usage={}
            for generation_pass in range(1,3):
                if not isinstance(self.client, CompatibleAIClient):
                    self.state.ai_budget.reserve()
                raw, metadata = self.client.complete(messages)
                for token,value in metadata["usage"].items(): total_usage[token]=total_usage.get(token,0)+value
                try:
                    reading = validate_reading_prose(validate_response(raw, context))
                    break
                except ValueError as error:
                    if generation_pass==2:
                        raise EngineError("AI_RESPONSE_UNBOUND", "Bài luận AI chưa đạt kiểm tra định dạng và dẫn chiếu; chưa được hiển thị.", 502) from None
                    # A single fresh pass gets machine-generated validation hints.
                    # Invalid prose is neither displayed nor treated as new facts.
                    issues=([{"type":"PROSE_CONTAINS_INTERNAL_NOTATION"}] if isinstance(error, UnreadableReading) else
                            [{"field":list(e["loc"]),"type":e["type"]} for e in error.errors()] if hasattr(error,"errors") else
                            [{"type":"CONTEXT_OR_REFERENCE_MISMATCH"}])
                    hints={"issues":issues,"context_id":context.context_id,"allowed_fact_refs":[f.id for f in context.facts],
                           "allowed_evidence_refs":[e.id for e in context.evidence]}
                    messages=[dict(m) for m in prepared["messages"]]
                    messages[0]["content"] += ("\nLƯỢT KIỂM TRA LẠI: Bản trước chưa đạt định dạng/dẫn chiếu. Viết lại từ cùng context cuối; "
                        "chỉ dùng ID trong danh sách dưới đây, không lấy ID từ các ví dụ. "
                        "Các trường lời luận và giới hạn phải là văn xuôi tiếng Việt: không chèn JSON, khối code, tên trường, mã trạng thái hoặc ID vào câu văn. "
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
