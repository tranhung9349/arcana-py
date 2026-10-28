"""Offline few-shot preparation; never calls a model or changes a saved reading."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from .reading_strategy import plan_reading

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "data/interpretation/plain_v4"
Method = Literal["BAZI_NATAL_V1", "MAIHOA_INTERNAL", "LIUYAO_NAJIA", "ZHOUYI_TEXT"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Fact(Strict):
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)


class Evidence(Strict):
    id: str = Field(min_length=1)
    title: str
    text: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    url: str | None
    kind: Literal["PRIMARY_TEXT", "PRODUCT_POLICY", "PROVIDER"]

    @model_validator(mode="after")
    def text_binding(self):
        if sha256(self.text.encode()).hexdigest() != self.sha256:
            raise ValueError("Evidence text hash mismatch")
        return self


class Finding(Strict):
    id: str = Field(min_length=1)
    text: str
    status: Literal["SUPPORTED", "CONDITIONAL", "UNRESOLVED"]
    fact_refs: list[str] = Field(min_length=1)
    evidence_refs: list[str] = Field(min_length=1)


class Context(Strict):
    schema_version: Literal["plain-reading-context-v2"] = "plain-reading-context-v2"
    context_id: str = Field(min_length=1)
    method: Method
    analysis_profile: str
    topic: str
    question: str = Field(max_length=2000)
    signals: list[str]  # Adapter-produced selection hints, never inferred from the question.
    facts: list[Fact] = Field(min_length=1)
    findings: list[Finding] = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)
    limitations: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def references(self):
        for rows in (self.facts, self.findings, self.evidence):
            if len({r.id for r in rows}) != len(rows):
                raise ValueError("Duplicate reference ID")
        facts, evidence = {f.id for f in self.facts}, {e.id for e in self.evidence}
        for finding in self.findings:
            if not set(finding.fact_refs) <= facts or not set(finding.evidence_refs) <= evidence:
                raise ValueError("Unbound finding reference")
        return self


class Claim(Strict):
    label: Literal["AI_INTERPRETATION"] = "AI_INTERPRETATION"
    text: str = Field(min_length=1, max_length=1400)
    fact_refs: list[str] = Field(min_length=1)
    evidence_refs: list[str] = Field(min_length=1)


class PracticalOption(Strict):
    kind: Literal["MODERN_APPLICATION"]
    text: str = Field(min_length=1, max_length=800)
    fact_refs: list[str] = Field(min_length=1)


class Response(Strict):
    schema_version: Literal["plain-reading-response-v2"] = "plain-reading-response-v2"
    context_id: str
    summary: Claim
    analysis: list[Claim] = Field(min_length=2, max_length=4)
    practical_options: list[PracticalOption] = Field(min_length=1, max_length=2)
    limits: list[str] = Field(min_length=1, max_length=3)


def validate_response(response, context):
    """Structural/reference checks, not a semantic truth or translation grader."""
    context = Context.model_validate(context)
    response = Response.model_validate(response)
    if context.context_id != response.context_id:
        raise ValueError("Response belongs to another consultation")
    facts = {f.id for f in context.facts}
    evidence = {e.id for e in context.evidence}
    for claim in [response.summary, *response.analysis]:
        if not set(claim.fact_refs) <= facts or not set(claim.evidence_refs) <= evidence:
            raise ValueError("Response contains a foreign reference")
    if any(not set(p.fact_refs) <= facts for p in response.practical_options):
        raise ValueError("Practical option contains a foreign reference")
    return response


def load_pack(directory=PACK):
    directory = Path(directory)
    manifest = json.loads((directory / "manifest.json").read_text())
    for item in manifest["files"]:
        path = ROOT / item["path"]
        if sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("Few-shot file changed: " + item["path"])
    sources = json.loads((directory / "sources.json").read_text())
    source_by_id = {s["id"]: s for s in sources}
    if len(source_by_id) != len(sources):
        raise ValueError("Duplicate source ID")
    for source in sources:
        if sha256(source["text"].encode()).hexdigest() != source["sha256"]:
            raise ValueError("Source excerpt hash mismatch")
        if source.get("raw_path") and source["text"] not in (ROOT / source["raw_path"]).read_text():
            raise ValueError("Source excerpt missing from pinned raw text")
    cases = json.loads((directory / "cases.json").read_text())
    if len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Duplicate few-shot case")
    for case in cases:
        ctx = Context.model_validate(case["context"])
        if case["review_status"] != "EDITORIAL_DRAFT_NOT_EXPERT_REVIEWED":
            raise ValueError("Unexpected editorial status")
        for evidence in ctx.evidence:
            original = source_by_id[evidence.id]
            if ctx.method not in original["methods"]:
                raise ValueError("Few-shot source belongs to another method")
            if evidence.model_dump() != {k: original[k] for k in Evidence.model_fields}:
                raise ValueError("Example evidence differs from its source")
        validate_response(case["response"], ctx)
    if manifest.get("method_guides"):
        guides = json.loads((ROOT / manifest["method_guides"]).read_text())
        for method, guide in guides.items():
            if any(key not in source_by_id or method not in source_by_id[key]["methods"] for key in guide["source_ids"]):
                raise ValueError("Method guide contains a foreign source")
    if manifest.get("reading_playbook"):
        playbook = json.loads((ROOT / manifest["reading_playbook"]).read_text())
        if set(playbook["methods"]) != set(Method.__args__):
            raise ValueError("Playbook must cover exactly the supported methods")
        route_ids = set()
        for method, config in playbook["methods"].items():
            routes = config["routes"]
            if not routes or routes[-1]["when_any"] or any(not r["when_any"] for r in routes[:-1]):
                raise ValueError("Playbook requires one final default route")
            for route in routes:
                if route["id"] in route_ids:
                    raise ValueError("Duplicate playbook route")
                route_ids.add(route["id"])
                if not route["source_ids"] or any(key not in source_by_id or method not in source_by_id[key]["methods"] for key in route["source_ids"]):
                    raise ValueError("Playbook route contains a foreign source")
    return manifest, sources, cases


def select_cases(context, cases, limit=3, playbook=None):
    ctx = Context.model_validate(context)
    if type(limit) is not int or not 1 <= limit <= 3:
        raise ValueError("Select between one and three examples")
    signals = set(ctx.signals)
    candidates = [c for c in cases if c["context"]["method"] == ctx.method]
    exclusive_groups = [
        {"STRONG", "WEAK", "MIXED"},
        {"SAME", "USE_GENERATES_BODY", "BODY_CONTROLS_USE", "BODY_GENERATES_USE", "USE_CONTROLS_BODY"},
        {"SELECTED_USE", "AMBIGUOUS_USE", "PROVISIONAL_USE"},
    ]
    def compatible(case):
        example = set(case["context"]["signals"])
        return all(not (signals & group and example & group) or bool(signals & example & group) for group in exclusive_groups)
    candidates = [case for case in candidates if compatible(case)]
    plan = plan_reading(ctx, playbook) if playbook else None
    def rank(case):
        c = case["context"]
        overlap = len(signals & set(c["signals"]))
        focus = plan is not None and plan["primary_id"] in case.get("teaches_routes", [])
        intent = plan is not None and plan["intent"] == case.get("teaches_intent")
        return (-(c["topic"] == ctx.topic), -focus, -intent, -overlap, case["id"])
    return sorted(candidates, key=rank)[:limit]


def build_messages(context, limit=3):
    ctx = Context.model_validate(context)
    manifest, _, cases = load_pack()
    playbook = json.loads((ROOT / manifest["reading_playbook"]).read_text()) if manifest.get("reading_playbook") else None
    plan = plan_reading(ctx, playbook) if playbook else None
    selected = select_cases(ctx, cases, limit, playbook)
    prompt = (ROOT / manifest.get("system_prompt", "docs/prompts/plain_vietnamese_v2.system.txt")).read_text()
    if manifest.get("method_guides"):
        guides = json.loads((ROOT / manifest["method_guides"]).read_text())
        guide = guides[ctx.method]
        prompt += "\nHƯỚNG DẪN ĐÚNG PHƯƠNG PHÁP CỦA PHIÊN\n" + guide["instruction"]
    if plan:
        prompt += "\n" + plan["instruction"]
    schema = json.dumps(Response.model_json_schema(), ensure_ascii=False)
    messages = [{"role": "system", "content": prompt + "\nresponse_schema=" + schema}]
    for case in selected:
        messages += [{"role": "user", "content": json.dumps(case["context"], ensure_ascii=False)},
                     {"role": "assistant", "content": json.dumps(case["response"], ensure_ascii=False)}]
    messages.append({"role": "user", "content": ctx.model_dump_json()})
    return {"pack_version": manifest["version"], "model_called": False,
            "reading_plan": {k: v for k, v in plan.items() if k != "instruction"} if plan else None,
            "messages_sha256": sha256(json.dumps(messages, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
            "case_ids": [c["id"] for c in selected], "messages": messages}


def bazi_context(saved):
    """Adapt an existing typed snapshot; no calendar/rule recalculation or PII fields."""
    from randomyst.bazi_models import BaziResponse
    saved = BaziResponse.model_validate(saved)
    rows = []
    for pillar in saved.chart.pillars:
        p = pillar.model_dump()
        rows.append({"id": pillar.fact_id, "text": f"{pillar.label}: {pillar.stem.name} {pillar.branch}."})
        for stem in [p["stem"], *p["hidden_stems"]]:
            rows.append({"id": stem["fact_id"], "text": f"{pillar.label}, {'can lộ' if stem['fact_id'] == pillar.stem.fact_id else 'tàng can'}: {stem['name']} {stem['element']}, {stem['ten_god_name']}."})
    rows += [{"id": "facts:season", "text": f"Tháng {saved.chart.month.branch}, hành {saved.chart.month.element}; trợ lực mùa: {saved.chart.month.seasonal_support}."},
             {"id": "facts:distribution", "text": json.dumps([r.model_dump() for r in saved.facts.distribution], ensure_ascii=False)}]
    rows += [{"id": r.fact_id, "text": f"Căn {r.stem}, trụ {r.pillar}, mức {r.level}; tham chiếu {r.stem_ref}."} for r in saved.facts.roots]
    rows += [{"id": r.fact_id, "text": f"{r.name}: {', '.join(r.tokens)} tại {', '.join(r.pillar_refs)}; chưa kết luận hóa hành."} for r in saved.facts.relations]
    findings = [{"id": f.finding_id, "text": f.text, "status": f.state,
                 "fact_refs": list(f.fact_refs), "evidence_refs": list(f.evidence_refs)} for f in saved.findings]
    # Explicit assessment facts preserve categorical states that prose alone can obscure.
    rows.append({"id": "assessment:snapshot", "text": saved.assessment.model_dump_json()})
    signals = [saved.assessment.strength, "NATAL_ONLY"]
    if saved.assessment.climate_conflict:
        signals.append("CLIMATE_CONFLICT")
    if saved.assessment.structures:
        signals.append("CANDIDATE_STRUCTURE")
    if saved.facts.relations:
        signals.append("HAS_RELATIONS")
    return Context.model_validate({"context_id": str(saved.request_id), "method": "BAZI_NATAL_V1",
        "analysis_profile": saved.analysis_profile + ":" + saved.rules_version, "topic": saved.reading.topic,
        "question": saved.reading.question, "signals": signals, "facts": rows, "findings": findings,
        "evidence": [{"id": e.evidence_id, "title": e.title, "text": e.text, "sha256": e.sha256, "url": e.url, "kind": e.kind} for e in saved.evidence],
        "limitations": [c.detail for c in saved.coverage if c.status != "SUPPORTED"] +
                        ["Câu hỏi được lưu làm ngữ cảnh; engine chưa phân tích ngữ nghĩa câu hỏi. Mẫu prompt chỉ diễn giải dữ kiện đã có."]})


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("context", type=Path)
    parser.add_argument("--bazi-snapshot", action="store_true")
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.context.read_text())
    ctx = bazi_context(payload) if args.bazi_snapshot else Context.model_validate(payload)
    output = build_messages(ctx, args.limit)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"pack_version": output["pack_version"], "case_ids": output["case_ids"], "model_called": False}))


if __name__ == "__main__":
    main()
