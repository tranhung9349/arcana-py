"""Plain Vietnamese explanations of saved natal findings, without new predictions."""
from .bazi_models import NatalReading

NARRATIVE_VERSION = "bazi-narrative-2026-10-28-v2"
TINIX_NARRATIVE_VERSION = "bazi-tinix-narrative-v1"
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


TINIX_TOPIC_COPY = {
    "CAREER": ("Công việc qua các can lộ", {
        "DIRECT_OFFICER": "Chính Quan hướng phép đọc về vai trò có trách nhiệm và tiêu chí rõ. Khi cân nhắc một vị trí, hãy hỏi trước phần việc mình được quyền quyết định.",
        "SEVEN_KILLINGS": "Thất Sát hướng phép đọc về cách xử lý áp lực và yêu cầu khó. Khi cân nhắc một vị trí, hãy đối chiếu khối lượng việc với quyền hạn và nguồn hỗ trợ.",
        "EATING_GOD": "Thực Thần hướng phép đọc về kỹ năng có thể chuyển thành sản phẩm cụ thể. Bạn có thể chọn một việc đã làm tốt và xem kết quả nào chứng minh được kỹ năng đó.",
        "HURTING_OFFICER": "Thương Quan hướng phép đọc về cách trình bày và thử cách làm mới. Nếu đang đề xuất thay đổi, hãy thử ở quy mô nhỏ và ghi kết quả để trao đổi với nhóm.",
    }),
    "WEALTH": ("Tài chính qua các can lộ", {
        "DIRECT_WEALTH": "Chính Tài hướng phép đọc về khoản thu có điều kiện rõ. Hãy đối chiếu thu nhập thực nhận, thời điểm nhận và các khoản chi cố định.",
        "INDIRECT_WEALTH": "Thiên Tài hướng phép đọc về khoản thu theo cơ hội hoặc theo từng việc. Khi xem một cơ hội, hãy ghi rõ chi phí ban đầu, thời hạn và điều kiện được trả.",
    }),
    "STUDY": ("Học tập qua các can lộ", {
        "DIRECT_RESOURCE": "Chính Ấn hướng phép đọc về tài liệu nền và người hướng dẫn. Có thể học một phần theo trình tự rồi tự giải một bài để kiểm tra chỗ còn vướng.",
        "INDIRECT_RESOURCE": "Thiên Ấn hướng phép đọc về cách tự tìm tài liệu và thử nhiều cách hiểu. Có thể so hai cách giải trên cùng một bài để xem cách nào giảm lỗi.",
    }),
}


