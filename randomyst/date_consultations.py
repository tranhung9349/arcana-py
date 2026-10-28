"""Persist one selected date, with the rules used, before requesting AI prose."""
from datetime import datetime, timezone
import json
from typing import Literal
from uuid import UUID

from pydantic import model_validator

from .date_models import DateSearchRequest, DateSearchResponse
from .date_reading import explain_day
from .engine import EngineError
from .liuyao_analysis import digest
from .models import StrictModel


class DateConsultationRequest(StrictModel):
    request_id: UUID
    search: DateSearchRequest

    @model_validator(mode="after")
    def selected_day(self):
        if self.search.date_range.start != self.search.date_range.end:
            raise ValueError("Chọn một ngày cụ thể để đọc lời luận.")
        if self.search.date_range.start.weekday() not in self.search.allowed_weekdays:
            raise ValueError("Ngày cần luận nằm ngoài lịch đã chọn.")
        return self


class DateExplanation(StrictModel):
    version: Literal["date-explanation-v1"]
    summary: str
    focus_start_at: str
    focus_end_at: str
    reasons: list[str]
    cautions: list[str]


class DateConsultation(StrictModel):
    schema_version: Literal["date-consultation-v1"] = "date-consultation-v1"
    request_id: UUID
    created_at: datetime
    result: DateSearchResponse
    scoring: dict
    rules_sha256: str
    explanation: DateExplanation


class DateConsultationStore:
    def __init__(self, store):
        self.store = store
        with store.connect() as con:
            con.execute("CREATE TABLE IF NOT EXISTS date_consultations (request_id TEXT PRIMARY KEY, payload_hash TEXT NOT NULL, response TEXT NOT NULL)")

    def execute(self, payload, engine):
        key, hashed = str(payload.request_id), digest(payload.search.model_dump(mode="json"))
        with self.store.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute("SELECT payload_hash, response FROM date_consultations WHERE request_id=?", (key,)).fetchone()
            if row:
                if row[0] != hashed:
                    raise EngineError("REQUEST_ID_CONFLICT", "Mã ngày đã dùng với hồ sơ hoặc bộ lọc khác. Hãy mở lại ngày.", 409)
                return json.loads(row[1])
            result = engine.search(payload.search.model_copy(update={"include_details": True}))
            config = engine.evaluator.config
            scoring = (config.day_scoring if result["evaluation_mode"] == "DAY_ONLY" else config.scoring).model_dump()
            saved = DateConsultation(request_id=key, created_at=datetime.now(timezone.utc), result=result,
                scoring=scoring, rules_sha256=digest(config.model_dump(mode="json")),
                explanation=explain_day(result, scoring)).model_dump(mode="json")
            con.execute("INSERT INTO date_consultations VALUES (?, ?, ?)", (key, hashed, json.dumps(saved, ensure_ascii=False)))
            return saved

    def get(self, request_id):
        with self.store.connect() as con:
            row = con.execute("SELECT response FROM date_consultations WHERE request_id=?", (str(request_id),)).fetchone()
        if not row:
            raise EngineError("DATE_CONSULTATION_NOT_FOUND", "Hãy mở một ngày để tải căn cứ trước khi đọc lời luận AI.", 404)
        return json.loads(row[0])
