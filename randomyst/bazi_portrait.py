"""Whole-life reading contracts; periods stay bound to saved engine cycles."""
import json
from typing import Literal

from pydantic import Field

from .models import StrictModel

Area = Literal["CAREER", "FINANCES", "RELATIONSHIPS"]
AREA_TITLES = {"CAREER": "Sự nghiệp và đường phát triển", "FINANCES": "Tài chính và tích lũy",
               "RELATIONSHIPS": "Tình cảm, quan hệ và gia đình"}


class PortraitClaim(StrictModel):
    id: str
    status: Literal["SUPPORTED", "LIMITED"]
    text: str = Field(min_length=1, max_length=2400)
    opportunity: str = Field(min_length=1, max_length=1000)
    challenge: str = Field(min_length=1, max_length=1000)
    condition: str = Field(min_length=1, max_length=1000)
    limit: str = Field(min_length=1, max_length=1000)
    fact_refs: list[str] = Field(min_length=2, max_length=20)
    evidence_refs: list[str] = Field(min_length=1, max_length=12)


class PortraitArea(PortraitClaim):
    area: Area


class PortraitPeriodKey(StrictModel):
    id: str = Field(pattern=r"^V0[1-3]$")
    cycle_indices: list[int] = Field(min_length=1, max_length=3)
    start_year: int
    end_year: int
    start_age: int
    end_age: int


class PortraitPeriod(PortraitClaim, PortraitPeriodKey):
    pass


class WholeLifeAnalysis(StrictModel):
    overview: PortraitClaim
    areas: list[PortraitArea] = Field(min_length=3, max_length=3)
    periods: list[PortraitPeriod] = Field(max_length=3)
    timing_status: Literal["AVAILABLE", "NOT_AVAILABLE"]
    timing_note: str = Field(min_length=1, max_length=1000)


class PortraitAreaText(StrictModel):
    source_id: str
    area: Area
    text: str = Field(min_length=1, max_length=9000)


class PortraitPeriodText(PortraitPeriodKey):
    text: str = Field(min_length=1, max_length=9000)


class WholeLifeReading(StrictModel):
    areas: list[PortraitAreaText] = Field(min_length=3, max_length=3)
    periods: list[PortraitPeriodText] = Field(max_length=3)
    timing_status: Literal["AVAILABLE", "NOT_AVAILABLE"]
    timing_note: str = Field(min_length=1, max_length=1000)


class PortraitAreaProse(StrictModel):
    source_id: Literal["L01", "L02", "L03"]
    text: str = Field(min_length=1, max_length=9000)


class PortraitPeriodProse(StrictModel):
    id: Literal["V01", "V02", "V03"]
    text: str = Field(min_length=1, max_length=9000)


class WholeLifeProse(StrictModel):
    schema_version: Literal["bazi-whole-life-prose-v1"] = "bazi-whole-life-prose-v1"
    overview: str = Field(min_length=1, max_length=9000)
    areas: list[PortraitAreaProse] = Field(min_length=3, max_length=3)
    periods: list[PortraitPeriodProse] = Field(max_length=3)
    takeaway: str = Field(min_length=1, max_length=9000)
    limit: str = Field(min_length=1, max_length=1200)


def prose_outline(analysis):
    return {"schema_version": "bazi-whole-life-prose-v1", "overview": "",
            "areas": [{"source_id": row.id, "text": ""} for row in analysis.areas],
            "periods": [{"id": row.id, "text": ""} for row in analysis.periods],
            "takeaway": "", "limit": ""}


def bind_prose(raw, outline):
    value = WholeLifeProse.model_validate(raw)
    if ([row.source_id for row in value.areas] != [row["source_id"] for row in outline["whole_life"]["areas"]]
            or [row.id for row in value.periods] != [row["id"] for row in outline["whole_life"]["periods"]]):
        raise ValueError("LIFE_PORTRAIT_PROSE_COVERAGE_MISMATCH")
    outline["overview"]["text"] = value.overview
    outline["takeaway"]["text"] = value.takeaway
    outline["limits"][0]["text"] = value.limit
    for target, source in zip(outline["whole_life"]["areas"], value.areas):
        target["text"] = source.text
    for target, source in zip(outline["whole_life"]["periods"], value.periods):
        target["text"] = source.text
    return outline


def period_plan(context):
    luck = next((json.loads(f.text) for f in context.facts if f.id == "engine:luck_cycles"), {})
    cycles = luck.get("cycles", [])
    if luck.get("status") != "AVAILABLE" or not cycles:
        return []
    # Three contiguous spans from saved cycles, without inventing round ages,
    # new boundaries, life events, or an implied age of death.
    result = []
    for start, end in ((0, 2), (2, 5), (5, 7)):
        selected = cycles[start:end]
        if not selected:
            continue
        result.append({"id": f"V{len(result)+1:02}", "cycle_indices": list(range(start, start+len(selected))),
            "start_year": selected[0]["start"], "end_year": selected[-1]["end"],
            "start_age": selected[0]["startAge"], "end_age": selected[-1]["endAge"]})
    return result


def validate_portrait(value, context):
    facts, evidence = {f.id for f in context.facts}, {e.id for e in context.evidence}
    if value.overview.id != "O01" or [(row.id, row.area) for row in value.areas] != [
        ("L01", "CAREER"), ("L02", "FINANCES"), ("L03", "RELATIONSHIPS")]:
        raise ValueError("PORTRAIT_AREA_COVERAGE_INVALID")
    for claim in [value.overview, *value.areas, *value.periods]:
        if len(set(claim.fact_refs)) < 2 or not set(claim.fact_refs) <= facts or not set(claim.evidence_refs) <= evidence:
            raise ValueError("PORTRAIT_FOREIGN_OR_THIN_BASIS")
    plan = period_plan(context)
    periods = [{key: getattr(row, key) for key in PortraitPeriodKey.model_fields} for row in value.periods]
    if periods != plan or value.timing_status != ("AVAILABLE" if plan else "NOT_AVAILABLE"):
        raise ValueError("PORTRAIT_PERIOD_NOT_IN_ENGINE")
    if any("engine:luck_cycles" not in row.fact_refs for row in value.periods):
        raise ValueError("PORTRAIT_PERIOD_WITHOUT_CYCLE_BASIS")
    return value


def portrait_outline(analysis):
    return {"areas": [{"source_id": row.id, "area": row.area, "text": ""} for row in analysis.areas],
        "periods": [{**{key: getattr(row, key) for key in PortraitPeriodKey.model_fields}, "text": ""} for row in analysis.periods],
        "timing_status": analysis.timing_status,
        "timing_note": ("Các mốc là phạm vi Đại vận đã tính, không ấn định sự kiện hoặc tuổi thọ."
                        if analysis.timing_status == "AVAILABLE" else "Chưa có dữ liệu Đại vận để chia các chặng đường đời.")}


def portrait_metadata(value):
    """Only prose is editable by the writer; references and periods are fixed."""
    raw = value.model_dump(mode="json") if isinstance(value, WholeLifeReading) else value
    return {**raw, "areas": [{k: v for k, v in row.items() if k != "text"} for row in raw["areas"]],
            "periods": [{k: v for k, v in row.items() if k != "text"} for row in raw["periods"]]}
