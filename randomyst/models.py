from datetime import datetime, timedelta
from typing import Literal
from uuid import UUID
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Element = Literal["Mộc", "Hỏa", "Thổ", "Kim", "Thủy"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Location(StrictModel):
    longitude: float = Field(ge=-180, le=180)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    source: Literal["MANUAL", "DEVICE", "IP", "DEFAULT"] = "MANUAL"
    accuracy_m: float | None = Field(default=None, ge=0)
    longitude_uncertainty_degrees: float | None = Field(default=None, ge=0, le=180)
    acquired_at: datetime | None = None
    fallback_reason: str | None = Field(default=None, max_length=200)

    @field_validator("acquired_at")
    @classmethod
    def aware_timestamp(cls, value):
        if value is not None and value.utcoffset() is None:
            raise ValueError("acquired_at requires a timezone")
        return value

    @model_validator(mode="after")
    def source_fields(self):
        if self.source == "DEFAULT" and self.longitude != 105:
            raise ValueError("DEFAULT location must use 105°E")
        if self.source in ("DEVICE", "IP") and self.acquired_at is None:
            raise ValueError("Automatic locations require acquired_at")
        if self.source == "DEVICE" and self.accuracy_m is None:
            raise ValueError("Device location requires coords.accuracy")
        return self


def civil_validator(value):
    if value.utcoffset() != timedelta(hours=7):
        raise ValueError("Civil datetime must explicitly use UTC+7")
    return value


class Birth(StrictModel):
    civil_datetime: datetime
    location: Location | None = None
    clock_uncertainty_seconds: float | None = Field(default=None, ge=0, le=86400)
    override_dung_than: Element | None = None

    @field_validator("civil_datetime")
    @classmethod
    def valid_birth(cls, value):
        civil_validator(value)
        if not 1950 <= value.year <= 2026:
            raise ValueError("Birth year must be 1950–2026")
        return value


class Casting(StrictModel):
    mode: Literal["CURRENT", "CUSTOM"] = "CURRENT"
    clicked_at: datetime | None = None
    custom_timestamp: datetime | None = None
    location: Location | None = None
    clock_uncertainty_seconds: float | None = Field(default=None, ge=0, le=86400)

    @field_validator("clicked_at", "custom_timestamp")
    @classmethod
    def valid_casting(cls, value):
        if value is not None:
            civil_validator(value)
            if not 2024 <= value.year <= 2030:
                raise ValueError("Casting year must be 2024–2030")
        return value

    @model_validator(mode="after")
    def timestamp_choice(self):
        if self.mode == "CURRENT" and (self.clicked_at is None or self.custom_timestamp is not None):
            raise ValueError("CURRENT requires clicked_at only")
        if self.mode == "CUSTOM" and (self.custom_timestamp is None or self.clicked_at is not None):
            raise ValueError("CUSTOM requires custom_timestamp only")
        return self


class DrawRequest(StrictModel):
    request_id: UUID
    birth: Birth
    casting: Casting


class DrawResponse(StrictModel):
    schema_version: Literal["draw-response-v1", "draw-response-v2"]
    request_id: UUID
    rules_version: str
    numbers: list[Annotated[str, Field(pattern=r"^[0-9]{2}$")]] = Field(min_length=6, max_length=6)
    status: Literal["OPTIMAL", "SUB_OPTIMAL"]
    score: float = Field(ge=0, le=100)
    threshold: Literal[70, 75, 80, 85]
    attempts: int = Field(ge=1, le=5)
    selected_attempt: int = Field(ge=1, le=5)
    warnings: list[dict]
    disclaimer: str
    trace: dict

    @model_validator(mode="after")
    def unique_result(self):
        if len(set(self.numbers)) != 6 or self.numbers != sorted(self.numbers):
            raise ValueError("Six distinct sorted numbers required")
        if self.selected_attempt > self.attempts:
            raise ValueError("Selected attempt was not executed")
        return self


class SourceReference(StrictModel):
    repository: Literal["john-walks-slow/open-iching", "vhphuoc1102/tinix-bazi"]
    commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    path: str
    key: str
    url: str


class SourceTranslation(StrictModel):
    label: Literal["AI_TRANSLATION"]
    language: Literal["vi"]
    text: str = Field(min_length=1)
    review_status: Literal["UNREVIEWED"]
    version: str
    references: list[str] = Field(min_length=1, max_length=1)
    source_text_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class SourceCard(StrictModel):
    evidence_id: str
    title: str
    text_type: str
    language: Literal["zh", "vi"]
    label: Literal["SOURCE_ORIGINAL"]
    text: str = Field(min_length=1)
    source: SourceReference
    translation: SourceTranslation | None

    @model_validator(mode="after")
    def translation_binding(self):
        import hashlib
        if self.translation is not None:
            if self.translation.references != [self.evidence_id] or self.language != "zh":
                raise ValueError("Translation must reference its exact Hán evidence")
            if self.translation.source_text_sha256 != hashlib.sha256(self.text.encode()).hexdigest():
                raise ValueError("Translation/source text hash mismatch")
        expected = f"https://github.com/{self.source.repository}/blob/{self.source.commit}/{self.source.path}"
        if self.source.url != expected:
            raise ValueError("Source URL must point to the pinned repository file")
        return self


class SourceOverview(StrictModel):
    label: Literal["AI_INTERPRETATION"]
    language: Literal["vi"]
    text: str
    review_status: Literal["UNREVIEWED"]
    references: list[str]


class HexagramExplanation(StrictModel):
    hexagram_id: int = Field(ge=1, le=64)
    name_zh: str
    name_vi: str
    symbol: str
    moving_line: int | None = Field(ge=1, le=6)
    overview: SourceOverview
    cards: list[SourceCard]
    source_gaps: list[dict]

    @model_validator(mode="after")
    def references_present(self):
        ids = [c.evidence_id for c in self.cards]
        if len(set(ids)) != len(ids) or not set(self.overview.references).issubset(ids):
            raise ValueError("Overview references must identify unique evidence")
        return self


class BaziExplanation(StrictModel):
    day_master: str
    structure: str
    strength: str
    primary_used: Element
    primary_calculated: Element
    overridden: bool
    dung_than: list[Element]
    hy_than: list[Element]
    ky_than: list[Element]
    birth_season: str
    cards: list[SourceCard]
    source_gaps: list[dict]


class DisplayExplanations(StrictModel):
    mutual: HexagramExplanation | None
    changed: HexagramExplanation | None


class ReadingEvidence(StrictModel):
    evidence_id: str
    kind: Literal["SOURCE_ORIGINAL", "SAVED_FACT", "IMPLEMENTATION_RULE"]
    title: str
    text: str
    url: str | None = None

    @field_validator("url")
    @classmethod
    def source_url(cls, value):
        if value is not None and not value.startswith(("https://github.com/", "https://zh.wikisource.org/w/index.php?oldid=")):
            raise ValueError("Reading evidence must link to a supported source")
        return value


class ReadingSection(StrictModel):
    title: str
    text: str = Field(min_length=1)
    references: list[str] = Field(min_length=1)


class ModuleReading(StrictModel):
    module: Literal["BAZI", "MAIHOA"]
    version: str
    title: str
    summary: str
    sections: list[ReadingSection] = Field(min_length=1)
    evidence: list[ReadingEvidence] = Field(min_length=1)
    facts: dict
    limitations: list[str]
    provenance: Literal["RULE_BASED_INTERPRETATION"] = "RULE_BASED_INTERPRETATION"

    @model_validator(mode="after")
    def bound_sections(self):
        ids = [row.evidence_id for row in self.evidence]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate reading evidence")
        if any(not set(row.references).issubset(ids) for row in self.sections):
            raise ValueError("Reading section has missing evidence")
        return self


class DrawDeepReadings(StrictModel):
    bazi: ModuleReading
    maihoa: ModuleReading

    @model_validator(mode="after")
    def correct_modules(self):
        if self.bazi.module != "BAZI" or self.maihoa.module != "MAIHOA":
            raise ValueError("Deep reading modules do not match their slots")
        return self


class SourceExplanation(StrictModel):
    schema_version: Literal["source-explanation-v1", "source-explanation-v2"]
    context_id: UUID
    rules_version: str
    corpus_version: str
    model_called: Literal[False]
    affects_generation: Literal[False]
    affects_evaluation: Literal[False]
    original: HexagramExplanation
    bazi: BaziExplanation
    display_hexagrams: DisplayExplanations
    relation: dict
    limitations: list[str]
    disclaimer: str
    readings: DrawDeepReadings | None = None

    @model_validator(mode="after")
    def v2_readings(self):
        if self.schema_version == "source-explanation-v2" and self.readings is None:
            raise ValueError("Explanation v2 requires both interpretation modules")
        return self
