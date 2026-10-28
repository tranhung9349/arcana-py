"""Vietnamese natal prose assembled only from saved facts and findings."""
from .bazi_models import NatalReading
from .bazi_rules import GROUP_GODS

NARRATIVE_VERSION = "bazi-narrative-2026-10-26-v1"
TOPICS = {"GENERAL": "Tổng quan", "CAREER": "Công việc", "WEALTH": "Tài chính", "STUDY": "Học tập", "RELATIONSHIPS": "Quan hệ"}
FOCUS = {
    "CAREER": ("OFFICER", "OUTPUT", "Quan Sát cho biết trục khuôn phép và trách nhiệm; Thực Thương cho biết đường biểu đạt và tạo ra kết quả. "
               "Đọc hai phía cùng khí thế Nhật chủ để cân nhắc giữa gánh trách nhiệm và khoảng chủ động."),
    "WEALTH": ("WEALTH", "OUTPUT", "Tài biểu thị quan hệ với nguồn lực; Thực Thương là đường tạo ra đầu ra để kết nối với nguồn lực ấy. "
               "Khả năng đảm đương phải được xét cùng Nhật chủ, thay vì đếm Tài rồi suy thành mức giàu có."),
    "STUDY": ("RESOURCE", "OUTPUT", "Ấn là trục tiếp nhận và sinh trợ; Thực Thương là đường diễn đạt, thực hành và tạo đầu ra. "
              "Đọc cả hai phía để cân nhắc nhịp tiếp thu và nhịp vận dụng."),
    "RELATIONSHIPS": ("SELF", "OFFICER", "Tỷ Kiếp là trục đồng hành và chia sẻ; Quan Sát là trục giới hạn và trách nhiệm. "
                      "Phần này đọc cách phối hợp các lực trong một lá số; chưa xác định đối tượng, hôn kỳ hoặc mức hợp với một người khác."),
}


