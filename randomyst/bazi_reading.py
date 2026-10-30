"""Vietnamese interpretation of the saved Bazi result, without recalculating it."""
from copy import deepcopy

from .bazi import SOURCE_COMMIT, SOURCE_PATH, STEM_ELEMENTS
from .models import ModuleReading
from .sampling import GENERATES, element_of
from .time_engine import BRANCH_ELEMENTS

REASONS = {
    "FOLLOW_STRONG": ("Thuận theo thế vượng", "Lá số được xếp vào nhánh Tòng Vượng: trợ lực cho Nhật chủ đã tập trung mạnh. Phép xét này chọn thuận theo thế đang có, ưu tiên hành của Nhật chủ và hành sinh trợ cho nó."),
    "FOLLOW_WEALTH": ("Thuận theo nhóm Tài", "Nhật chủ được xếp vào nhánh rất ít trợ lực, trong khi nhóm Tài nổi trội. Nhánh Tòng Tài chọn theo thế Tài thay vì áp dụng cách bổ trợ Nhật chủ của lá số thông thường."),
    "FOLLOW_OFFICER": ("Thuận theo nhóm Quan Sát", "Nhật chủ được xếp vào nhánh rất ít trợ lực, trong khi nhóm Quan Sát nổi trội. Nhánh Tòng Sát chọn theo thế này; đây là cách đọc riêng của ngoại cách."),
    "FOLLOW_OUTPUT": ("Thuận theo nhóm Thực Thương", "Nhật chủ được xếp vào nhánh rất ít trợ lực, trong khi nhóm sinh xuất nổi trội. Nhánh Tòng Nhi chọn theo thế sinh xuất, thay vì chỉ bổ thêm hành cùng Nhật chủ."),
    "STRONG_RESOURCE": ("Điều tiết nguồn sinh trợ", "Nhật chủ được xếp vào nhóm vượng, với trợ lực từ Ấn nhiều hơn nhóm đồng hành. Phép xét lá số chọn Tài để điều tiết phần sinh trợ đang tập trung, tạo thêm thế cân bằng."),
    "STRONG_SELF_OFFICER": ("Dùng Quan Sát để điều tiết", "Nhật chủ được xếp vào nhóm vượng và nhóm Quan Sát hiện diện đủ rõ. Nhánh này ưu tiên Quan Sát, tức nhóm khắc Nhật chủ, để điều tiết thế vượng."),
    "STRONG_SELF_OUTPUT": ("Mở đường sinh xuất", "Nhật chủ được xếp vào nhóm vượng. Nhánh này ưu tiên Thực Thương, tức hành do Nhật chủ sinh ra, để có đường sinh xuất thay vì tiếp tục dồn thêm trợ lực."),
    "WEAK_OFFICER": ("Bổ trợ trước áp lực Quan Sát", "Nhật chủ được xếp vào nhóm nhược, với nhóm Quan Sát ít nhất ngang nhóm Tài. Phép xét này chọn Ấn, tức hành sinh Nhật chủ, để bổ sung trợ lực."),
    "WEAK_WEALTH": ("Củng cố hành của Nhật chủ", "Nhật chủ được xếp vào nhóm nhược, trong khi nhóm Tài nổi hơn nhóm sinh xuất. Nhánh này ưu tiên hành cùng Nhật chủ để tăng trợ lực cho phía đang yếu."),
    "WEAK_OUTPUT": ("Bù trợ lực khi sinh xuất", "Nhật chủ được xếp vào nhóm nhược và cần xét phần sinh xuất. Nhánh này chọn Ấn, tức hành sinh Nhật chủ, làm nguồn bổ trợ."),
}
STRUCTURES = {
    "Chính Quan Cách": "Quan là nhóm khắc Nhật chủ, được dùng để đọc quan hệ với khuôn phép và sự điều tiết. Cần xét Quan có cân xứng với sức của Nhật chủ hay không.",
    "Thất Sát Cách": "Sát thuộc nhóm khắc Nhật chủ. Điểm cần đọc là sức chế ước này có được cân bằng bằng trợ lực hoặc đường tiết chế hay không; tên cách không tự quyết định cả lá số tốt hay xấu.",
    "Chính Tài Cách": "Tài là nhóm do Nhật chủ khắc. Phép đọc đặt trọng tâm vào quan hệ giữa khả năng đảm đương của Nhật chủ và phần Tài, rồi mới xét cần bổ trợ hay điều tiết.",
    "Thiên Tài Cách": "Tài là nhóm do Nhật chủ khắc. Cần đọc cùng thế vượng nhược để biết lá số đang nghiêng về bổ trợ Nhật chủ hay thuận theo Tài.",
    "Thực Thần Cách": "Thực Thần thuộc nhóm Nhật chủ sinh ra. Đây là đường sinh xuất: có thể giúp điều tiết thế vượng, nhưng cũng làm Nhật chủ phải dành thêm lực khi đang nhược.",
    "Thương Quan Cách": "Thương Quan thuộc nhóm Nhật chủ sinh ra. Trọng tâm là đường sinh xuất và quan hệ của nó với các nhóm khác; cần xét sức Nhật chủ trước khi kết luận nên tăng hay giảm.",
    "Chính Ấn Cách": "Ấn là nhóm sinh Nhật chủ. Trợ lực này hữu ích khi Nhật chủ nhược, nhưng nếu đã tập trung quá nhiều thì phép xét lá số có thể ưu tiên điều tiết.",
    "Thiên Ấn Cách": "Ấn là nhóm sinh Nhật chủ. Cần đọc lượng trợ lực cùng phần đồng hành và phần sinh xuất, thay vì mặc định cứ thêm sinh trợ là tốt.",
    "Kiến Lộc Cách/Nguyệt Kiếp": "Tháng sinh có quan hệ nổi bật với hành Nhật chủ. Phép đọc chú ý phần đồng hành và cách điều tiết, rồi kết hợp thế vượng nhược của cả lá số.",
    "Tòng Vượng Cách": "Đây là nhánh ngoại cách thuận theo thế vượng. Cách chọn hành vì vậy khác với phép cân bằng của nội cách thông thường.",
    "Tòng Tài Cách": "Đây là nhánh ngoại cách thuận theo nhóm Tài đang nổi trội. Không áp dụng máy móc cách bổ Nhật chủ của nội cách.",
    "Tòng Sát Cách": "Đây là nhánh ngoại cách thuận theo nhóm Quan Sát đang nổi trội. Cần giữ cách đọc ngoại cách khi giải thích lựa chọn hành.",
    "Tòng Nhi Cách": "Đây là nhánh ngoại cách thuận theo phần sinh xuất. Hành được ưu tiên đi theo thế này thay vì chỉ bổ thêm hành của Nhật chủ.",
}


