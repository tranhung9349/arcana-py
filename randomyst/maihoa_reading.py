"""Readable synthesis using the same Mai Hoa interpreter as consultations."""
from copy import deepcopy

from .models import ModuleReading

PHASES = {
    "BEGINNING": ("Khởi sự · Thể và Dụng", "dung"),
    "MIDDLE_BODY": ("Diễn tiến giữa chặng · phía chủ thể", "mutual_body"),
    "MIDDLE_USE": ("Diễn tiến giữa chặng · phía hoàn cảnh", "mutual_use"),
    "ENDING": ("Chiều biến chuyển · Dụng biến", "changed_use"),
}
MEANINGS = {
    "SAME": "cùng hành với Thể nên có thế tỷ hòa: hai phía được đọc như có sự đồng nhịp",
    "USE_GENERATES_BODY": "sinh hành của Thể, tạo thế chủ thể nhận được trợ lực",
    "BODY_CONTROLS_USE": "bị hành của Thể khắc, tạo thế chủ thể chủ động điều tiết hoàn cảnh",
    "BODY_GENERATES_USE": "được Thể sinh, tạo thế sinh xuất: chủ thể phải dành lực cho phía đang xét",
    "USE_CONTROLS_BODY": "khắc hành của Thể, tạo thế chủ thể chịu sức chế ước hoặc cản trở",
}


class DrawMaiHoaInterpreter:
    version = "draw-maihoa-reading-2026-10-26-v1"

    def __init__(self, maihoa_service):
        self.service = maihoa_service

    def interpret(self, draw, original):
        trace, saved = draw["trace"], draw["trace"]["maihoa"]
        # Use the saved chart and saved casting month, including legacy mutuals.
        reading = self.service.interpret_chart(saved, trace["casting_solar_month"], "GENERAL")
        chart, season = reading["chart"], reading["season"]
        body, use = chart["the"], chart["dung"]
        evidence = [{"evidence_id": "facts:maihoa", "kind": "SAVED_FACT", "title": "Quẻ và tháng gieo đã lưu",
                     "text": f"Quẻ {original['name_vi']}, hào {chart['moving_line']} động; Thể {body['name']} ({body['element']}), Dụng {use['name']} ({use['element']}); tháng {season['month_branch']}."}]
        evidence.extend({"evidence_id": row["evidence_id"], "kind": "SOURCE_ORIGINAL", "title": row["title"],
                         "text": row["text"], "url": row["source"]["url"]} for row in reading["evidence"])
        body_strength = {
            "STRONG": f"Thể {body['name']} thuộc hành {body['element']}, đang nằm trong nhóm vượng của tháng; đây là trợ lực cần tính khi đọc các quan hệ.",
            "WEAK": f"Thể {body['name']} thuộc hành {body['element']}, đang nằm trong nhóm suy của tháng; vì vậy một dấu hiệu sinh trợ đơn lẻ chưa đủ để kết luận thuận.",
            "NOT_SPECIFIED": f"Hành {body['element']} của Thể không được gán riêng là vượng hay suy trong bảng thời khí của tháng này."
        }[body["strength"]]
        sections = [
            {"title": "Hiểu Thể và Dụng trong quẻ này", "text": f"Thể {body['name']} ({body['element']}) làm điểm quy chiếu của chủ thể; Dụng {use['name']} ({use['element']}) đại diện phía tình huống đang tác động. Hào {chart['moving_line']} động nằm ở phía Dụng. Phần này luận tổng quát thời điểm gieo, vì phiên gieo số không có câu hỏi riêng.",
             "references": ["facts:maihoa", "BODY_USE", "GENERAL_" + reading["findings"][0]["relation"]]},
            {"title": "Thời khí nâng đỡ hay làm yếu quẻ?", "text": f"Tháng {season['month_branch']} được xét theo tháng tiết khí đã lưu: hành {season['strong_element']} vượng, hành {season['weak_element']} suy. " + body_strength,
             "references": ["facts:maihoa", "STRONG", "WEAK", "STRENGTH"]},
        ]
        for finding in reading["findings"]:
            title, key = PHASES[finding["phase"]]
            other = chart[key]
            text = f"{other['name']} ({other['element']}) " + MEANINGS[finding["relation"]] + ". "
            text += ("Quan hệ này nghiêng về chiều thuận trong phép đọc Mai Hoa."
                     if finding["indication"] == "FAVOURABLE" else "Quan hệ này là điểm cần cân nhắc trong phép đọc Mai Hoa.")
            refs = ["facts:maihoa", *finding["evidence_refs"]]
            if other["strength"] == "STRONG":
                text += " Quái này đang vượng theo thời khí, nên tác động của quan hệ cần được chú ý thêm."
                refs.append("STRENGTH")
            elif other["strength"] == "WEAK":
                text += " Quái này đang suy theo thời khí; cần đọc cùng sức của Thể thay vì chỉ dựa vào tên quan hệ."
                refs.append("STRENGTH")
            sections.append({"title": title, "text": text, "references": refs})
        missing = []
        if chart["mutual"] is None:
            missing.append("Phiên đã lưu thiếu quẻ hỗ nên chưa diễn giải phần trung gian.")
        if chart["changed"] is None:
            missing.append("Phiên đã lưu thiếu quẻ biến nên chưa diễn giải chiều cuối.")
        synthesis = reading["summary"]["sequence"]
        if reading["summary"]["pattern"] == "MIXED_INDICATIONS":
            synthesis += " Vì có cả quan hệ thuận và quan hệ cản trở, nên đọc theo diễn tiến từng chặng thay vì gộp cả quẻ thành một chữ tốt hoặc xấu."
        synthesis += " " + " ".join(row["message"] for row in reading["warnings"])
        if missing:
            synthesis += " " + " ".join(missing)
        sections.append({"title": "Ghép các phần để hiểu toàn quẻ", "text": synthesis.strip(),
                         "references": ["facts:maihoa", "SYNTHESIS", "STRENGTH", "CONTEXT"]})
        return ModuleReading.model_validate({
            "module": "MAIHOA", "version": self.version, "title": original["name_vi"] + " · nhịp vận động của quẻ",
            "summary": reading["summary"]["text"] + " " + reading["summary"]["sequence"],
            "sections": sections, "evidence": evidence,
            "facts": {"chart": deepcopy(chart), "season": deepcopy(season), "findings": deepcopy(reading["findings"]),
                      "summary": deepcopy(reading["summary"]), "warnings": deepcopy(reading["warnings"]),
                      "rules_version": self.service.rules.config["rules_version"], "rules_sha256": self.service.rules.sha256,
                      "topic": "GENERAL", "uses_saved_chart": True, "missing_phases": missing},
            "limitations": ["Luận tổng quát từ đúng quẻ đã lưu; không tự chuyển thành lời đoán cầu tài, giao dịch hay trúng thưởng.",
                            "Hỗ và Biến được dùng để diễn giải diễn tiến, không thay đổi bộ số hoặc điểm đã chốt.",
                            "Ngoại ứng, ứng kỳ cụ thể và ngữ cảnh một việc hỏi chưa được suy đoán trong phần đọc này.", *missing],
        }).model_dump(mode="json")
