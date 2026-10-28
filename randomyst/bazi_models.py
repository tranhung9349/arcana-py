"""Contracts for independent, source-bound natal readings."""
from datetime import datetime
from hashlib import sha256
from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from .models import Element, StrictModel, civil_validator

Topic = Literal["GENERAL", "CAREER", "WEALTH", "STUDY", "RELATIONSHIPS"]
God = Literal["DAY_MASTER", "PEER", "ROB_WEALTH", "EATING_GOD", "HURTING_OFFICER",
              "INDIRECT_WEALTH", "DIRECT_WEALTH", "SEVEN_KILLINGS", "DIRECT_OFFICER",
              "INDIRECT_RESOURCE", "DIRECT_RESOURCE"]
PillarName = Literal["year", "month", "day", "hour"]


class BaziBirth(StrictModel):
    civil_datetime: datetime
    clock_uncertainty_seconds: float | None = Field(default=None, ge=0, le=86400)

    @field_validator("civil_datetime")
    @classmethod
    def valid_birth(cls, value):
        civil_validator(value)
        if not 1950 <= value.year <= 2026 or value.microsecond:
            raise ValueError("Ngày sinh phải trong 1950–2026, độ phân giải đến giây.")
        return value


class ReadingContext(StrictModel):
    topic: Topic = "GENERAL"
    question: str = Field(default="", max_length=2000)

    @field_validator("question", mode="before")
    @classmethod
    def trim_question(cls, value):
        return value.strip() if isinstance(value, str) else value


class BaziRequest(ReadingContext):
    request_id: UUID
    display_name: str = Field(default="", max_length=80)
    birth: BaziBirth

    @field_validator("display_name", mode="before")
    @classmethod
    def trim_name(cls, value):
        return value.strip() if isinstance(value, str) else value


class BaziReadingRequest(ReadingContext):
    reading_id: UUID


class StemFact(StrictModel):
    fact_id: str
    index: int = Field(ge=0, le=9)
    name: str
    zh: str
    element: Element
    polarity: Literal["Dương", "Âm"]
    ten_god: God
    ten_god_name: str


class NatalPillar(StrictModel):
    fact_id: str
    position: PillarName
    label: str
    stem: StemFact
    branch_index: int = Field(ge=0, le=11)
    branch: str
    branch_zh: str
    branch_element: Element
    hidden_stems: list[StemFact] = Field(min_length=1, max_length=3)


class NatalMonth(StrictModel):
    fact_id: Literal["facts:season"] = "facts:season"
    branch: str
    branch_index: int = Field(ge=0, le=11)
    element: Element
    jie_name: str
    jie_start_beijing: datetime
    seasonal_support: bool


class NatalChart(StrictModel):
    civil_datetime: datetime
    beijing_datetime: datetime
    provider: Literal["lunar-python-1.4.8"]
    sect: Literal[1]
    day_boundary: Literal["23:00_BEIJING"]
    pillars: list[NatalPillar] = Field(min_length=4, max_length=4)
    month: NatalMonth

    @model_validator(mode="after")
    def ordered(self):
        if [p.position for p in self.pillars] != ["year", "month", "day", "hour"]:
            raise ValueError("Natal pillars must be ordered year/month/day/hour")
        if self.pillars[2].stem.ten_god != "DAY_MASTER":
            raise ValueError("Day stem must be labelled Nhật chủ")
        if self.month.branch_index != self.pillars[1].branch_index:
            raise ValueError("Month facts must match the month pillar")
        return self


class RootFact(StrictModel):
    fact_id: str
    pillar: PillarName
    stem_ref: str
    stem: str
    level: Literal["MAIN_QI", "OTHER_QI"]


class NatalRelation(StrictModel):
    fact_id: str
    kind: Literal["STEM_COMBINATION", "SIX_COMBINATION", "CLASH", "THREE_COMBINATION",
                  "THREE_MEETING", "HARM", "PUNISHMENT", "SELF_PUNISHMENT"]
    name: str
    pillar_refs: list[str] = Field(min_length=2, max_length=4)
    tokens: list[str] = Field(min_length=1, max_length=3)
    evidence_id: str
    transformation_assumed: Literal[False] = False


class ElementCount(StrictModel):
    element: Element
    visible_stems: int = Field(ge=0, le=4)
    hidden_occurrences: int = Field(ge=0, le=12)


class NatalFacts(StrictModel):
    roots: list[RootFact]
    visible_support_refs: list[str]
    visible_drain_refs: list[str]
    resource_refs: list[str]
    relations: list[NatalRelation]
    distribution: list[ElementCount] = Field(min_length=5, max_length=5)


