"""A consultation is independent of number draws and auspicious-date scores."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from .models import Casting, HexagramExplanation, StrictModel

Topic = Literal["GENERAL", "WEALTH", "TRADE", "PLANNING", "MARRIAGE", "TRAVEL"]
Relation = Literal["SAME", "USE_GENERATES_BODY", "BODY_CONTROLS_USE", "BODY_GENERATES_USE", "USE_CONTROLS_BODY"]


class MaiHoaRequest(StrictModel):
    request_id: UUID
    question: str = Field(min_length=5, max_length=2000)
    topic: Topic = "GENERAL"
    casting: Casting

    @field_validator("question", mode="before")
    @classmethod
    def clean_question(cls, value):
        return value.strip() if isinstance(value, str) else value


class Hexagram(StrictModel):
    hexagram_id: int = Field(ge=1, le=64)
    name_zh: str
    symbol: str
    lines_bottom_to_top: list[Literal[0, 1]] = Field(min_length=6, max_length=6)


class Trigram(StrictModel):
    trigram: int = Field(ge=1, le=8)
    name: str
    element: str
    position: Literal["UPPER", "LOWER"]
    strength: Literal["STRONG", "WEAK", "NOT_SPECIFIED"]


class MaiHoaChart(StrictModel):
    core_version: Literal["maihoa-ymdh-source-v2"]
    variables: dict[str, int]
    upper: int = Field(ge=1, le=8)
    lower: int = Field(ge=1, le=8)
    moving_line: int = Field(ge=1, le=6)
    mutual_basis: Literal["ORIGINAL", "CHANGED_FOR_PURE"]
    original: Hexagram
    mutual: Hexagram
    changed: Hexagram
    the: Trigram
    dung: Trigram
    mutual_body: Trigram
    mutual_use: Trigram
    changed_use: Trigram


class MaiHoaSource(StrictModel):
    path: str
    title: str
    revision_id: int = Field(gt=0)
    timestamp: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    url: str

    @model_validator(mode="after")
    def pinned_url(self):
        if self.url != f"https://zh.wikisource.org/w/index.php?oldid={self.revision_id}":
            raise ValueError("Mai Hoa evidence must identify the pinned revision")
        return self


class MaiHoaEvidence(StrictModel):
    evidence_id: str
    title: str
    text: str = Field(min_length=1)
    text_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    section_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    section: str
    volume: int = Field(ge=1, le=3)
    source: MaiHoaSource

    @model_validator(mode="after")
    def text_binding(self):
        from hashlib import sha256
        if sha256(self.text.encode()).hexdigest() != self.text_sha256:
            raise ValueError("Mai Hoa quotation hash mismatch")
        return self


class MaiHoaFinding(StrictModel):
    rule_id: str
    phase: Literal["BEGINNING", "MIDDLE_BODY", "MIDDLE_USE", "ENDING"]
    title: str
    relation: Relation
    indication: Literal["FAVOURABLE", "CAUTION"]
    text_vi: str
    translation_status: Literal["AI_DRAFT_UNREVIEWED"]
    evidence_refs: list[str] = Field(min_length=1)


class MaiHoaResponse(StrictModel):
    schema_version: Literal["maihoa-consultation-v1"]
    request_id: UUID
    created_at: datetime
    rules_version: str
    corpus_version: str
    question: str
    topic: Topic
    topic_name: str
    calendar: dict
    calendar_policy: dict
    season: dict
    chart: MaiHoaChart
    findings: list[MaiHoaFinding] = Field(min_length=4, max_length=4)
    summary: dict
    evidence: list[MaiHoaEvidence]
    texts: dict[str, HexagramExplanation]
    warnings: list[dict]
    limitations: list[str]
    automated_scope: Literal["INTERNAL_TRIGRAM_RELATIONS"]
    interpretation_review_status: Literal["AI_DRAFT_UNREVIEWED"]

    @model_validator(mode="after")
    def references_present(self):
        ids = [e.evidence_id for e in self.evidence]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate Mai Hoa evidence")
        for finding in self.findings:
            if not set(finding.evidence_refs).issubset(ids):
                raise ValueError("Unbound Mai Hoa finding")
        return self