def compose(chart, facts, assessment, findings, topic, question):
    by_id = {f.finding_id: f for f in findings}
    day = chart.pillars[2].stem
    sections = []
    if topic != "GENERAL":
        first, second, intro = FOCUS[topic]
        a, b = by_id["group:" + first], by_id["group:" + second]
        if assessment.strength == "STRONG":
            nuance = "Khí thế đang thiên về vượng, nên đáng chú ý cách chuyển trợ lực thành đầu ra và trách nhiệm có giới hạn."
        elif assessment.strength == "WEAK":
            nuance = "Khí thế đang thiên về nhược, nên cần đọc phần trợ lực trước khi đề cao khả năng gánh thêm yêu cầu."
        else:
            nuance = "Khí thế có tín hiệu đan xen; ưu tiên xem điều kiện hỗ trợ và điểm cần cân nhắc, chưa xếp chủ đề này là thuận hoặc nghịch toàn diện."
        visible_first = [p for p in chart.pillars if p.stem.ten_god in GROUP_GODS[first]]
        visible_second = [p for p in chart.pillars if p.stem.ten_god in GROUP_GODS[second]]
        if visible_first and not visible_second:
            integration = {
                "CAREER": "Trong tầng can lộ, phía trách nhiệm hiện rõ hơn phía biểu đạt. Điểm đáng khảo sát là đường để năng lực tạo đầu ra cùng gánh những yêu cầu đang nổi lên.",
                "WEALTH": "Tài lộ nhưng đường sinh xuất chưa lộ trên can. Vì vậy cần đọc kỹ nguồn tạo ra và nuôi dưỡng phần Tài trước khi chỉ chú ý vào việc nắm giữ nguồn lực.",
                "STUDY": "Phía tiếp nhận hiện rõ trên can hơn phía biểu đạt. Điểm đáng cân nhắc là cách chuyển điều đã tiếp thu thành thực hành và kết quả cụ thể.",
                "RELATIONSHIPS": "Phía đồng hành hiện rõ trên can, còn trục trách nhiệm cần đọc thêm trong chi. Có thể dùng cặp lực này để suy ngẫm về chia sẻ và giới hạn khi phối hợp.",
            }[topic]
        elif visible_second and not visible_first:
            integration = {
                "CAREER": "Phía biểu đạt hiện rõ trên can hơn trục trách nhiệm. Điểm đáng khảo sát là cách đặt đầu ra cá nhân vào yêu cầu và giới hạn của công việc.",
                "WEALTH": "Đường sinh xuất hiện rõ hơn Tài trên can. Khi đọc chủ đề nguồn lực, cần xem cầu nối giữa việc tạo đầu ra và khả năng chuyển đầu ra ấy thành giá trị.",
                "STUDY": "Phía biểu đạt hiện rõ hơn phía tiếp nhận trên can. Điểm đáng cân nhắc là nguồn hỗ trợ để quá trình thực hành có chỗ dựa, thay vì chỉ tăng nhịp đầu ra.",
                "RELATIONSHIPS": "Trục trách nhiệm hiện rõ hơn phía đồng hành trên can. Có thể đọc sự phối hợp này qua cách phân định yêu cầu, khoảng riêng và phần chia sẻ.",
            }[topic]
        elif visible_first and visible_second:
            integration = "Hai phía đều lộ trên can. Cần đọc cách chúng sinh trợ hoặc điều tiết nhau cùng căn khí Nhật chủ, thay vì chỉ chọn một phía nổi bật."
        else:
            integration = "Hai phía chưa lộ trên can; trọng tâm nằm ở các tàng can và quan hệ phối hợp đã liệt kê. Sự vắng mặt trên can không đủ để kết luận thiếu năng lực hoặc thiếu cơ hội."
        refs = [a.finding_id, b.finding_id, "strength"]
        if topic == "RELATIONSHIPS":
            day_relations = [r for r in facts.relations if "pillar:day" in r.pillar_refs]
            if day_relations:
                integration += " Chi ngày tham gia các quan hệ " + ", ".join(dict.fromkeys(r.name for r in day_relations)) + "; cần đọc cùng phần tương tác bên dưới."
                refs.append("relations")
        sections.append({"title": TOPICS[topic] + " trong lá số này", "text": a.text + " " + b.text + "\n\n" + integration + " " + nuance + "\n\n" + intro,
                         "finding_refs": refs})
    for key in ("natal_context", "roots", "strength", "structure", "special_caution", "balance", "climate", "relations"):
        if key in by_id:
            f = by_id[key]
            sections.append({"title": f.title, "text": f.text, "finding_refs": [f.finding_id]})
    if topic == "GENERAL":
        visible = [p.stem for p in chart.pillars if p.position != "day"]
        names = "; ".join(f"{p.label.lower()}: {p.stem.name} là {p.stem.ten_god_name}" for p in chart.pillars if p.position != "day")
        sections.insert(3, {"title": "Thập Thần đang lộ ra", "text": names[0].upper() + names[1:] + ". "
            "Đây là ba vai trò đang lộ trên can. Những vai trò còn lại cần xem trong tàng can và các quan hệ phối hợp; vắng trên can chưa có nghĩa vắng khỏi lá số.",
            "finding_refs": ["group:" + group for group, gods in GROUP_GODS.items()
                             if any(h.ten_god in gods for h in visible)]})
    summary = f"Nhật chủ {day.name} ({day.polarity} {day.element}), sinh tháng {chart.month.branch}. "
    summary += assessment.strength_name + f", với {len(facts.roots)} vị trí căn cùng hành và {len(facts.visible_support_refs)} can sinh trợ ngoài Nhật chủ. "
    if assessment.balance.preferred:
        summary += "Hướng phù ức tạm ưu tiên " + "、".join(assessment.balance.preferred) + "; cần đọc cùng các điều kiện phía dưới."
    else:
        summary += "Phần lấy dụng được giữ mở để tránh ép các tín hiệu khác hướng thành một kết luận."
    return NatalReading.model_validate({"topic": topic, "topic_name": TOPICS[topic], "question": question,
        "title": f"{day.name} {day.element} · {TOPICS[topic]}", "summary": summary,
        "highlights": ["strength", "roots", "balance", "relations"], "sections": sections, "narrative_version": NARRATIVE_VERSION})
