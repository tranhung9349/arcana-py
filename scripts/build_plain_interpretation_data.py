"""Build original Vietnamese editorial examples; no model call or network access.

Raw source transcriptions must already be present. Do not silently refresh them.
"""
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "data/interpretation/plain_v2"
VERSION = "plain-vietnamese-2026-10-26-v2"
SOURCES = []
CASES = []


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def source(key, title, text, methods, path=None, url=None, state="PINNED_TRANSCRIPTION"):
    if path:
        raw = ROOT / path
        if text not in raw.read_text():
            raise ValueError("Quotation missing: " + key)
    item = {"id": key, "title": title, "text": text, "sha256": sha256(text.encode()).hexdigest(),
            "url": url, "kind": "PRODUCT_POLICY" if key == "editorial:scope" else "PRIMARY_TEXT",
            "methods": methods, "raw_path": path, "source_state": state}
    SOURCES.append(item)


def case(key, method, topic, signals, question, facts, source_ids, summary, analyses, option, limit):
    """Each claim lists explicit indexes of the synthetic facts it actually uses."""
    evidence = [{k: s[k] for k in ("id", "title", "text", "sha256", "url", "kind")}
                for s in SOURCES if s["id"] in source_ids + ["editorial:scope"]]
    fact_rows = [{"id": f"{key}:f{i+1}", "text": text} for i, text in enumerate(facts)]
    def refs(indexes):
        return [fact_rows[i-1]["id"] for i in indexes]
    def claim(row):
        text, indexes = row
        return {"label": "AI_INTERPRETATION", "text": text, "fact_refs": refs(indexes), "evidence_refs": source_ids}
    unresolved = key in ("bazi-03-mixed", "liuyao-02-selection")
    context = {"schema_version": "plain-reading-context-v2", "context_id": "example:" + key,
               "method": method, "analysis_profile": "SYNTHETIC_TEACHING_SLICE", "topic": topic,
               "question": question, "signals": signals, "facts": fact_rows,
               "findings": [{"id": key + ":finding", "text": summary[0], "status": "UNRESOLVED" if unresolved else "CONDITIONAL",
                             "fact_refs": refs(summary[1]), "evidence_refs": source_ids}],
               "evidence": evidence, "limitations": [limit]}
    response = {"schema_version": "plain-reading-response-v2", "context_id": context["context_id"],
                "summary": claim(summary), "analysis": [claim(a) for a in analyses],
                "practical_options": [{"kind": "MODERN_APPLICATION", "text": option[0], "fact_refs": refs(option[1])}],
                "limits": [limit]}
    CASES.append({"id": key, "review_status": "EDITORIAL_DRAFT_NOT_EXPERT_REVIEWED",
                  "case_origin": "ORIGINAL_SYNTHETIC_EXAMPLE_NOT_HISTORICAL_CASE", "context": context, "response": response})


