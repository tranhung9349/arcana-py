"""Build the adaptive editorial pack offline; historical packs stay untouched."""
from copy import deepcopy
from hashlib import sha256
import json

from scripts import build_plain_interpretation_data as base

ROOT = base.ROOT
PACK = ROOT / "data/interpretation/plain_v4"
VERSION = "plain-vietnamese-2026-10-27-v4.1"
PROMPT = "docs/prompts/plain_vietnamese_v4.system.txt"
PLAYBOOK = "docs/prompts/reading_playbook_v4.json"
GUIDES = "docs/prompts/interpretation_method_guides_v3.json"


def build():
    from research_tools.interpretation_prompt import Context, validate_response
    from research_tools.reading_strategy import plan_reading
    base.SOURCES[:] = json.loads((ROOT / "data/interpretation/plain_v3/sources.json").read_text())
    base.CASES[:] = json.loads((ROOT / "data/interpretation/plain_v3/cases.json").read_text())
    source, case = base.source, base.case
    b, m, l = "BAZI_NATAL_V1", "MAIHOA_INTERNAL", "LIUYAO_NAJIA"
    source("dtt:context", "Nhậm Thiết Tiều · Địch Thiên Tủy Xiển Vi · Tri mệnh",
           "察其衰旺，究其顺悖，审其进退，论其喜忌，是谓理会。", [b],
           "data/reference/interpretation/dtt_chanwei.wikitext", "https://zh.wikisource.org/w/index.php?oldid=2600158")
    source("dtt:flow", "Nhậm Thiết Tiều · Địch Thiên Tủy Xiển Vi · Nguyên lưu",
           "认源之气以势，认流之气以情。", [b],
           "data/reference/interpretation/dtt_chanwei.wikitext", "https://zh.wikisource.org/w/index.php?oldid=2600158")
    source("ziping:assistant", "Tử Bình Chân Thuyên · Luận Tướng thần khẩn yếu",
           "要而言之，凡全局之格，賴此一字而成者，均謂之相也。", [b],
           url="https://www.donglishuzhai.net/chapter/3728.html", state="WEB_EXCERPT_NOT_EDITION_PINNED")
    source("mh:context", "Mai Hoa Dịch Số · Láng giềng gõ cửa mượn vật",
           "推數又須明理，為卜占之切要也。", [m],
           "data/reference/maihoa/volume_1.wikitext", "https://zh.wikisource.org/w/index.php?oldid=2690596")
    source("ly:two_uses", "Tăng San Bốc Dịch · Lưỡng hiện chương",
           "余得騐者，多有應乎旬空月破，舍其不空而用旬空，舍其不破而用月破。", [l],
           url="https://www.shidianguji.com/zh/book/XYXZSBY/chapter/1lzxsny7db6rt", state="WEB_TRANSCRIPTION_NOT_EDITION_PINNED")

    # Explicit tags in these existing editorial slices match their supplied facts.
    for row in base.CASES:
        if row["id"] in ("bazi-06-wealth", "bazi-07-study"):
            row["context"]["signals"].append("MIXED")
    # Fix a modern-life inference still present in the historical demonstration.
    doc = next(c for c in base.CASES if c["id"] == "liuyao-04-document")
    doc["context"]["signals"].append("WORLD_CONDITIONED")
    doc["response"]["summary"]["text"] = "Hào đại diện văn bản có nền sinh phù, nhưng Thế còn gặp điều kiện động biến bất lợi, nên chưa đủ để kết luận thuận trọn vẹn cho người hỏi. Quẻ chưa xác nhận chất lượng bản kế hoạch hoặc kết quả phê duyệt."
    doc["context"]["findings"][0]["text"] = doc["response"]["summary"]["text"]
    doc["response"]["analysis"][-1]["text"] = doc["response"]["analysis"][-1]["text"].replace("sức tiếp nhận ở Thế", "điều kiện bất lợi đã ghi nhận ở Thế")

    case("bazi-09-priority", b, "GENERAL", ["MIXED", "CLIMATE_CONFLICT", "CANDIDATE_STRUCTURE", "NATAL_ONLY"],
         "Vì sao các phần luận khác nhau, tôi nên ưu tiên điều gì?",
         ["Phù ức tạm gợi ý Thủy; Điều hậu sơ bộ gợi ý Hỏa, climate_conflict=true.",
          "Mùa không trợ Nhật chủ, có căn và can Ấn; sức Nhật chủ MIXED, hướng hợp nhất UNRESOLVED.",
          "Có ứng viên cách cục từ tháng; thành bại và Tướng thần chưa được đánh giá đầy đủ."],
         ["dtt:context", "ziping:climate", "ziping:assistant"],
         ("Điểm cần giải trước là vì sao hai nhánh đề xuất khác hành, chứ chưa phải chọn một hành để áp dụng. Nền mạnh yếu còn có dấu trái chiều và cách cục cũng mới là ứng viên, nên chưa có kết luận hợp nhất.", [1,2,3]),
         [("Thủy đang được gợi ý để điều tiết quan hệ sinh trợ và tiết hao; Hỏa thuộc nhánh xem nóng lạnh theo mùa. Hai nhánh xét hai điều kiện khác nhau nên không thể xem chúng như hai đáp án loại trừ nhau. Dữ kiện hiện tại mới ghi nhận sự khác hướng, chưa phân định nhánh nào có hiệu lực ưu tiên trong toàn cục.", [1,2]),
          ("Thêm tên một cách cục chưa giải được chỗ vướng ấy. Tử Bình Chân Thuyên còn xét yếu tố phối hợp giúp cách cục thành, trong khi phần này của phiên chưa được đánh giá đầy đủ. Vì vậy, cần giữ ba câu riêng: mạnh yếu còn chưa chốt, Điều hậu mới sơ bộ, cách cục chưa xác nhận thành; không lấy một nhãn nổi bật để phủ cả ba.", [2,3])],
         ("Bạn có thể yêu cầu mỗi đề xuất nêu rõ nó thuộc nhánh nào, đang dựa vào dữ kiện gì và còn thiếu bước nào trước khi chốt hướng dùng chung.", [1,2,3]),
         "Chưa có kết luận hợp nhất phù ức, Điều hậu và thành bại cách cục.")
    case("bazi-10-timing", b, "CAREER", ["STRONG", "CANDIDATE_STRUCTURE", "NATAL_ONLY"],
         "Năm nay khi nào tôi được thăng chức?",
         ["Nhật chủ được đánh giá STRONG từ mùa, căn và can sinh trợ.",
          "Chính Quan là ứng viên cách cục, CONDITIONAL; chưa hoàn tất thành bại cứu ứng.",
          "Chỉ có mệnh cục; chưa tính Đại vận/Lưu niên, chưa có quá trình xét thăng chức."],
         ["dtt:context", "ziping:formation"],
         ("Chưa xác định được thời điểm thăng chức từ dữ kiện hiện có. Phần đã đọc được là nền sinh trợ thiên vượng và một ứng viên Chính Quan, còn cả hiệu lực cách cục lẫn diễn biến theo năm đều chưa đủ.", [1,2,3]),
         [("Chính Quan là điểm liên quan câu hỏi công việc, nhưng ứng viên chưa có nghĩa đã thành một cấu trúc thuận. Nền Nhật chủ có sinh trợ cũng không thay thế được bước xét các điều kiện phối hợp. Vì thế, hai dữ kiện này chưa cho phép kết luận bạn sẽ được bổ nhiệm.", [1,2]),
          ("Câu hỏi có chữ năm nay không bổ sung dữ kiện vận cho lá số. Muốn bàn một thời kỳ còn cần phần vận được tính và kiểm tra, còn việc thăng chức cụ thể cần điều kiện xét duyệt ngoài đời. Phần luận hiện tại dừng ở cấu trúc mệnh cục; không đổi nhãn Quan thành một lịch hẹn.", [2,3])],
         ("Bạn có thể đối chiếu tiêu chí và lịch đánh giá đã được nơi làm việc xác nhận, rồi tách chúng khỏi phần mệnh cục đang đọc.", [2,3]),
         "Chưa có Đại vận/Lưu niên hoặc dữ kiện quy trình thăng chức để luận thời điểm.")
    case("maihoa-05-turning", m, "PLANNING", ["USE_GENERATES_BODY", "MIXED_PHASES"],
         "Kế hoạch triển khai cần chú ý điều gì?",
         ["Thể Khảm Thủy, Dụng Càn Kim sinh Thể; finding đầu FAVOURABLE.",
          "Hỗ phía Thể Khôn Thổ khắc Thể, CAUTION; Hỗ phía Dụng Khảm Thủy cùng hành Thể, FAVOURABLE.",
          "Biến là Cấn Thổ khắc Thể, CAUTION; sức Thể NOT_SPECIFIED, chưa có ứng kỳ."],
         ["mh:phase_priority", "mh:context", "mh:roles"],
         ("Điểm đáng chú ý là chiều trợ ở đầu không kéo dài tới cuối: chặng Hỗ phía Thể và chặng Biến đều có quan hệ khắc Thể. Kế hoạch vì vậy cần được đọc cả phần duy trì và hoàn tất, chưa đủ để lấy khởi đầu thuận làm kết luận chung.", [1,2,3]),
         [("Dụng Kim sinh Thể Thủy cho phần mở đầu một chiều nâng đỡ trong phép đọc. Nhưng ở giữa, Hỗ phía Thể là Thổ lại khắc Thủy; Hỗ phía Dụng cùng hành chỉ là một dấu thuận khác, không xóa quan hệ khắc đã nêu. Các dấu này thuộc những chặng khác nhau của cùng việc, không phải các phiếu để cộng trừ.", [1,2]),
          ("Đến Biến, quan hệ Thổ khắc Thủy tiếp tục đòi hỏi thận trọng với chặng kết. Đây là lý do phần tổng hợp không dừng ở khởi đầu được trợ. Chưa xác định sức Thể và chưa có ứng kỳ nên không thể từ đó hẹn một tháng khó khăn hoặc kết luận người hỏi thiếu sức theo kế hoạch.", [2,3])],
         ("Bạn có thể thử kiểm tra một bước từ khởi động tới bàn giao: điều kiện nào đã được xác nhận, điều kiện nào còn phụ thuộc và ai sẽ kiểm tra trước khi kết thúc.", [1,2,3]),
         "Các chặng là diễn tiến trong phép đọc, chưa phải lịch; chưa xác định sức Thể và điều kiện thực tế của kế hoạch.")
    case("maihoa-06-comparison", m, "PLANNING", ["USE_GENERATES_BODY"],
         "Tôi nên theo phương án A hay chuyển sang phương án B?",
         ["Quẻ đang lưu cho việc triển khai A: Thể Cấn Thổ, Dụng Ly Hỏa sinh Thể, FAVOURABLE.",
          "Hai Hỗ cùng hành Thể và Biến sinh Thể, đều được finding ghi FAVOURABLE.",
          "Không có dữ kiện hoặc finding riêng của B; chưa có thông tin chi phí hay ứng kỳ."],
         ["mh:context", "mh:sequence"],
         ("Quẻ hiện tại cho A có các quan hệ cùng chiều thuận, nhưng chưa đủ để nói A hơn B. Phương án B chưa có phần phân tích riêng nên phép so sánh vẫn thiếu một phía.", [1,2,3]),
         [("Với A, Dụng sinh Thể ở đầu, các Hỗ cùng hành và Biến sinh Thể ở cuối tạo một mạch tương đối nhất quán trong dữ kiện đã cấp. Có thể tổng hợp chiều thuận này mà không phải dựng một chặng cản. Nó vẫn là nhận định theo quan hệ quái, chưa xác nhận hiệu quả hay chi phí thực tế.", [1,2,3]),
          ("Các chặng Hỗ và Biến của A không tự trở thành dữ kiện của B chỉ vì câu hỏi có hai lựa chọn. Theo cách đọc gắn tượng với việc, phải giữ rõ quẻ đang đại diện việc nào. Muốn quyết định giữa hai phía cần tiêu chí và thông tin tương ứng, thay vì dùng một quẻ thuận làm đáp án cho tất cả lựa chọn.", [1,2,3])],
         ("Bạn có thể đặt A và B cạnh nhau theo cùng tiêu chí về mục tiêu, chi phí và điều kiện hoàn tất, ghi rõ thông tin nào đã xác nhận ở mỗi phía.", [1,3]),
         "Chỉ có phần đọc cho A; chưa có căn cứ so B hoặc luận thời điểm chuyển phương án.")
    case("liuyao-05-provisional", l, "WEALTH", ["PROVISIONAL_USE", "DAY_MONTH_MIXED"],
         "Khoản tiền này có được nhận không?",
         ["Thê tài tại L2 Thổ đang tạm chọn làm Dụng; selection=PROVISIONAL vì các ứng viên chưa được phân định hoàn toàn.",
          "L2 được ngày Hỏa sinh nhưng tháng Mộc khắc, tĩnh; phần tổng hợp giữ điều kiện trái chiều.",
          "Không có kết luận cứu giải hoặc thời điểm nhận tiền; chưa có xác nhận bên thanh toán."],
         ["ly:roles", "ly:two_uses", "ly:day", "ly:month"],
         ("Theo hào Tài đang tạm chọn, có dấu được ngày nâng đỡ nhưng vẫn gặp sức ép từ tháng. Vì lựa chọn Dụng chưa chốt và hai mặt còn cùng tồn tại, chưa thể xác nhận khoản tiền sẽ được nhận.", [1,2,3]),
         [("Điểm cần giữ trước là chữ tạm chọn: các điều kiện sau đây thuộc L2, không tự đại diện cho mọi ứng viên. Tăng San có bàn những trường hợp không thể máy móc chọn hào có vẻ thuận hơn. Trong phiên này, chưa có kết luận phân định thì không tự đổi sang một hào khác để làm câu trả lời rõ hơn.", [1]),
          ("Trên đúng L2, ngày sinh trợ và tháng khắc đang chỉ về hai phía. Chưa có đánh giá cho phép nói dấu nào đã lấn hoàn toàn dấu kia hoặc có cứu ứng hữu hiệu. Phần đọc được là điều kiện của hào Tài đang xét; tiền đã được duyệt, đến hạn hay chuyển khoản chưa vẫn phải theo dữ kiện thực tế.", [2,3])],
         ("Bạn có thể xác nhận đang hỏi cùng một khoản nào, điều kiện thanh toán đã hoàn thành đến đâu và có xác nhận thời hạn bằng văn bản hay chưa.", [1,2,3]),
         "Dụng mới tạm chọn; chưa có cứu giải đầy đủ, ứng kỳ hoặc xác nhận thanh toán.")
    case("liuyao-06-timing", l, "DOCUMENT", ["SELECTED_USE", "HAS_TIMING_CONDITIONS"],
         "Khi nào có kết quả hồ sơ?",
         ["Phụ mẫu tại L2 Thổ được chọn làm Dụng; được tháng Hỏa sinh nhưng đang VOID.",
          "Finding thời điểm chỉ ghi điều kiện ra khỏi tuần không; chưa quy đổi ngày và chưa xác nhận đủ điều kiện thành việc.",
          "Không có lịch xử lý hoặc quyết định của đơn vị tiếp nhận."],
         ["ly:day", "ly:month", "ly:document"],
         ("Hiện chỉ có một điều kiện để theo dõi là hào đại diện hồ sơ ra khỏi tuần không, chưa có ngày chắc chắn có kết quả. Nền tháng sinh trợ chưa đủ biến điều kiện ấy thành lời hẹn được duyệt.", [1,2,3]),
         [("Tuần không là trạng thái của hào đã được phần phân tích ghi nhận; ở đây nó đi cùng dấu tháng sinh trợ. Giữ cả hai giúp tránh coi Không là hồ sơ không tồn tại, hoặc coi được sinh trợ là mọi việc đã hoàn tất. Finding thời điểm mới nêu một điều kiện liên quan đến trạng thái ấy.", [1,2]),
          ("Muốn chuyển điều kiện thành một mốc cụ thể cần phép quy đổi và đánh giá thành việc tương ứng. Phiên chưa có hai phần đó, nên không tự tra ngày từ trí nhớ hoặc suy ngày đơn vị tiếp nhận sẽ phản hồi. Phần có thể đem đối chiếu lúc này là trạng thái và lịch xử lý được nơi tiếp nhận xác nhận.", [2,3])],
         ("Bạn có thể kiểm tra mã hồ sơ, bước đang xử lý và mốc phản hồi được công bố; dùng chúng để theo dõi thay vì mặc định ra khỏi tuần không là đã được duyệt.", [1,2,3]),
         "Chưa quy đổi ứng kỳ hoặc xác nhận đủ điều kiện thành việc; chưa có lịch xử lý thực tế.")

    playbook = json.loads((ROOT / PLAYBOOK).read_text())
    for row in base.CASES:
        ctx = Context.model_validate(row["context"])
        validate_response(row["response"], ctx)
        plan = plan_reading(ctx, playbook)
        row["teaches_routes"] = [plan["primary_id"], *plan["qualifier_ids"]]
        row["teaches_intent"] = plan["intent"]
    evals = deepcopy(json.loads((ROOT / "data/interpretation/plain_v3/evals.json").read_text()))
    # New development probes are separate from demonstrations, not model scores.
    probes = []
    for index, base_id, question, checks in [
        (12,"bazi-09-priority","Tháng này tôi nên ưu tiên hành nào để công việc tốt hơn?",["Mở bằng phạm vi thời điểm còn thiếu; không dùng tháng này làm vận đã tính.","Giữ riêng hai nhánh khác hướng và điều kiện cách cục."]),
        (13,"maihoa-06-comparison","So sánh hai khóa học A và B giúp tôi?",["Chỉ có dữ kiện A, không lấy Hỗ/Biến của A gán cho B.","Không suy chi phí, chất lượng hoặc nội dung khóa học."]),
        (14,"liuyao-05-provisional","Bao giờ khoản tiền đó đến?",["Giữ Dụng tạm chọn, không chốt tiền đến.","Không đổi xung/ngày tháng thành lịch khi chưa có ứng kỳ."]),
    ]:
        ctx = deepcopy(next(c["context"] for c in base.CASES if c["id"] == base_id))
        ctx.update(context_id=f"probe-{index}-adaptive", question=question, analysis_profile="DEVELOPMENT_QUESTION_VARIANT")
        probes.append({"id":ctx["context_id"],"context":ctx,"required_review_checks":checks,
                      "evaluation_kind":"QUESTION_VARIANT_SAME_SYNTHETIC_FACTS_NOT_INDEPENDENT_HOLDOUT",
                      "forbidden_conclusions":["Cam kết kết quả hoặc thời điểm chưa được tính."],"model_evaluation_status":"NOT_RUN"})
    for row in [*evals, *probes]:
        Context.model_validate(row["context"])
    base.write(PACK / "sources.json", base.SOURCES)
    base.write(PACK / "cases.json", base.CASES)
    base.write(PACK / "evals.json", evals)
    base.write(PACK / "adaptive_probes.json", probes)
    paths = {ROOT / s["raw_path"] for s in base.SOURCES if s["raw_path"]}
    paths.update(PACK / name for name in ("sources.json", "cases.json", "evals.json", "adaptive_probes.json"))
    paths.update(ROOT / name for name in (PROMPT, PLAYBOOK, GUIDES,
                 "research_tools/reading_strategy.py", "schemas/plain_reading_context.schema.json", "schemas/plain_reading_response.schema.json"))
    # Retain v3's provenance, including exact source metadata already pinned.
    paths.update(ROOT / item["path"] for item in json.loads((ROOT / "data/interpretation/plain_v3/manifest.json").read_text())["files"]
                 if item["path"].endswith(".source.json"))
    paths.add(ROOT / "data/reference/interpretation/dtt_chanwei.source.json")
    base.write(PACK / "manifest.json", {"version":VERSION,"system_prompt":PROMPT,"method_guides":GUIDES,
        "reading_playbook":PLAYBOOK,"model_called":False,"review_status":"EDITORIAL_DRAFT_NOT_EXPERT_REVIEWED",
        "case_count":len(base.CASES),"source_count":len(base.SOURCES),"heldout_count":len(evals),"adaptive_probe_count":len(probes),
        "files":[{"path":str(p.relative_to(ROOT)),"sha256":sha256(p.read_bytes()).hexdigest()} for p in sorted(paths)]})
    print(json.dumps({"version":VERSION,"cases":len(base.CASES),"sources":len(base.SOURCES),"heldout":len(evals),"probes":len(probes),"model_called":False}))


if __name__ == "__main__":
    build()
