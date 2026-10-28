"""Adapt a saved date decision; omit birth times and unrelated natal analysis."""
from hashlib import sha256
import json
from typing import Literal

from research_tools.interpretation_prompt import Context
from .date_consultations import DateConsultation
from .date_reading import period_label


class DateReadingContext(Context):
    method: Literal["DATE_SELECTION"] = "DATE_SELECTION"


def date_context(saved):
    s = DateConsultation.model_validate(saved).model_dump(mode="json")
    result, explanation = s["result"], s["explanation"]
    day = result["days"][0]
    day_only = result["evaluation_mode"] == "DAY_ONLY"
    rows = day["day_periods"] if day_only else day["windows"]
    focus = next(w for w in rows if w["start_at"] == explanation["focus_start_at"])
    # De-identify subject IDs too: the model only needs each selected role and
    # derived element bands. No birth time, natal pillars, name or location.
    roles = {p["subject_id"]: p["role"] for p in result["subject_summaries"]}
    profiles = [{k: p[k] for k in ("role", "primary", "hy", "ky", "overridden")}
                for p in result["subject_summaries"]]
    people = [{k: p[k] for k in ("status", "penalty", "elements", "element_bands", "blocked")}
              | {"role": roles[p["subject_id"]], "natal_clash": bool(p["clashing_natal_branch_indices"]),
                 "positions": ["Can ngày", "Chi ngày"] if day_only else ["Can ngày", "Can giờ", "Chi ngày", "Chi giờ"]}
              for p in focus["subject_assessments"]]
    # Rule matches are copied, never inferred from other calendrical features.
    exclusions = ["NATAL_CLASH:" + roles[c.split(":", 1)[1]] if c.startswith("NATAL_CLASH:") else c
                  for c in focus["hard_exclusions"]]
    facts = {"date:activity": {"name": result["activity_name"], "anchor": result["activity_spec"]["event_anchor"],
                              "mode": result["evaluation_mode"], "scope": result["activity_spec"]["scope_note"]},
             "date:decision": {"date": day["date"], "grade": day["grade"], "score": day["score"],
                               "assessment_state": day["assessment_state"], "has_unresolved_periods": day["has_unresolved_windows"]},
             "date:recommended": [{"period_vietnam": period_label(w), "score": w["score"]} for w in rows if w["grade"] == "GOOD"],
             "date:focus": {"period_vietnam": period_label(focus), "grade": focus["grade"], "score": focus["score"],
                            "raw_score": focus["raw_score"], "assessment_state": focus["assessment_state"],
                            "calendar_class": focus["calendar_class"], "day_officer": focus["day_officer"],
                            "day_activity_status": focus["day_activity_status"],
                            **({} if day_only else {"hour_activity_status": focus["hour_activity_status"]}),
                            "hard_exclusions": exclusions, "penalties": focus["penalties"], "warnings": focus["rule_warnings"]},
             "date:profiles": profiles, "date:personal": people, "date:score_policy": s["scoring"]}
    # This is a product rule explanation, not a quotation from an ancient work.
    policy = ("Quy tắc tra ngày " + result["date_rules_version"] + "; hash=" + s["rules_sha256"] + ". "
              "Nên/kỵ theo đúng việc đã chọn; điều kiện loại trừ không được bù bằng điểm. "
              "Mức Ngày Đẹp còn cần lịch ngày hỗ trợ và tất cả hồ sơ SUPPORTED; DIRECT_YI_JI cần cả lịch giờ hỗ trợ. "
              "Hai hồ sơ lấy mức trừ hành lớn hơn. DAY_ONLY không đánh giá trụ giờ hay đưa ra giờ đẹp. "
              "Ngày được xếp theo khoảng đạt mức cao nhất; kết luận không bao trùm các khoảng còn lại. "
              "Hành cá nhân dùng bảng đối chiếu của tính năng tra ngày, chưa phải bài luận Bát Tự đầy đủ.")
    evidence = [{"id": "date:policy", "title": "Quy tắc tra ngày đã lưu", "text": policy,
                 "sha256": sha256(policy.encode()).hexdigest(), "url": "/api/v2/auspicious-dates/rules", "kind": "PRODUCT_POLICY"}]
    findings = [{"id": "date:summary", "text": explanation["summary"],
                 "status": "UNRESOLVED" if day["grade"] is None else "CONDITIONAL",
                 "fact_refs": ["date:decision", "date:recommended", "date:focus"], "evidence_refs": ["date:policy"]}]
    findings += [{"id": f"date:reason:{i}", "text": text, "status": "CONDITIONAL",
                  "fact_refs": ["date:focus", "date:personal", "date:profiles", "date:score_policy", "date:activity"],
                  "evidence_refs": ["date:policy"]} for i, text in enumerate(explanation["reasons"])]
    signals = [result["evaluation_mode"], day["grade"] or "UNRESOLVED", "TWO_SUBJECTS" if len(people) == 2 else "ONE_SUBJECT"]
    if exclusions: signals.append("HARD_EXCLUSION")
    if any(p["status"] == "TENSION" for p in people): signals.append("PERSONAL_TENSION")
    return DateReadingContext(context_id=s["request_id"], analysis_profile=result["date_rules_version"] + ":" + s["rules_sha256"],
        topic=result["activity"], question="Vì sao ngày này được xếp như vậy cho việc " + result["activity_name"].lower() + "?",
        signals=signals, facts=[{"id": k, "text": json.dumps(v, ensure_ascii=False)} for k, v in facts.items()],
        findings=findings, evidence=evidence, limitations=explanation["cautions"] + [
            "Bài luận chỉ phân tích khoảng được xếp cao nhất và liệt kê các khoảng được khuyến nghị; không suy rộng căn cứ đó sang mọi khung khác.",
            "Chưa đánh giá Tam Nương; không thêm quy tắc chọn ngày, vận hạn, quẻ Dịch hay cam kết kết quả của sự kiện."])