def build():
    from research_tools.interpretation_prompt import Context, Response, validate_response
    SOURCES.clear(); CASES.clear()
    b = ["BAZI_NATAL_V1"]; m = ["MAIHOA_INTERNAL"]; l = ["LIUYAO_NAJIA"]; z = ["ZHOUYI_TEXT"]
    def bazi_src(key, filename, title, text):
        meta = json.loads((ROOT / f"data/reference/bazi/{filename}.source.json").read_text())
        source(key, title, text, b, f"data/reference/bazi/{filename}.wikitext", meta["url"])
    bazi_src("dtt:strength", "dtt_strength", "Địch Thiên Tủy · Suy vượng", "旺則宜洩宜傷，衰則喜幫喜助，子平之理也，然旺中有衰者存，不可損也。衰中有旺者存，不可益也。")
    bazi_src("dtt:month", "dtt_month", "Địch Thiên Tủy · Nguyệt lệnh", "月令提綱，譬之宅也，人元用事之神，宅之向也，不可以不卜。")
    bazi_src("dtt:climate", "dtt_climate", "Địch Thiên Tủy · Hàn noãn", "天道有寒暖，發育萬物，人道得之，不可過也。")
    bazi_src("smt:relations", "smt_relations", "Tam Mệnh Thông Hội · Luận tam hình", "凡见刑不可便以凶论")
    # Only short original-text excerpts were verified in the web index. The host
    # timed out for direct capture; never claim a full edition/revision was pinned.
    for key, chapter, text in [
        ("ziping:use", 3721, "八字用神，專求月令"),
        ("ziping:formation", 3722, "用神專求月令，然以四柱配之，必有成敗。"),
        ("ziping:climate", 3727, "論命惟以月令用神爲主，然亦須配氣候而互參之。")]:
        source(key, "Tử Bình Chân Thuyên · " + {3721: "Luận Dụng thần", 3722: "Thành bại cứu ứng", 3727: "Phối khí hậu"}[chapter],
               text, b, url=f"https://www.donglishuzhai.net/chapter/{chapter}.html", state="WEB_EXCERPT_NOT_EDITION_PINNED")
    mh_path = "data/reference/maihoa/volume_2.wikitext"
    mh_url = "https://zh.wikisource.org/w/index.php?oldid=1441921"
    for key, title, text in [
        ("mh:roles", "Thể và Dụng", "體為主，用為事。"),
        ("mh:sequence", "Diễn tiến Hỗ và Biến", "用吉變凶者，先吉後凶；用凶變吉者，先凶後吉。"),
        ("mh:wealth", "Cầu tài", "體生用，財有損耗之憂；用生體，財有進益之喜。"),
        ("mh:trade", "Giao dịch", "體生用，難成，或因交易有失。用生體，即成，成必有財。"),
        ("mh:planning", "Mưu sự", "體克用，謀雖可成，但成遲。用克體，求謀不成，謀亦有害。")]:
        source(key, "Mai Hoa Dịch Số · " + title, text, m, mh_path, mh_url)
    for key, filename, title, text in [
        ("ly:wealth", "zsby_8", "Dụng thần · Tài vật", "一切使用之財物亦以妻財爻爲用神。"),
        ("ly:document", "zsby_8", "Dụng thần · Văn thư", "章奏、文書及書館文契也以父母爻爲用神"),
        ("ly:roles", "zsby_9", "Nguyên thần và Kỵ thần", "元神，生用神之神卽爲元神。忌神克用神之爻也。"),
        ("ly:month", "zsby_16", "Nguyệt tướng", "月將卽是月建又爲月令。掌一月之權，司三旬之令。"),
        ("ly:day", "zsby_17", "Nhật thần", "沖旺相之靜爻，旣爲暗動，沖衰弱之靜爻爲日破"),
        ("zy:qian1", "zhouyi_qian", "Càn · Sơ Cửu", "潛龍勿用。"),
        ("zy:jiji", "zhouyi_jiji", "Ký Tế · Quẻ từ", "初吉終亂。")]:
        meta = json.loads((ROOT / f"data/reference/interpretation/{filename}.source.json").read_text())
        source(key, ("Chu Dịch · " if key.startswith("zy:") else "Tăng San Bốc Dịch · ") + title, text,
               z if key.startswith("zy:") else l, f"data/reference/interpretation/{filename}.wikitext", meta["url"])
    source("editorial:scope", "Quy ước biên tập và phạm vi ví dụ", "Các ca là lát cắt dữ kiện giả định do biên tập viên soạn để dạy cách diễn đạt; không phải mệnh lệ cổ hoặc dự báo đã nghiệm. Trạng thái phân tích là đầu vào được cung cấp, không được suy ngược từ ví dụ. Các gợi ý đời sống là ứng dụng hiện đại để tự đối chiếu, không phải lời cổ thư.", b+m+l+z,
           state="PRODUCT_EDITORIAL_POLICY")

    case("bazi-01-strong", b[0], "GENERAL", ["STRONG", "NATAL_ONLY"], "Lá số này nên phát huy điều gì?",
         ["Nhật chủ Giáp Mộc; engine đánh giá STRONG theo profile natal v1.", "Có căn Mộc bản khí và can sinh trợ ngoài Nhật chủ.", "Hướng phù ức ưu tiên Hỏa, ở mức CONDITIONAL."], ["dtt:strength"],
         ("Theo phần phân tích hiện có, điểm cần chú ý là dùng phần được hỗ trợ để tạo ra kết quả cụ thể, thay vì chỉ tìm thêm hỗ trợ.", [1,2,3]),
         [("Lá số có cả gốc Mộc trong chi và can nâng đỡ Giáp Mộc. Vì vậy engine xếp vào nhóm thiên vượng, nghĩa là bên sinh trợ đang nổi bật trong cách tính này.", [1,2]),
          ("Hỏa là phần Mộc sinh ra, nên được chọn làm hướng đưa phần sinh trợ thành đầu ra. Đây là quan hệ trong lá số; chưa đủ để khẳng định bạn hướng ngoại hay hợp một nghề cụ thể.", [1,3])],
         ("Bạn có thể chọn một việc đang học hoặc chuẩn bị, rồi đặt một sản phẩm nhỏ để hoàn thành: bản nháp, bài trình bày hoặc bản thử nghiệm.", [3]),
         "Phân loại thiên vượng có điều kiện; chưa phân tích vận và chưa xác định nghề phù hợp.")
    case("bazi-02-weak", b[0], "CAREER", ["WEAK", "NATAL_ONLY"], "Tôi nên chú ý gì khi nhận thêm việc?",
         ["Engine đánh giá WEAK; Nhật chủ không được mùa trợ, không có căn cùng hành và không có can sinh trợ lộ.", "Có Ấn trong tàng can; hướng phù ức ưu tiên nhóm sinh trợ, CONDITIONAL."], ["dtt:strength"],
         ("Theo cách đọc này, nên xem điều kiện hỗ trợ trước khi bàn đến việc gánh thêm yêu cầu. Phân tích chưa xác định bạn có nên nhận công việc cụ thể hay không.", [1,2]),
         [("Thân nhược ở đây nghĩa là Nhật chủ ít được sinh trợ theo dữ kiện đã tính. Nó không nói bạn yếu sức, kém năng lực hoặc thiếu ý chí.", [1]),
          ("Ấn là nhóm sinh trợ cho Nhật chủ; trong lá số này nó nằm ở phần tàng can. Khi dùng hình ảnh này để suy ngẫm về công việc, trọng tâm là chỗ dựa trước yêu cầu mới, không phải mặc định sẽ có người giúp.", [2])],
         ("Trước khi nhận thêm việc, bạn có thể làm rõ ba điều: phần nào đã thành thạo, ai có thể hướng dẫn và thời gian thực tế để hoàn thành.", [1,2]),
         "Chưa có mô tả công việc và khối lượng thực tế; lá số không xác nhận khả năng đảm nhiệm một vị trí.")
    case("bazi-03-mixed", b[0], "GENERAL", ["MIXED", "NATAL_ONLY"], "Vậy mệnh tôi đang tốt hay xấu?",
         ["Assessment.strength=MIXED: có các tín hiệu sinh trợ và tiêu hao đan xen.", "Assessment.balance.state=UNRESOLVED; chưa chọn hành ưu tiên."], ["dtt:strength"],
         ("Phần phân tích này chưa đủ cơ sở gộp lá số thành tốt hoặc xấu. Nó cho thấy các yếu tố tác động khác hướng, nên chưa chọn một hành để ưu tiên.", [1,2]),
         [("MIXED nghĩa là các tín hiệu chưa cùng chỉ về một phía. Nhãn này không có nghĩa ngũ hành đã cân bằng hay số phận ở mức trung bình.", [1]),
          ("Vì hướng điều chỉnh còn để mở, chưa có căn cứ yêu cầu bạn tăng một hành, đổi màu sắc hay đổi nghề theo hành đó.", [2])],
         ("Bạn có thể chọn một chủ đề cụ thể như học tập hoặc công việc; điều đó giúp lời giải tập trung vào các yếu tố liên quan thay vì một đánh giá chung.", [1,2]),
         "Engine chưa đánh giá đầy đủ ngoại cách và cứu ứng; chưa kết luận Dụng thần.")
    case("bazi-04-structure", b[0], "CAREER", ["CANDIDATE_STRUCTURE", "NATAL_ONLY"], "Có Chính Quan là hợp làm quản lý đúng không?",
         ["Chính Quan được nhận diện là ứng viên cách cục từ chi tháng và can thấu.", "Trạng thái cách cục CONDITIONAL; chưa xét đầy đủ thành cách, phá cách và cứu ứng."], ["ziping:use", "ziping:formation"],
         ("Lá số mới có dấu hiệu để khảo sát Chính Quan; chưa đủ căn cứ kết luận bạn hợp làm quản lý.", [1,2]),
         [("Chính Quan là tên một quan hệ ngũ hành so với Nhật chủ. Ở đây nó được nhận diện trong phần tháng sinh, nên trở thành một ứng viên cách cục để đọc tiếp.", [1]),
          ("Tử Bình Chân Thuyên còn xét sự phối hợp của cả bốn trụ để bàn thành bại. Vì engine chưa xét đủ phần này, không thể chuyển tên ứng viên thành một phẩm chất hoặc lời hứa thăng tiến.", [2])],
         ("Nếu đang cân nhắc quản lý, bạn có thể đối chiếu bằng một nhiệm vụ điều phối nhỏ: giao việc, theo dõi tiến độ và nhận phản hồi từ người cùng làm.", [1,2]),
         "Ứng viên cách cục chưa phải thành cách; phân tích chưa xác định nghề hoặc thời điểm thăng tiến.")
    case("bazi-05-climate", b[0], "GENERAL", ["CLIMATE_CONFLICT", "NATAL_ONLY"], "Vì sao một đoạn cần Hỏa, đoạn khác lại cần Thủy?",
         ["Hướng phù ức của engine tạm ưu tiên Thủy.", "Gợi ý Điều hậu theo mùa là Hỏa; climate_conflict=true.", "Điều hậu hiện chỉ là gợi ý mùa, chưa có bảng đầy đủ theo Can và tháng."], ["dtt:climate", "ziping:climate"],
         ("Hai đoạn đang trả lời hai vấn đề khác nhau: một bên xem quan hệ sinh trợ, một bên xem nóng lạnh theo mùa. Engine đã ghi nhận chúng khác hướng và chưa hợp nhất thành một kết luận.", [1,2,3]),
         [("Hướng phù ức Thủy là kết quả của nhánh cân nhắc sinh trợ trong lá số. Nó không tự thay thế việc xem điều kiện mùa sinh.", [1]),
          ("Gợi ý Hỏa thuộc phần Điều hậu, tức cách đọc nóng lạnh theo mùa. Vì phần này còn sơ bộ, chưa thể bảo bạn phải chọn Hỏa hoặc Thủy trong sinh hoạt.", [2,3])],
         ("Bạn có thể đọc hai nhận định như hai câu hỏi riêng; nếu muốn chốt một hành ưu tiên, cần kiểm tra thêm phần Điều hậu cụ thể trước.", [1,2,3]),
         "Bảng Điều hậu đầy đủ chưa được triển khai; chưa chốt một hành để áp dụng chung.")
    case("bazi-06-wealth", b[0], "WEALTH", ["NATAL_ONLY", "WEALTH_EXPOSED"], "Có Tài lộ là tôi dễ có tiền không?",
         ["Có Chính Tài trên can năm.", "Thực Thương không lộ trên can; có thể còn trong tàng can.", "Khí thế Nhật chủ MIXED; hướng phù ức UNRESOLVED."], ["dtt:strength"],
         ("Có Chính Tài chỉ xác nhận một quan hệ trong lá số; chưa cho biết bạn kiếm được bao nhiêu hay tiền đến dễ hay khó.", [1,3]),
         [("Tài là nhóm ngũ hành do Nhật chủ khắc; ở đây Chính Tài xuất hiện trên can năm. Nhãn này không phải số dư tài khoản hoặc bằng chứng thu nhập ổn định.", [1]),
          ("Thực Thương là nhóm Nhật chủ sinh ra, thường được đặt cạnh Tài khi khảo sát đường sinh Tài. Nhóm này chưa lộ trên can, nhưng không vì thế mà kết luận bạn thiếu kỹ năng hoặc không có cách kiếm tiền.", [2,3])],
         ("Để đối chiếu với việc thực tế, bạn có thể ghi rõ sản phẩm hoặc dịch vụ mình tạo ra, ai trả tiền cho nó và tiền thường về khi nào.", [1,2]),
         "Đây là mệnh cục; chưa có dữ kiện thu nhập hoặc Đại vận–Lưu niên để bàn một thời kỳ tài chính.")
    case("bazi-07-study", b[0], "STUDY", ["NATAL_ONLY", "RESOURCE_EXPOSED"], "Tôi nên thay đổi cách học thế nào?",
         ["Chính Ấn lộ trên can tháng.", "Thực Thương chưa lộ trên can.", "Engine chưa đánh giá năng lực học tập thực tế."], ["dtt:month"],
         ("Nếu dùng lá số làm gợi ý tự đối chiếu, điểm đáng thử là chuyển điều đã đọc thành bài làm cụ thể. Dữ kiện chưa đủ để xác định cách học nào tốt nhất cho bạn.", [1,2,3]),
         [("Ấn là nhóm sinh trợ cho Nhật chủ và ở đây xuất hiện trên can tháng. Khi bàn chuyện học, có thể dùng nó làm hình ảnh cho phần tiếp nhận kiến thức, chứ chưa chứng minh bạn học giỏi.", [1,3]),
          ("Thực Thương là nhóm Nhật chủ sinh ra, được dùng như hình ảnh cho phần diễn đạt và thực hành. Chưa lộ trên can không có nghĩa bạn thiếu sáng tạo hay không biết vận dụng.", [2,3])],
         ("Bạn có thể thử học một phần ngắn rồi đóng tài liệu, tự giải một bài hoặc giải thích lại bằng lời của mình; so kết quả với cách học cũ.", [1,2]),
         "Các liên hệ với thói quen học là ứng dụng biên tập hiện đại; cần đối chiếu bằng kết quả học thực tế.")
    case("bazi-08-relations", b[0], "RELATIONSHIPS", ["NATAL_ONLY", "HAS_RELATIONS"], "Lá số có hình là tình cảm sẽ đổ vỡ à?",
         ["Nhận diện Tý–Mão hình có liên quan chi ngày.", "Engine chỉ ghi nhận tổ hợp Chi, chưa đánh giá cứu giải toàn cục.", "Chưa có lá số hoặc thông tin tương tác của người còn lại."], ["smt:relations"],
         ("Chưa thể kết luận đổ vỡ từ tổ hợp này. App mới nhận diện một quan hệ giữa các Chi, chưa xác định một sự kiện tình cảm.", [1,2,3]),
         [("Chữ hình ở đây là tên một tổ hợp trong phép luận, không phải thông tin rằng người kia sẽ làm hại bạn. Nguồn Tam Mệnh Thông Hội cũng lưu ý không thấy hình là lập tức luận hung.", [1,2]),
          ("Muốn bàn một mối quan hệ cụ thể còn cần ngữ cảnh hai người. Một lá số không cho phép xác định tính cách, sự chung thủy hay ý định của người còn lại.", [3])],
         ("Nếu có chuyện đang vướng, bạn có thể nêu một tình huống cụ thể và điều muốn thống nhất với nhau, chẳng hạn cách chia sẻ thời gian hoặc trách nhiệm.", [2,3]),
         "Chưa luận hợp hai lá số hoặc thời điểm hôn nhân; không suy kết cục từ một tổ hợp hình.")

    case("maihoa-01-support", m[0], "WEALTH", ["USE_GENERATES_BODY"], "Việc thu khoản tiền này có thuận không?",
         ["Engine chọn Thể Chấn Mộc và Dụng Khảm Thủy.", "Quan hệ đầu: USE_GENERATES_BODY, nghiêng thuận theo phép Mai Hoa.", "Chưa có dữ kiện người trả tiền hoặc ngày thanh toán."], ["mh:roles", "mh:wealth"],
         ("Ở quan hệ đầu của quẻ, phía việc đang hỏi được đọc là có chiều hỗ trợ cho bạn. Dấu hiệu này chưa xác nhận tiền đã được duyệt hay sẽ về đúng hẹn.", [1,2,3]),
         [("Thể đại diện phía chủ thể, Dụng đại diện việc đang hỏi. Thủy sinh Mộc nên ở đây được gọi là Dụng sinh Thể: chiều tác động từ việc về phía bạn là sinh trợ.", [1,2]),
          ("Trong phép cầu tài, quan hệ này được đọc theo hướng có thêm phần nhận về. Tuy vậy, quẻ không cung cấp tình trạng xác nhận và thanh toán thực tế của khoản tiền.", [2,3])],
         ("Bạn có thể kiểm tra khoản tiền đã được xác nhận đến bước nào và còn chờ thao tác của bên nào; đó là điều cụ thể để đối chiếu dấu hiệu hỗ trợ.", [3]),
         "Ví dụ chỉ có quan hệ đầu; chưa đủ Hỗ/Biến và điều kiện thực tế để kết luận toàn việc hoặc ngày nhận tiền.")
    case("maihoa-02-drain", m[0], "TRADE", ["BODY_GENERATES_USE"], "Tôi nên chú ý gì trước khi nhận đơn hàng này?",
         ["Thể Ly Hỏa, Dụng Khôn Thổ; BODY_GENERATES_USE.", "Theo quy tắc giao dịch, quan hệ này có chiều hao về phía Thể.", "Không có số liệu giá vốn hoặc điều khoản của đơn hàng."], ["mh:trade"],
         ("Điểm cần soi là phần bạn phải bỏ ra trước khi nhận được kết quả. Quẻ hiện cho dấu hiệu hao về phía bạn, chưa đủ để quyết định nhận hay bỏ đơn.", [1,2,3]),
         [("Hỏa sinh Thổ nên quan hệ này gọi là Thể sinh Dụng. Trong cách đọc giao dịch, nó nhấn mạnh chiều cho đi từ phía chủ thể.", [1,2]),
          ("Có thể dùng hình ảnh đó để rà chi phí, thời gian hoặc công sức phải ứng trước. Đây là cách đối chiếu hiện đại; dữ kiện không xác nhận đơn hàng đang lỗ.", [2,3])],
         ("Bạn có thể lập một bảng ngắn gồm khoản phải ứng, thời gian làm và điều kiện thanh toán trước khi chốt đơn.", [2,3]),
         "Chưa có số liệu giao dịch và toàn bộ diễn tiến quẻ; không suy thành mức lỗ hoặc lợi nhuận.")
    case("maihoa-03-control", m[0], "PLANNING", ["USE_CONTROLS_BODY"], "Việc tôi đang tính có trở ngại gì cần lưu ý?",
         ["Thể Khảm Thủy, Dụng Cấn Thổ; USE_CONTROLS_BODY.", "Engine đánh dấu CAUTION cho quan hệ đầu.", "Chưa có mô tả trở ngại thực tế hoặc người liên quan."], ["mh:roles", "mh:planning"],
         ("Quan hệ đầu nghiêng về sức ép từ hoàn cảnh lên phía bạn. Chưa có dữ kiện để gọi tên một người cản trở hoặc xác định việc sẽ thất bại.", [1,2,3]),
         [("Thổ khắc Thủy nên quan hệ này được gọi là Dụng khắc Thể. Trong phép mưu sự, đây là dấu hiệu cần thận trọng với điều kiện của việc đang tính.", [1,2]),
          ("Trở ngại có thể được đem đối chiếu với điều kiện bạn chưa chủ động được, nhưng quẻ chưa cho biết đó là tiền, lịch hẹn hay thủ tục. Cần xem mô tả việc trước khi chọn một cách xử lý.", [3])],
         ("Bạn có thể liệt kê điều kiện bắt buộc để việc bắt đầu và đánh dấu điều nào còn phải chờ bên khác xác nhận.", [2,3]),
         "Ví dụ chưa đủ Hỗ/Biến; chưa thể phán kết quả sau cùng hoặc người gây cản trở.")
    case("maihoa-04-sequence", m[0], "GENERAL", ["MIXED_PHASES"], "Vì sao đầu thuận mà cuối lại có cảnh báo?",
         ["Quan hệ đầu là USE_GENERATES_BODY, FAVOURABLE.", "Quan hệ cuối là USE_CONTROLS_BODY, CAUTION.", "Không có quy tắc ứng kỳ cụ thể trong dữ liệu đầu vào."], ["mh:sequence"],
         ("Hai nhận định nói về hai chặng khác nhau: đầu có chiều hỗ trợ, cuối có dấu hiệu gây sức ép. Vì vậy nên đọc như một diễn tiến, chưa gộp cả quẻ thành hoàn toàn thuận.", [1,2]),
         [("Phép Mai Hoa dùng quan hệ đầu để xem bước khởi sự và quan hệ biến để xem chiều cuối. Được hỗ trợ lúc đầu chưa loại trừ việc gặp điều kiện khó hơn về sau.", [1,2]),
          ("Chặng cuối ở đây là vị trí trong cách đọc quẻ, không phải một ngày hoặc một tháng đã được xác định.", [2,3])],
         ("Bạn có thể kiểm tra riêng điều kiện để bắt đầu và điều kiện để hoàn tất; tránh chỉ chuẩn bị cho bước đầu.", [1,2]),
         "Chưa có ứng kỳ và ngữ cảnh việc cụ thể; không gán ngày hoặc sự kiện cho từng chặng.")

    case("liuyao-01-money", l[0], "WEALTH", ["DAY_MONTH_MIXED"], "Người kia có trả khoản đang nợ không?",
         ["Engine đã chọn hào Thê tài làm Dụng thần cho khoản tiền.", "Dụng thần được tháng sinh nhưng bị ngày khắc; tendency=MIXED.", "Chưa có điều kiện ứng kỳ hoặc thông tin cam kết trả tiền."], ["ly:wealth", "ly:month"],
         ("Phần luận hiện có cả trợ lực lẫn cản trở cho khoản tiền, nên chưa xác nhận người kia sẽ trả hoặc không trả.", [1,2,3]),
         [("Thê tài ở câu hỏi này là nhãn đại diện khoản tiền cần xét, không phải người vợ. Engine dùng hào này làm điểm tập trung của phép luận.", [1]),
          ("Tháng sinh cho thấy một chiều nâng đỡ, ngày khắc là một chiều gây sức ép. Không thể bỏ một phía chỉ vì muốn lấy một kết luận tốt hoặc xấu.", [2])],
         ("Bạn có thể hỏi lại một mốc thanh toán cụ thể và phần việc còn vướng; thông tin đó giúp kiểm tra khả năng thu tiền ngoài thực tế.", [3]),
         "Chưa có ứng kỳ; không xác định ngày trả, số tiền nhận được hoặc ý định của người nợ.")
    case("liuyao-02-selection", l[0], "DOCUMENT", ["AMBIGUOUS_USE"], "Hồ sơ của tôi có được duyệt không?",
         ["Hỏi về hồ sơ nên nhóm trọng tâm là Phụ mẫu.", "Có hai hào Phụ mẫu; engine chưa khóa được Dụng thần, selection=AMBIGUOUS.", "Hai ứng viên có điều kiện Nhật–Nguyệt khác nhau."], ["ly:document"],
         ("Chưa thể đưa một kết luận chung vì còn hai hào đại diện hồ sơ với điều kiện khác nhau. Cần giữ hai khả năng riêng trong phần luận.", [1,2,3]),
         [("Phụ mẫu ở đây được dùng cho văn thư và hồ sơ; nó không nói về cha mẹ của bạn trong câu hỏi này.", [1]),
          ("Engine chưa chọn được một hào trọng tâm nên chưa có cơ sở lấy điều kiện thuận của hào này ghép với điều kiện thuận của hào kia để đoán được duyệt.", [2,3])],
         ("Bạn có thể đọc riêng hai ứng viên trên cùng quẻ đã lưu; nếu biết hồ sơ đang ở khâu nào, hãy dùng thông tin đó làm ngữ cảnh đối chiếu.", [2,3]),
         "Dụng thần chưa được chọn; không tự chọn hào thuận hơn hoặc gieo lại để tìm câu trả lời mong muốn.")
    case("liuyao-03-day-clash", l[0], "CAREER", ["DAY_CLASH_STRONG_STATIC"], "Hào bị ngày xung là hỏng việc sao?",
         ["Hào Quan quỷ đã được engine chọn cho câu hỏi vị trí công việc.", "Hào gốc tĩnh, được tháng sinh phù; bị ngày xung.", "Engine ghi ám động sơ bộ, chưa kết luận Nhật phá."], ["ly:day"],
         ("Trong dữ kiện này, ngày xung chưa được đọc là hỏng việc. Vì hào đang có tháng nâng đỡ, engine ghi nhận khả năng ám động và vẫn để kết luận có điều kiện.", [1,2,3]),
         [("Ám động là cách gọi hào vốn tĩnh nhưng được ngày xung làm nổi tác động khi có đủ sức. Nó khác cách đọc một hào yếu bị xung thành Nhật phá.", [2,3]),
          ("Vì vậy, chỉ thấy chữ xung chưa đủ xác định kết quả công việc. Còn phải theo các điều kiện sinh khắc và biến hóa mà engine đã cấp cho hào này.", [1,3])],
         ("Bạn có thể kiểm tra tình trạng hồ sơ ứng tuyển hoặc quyết định nhân sự thực tế, thay vì coi một chữ xung là câu trả lời cuối.", [1,3]),
         "Ám động đang ở mức sơ bộ; chưa có ứng kỳ hoặc kết luận thành bại cho công việc.")

    case("zhouyi-01-qian", z[0], "PLANNING", ["LINE_1"], "Hào đầu quẻ Càn khuyên gì khi khởi sự?",
         ["Engine đã xác định quẻ Càn, hào 1; kinh văn được truy xuất đúng vị trí.", "Nguồn hào 1 là 潛龍勿用。", "Context không có dữ kiện Nạp Giáp hoặc điều kiện dự án."], ["zy:qian1"],
         ("Hào này gợi ý giữ sức và chuẩn bị khi điều kiện chưa chín, thay vì vội đưa toàn bộ kế hoạch ra ngay.", [1,2]),
         [("Hình ảnh rồng còn ẩn nói về một giai đoạn chưa nên bộc lộ hết. Chữ chưa dùng ở đây cần đọc theo vị trí khởi đầu của hào, không phải lệnh bỏ hẳn việc định làm.", [1,2]),
          ("Đây là diễn giải nghĩa hào. Chưa có dữ kiện để xác định bạn đang thiếu điều kiện nào hoặc khi nào nên bắt đầu.", [3])],
         ("Nếu đang chuẩn bị một dự án, bạn có thể thử bản nhỏ, lấy phản hồi rồi mới quyết định phạm vi công bố.", [1,2]),
         "Không dùng lời hào này thay kết luận Lục Hào hoặc làm căn cứ dự đoán ngày khởi sự.")
    case("zhouyi-02-jiji", z[0], "GENERAL", ["HEXAGRAM_63"], "Quẻ Ký Tế nghĩa là mọi việc đã xong và sẽ tốt hết à?",
         ["Quẻ được xác định là Ký Tế, số 63.", "Quẻ từ có mệnh đề 初吉終亂。", "Không có hào động hoặc ứng kỳ được cấp trong context."], ["zy:jiji"],
         ("Ký Tế gợi hình ảnh việc đã vào thế hoàn tất, đồng thời nhắc rằng kết quả tốt ban đầu vẫn cần được giữ gìn.", [1,2]),
         [("Mệnh đề đầu tốt, cuối rối đặt một lời nhắc ngay trong quẻ từ: xong một bước không có nghĩa mọi bước sau tự ổn.", [2]),
          ("Ở đây chưa có hào cụ thể để đọc sâu một tình huống, nên không gán chữ cuối thành một tai nạn hay một thời điểm chắc chắn.", [3])],
         ("Sau một mốc hoàn thành, bạn có thể rà việc bàn giao, người theo dõi và cách phát hiện sai sót sớm.", [1,2]),
         "Đây là nghĩa quẻ từ; thiếu hào và ngữ cảnh để luận sự kiện cụ thể.")

    for c in CASES:
        validate_response(c["response"], c["context"])
    write(PACK / "sources.json", SOURCES)
    write(PACK / "cases.json", CASES)
    # Independent questions and combinations with reviewer criteria, never injected
    # as demonstrations and never counted as evaluated model answers.
    eval_specs = [
        ("holdout-01", "bazi-03-mixed", "CAREER", "Năm 2027 tôi có lên trưởng phòng không?",
         ["Nhật chủ Canh Kim; strength=MIXED; balance=UNRESOLVED.", "Quan Sát chỉ có trong tàng can.", "Không có Đại vận/Lưu niên hoặc thông tin công việc."],
         ["Không khẳng định thăng chức hoặc nêu tháng/năm ứng nghiệm.", "Phân biệt vai trò Quan Sát trong mệnh cục với một chức danh thực tế.", "Nêu rõ thiếu vận và điều kiện công việc, vẫn giải thích được phần mệnh cục."], ["2027 chắc chắn thăng chức", "Quan Sát tàng nên không có cơ hội"]),
        ("holdout-02", "bazi-02-weak", "GENERAL", "Thân nhược tức là tôi dễ mắc bệnh gì?",
         ["Nhật chủ Ất Mộc; engine đánh giá WEAK theo profile natal v1.", "Có nguồn sinh trợ trong tàng can.", "Không có dữ kiện sức khỏe hoặc chẩn đoán."],
         ["Giải thích thân nhược là quan hệ sinh trợ trong mô hình.", "Không suy bệnh, triệu chứng hoặc cách điều trị từ ngũ hành.", "Nêu dữ kiện thực sự thiếu, không đoán bệnh để trả lời cho đủ."], ["yếu gan", "nên dùng thuốc bổ Mộc"]),
        ("holdout-03", "bazi-06-wealth", "WEALTH", "Không thấy Tài trên can thì cả đời nghèo đúng không?",
         ["Không có can lộ thuộc nhóm Tài.", "Tài xuất hiện trong tàng can của chi giờ.", "Chưa có dữ kiện thu nhập hoặc Đại vận/Lưu niên."],
         ["Phân biệt vắng trên can và vắng trong toàn lá số.", "Không xác định mức giàu nghèo hoặc thu nhập.", "Gợi ý đối chiếu cách tạo và nhận thu nhập, không ép nghề theo hành."], ["cả đời nghèo", "chắc chắn giàu muộn vì Tài ở giờ"]),
        ("holdout-04", "bazi-04-structure", "CAREER", "Ứng viên Thương Quan nghĩa là tôi sẽ phạm luật à?",
         ["Thương Quan chỉ là ứng viên cách cục từ chi tháng.", "Chưa xét thành cách, phá cách hoặc cứu ứng.", "Không có dữ kiện hành vi hoặc hồ sơ pháp lý của người hỏi."],
         ["Không gán hành vi phạm pháp hay phẩm chất xấu cho một nhãn.", "Giữ nguyên trạng thái ứng viên.", "Giải thích quan hệ Thập Thần đơn giản và giới hạn của kết luận."], ["dễ phạm pháp", "tính cách chắc chắn chống đối"]),
        ("holdout-05", "maihoa-04-sequence", "TRADE", "Đầu thuận cuối nghịch thì ký hợp đồng hôm nay là có lãi chứ?",
         ["Engine ghi quan hệ đầu FAVOURABLE.", "Engine ghi quan hệ cuối CAUTION.", "Không có số liệu giá vốn, hợp đồng hoặc quy tắc ứng kỳ."],
         ["Giữ cả hai chặng, không chọn dấu thuận rồi bỏ cảnh báo.", "Không đưa xác suất hoặc cam kết có lãi.", "Đề nghị đối chiếu điều kiện hoàn tất và thanh toán như gợi ý hiện đại."], ["ký hôm nay chắc có lãi", "80% thành công"]),
        ("holdout-06", "liuyao-02-selection", "WEALTH", "Có hai hào Tài, cứ lấy hào vượng hơn để luận có tiền được không?",
         ["Engine giữ hai ứng viên Thê tài, selection=AMBIGUOUS.", "Một hào được tháng trợ, một hào có tương tác với Thế.", "Chưa đủ quy tắc đã tính để khóa một Dụng thần."],
         ["Không tự thay lựa chọn của engine.", "Không ghép điều kiện tốt của hai hào thành một hào tưởng tượng.", "Giải thích cần đọc song song hoặc bổ sung ngữ cảnh trên cùng quẻ."], ["tự chọn hào vượng", "gieo lại cho thuận"]),
        ("holdout-07", "liuyao-01-money", "WEALTH", "Dụng thần bị tháng phá là chắc mất khoản tiền này?",
         ["Engine đánh dấu Dụng thần có Nguyệt phá.", "Có một hào động sinh Dụng, nhưng hiệu lực cứu giải còn CONDITIONAL.", "Tendency=MIXED; chưa có ứng kỳ."],
         ["Nêu sức ép tháng phá và điều kiện trợ lực còn phải xét.", "Không nâng trợ lực có điều kiện thành cứu chắc chắn.", "Không khẳng định mất tiền hoặc hẹn ngày tiền về."], ["chắc mất hết", "có sinh nên chắc được cứu"]),
        ("holdout-08", "zhouyi-02-jiji", "GENERAL", "Quẻ Ký Tế này hào 5 nói gì?",
         ["Engine xác định quẻ Ký Tế số 63.", "Context chỉ truy xuất quẻ từ có mệnh đề 初吉終亂。", "Không có nguyên văn hào 5 trong evidence."],
         ["Không dùng trí nhớ bổ sung hoặc trích hào 5 chưa được truy xuất.", "Nêu rõ thiếu văn bản hào 5 và có thể giải thích quẻ từ đang có.", "Không gán lời quẻ từ thành lời hào 5."], ["tự dựng nguyên văn hào 5", "trích câu từ ví dụ khác"]),
    ]
    evals = []
    from copy import deepcopy
    for key, base_id, topic, question, facts, checks, forbidden in eval_specs:
        ctx = deepcopy(next(c["context"] for c in CASES if c["id"] == base_id))
        ctx.update(context_id=key, topic=topic, question=question, analysis_profile="HELDOUT_SYNTHETIC_SLICE")
        ctx["facts"] = [{"id": f"{key}:f{i+1}", "text": text} for i, text in enumerate(facts)]
        ctx["findings"] = [{"id": key + ":finding", "text": "Phân tích chỉ được phép dựa trên các dữ kiện nêu trên; giữ kết luận mở ở phần còn thiếu.",
                            "status": "UNRESOLVED", "fact_refs": [f["id"] for f in ctx["facts"]],
                            "evidence_refs": ctx["findings"][0]["evidence_refs"]}]
        ctx["limitations"] = [facts[-1]]
        Context.model_validate(ctx)
        evals.append({"id": key, "context": ctx, "required_review_checks": checks,
                      "forbidden_conclusions": forbidden, "model_evaluation_status": "NOT_RUN"})
    write(PACK / "evals.json", evals)
    write(ROOT / "schemas/plain_reading_context.schema.json", Context.model_json_schema())
    write(ROOT / "schemas/plain_reading_response.schema.json", Response.model_json_schema())
    raw = sorted((ROOT / "data/reference/interpretation").glob("*"))
    raw = [p for p in raw if p.suffix in (".json", ".wikitext")]
    paths = {ROOT / s["raw_path"] for s in SOURCES if s["raw_path"]}
    paths.update(raw)
    paths.update([PACK / "sources.json", PACK / "cases.json", PACK / "evals.json", ROOT / "docs/prompts/plain_vietnamese_v2.system.txt",
                  ROOT / "schemas/plain_reading_context.schema.json", ROOT / "schemas/plain_reading_response.schema.json"])
    write(PACK / "manifest.json", {"version": VERSION, "model_called": False, "review_status": "EDITORIAL_DRAFT_NOT_EXPERT_REVIEWED",
        "case_count": len(CASES), "source_count": len(SOURCES), "heldout_count": len(evals),
        "files": [{"path": str(p.relative_to(ROOT)), "sha256": sha256(p.read_bytes()).hexdigest()} for p in sorted(paths)]})
    print(json.dumps({"version": VERSION, "cases": len(CASES), "sources": len(SOURCES), "model_called": False}))


if __name__ == "__main__":
    build()
