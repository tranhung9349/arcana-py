"""Adapters read saved analysis snapshots; no calendar or divination is rerun."""
from hashlib import sha256
import json

from research_tools.interpretation_prompt import Context, bazi_context, load_pack
from .bazi_models import BaziResponse
from .liuyao_analysis import digest
from .liuyao_models import LiuYaoAnalysis
from .maihoa_models import MaiHoaResponse
from .coins_models import CoinResponse
from .liuyao_sources import casting_sources, method_sources


def _fact(key, value):
    return {"id": key, "text": value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)}


def _source_enriched(context):
    """Attach primary excerpts, never new chart facts or assessment decisions."""
    _, sources, _ = load_pack()
    payload = context.model_dump(mode="json")
    known = {e["id"] for e in payload["evidence"]}
    payload["evidence"] += [{k: e[k] for k in ("id", "title", "text", "sha256", "url", "kind")}
                            for e in sources if context.method in e["methods"] and e["kind"] == "PRIMARY_TEXT" and e["id"] not in known]
    return Context.model_validate(payload)


def maihoa_context(saved):
    s = MaiHoaResponse.model_validate(saved).model_dump(mode="json")
    rows = [_fact("chart:" + key, value) for key, value in s["chart"].items()]
    rows += [_fact("season", s["season"]), _fact("summary", s["summary"]), _fact("warnings", s["warnings"])]
    findings = [{"id": f["phase"] + ":" + f["rule_id"], "text": f["text_vi"], "status": "CONDITIONAL",
                 "fact_refs": ["chart:the", "chart:" + {"BEGINNING": "dung", "MIDDLE_BODY": "mutual_body", "MIDDLE_USE": "mutual_use", "ENDING": "changed_use"}[f["phase"]], "season", "summary"],
                 "evidence_refs": f["evidence_refs"]} for f in s["findings"]]
    # Calendar timestamps are omitted; the chart and already-derived season suffice.
    return _source_enriched(Context.model_validate({"context_id": s["request_id"], "method": "MAIHOA_INTERNAL", "analysis_profile": s["rules_version"],
        "topic": s["topic"], "question": s["question"], "signals": [s["findings"][0]["relation"]] + (["MIXED_PHASES"] if s["summary"]["pattern"] == "MIXED_INDICATIONS" else []),
        "facts": rows, "findings": findings, "evidence": [{"id": e["evidence_id"], "title": e["title"], "text": e["text"],
            "sha256": e["text_sha256"], "url": e["source"]["url"], "kind": "PRIMARY_TEXT"} for e in s["evidence"]],
        "limitations": s["limitations"]}))