class BaziInterpreter:
    version = "bazi-reading-2026-10-28-v2"

    def interpret(self, draw, source_reading):
        b = draw["trace"]["bazi"]
        natal = b["natal"]
        day = natal["pillars"][2]
        day_element = STEM_ELEMENTS[natal["gans"][2]]
        month = natal["pillars"][1]
        month_element = BRANCH_ELEMENTS[natal["zhis"][1]]
        primary, calculated = b["primary_used"], b["primary_dung_than"]
        evidence = [{"evidence_id": "facts:bazi", "kind": "SAVED_FACT", "title": "Lá số của phiên đã lưu",
                     "text": f"Nhật chủ {day['stem']} ({day_element}); tháng {month['branch']} ({month_element}); {b['strength']}; {b['structure']}."},
                    {"evidence_id": "rules:bazi", "kind": "IMPLEMENTATION_RULE", "title": "Phép xét vượng nhược và Dụng Thần",
                     "text": "Nhánh tính Bát Tự đã dùng khi gieo: " + b["reason_code"],
                     "url": f"https://github.com/vhphuoc1102/tinix-bazi/blob/{SOURCE_COMMIT}/{SOURCE_PATH}"},
                    {"evidence_id": "facts:numbers", "kind": "SAVED_FACT", "title": "Bộ số và hành ưu tiên đã dùng",
                     "text": " · ".join(draw["numbers"]) + "; hành ưu tiên: " + primary}]
        evidence.extend({"evidence_id": card["evidence_id"], "kind": "SOURCE_ORIGINAL", "title": card["title"],
                         "text": card["text"], "url": card["source"]["url"]} for card in source_reading["cards"])
        month_support = ("Mùa sinh được tính là một dấu hiệu hỗ trợ trong phép đối chiếu này."
                         if b["month_support"] else "Mùa sinh không được tính là dấu hiệu hỗ trợ trong phép đối chiếu này.")
        reason = REASONS.get(b["reason_code"])
        reason_title, reason_text = reason or ("Lựa chọn được lưu trong lá số", "Phiên đã lưu chọn hành " + calculated + ". Chưa có lời diễn giải riêng khớp nhánh tính này.")
        evidence.append({"evidence_id": "rules:reason", "kind": "IMPLEMENTATION_RULE", "title": reason_title,
                         "text": reason_text, "url": evidence[1]["url"]})
        structure_refs = [card["evidence_id"] for card in source_reading["cards"] if card["text_type"] == "BAZI_STRUCTURE"]
        structure_text = STRUCTURES.get(b["structure"]) if structure_refs else None
        sections = [
            {"title": "Hồ sơ sinh được dùng thế nào?", "text": f"Ký hiệu ngày sinh {day['stem']} {day_element} được lấy làm điểm so với các phần còn lại của lá số. " + month_support + " Các ký hiệu này không tự mô tả tính cách hay năng lực của bạn.",
             "references": ["facts:bazi", "rules:bazi"]},
            {"title": "Vì sao bộ số ưu tiên yếu tố này?", "text": f"Phép đối chiếu hồ sơ sinh chọn {calculated} làm yếu tố ưu tiên khi chấm bộ số. Đây là quy tắc chọn số của phiên gieo, chưa phải hướng dẫn chọn nghề, màu sắc hay vật phẩm.",
             "references": ["facts:bazi", "rules:bazi", "rules:reason"]},
            {"title": "Tên phân loại có ý nghĩa gì?", "text": "Bảng tra đặt tên nhóm của lá số là " + b["structure"] + ". Tên này mô tả cách nhóm các ký hiệu; nó không xác nhận bạn giàu nghèo, hợp nghề nào hay sẽ gặp sự kiện gì."
             + ("" if structure_text else " Tập nguồn chưa có mục khớp chính xác tên nhóm này để giải thích thêm."),
             "references": ["facts:bazi", *structure_refs]},
            {"title": "Các yếu tố được dùng khi chọn số",
             "text": "Ưu tiên: " + ", ".join(b["dung_than"]) + ". Hỗ trợ: " + ", ".join(b["hy_than"]) + ". Cần tiết chế: " + ", ".join(b["ky_than"]) + ". Đây là cách đối chiếu các nhóm số, không phải phán xét tốt xấu về con người.",
             "references": ["facts:bazi", "rules:bazi"]},
        ]
        if b["overridden"]:
            sections.append({"title": "Lựa chọn riêng cho phiên gieo", "text": f"Lá số tính ra hành {calculated}, còn bạn chọn {primary} làm hành ưu tiên cho bộ số. Phần luận lá số vẫn theo kết quả đã tính; phần giải thích bộ số dùng lựa chọn {primary} của bạn.", "references": ["facts:bazi", "facts:numbers"]})
        supportive = [n for n in draw["numbers"] if element_of(int(n)) == primary or GENERATES[element_of(int(n))] == primary]
        link = (f"Các số {' · '.join(supportive)} được xếp cùng nhóm hoặc nhóm hỗ trợ {primary}, nên có liên quan trực tiếp đến yếu tố được ưu tiên khi chọn số."
                if supportive else f"Bộ này không có số thuộc nhóm {primary} hoặc nhóm hỗ trợ nó; điểm còn phụ thuộc các tiêu chí khác của phiên gieo.")
        sections.append({"title": "Lá số liên hệ với bộ số như thế nào?", "text": link + " Bộ số được xét đồng thời với lá số sinh và quẻ tại thời điểm gieo, nên không chỉ có một hành hiện diện.", "references": ["facts:numbers", "rules:bazi"]})
        return ModuleReading.model_validate({
            "module": "BAZI", "version": self.version, "title": "Hồ sơ sinh liên quan gì đến bộ số?",
            "summary": f"Hồ sơ sinh được dùng để chọn {calculated} làm yếu tố ưu tiên khi chấm số. Kết quả này giải thích cách bộ số được chọn; chưa cho biết khả năng trúng hoặc vận may của bạn.",
            "sections": sections, "evidence": evidence,
            "facts": {"reason_code": b["reason_code"], "day_element": day_element, "birth_month_branch": month["branch"],
                      "birth_season": source_reading["birth_season"], "primary_calculated": calculated, "primary_used": primary,
                      "strength": b["strength"], "structure": b["structure"], "overridden": b["overridden"],
                      "supportive_numbers": supportive, "natal": deepcopy(natal)},
            "limitations": ["Phần luận diễn giải nhánh tính đã lưu của lá số; chưa triển khai đại vận, lưu niên hoặc luận toàn bộ đời người.",
                            "Các phân loại thuộc cách đọc Bát Tự của nguồn đã ghim; không phải đánh giá khoa học về tính cách hay năng lực.",
                            *[gap["message"] for gap in source_reading["source_gaps"]]],
        }).model_dump(mode="json")