class BaziEvidence(StrictModel):
    evidence_id: str
    kind: Literal["PRIMARY_TEXT", "PROVIDER", "PRODUCT_POLICY"]
    title: str
    text: str
    url: str | None = None
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator("url")
    @classmethod
    def source_url(cls, value):
        if value is not None and not value.startswith(("https://github.com/", "https://zh.wikisource.org/w/index.php?oldid=")):
            raise ValueError("Unsupported evidence URL")
        return value

    @model_validator(mode="after")
    def text_hash(self):
        if sha256(self.text.encode()).hexdigest() != self.sha256:
            raise ValueError("Bazi evidence hash mismatch")
        return self


class BaziFinding(StrictModel):
    finding_id: str
    rule_id: str
    title: str
    text: str
    state: Literal["SUPPORTED", "CONDITIONAL", "UNRESOLVED"]
    fact_refs: list[str] = Field(min_length=1)
    evidence_refs: list[str] = Field(min_length=1)


class StructureCandidate(StrictModel):
    name: str
    ten_god: God
    hidden_stem_ref: str
    exposed_refs: list[str]
    state: Literal["CONDITIONAL"] = "CONDITIONAL"


class BalanceDirection(StrictModel):
    state: Literal["CONDITIONAL", "UNRESOLVED"]
    preferred: list[Element]
    supporting: list[Element]
    restrain: list[Element]


class NatalAssessment(StrictModel):
    strength: Literal["STRONG", "WEAK", "MIXED"]
    strength_name: str
    possible_following: bool
    structures: list[StructureCandidate]
    balance: BalanceDirection
    climate_element: Element | None
    climate_conflict: bool


class NatalSection(StrictModel):
    title: str
    text: str
    finding_refs: list[str] = Field(min_length=1)


class NatalReading(StrictModel):
    topic: Topic
    topic_name: str
    question: str
    title: str
    summary: str
    highlights: list[str] = Field(min_length=3, max_length=5)
    sections: list[NatalSection] = Field(min_length=5)
    narrative_version: str


class CoverageItem(StrictModel):
    feature: str
    status: Literal["SUPPORTED", "PARTIAL", "DEFERRED"]
    detail: str


class BaziResponse(StrictModel):
    schema_version: Literal["bazi-consultation-v1"]
    request_id: UUID
    created_at: datetime
    display_name: str
    analysis_profile: Literal["bazi_natal_v1"]
    rules_version: str
    corpus_version: str
    rules_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    calendar_policy: Literal["VN_INSTANT_TO_BEIJING_SECT1"]
    chart: NatalChart
    facts: NatalFacts
    assessment: NatalAssessment
    findings: list[BaziFinding] = Field(min_length=5)
    reading: NatalReading
    evidence: list[BaziEvidence] = Field(min_length=1)
    coverage: list[CoverageItem]
    model_called: Literal[False] = False
    review_status: Literal["RULES_TESTED_NOT_EXPERT_REVIEWED"] = "RULES_TESTED_NOT_EXPERT_REVIEWED"

    @model_validator(mode="after")
    def references(self):
        evidence_ids = [e.evidence_id for e in self.evidence]
        finding_ids = [f.finding_id for f in self.findings]
        facts = ["facts:season", "facts:distribution"]
        for p in self.chart.pillars:
            facts += [p.fact_id, p.stem.fact_id, *[h.fact_id for h in p.hidden_stems]]
        facts += [r.fact_id for r in self.facts.roots] + [r.fact_id for r in self.facts.relations]
        for values in (facts, evidence_ids, finding_ids):
            if len(values) != len(set(values)):
                raise ValueError("Duplicate Bazi reference IDs")
        for f in self.findings:
            if not set(f.fact_refs) <= set(facts) or not set(f.evidence_refs) <= set(evidence_ids):
                raise ValueError("Unbound Bazi finding")
        if any(not set(s.finding_refs) <= set(finding_ids) for s in self.reading.sections):
            raise ValueError("Unbound Bazi reading section")
        if not set(self.reading.highlights) <= set(finding_ids):
            raise ValueError("Unbound Bazi highlights")
        for r in self.facts.relations:
            if not set(r.pillar_refs) <= set(facts) or r.evidence_id not in evidence_ids:
                raise ValueError("Unbound Bazi relation")
        for r in self.facts.roots:
            if r.stem_ref not in facts:
                raise ValueError("Unbound Bazi root")
        for refs in (self.facts.visible_support_refs, self.facts.visible_drain_refs, self.facts.resource_refs):
            if not set(refs) <= set(facts):
                raise ValueError("Unbound natal support facts")
        for s in self.assessment.structures:
            if s.hidden_stem_ref not in facts or not set(s.exposed_refs) <= set(facts):
                raise ValueError("Unbound structure candidate")
        return self


class BaziReadingSnapshot(StrictModel):
    reading_id: UUID
    consultation_id: UUID
    created_at: datetime
    analysis_rules_version: str
    chart_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    reading: NatalReading
