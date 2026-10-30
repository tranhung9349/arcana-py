"""Build editorial date examples offline from explicit synthetic engine fixtures."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from uuid import UUID

from randomyst.date_ai_context import date_context, DateReadingContext
from randomyst.date_consultations import DateConsultation, DateConsultationRequest
from randomyst.date_engine import DateEngine
from randomyst.date_models import DateSearchRequest
from randomyst.date_reading import explain_day
from randomyst.liuyao_analysis import digest
from research_tools.interpretation_prompt import ROOT, validate_response

PACK = ROOT / "data/interpretation/date_v1"


def main():
    engine = DateEngine()
    cases = []
    specs = [("hour-good", "BUSINESS_OPENING", "2026-10-13", False),
             ("hour-normal", "BUSINESS_OPENING", "2026-10-02", False),
             ("hour-blocked", "BUSINESS_OPENING", "2026-10-01", False),
             ("day-two-people", "BETROTHAL_NACAI", "2026-10-02", False),
             ("day-blocked", "LAND_BREAKING", "2026-10-04", False),
             ("hour-unresolved", "BUSINESS_OPENING", "2026-10-13", True),
             ("day-unresolved", "LAND_BREAKING", "2026-10-01", True)]
    for n, (name, activity, date, unstable) in enumerate(specs, 1):
        spec = engine.evaluator.activities[activity]
        births = ["1994-10-08T05:00:00+07:00", "1990-06-15T09:30:00+07:00"]
        if unstable: births[0] = "2026-10-08T13:29:17+07:00"
        request = DateSearchRequest.model_validate({"activity": activity, "subjects": [
            {"subject_id": f"synthetic_{i}", "birth": {"civil_datetime": births[i],
             **({"clock_uncertainty_seconds": 2} if unstable and i == 0 else {})}} for i in range(spec.subject_count)],
            "date_range": {"start": date, "end": date}, "include_details": True})
        result = engine.search(request)
        config = engine.evaluator.config
        scoring = (config.day_scoring if result["evaluation_mode"] == "DAY_ONLY" else config.scoring).model_dump()
        explanation = explain_day(result, scoring)
        saved = DateConsultation(request_id=UUID(int=n), created_at=datetime(2026, 10, 27, tzinfo=timezone.utc), result=result,
            scoring=scoring, rules_sha256=digest(config.model_dump(mode="json")), explanation=explanation)
        ctx = date_context(saved)
        def claim(text, refs):
            return {"label": "AI_INTERPRETATION", "text": text, "fact_refs": refs, "evidence_refs": ["date:policy"]}
        if unstable:
            lead = "Kết quả còn để ngỏ vì sai số giờ sinh đã khai báo có thể làm đổi trụ. Vì vậy, các điểm thô hiện có chưa đủ để khuyến nghị dùng ngày này cho việc đã chọn."
            paragraphs = ["Nên/kỵ của lịch và điểm số vẫn được lưu để đối chiếu, nhưng hồ sơ cá nhân chưa ổn định. Chọn khoảng có điểm cao hơn không giải quyết được điểm thiếu này.",
                          "Cần xác định lại độ chính xác của giờ sinh trước khi tra lại. Đây là giới hạn của dữ liệu đầu vào, không phải dự báo rằng sự kiện sẽ gặp trở ngại."]
        elif name == "hour-good":
            lead = explanation["summary"] + " Lịch ngày hỗ trợ đúng việc và hồ sơ cá nhân không vướng điều kiện đang xét, nên lựa chọn có căn cứ rõ hơn một khung chỉ có điểm cao."
            paragraphs = ["Căn cứ theo việc là " + explanation["reasons"][0].lower() + " " + explanation["reasons"][1] + " Điều này gắn khuyến nghị với giờ bắt đầu khai trương, không suy ra mọi hoạt động trong ngày đều thuận.",
                          explanation["reasons"][2] + " Đó là đối chiếu theo bảng hành đã lưu; không phải kết luận rằng toàn bộ mệnh cục đều phù hợp với ngày này."]
        elif name == "day-two-people":
            lead = explanation["summary"] + " Lịch ngày chưa đề cập rõ việc đã chọn, và cả hai hồ sơ còn có hành thuộc Kỵ thần trong bảng đối chiếu. Vì vậy chưa đủ điều kiện gọi đây là ngày thuận cho cả hai."
            paragraphs = [explanation["reasons"][1] + " " + explanation["reasons"][2],
                          "Hai hồ sơ được đối chiếu riêng và lấy mức trừ lớn hơn, nên không thể dùng trung bình để kết luận cả hai cùng thuận. Những mốc giờ trong kết quả chỉ đánh dấu khoảng hiệu lực của đánh giá ngày; chưa có giờ đẹp được chọn."]
        elif "blocked" in name:
            lead = explanation["summary"]
            paragraphs = [explanation["reasons"][0] + " " + next((c for c in explanation["cautions"] if "Điều kiện loại trừ" in c), "Điểm còn thiếu được giữ nguyên theo bảng chấm."),
                          "Các mục được hỗ trợ hoặc điểm thô còn lại không xóa điều kiện loại trừ. Vì vậy, khoảng xếp cao nhất trong kết quả này cũng chưa phải khoảng được khuyến nghị; cần cân nhắc ngày khác trong lịch tra."]
        else:
            lead = explanation["summary"]
            paragraphs = [explanation["reasons"][0] + " " + explanation["reasons"][1] + " Không được coi việc lịch không đề cập là bằng chứng thuận; điểm còn lại chưa đủ để nâng nhãn.",
                          explanation["reasons"][2] + " Đối chiếu này giải thích phần điểm cá nhân; nó chưa cho phép dự đoán kết quả khai trương."]
        response = {"context_id": ctx.context_id, "summary": claim(lead, ["date:decision", "date:focus", "date:personal"]),
            "analysis": [claim(p, ["date:activity", "date:focus", "date:personal", "date:score_policy"]) for p in paragraphs],
            "practical_options": [{"kind": "MODERN_APPLICATION", "text": "Bạn có thể đối chiếu lịch của người tham gia và điều kiện tổ chức trước khi chốt mốc thực hiện.", "fact_refs": ["date:activity"]}],
            "limits": explanation["cautions"][:2]}
        validate_response(response, ctx)
        cases.append({"id": "date-" + name, "synthetic": True, "review_status": "EDITORIAL_DRAFT_NOT_EXPERT_REVIEWED",
                      "fixture": request.model_dump(mode="json"), "context": ctx.model_dump(mode="json"), "response": response})
    PACK.mkdir(parents=True, exist_ok=True)
    (PACK / "cases.json").write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n")
    for name, model in (("date_consultation_request", DateConsultationRequest), ("date_consultation_response", DateConsultation),
                        ("date_reading_context", DateReadingContext)):
        (ROOT / f"schemas/{name}.schema.json").write_text(json.dumps(model.model_json_schema(), ensure_ascii=False, indent=2) + "\n")
    files = ["docs/prompts/date_selection_v1.system.txt", "data/interpretation/date_v1/cases.json",
             "research_tools/date_interpretation_prompt.py", "randomyst/date_ai_context.py", "randomyst/date_reading.py",
             "config/mvp2_date_rules.json", "schemas/date_reading_context.schema.json"]
    manifest = {"version": "date-selection-2026-10-28-v1.1", "system_prompt": files[0], "model_called": False,
                "review_status": "EDITORIAL_DRAFT_NOT_EXPERT_REVIEWED", "case_count": len(cases),
                "files": [{"path": p, "sha256": sha256((ROOT / p).read_bytes()).hexdigest()} for p in files]}
    (PACK / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"cases": len(cases), "model_called": False}))


if __name__ == "__main__":
    main()
