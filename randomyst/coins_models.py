"""Three coins, six throws, ordered from the lowest line upward."""
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from .models import Casting, HexagramExplanation, SourceCard, StrictModel

CoinFace = Literal["BACK", "INSCRIPTION"]
Throw = Annotated[list[CoinFace], Field(min_length=3, max_length=3)]


class CoinRequest(StrictModel):
    request_id: UUID
    question: str = Field(min_length=5, max_length=2000)
    source: Literal["RANDOM", "MANUAL"] = "RANDOM"
    casting: Casting
    throws_bottom_to_top: list[Throw] | None = Field(default=None, min_length=6, max_length=6)

    @field_validator("question", mode="before")
    @classmethod
    def clean_question(cls, value):
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def source_fields(self):
        if self.source == "MANUAL" and self.throws_bottom_to_top is None:
            raise ValueError("Nhập đủ sáu lượt, mỗi lượt ba mặt đồng tiền.")
        if self.source == "RANDOM" and self.throws_bottom_to_top is not None:
            raise ValueError("Gieo trên app không nhận kết quả đồng tiền nhập sẵn.")
        return self


class CoinHexagram(StrictModel):
    hexagram_id: int = Field(ge=1, le=64)
    name_zh: str
    name_vi: str
    symbol: str
    lines_bottom_to_top: list[Literal[0, 1]] = Field(min_length=6, max_length=6)
    lower_trigram: str
    upper_trigram: str


class CoinReading(StrictModel):
    schema_version: Literal["coin-reading-v1"]
    corpus_version: str
    chart: CoinHexagram
    text: HexagramExplanation
    reference_lines: list[SourceCard] = Field(min_length=6, max_length=6)
    interpretation_review_status: Literal["AI_DRAFT_UNREVIEWED"]

    @model_validator(mode="after")
    def consistent_reading(self):
        if self.chart.hexagram_id != self.text.hexagram_id or self.text.moving_line is not None:
            raise ValueError("Reading must match its hexagram; moving positions are stored separately")
        expected = [f"iching__{self.chart.hexagram_id}_{i}__line_text" for i in range(1, 7)]
        if [card.evidence_id for card in self.reference_lines] != expected:
            raise ValueError("Reference lines must match their hexagram in bottom-to-top order")
        return self


class CoinCasting(StrictModel):
    method: Literal["THREE_COINS_SIX_THROWS"]
    source: Literal["RANDOM", "MANUAL"]
    throws_bottom_to_top: list[Throw] = Field(min_length=6, max_length=6)
    totals_bottom_to_top: list[Literal[6, 7, 8, 9]] = Field(min_length=6, max_length=6)
    convention: str
    randomness: Literal["SYSTEM_SECRETS", "USER_SUPPLIED"]


class NaJiaLine(StrictModel):
    position: int = Field(ge=1, le=6)
    stem: str
    branch: str
    branch_zh: str
    element: str
    relative: str
    spirit: str
    is_world: bool
    is_response: bool
    moving: bool
    void: bool
    month_clash: bool
    changed_stem: str | None
    changed_branch: str | None
    changed_element: str | None
    changed_relative: str | None


class NaJiaChart(StrictModel):
    palace: str
    palace_element: str
    stage: str
    world_line: int = Field(ge=1, le=6)
    response_line: int = Field(ge=1, le=6)
    void_branches: list[str] = Field(min_length=2, max_length=2)
    lines_bottom_to_top: list[NaJiaLine] = Field(min_length=6, max_length=6)
    scope: Literal["BASIC_NAJIA_CHART"]


class CoinResponse(StrictModel):
    schema_version: Literal["coin-consultation-v1"]
    request_id: UUID
    created_at: datetime
    rules_version: str
    question: str
    casting: CoinCasting
    calendar: dict
    original: CoinReading
    changed: CoinReading | None
    moving_lines: list[Literal[1, 2, 3, 4, 5, 6]]
    najia: NaJiaChart
    reading_guide: list[str]
    limitations: list[str]
    sources: list[dict]

    @model_validator(mode="after")
    def casting_matches_chart(self):
        totals = [sum(3 if face == "BACK" else 2 for face in row) for row in self.casting.throws_bottom_to_top]
        bits = [v % 2 for v in totals]
        moving = [i for i, v in enumerate(totals, 1) if v in (6, 9)]
        if totals != self.casting.totals_bottom_to_top or bits != self.original.chart.lines_bottom_to_top or moving != self.moving_lines:
            raise ValueError("Coin throws do not match the saved chart")
        changed = [bit ^ (i in moving) for i, bit in enumerate(bits, 1)]
        if bool(moving) != (self.changed is not None) or (self.changed and changed != self.changed.chart.lines_bottom_to_top):
            raise ValueError("Changed chart must flip exactly the moving lines")
        expected = "SYSTEM_SECRETS" if self.casting.source == "RANDOM" else "USER_SUPPLIED"
        if self.casting.randomness != expected:
            raise ValueError("Coin provenance does not match the source")
        return self