def compose_tinix(chart, facts, assessment, engine, topic, question):
    sections = []

    def add(title, text, *refs):
        sections.append({"title": title, "text": text, "finding_refs": list(refs)})

    day = chart.pillars[2]
    direction = {
        "STRONG": "phần trợ lực cho Nhật chủ trội hơn theo phép tính này",
        "WEAK": "phần tiết hao và chế ước Nhật chủ trội hơn theo phép tính này",
        "MIXED": "các dấu hiệu trợ lực và tiết hao cần được xét cùng nhau",
    }[assessment.strength]
    natal = f"Nhật chủ {day.stem.name} {day.stem.element} sinh vào tháng {chart.month.branch}. Phép cân bằng Ngũ Hành ghi nhận {direction}."
    summary = natal

    if topic in TINIX_TOPIC_COPY:
        title, copy = TINIX_TOPIC_COPY[topic]
        stems = [p for p in chart.pillars if p.stem.ten_god in copy]
        matches = [f"{p.stem.ten_god_name} ở trụ {p.label.lower()}" for p in stems]
        summary = ("Xét các thiên can hiện ra, lá số có " + ", ".join(matches) + "." if matches else
                   "Ở các thiên can hiện ra, nhóm dấu hiệu của chủ đề này chưa xuất hiện. Khi luận sâu cần xem thêm tàng can và đại vận.")
        meaning = " ".join(copy[god] for god in dict.fromkeys(p.stem.ten_god for p in stems))
        add(title, meaning or "Phần này xét thiên can lộ của trụ năm, tháng và giờ. Những dấu hiệu nằm trong tàng can cần được đọc cùng vị trí và mùa sinh.", "natal_context")
    elif topic == "RELATIONSHIPS":
        relations = [r for r in facts.relations if day.fact_id in r.pillar_refs and r.kind in {"CLASH", "SIX_COMBINATION"}]
        labels = [("xung " if r.kind == "CLASH" else "hợp ") + r.name for r in relations]
        summary = ("Chi ngày " + day.branch + " tham gia các quan hệ " + ", ".join(labels) + " trong Tứ Trụ." if labels else
                   f"Chi ngày {day.branch} chưa có cặp lục hợp hoặc lục xung trực tiếp trong bốn trụ.")
        add("Đọc quan hệ quanh chi ngày", "Hợp và xung mô tả cách các chi tương tác trong phép đọc. Khi liên hệ với đời sống, hãy đối chiếu với cách hai người trao đổi và giải quyết bất đồng.", "relations")
    else:
        add("Bốn trụ làm căn cứ", " · ".join(f"{p.label} {p.stem.name} {p.branch}" for p in chart.pillars) + ".", "natal_context")

    scores = engine.result["analysis"]["can_bang_ngu_hanh"]["nhan_dinh"]["diem_tuong_doi"]
    add("Vì sao có kết luận này?", f"{natal} Điểm trợ lực là {scores['ho_tro']}, điểm tiết hao và chế ước là {scores['khac_che']}.", "strength")

    balance = assessment.balance
    groups = [f"{label} {', '.join(elements)}" for label, elements in (
        ("ưu tiên", balance.preferred), ("hỗ trợ", balance.supporting), ("tiết chế", balance.restrain)
    ) if elements]
    balance_text = "Phép cân bằng gợi ý " + ", ".join(groups) + "." if groups else "Phép cân bằng chưa chọn được hành cần ưu tiên."
    add("Hướng cân bằng Ngũ Hành", balance_text, "balance")

    year = engine.target_year
    annual = engine.result["annual"]
    cycle = next((row for row in engine.result["luck_cycles"] if row["start"] <= year <= row["end"]), None)
    timing = f"Năm {year} là {annual['ganzhiVN']}. Quan hệ của can năm với Nhật chủ được xếp vào {annual['shishen']}."
    if cycle:
        timing += f" Năm này nằm trong Đại vận {cycle['can_chi']} ({cycle['start']}–{cycle['end']})."
    add("Đại vận và năm đang xem", timing, "luck_cycles")

    if assessment.climate_conflict:
        add("Điều kiện làm đổi cách đọc", f"Phép xét mùa sinh cần {assessment.climate_element}, trong khi phép cân bằng xếp hành này vào nhóm tiết chế. Cần xét riêng hai kết quả trước khi chọn hướng ưu tiên.", "climate", "balance")
    elif assessment.possible_following:
        add("Điều kiện làm đổi cách đọc", "Mức vượng hoặc nhược được đánh dấu là trường hợp có thể thuộc ngoại cách. Cần xác định có đủ điều kiện theo cách đó trước khi áp dụng hướng cân bằng thông thường.", "strength", "balance")
    else:
        add("Điều kiện làm đổi cách đọc", "Lời luận dựa vào bốn trụ và năm xem đã chọn. Nếu giờ sinh sát ranh đổi trụ, hãy đối chiếu lại giờ trước khi dùng kết quả để suy ngẫm.", "natal_context", "luck_cycles")
    return NatalReading(topic=topic, topic_name=TOPICS[topic], question=question, title="Bát Tự · " + TOPICS[topic],
                        summary=summary, highlights=["natal_context", "strength", "balance", "luck_cycles"],
                        sections=sections, narrative_version=TINIX_NARRATIVE_VERSION)