def liuyao_context(session, analysis):
    session = CoinResponse.model_validate(session).model_dump(mode="json")
    a = LiuYaoAnalysis.model_validate(analysis).model_dump(mode="json")
    if a["session_id"] != session["request_id"] or a["snapshot_sha256"] != digest(session):
        raise ValueError("Liu Yao analysis belongs to another saved casting")
    # Supply the complete saved casting, while explicitly marking which lines
    # have an assessed role in the findings. The writer must not invent a new
    # interaction just because another line is visible in the inventory.
    line_keys = {row["key"] for row in a["lines"]}
    relevant_keys = set(a["selection"]["candidate_keys"])
    relevant_keys.update(("L" + str(session["najia"]["world_line"]), "L" + str(session["najia"]["response_line"])))
    relevant_keys.update(key for f in a["findings"] for key in f["evidence"] if key in line_keys)
    rows = [_fact("line:" + row["key"], row) for row in a["lines"]]
    rows += [_fact("casting:throws", session["casting"]),
             _fact("chart:original", session["original"]["chart"]),
             _fact("chart:changed", session["changed"]["chart"] if session["changed"] else None),
             _fact("chart:moving_lines", session["moving_lines"]),
             _fact("chart:najia", session["najia"]),
             _fact("calendar:casting", session["calendar"])]
    rows += [_fact("selection", a["selection"]), _fact("tendency", a["tendency"]), _fact("roles", a["roles"]),
             _fact("timing", a["timing_conditions"]), _fact("intent", a["intent"]), _fact("question_context", a["context"])]
    rows.append(_fact("reading:anchors", {"world_key": "L" + str(session["najia"]["world_line"]),
                                         "response_key": "L" + str(session["najia"]["response_line"])}))
    # USE_WORLD already stores source, target and direction in `evidence`.
    # Its legacy reverse-direction prose uses target-centric labels that can be
    # misread as source-centric. Spell out that saved code without recomputing
    # any relation, selecting another line or changing the original snapshot.
    relation_words = {"SAME": "đồng hành với", "GENERATES": "sinh", "CONTROLS": "khắc",
                      "DRAINS": "được sinh bởi", "CONSUMES": "bị khắc bởi"}
    normalized = {}
    for finding in a["findings"]:
        if finding["rule"] == "USE_WORLD" and len(finding["evidence"]) >= 3:
            source, target, code = finding["evidence"][:3]
            if code in relation_words:
                relation = {"source_key": source, "target_key": target, "relation": code,
                            "reading": f"Dụng {source} {relation_words[code]} Thế {target}.",
                            "provenance": "SAVED_USE_WORLD_RELATION"}
                rows.append(_fact("relation:use_world", relation))
                normalized[finding["id"]] = relation["reading"] + " Tác dụng còn phụ thuộc sức hào và điều kiện động biến đã lưu."
    # Existing analysis citations are bibliography, not source quotations. Keep
    # their actual engine explanations explicitly labelled PRODUCT_POLICY. Only
    # the separately pinned primary excerpts below are labelled PRIMARY_TEXT.
    evidence = []
    for f in a["findings"]:
        text = normalized.get(f["id"], f["explanation"])
        evidence.append({"id": "engine:" + f["id"], "title": f["title"] + " · nhận định quy tắc đã lưu", "text": text,
                         "sha256": sha256(text.encode()).hexdigest(), "url": None, "kind": "PRODUCT_POLICY"})
    _, sources, _ = load_pack()
    classical, chart_documents, source_gaps = casting_sources(session)
    method, method_documents, source_map, method_refs = method_sources(a, sources)
    evidence += classical + method
    rows += [_fact("reading:provenance", {"schema_version": "liuyao-grounded-input-v1",
              "casting_snapshot_sha256": a["snapshot_sha256"], "casting_rules_version": session["rules_version"],
              "analysis_rules_version": a["rules_version"], "analysis_rules_sha256": a["rules_sha256"],
              "assessed_line_keys": sorted(relevant_keys), "line_order": "BOTTOM_TO_TOP",
              "vietnamese_ai_drafts_included": False}),
             _fact("sources:documents", {"hexagrams": chart_documents, "method": method_documents,
                                          "gaps": source_gaps}),
             _fact("sources:rule_bindings", source_map)]
    for f in a["findings"]:
        rows.append(_fact("assessment:" + f["id"], {**f, "explanation": normalized.get(f["id"], f["explanation"])}))
    findings = [{"id": f["id"], "text": normalized.get(f["id"], f["explanation"]), "status": "CONDITIONAL",
                 "fact_refs": ["selection", "tendency", "assessment:" + f["id"],
                               *dict.fromkeys("line:" + key for key in f["evidence"] if key in relevant_keys),
                               *(["relation:use_world"] if f["id"] in normalized else [])],
                 "evidence_refs": ["engine:" + f["id"], *method_refs[f["id"]]]} for f in a["findings"]]
    signals = [{"AMBIGUOUS":"AMBIGUOUS_USE", "SELECTED":"SELECTED_USE", "PROVISIONAL":"PROVISIONAL_USE"}[a["selection"]["status"]]]
    # The saved engine only assesses the casting's day/month. A date in the
    # question does not add a forecast for that period or an employment end date.
    scope = "Nhật–Nguyệt là ngày và tháng gieo quẻ. Chưa tính riêng diễn biến tháng/năm được hỏi, thời hạn công việc hoặc ngày kết thúc."
    rows.append(_fact("reading:time_scope", scope))
    evidence.append({"id": "policy:time_scope", "title": "Phạm vi thời gian của phần phân tích", "text": scope,
                     "sha256": sha256(scope.encode()).hexdigest(), "url": None, "kind": "PRODUCT_POLICY"})
    findings.append({"id": "scope:time", "text": scope, "status": "UNRESOLVED",
                     "fact_refs": ["reading:time_scope"], "evidence_refs": ["policy:time_scope"]})
    if a["tendency"] == "MIXED": signals.append("DAY_MONTH_MIXED")
    if any(r["activity"] == "DARK_ACTIVE" for r in a["lines"]): signals.append("DAY_CLASH_STRONG_STATIC")
    # Focus only a condition explicitly assessed by the saved analysis. Flags
    # alone must not cause the prompt layer to create a new world-line finding.
    if any(f["rule"] == "WORLD_CAPACITY" for f in a["findings"]):
        signals.append("WORLD_CONDITIONED")
    if a["timing_conditions"]:
        signals.append("HAS_TIMING_CONDITIONS")
    return Context.model_validate({"context_id": session["request_id"], "method": "LIUYAO_NAJIA", "analysis_profile": a["rules_version"],
        "topic": a["context"]["topic"], "question": session["question"], "signals": signals, "facts": rows, "findings": findings,
        "evidence": evidence, "limitations": a["limitations"] + [scope, "Dụng thần và trạng thái phải giữ nguyên lựa chọn của bài luận Lục Hào đang mở."]})


def natal_context(saved, reading=None):
    s = BaziResponse.model_validate(saved)
    if reading is not None:
        s = s.model_copy(update={"reading": reading})
    return _source_enriched(bazi_context(s))
