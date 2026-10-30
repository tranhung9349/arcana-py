"""Plain Vietnamese explanations of saved natal findings, without new predictions."""
from .bazi_models import NatalReading

NARRATIVE_VERSION = "bazi-narrative-2026-10-28-v2"
TOPICS = {"GENERAL": "Tổng quan", "CAREER": "Công việc", "WEALTH": "Tài chính", "STUDY": "Học tập", "RELATIONSHIPS": "Quan hệ"}
TOPIC_COPY = {
    "GENERAL": ("Kết quả này chưa phải kết luận về tính cách hay tương lai của bạn.",
                "Bạn có thể chọn một việc đang phân vân, ghi rõ các lựa chọn và điều muốn biết, rồi đọc theo chủ đề đó.", []),
    "CAREER": ("Lá số chưa cho biết bạn hợp nghề nào hoặc có nên đổi việc.",
               "Bạn có thể so hai công việc theo ba mục: việc phải làm, kỹ năng đã có và thời gian cần bỏ ra.", ["group:OFFICER", "group:OUTPUT"]),
    "WEALTH": ("Lá số chưa cho biết bạn kiếm tiền dễ hay khó, hoặc sẽ nhận được bao nhiêu.",
               "Với một khoản thu đang cân nhắc, bạn có thể ghi số tiền thực nhận, điều kiện được trả và chi phí đi kèm.", ["group:WEALTH", "group:OUTPUT"]),
    "STUDY": ("Lá số chưa xác định cách học nào hiệu quả nhất với bạn.",
              "Bạn có thể học thử một phần ngắn, đóng tài liệu rồi tự giải hoặc kể lại. So lỗi còn mắc với cách học trước.", ["group:RESOURCE", "group:OUTPUT"]),
    "RELATIONSHIPS": ("Một lá số chưa cho biết người khác nghĩ gì hoặc mối quan hệ sẽ đi đến đâu.",
                      "Nếu đang có bất đồng, bạn có thể chọn một việc cụ thể để trao đổi: mỗi người mong điều gì và có thể thống nhất điều gì.", ["group:SELF", "group:OFFICER"]),
}
STRENGTH_COPY = {
    "STRONG": "Trong cách đọc Bát Tự, các dấu hiệu hỗ trợ cho yếu tố đại diện cho bạn đang cùng một hướng khá rõ. Điều này không có nghĩa bạn giỏi hơn người khác hoặc mọi việc sẽ thuận.",
    "WEAK": "Trong cách đọc Bát Tự, yếu tố đại diện cho bạn có ít dấu hiệu hỗ trợ rõ. Điều này không có nghĩa bạn yếu đuối hoặc thiếu năng lực.",
    "MIXED": "Các dấu hiệu trong lá số chưa thống nhất, nên hiện chưa chọn được một hướng điều chỉnh rõ ràng. Đây không phải kết luận lá số tốt hay xấu.",
}


def compose(chart, facts, assessment, findings, topic, question):
    by_id = {f.finding_id: f for f in findings}
    meaning, action, topic_refs = TOPIC_COPY[topic]
    caution = "Gợi ý trên là việc để bạn tự kiểm tra trong thực tế, không phải dự báo từ ngày giờ sinh. Phần này chưa xác định thời điểm một việc sẽ xảy ra."
    sections = [
        {"title": "Bạn có thể làm gì?", "text": action, "finding_refs": ["strength", *topic_refs]},
        {"title": "Cần nhớ", "text": caution, "finding_refs": ["strength"]},
    ]

    def add(key, title, value):
        if key in by_id:
            sections.append({"title": title, "text": value, "finding_refs": [key]})

    day = chart.pillars[2].stem
    add("natal_context", "Ngày giờ sinh được dùng thế nào?",
        f"Lá số được lập từ năm, tháng, ngày và giờ sinh. Phép đọc lấy {day.name} {day.element}, ký hiệu của ngày sinh, làm điểm để so các phần còn lại. Ký hiệu này không tự nói lên tính cách của bạn.")
    add("roots", "Những dấu hiệu hỗ trợ đã tìm thấy",
        f"Bảng tra ghi nhận {len(facts.roots)} vị trí có cùng yếu tố {day.element} và {len(facts.visible_support_refs)} ký hiệu hỗ trợ ở phần hiện ra của lá số. Số lần xuất hiện không phải điểm năng lực, may mắn hay xác suất thành công.")
    add("strength", "Vì sao kết quả được đọc như vậy?", STRENGTH_COPY[assessment.strength])
    add("structure", "Các tên phân loại nói lên điều gì?",
        "Những tên phân loại bên dưới là cách nhóm các dấu hiệu trong lá số. Kết quả mới ghi nhận những nhóm cần xem xét, chưa xác nhận chúng có tác dụng ra sao. Không dùng một tên nhóm để chọn nghề hoặc dự đoán giàu nghèo.")
    add("special_caution", "Vì sao chưa chọn hướng điều chỉnh?",
        "Lá số này có trường hợp cần xem xét riêng. Phần phân tích chưa đủ để chọn cách điều chỉnh; không nên tự áp một công thức chung chỉ vì thấy ít dấu hiệu hỗ trợ.")
    balance = ("Phần đối chiếu tạm gợi ý " + ", ".join(assessment.balance.preferred) + ". Đây là tên các yếu tố trong phép đọc, chưa phải hướng dẫn chọn nghề, màu sắc hay vật phẩm."
               if assessment.balance.preferred else
               "Phần đối chiếu chưa chọn được yếu tố nào để ưu tiên. Kết quả đang được giữ mở; không có cơ sở biến nó thành một lời khuyên chắc chắn cho bạn.")
    add("balance", "Có thể làm gì với gợi ý theo yếu tố?", balance)
    climate = ("Hai cách đối chiếu đang cho gợi ý khác nhau: một cách xét quan hệ giữa các yếu tố, một cách xét nóng lạnh theo mùa sinh. Vì chưa xác định cách nào cần ưu tiên, chưa thể gộp thành một lựa chọn cho bạn."
               if assessment.climate_conflict else
               "Phần này xem thêm mùa sinh nóng hay lạnh trong cách đọc truyền thống. Nó chưa cho biết sức khỏe của bạn hoặc thời tiết nơi bạn sống, và chưa đủ để chọn một cách điều chỉnh cụ thể.")
    add("climate", "Vì sao có thêm phần xét mùa sinh?", climate)
    relation = ("Bảng tra có nhận diện các cặp hoặc nhóm ký hiệu liên quan nhau. Tên như hợp, xung hay hình chỉ gọi kiểu quan hệ giữa các ký hiệu; chúng chưa chứng minh ngoài đời có bất đồng, chia tay hay tai họa."
                if facts.relations else
                "Chưa thấy những kiểu quan hệ mà bảng tra hiện hỗ trợ. Điều này không phải bằng chứng cuộc sống hoặc các mối quan hệ của bạn sẽ luôn suôn sẻ.")
    add("relations", "Các dấu hiệu liên quan đến nhau có đáng lo?", relation)
    return NatalReading.model_validate({"topic": topic, "topic_name": TOPICS[topic], "question": question,
        "title": "Bát Tự · " + TOPICS[topic], "summary": STRENGTH_COPY[assessment.strength] + " " + meaning,
        "highlights": ["strength", "roots", "balance", "relations"], "sections": sections, "narrative_version": NARRATIVE_VERSION})
