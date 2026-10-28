"""Build source-guided synthesis examples offline; preserve the historical v2 pack."""
from copy import deepcopy
from hashlib import sha256
import json

from scripts import build_plain_interpretation_data as base

ROOT = base.ROOT
PACK = ROOT / "data/interpretation/plain_v3"
VERSION = "plain-vietnamese-2026-10-27-v3.2"
GUIDES_PATH = "docs/prompts/interpretation_method_guides_v3.json"
PROMPT_PATH = "docs/prompts/plain_vietnamese_v3.system.txt"


def build():
    from research_tools.interpretation_prompt import Context, validate_response
    base.SOURCES[:] = json.loads((ROOT / "data/interpretation/plain_v2/sources.json").read_text())
    base.CASES.clear()
    case, source = base.case, base.source
    b, m, l, z = "BAZI_NATAL_V1", "MAIHOA_INTERNAL", "LIUYAO_NAJIA", "ZHOUYI_TEXT"
    source("mh:reason", "Mai Hoa Dịch Số · Chiêm bốc luận lý quyết", "數說當也，必以理論之而後備。", [m],
           "data/reference/maihoa/volume_2.wikitext", "https://zh.wikisource.org/w/index.php?oldid=1441921")
    source("mh:phase_priority", "Mai Hoa Dịch Số · Thể Dụng Hỗ Biến chi quyết",
           "用為占之即應，互為中間之應，變為事占之終應。", [m],
           "data/reference/maihoa/volume_3.wikitext", "https://zh.wikisource.org/w/index.php?oldid=1441927")
    source("ly:effective", "Tăng San Bốc Dịch · Nguyên thần Kỵ thần suy vượng",
           "元神𨿽生用神，須要旺相，方可生得用神。", [l],
           "data/reference/interpretation/zsby_10.wikitext", "https://zh.wikisource.org/w/index.php?oldid=2100301")
    source("ziping:rescue", "Tử Bình Chân Thuyên · Thành bại cứu ứng",
           "成中有敗，必是帶忌；敗中有成，全憑救應。", [b],
           url="https://m.donglishuzhai.net/chapter/3722.html", state="WEB_EXCERPT_NOT_EDITION_PINNED")

    # Original editorial slices: supplied assessments are teaching inputs, never
    # independently calculated natal charts or historical cases with outcomes.
    case("bazi-01-strong", b, "GENERAL", ["STRONG", "NATAL_ONLY"], "Lá số này nên phát huy điều gì?",
         ["Nhật chủ Giáp Mộc; mùa sinh trợ Mộc, có căn Mộc bản khí và can cùng hành lộ.",
          "Phân tích đã xếp STRONG, hướng phù ức tạm ưu tiên Hỏa, CONDITIONAL.",
          "Chưa xét đầy đủ cách cục và khí hậu; chưa có dữ kiện nghề nghiệp hoặc vận."], ["dtt:strength", "dtt:month"],
         ("Điểm chính của lá số là phần sinh trợ cho Giáp Mộc đã nổi bật; hướng điều tiết đang được đề xuất là Hỏa, tức phần Mộc sinh ra. Có thể dùng nhận định này để suy ngẫm về cách vận dụng điều đang có, chưa đủ để chọn nghề hoặc định tính cách.", [1,2,3]),
         [("Nhật chủ là can ngày, ở đây là Giáp Mộc, làm điểm quy chiếu cho các quan hệ. Mộc vừa được mùa sinh trợ vừa có gốc trong chi và có can cùng hành hỗ trợ. Ba dấu hiệu cùng chiều là nền cho nhận định thiên vượng đã được cung cấp; kết luận này không dựa vào việc chỉ đếm số chữ Mộc.", [1,2]),
          ("Trên nền đó, Hỏa được đề xuất vì Mộc sinh Hỏa: quan hệ này đưa phần sinh trợ sang phía được Nhật chủ sinh ra. Nhận định vì vậy nối tiếp điều đã thấy ở mùa và căn, chứ không phải khuyết hành nào thì bổ hành đó. Đề xuất vẫn có điều kiện vì phần cách cục và nóng lạnh chưa được xét đủ.", [1,2,3]),
          ("Đọc gộp lại, điểm đáng giữ là phân biệt được hỗ trợ với sử dụng sự hỗ trợ ấy. Nếu liên hệ với công việc, có thể lấy đây làm câu hỏi về đầu ra cụ thể sau giai đoạn chuẩn bị. Lá số chưa chứng minh bạn đang chuẩn bị quá lâu hoặc hợp nghề thuộc Hỏa; những điều đó cần đối chiếu ngoài đời.", [1,2,3])],
         ("Bạn có thể chọn một việc đã chuẩn bị tương đối đủ, hoàn thành một bản thử nhỏ rồi lấy phản hồi; so kết quả với việc tiếp tục chỉ bổ sung tài liệu.", [1,2]),
         "Hướng phù ức còn có điều kiện; chưa phân tích vận, cách cục đầy đủ hoặc nghề nghiệp thực tế.")
    case("bazi-02-weak", b, "CAREER", ["WEAK", "NATAL_ONLY"], "Tôi nên chú ý gì khi nhận thêm việc?",
         ["Nhật chủ chưa được mùa trợ, không có căn cùng hành và không có can sinh trợ lộ; assessment=WEAK.",
          "Có Ấn trong tàng can; hướng phù ức ưu tiên nhóm sinh trợ, CONDITIONAL.",
          "Chưa có mô tả nhiệm vụ, thời gian hoặc hỗ trợ thực tế."], ["dtt:strength"],
         ("Nếu dùng lá số để đối chiếu lựa chọn này, nên làm rõ chỗ dựa trước khi tăng yêu cầu. Nền sinh trợ đang được đánh giá là mỏng, nhưng vẫn có Ấn trong phần tàng nên không thể đọc thành hoàn toàn không có trợ lực.", [1,2]),
         [("Thân nhược ở đây là nhận định về mức sinh trợ cho can ngày, không phải yếu sức hoặc kém năng lực. Mùa, căn và can lộ đang cùng chỉ về phía ít hỗ trợ. Bởi vậy, nhánh phù ức đề xuất sinh trợ thay vì tiếp tục làm tăng phía tiết hao.", [1,2]),
          ("Tuy nhiên, Ấn là nhóm sinh cho Nhật chủ và vẫn có trong tàng can. Dữ kiện này ngăn cách đọc tuyệt đối rằng lá số không có chỗ dựa. Nó chưa đủ để đảo kết luận thành vượng, cũng chưa xác nhận ngoài đời sẽ có người hướng dẫn hoặc giúp đỡ đúng lúc.", [1,2]),
          ("Với việc nhận thêm nhiệm vụ, ý nghĩa có thể đem đối chiếu là yêu cầu mới phải đi cùng điều kiện thực hiện. Chỗ cần kiểm tra là mức hỗ trợ có sẵn so với phần việc tăng thêm; không lấy chữ nhược làm câu trả lời nhận hay từ chối. Quyết định cụ thể còn thiếu khối lượng, kỹ năng và thời gian thực tế.", [1,2,3])],
         ("Bạn có thể ghi phần việc tăng thêm, số giờ có thể dành và người hỗ trợ đã xác nhận; thử một giai đoạn nhỏ trước khi cam kết toàn bộ.", [1,2,3]),
         "Lá số chưa xác định năng lực đảm nhiệm hoặc kết quả của công việc cụ thể.")
    case("bazi-03-mixed", b, "GENERAL", ["MIXED", "NATAL_ONLY"], "Vậy mệnh tôi đang tốt hay xấu?",
         ["Mùa không sinh trợ Nhật chủ, nhưng có căn cùng hành trong chi và có can Ấn sinh trợ.",
          "Có can thuộc nhóm khắc Nhật chủ; assessment.strength=MIXED.",
          "Balance=UNRESOLVED; chưa chốt hành ưu tiên, chưa có Đại vận/Lưu niên."], ["dtt:strength", "dtt:month"],
         ("Lá số có cả phần nâng đỡ lẫn phần gây sức ép, nên chưa có cơ sở gộp thành tốt hoặc xấu. Điểm cần hiểu là hai phía chưa được phân định đủ rõ để chọn hướng điều tiết.", [1,2,3]),
         [("Tháng sinh không nâng đỡ Nhật chủ là một bất lợi trong nhánh xem mùa, nhưng chưa phải toàn bộ lá số. Căn cùng hành trong chi và can Ấn lại bổ sung sinh trợ. Nếu chỉ lấy một phía, nhận định sẽ bỏ mất chính những dấu hiệu khiến phần phân tích giữ trạng thái đan xen.", [1,2]),
          ("Phía khắc Nhật chủ cũng có mặt trên can, vì vậy có gốc và có trợ lực chưa đồng nghĩa đã thiên vượng. Bộ điều kiện hiện có chưa so được hiệu lực hai phía đến mức chốt vượng hay nhược. Đan xen không có nghĩa chúng đã cân bằng hoặc triệt tiêu nhau.", [1,2,3]),
          ("Từ đó, kết luận hợp lý là giữ việc chọn hành ở trạng thái để mở. Phần đọc được vẫn hữu ích ở chỗ xác định những lực nào cần đặt cạnh nhau; phần chưa đọc được là lực nào đủ vai trò chủ đạo. Chọn một chủ đề cụ thể sẽ giúp tập trung phân tích, nhưng không tự bổ sung được vận hoặc điều kiện còn thiếu.", [1,2,3])],
         ("Bạn có thể đặt một câu hỏi cụ thể về học tập hoặc công việc, rồi đối chiếu riêng điều đang hỗ trợ và điều đang đòi hỏi thêm ở tình huống đó.", [1,2]),
         "Chưa chốt hướng phù ức hoặc có dữ kiện vận để kết luận một thời kỳ thuận nghịch.")
    case("bazi-04-structure", b, "CAREER", ["CANDIDATE_STRUCTURE", "NATAL_ONLY"], "Có Chính Quan là hợp làm quản lý đúng không?",
         ["Chính Quan là ứng viên cách cục từ chi tháng, có can thấu phù hợp.",
          "Cách cục CONDITIONAL; chưa xét đủ thành bại, phá cách và cứu ứng.",
          "Chưa có thông tin kinh nghiệm điều phối, nhiệm vụ quản lý hoặc vận."], ["ziping:use", "ziping:formation", "ziping:rescue"],
         ("Chính Quan đang là một hướng để khảo sát cấu trúc lá số, chưa phải kết luận bạn hợp làm quản lý. Cần phân biệt dấu hiệu hình thành một cách cục với hiệu quả của nó khi phối hợp cả bốn trụ.", [1,2]),
         [("Ứng viên này xuất phát từ quan hệ giữa can ngày với tháng sinh và việc có can thấu, tức yếu tố trong chi xuất hiện trên can. Đây là lý do nó được đưa vào phần khảo sát, thay vì chỉ vì thấy chữ Quan ở đâu đó. Dữ kiện xác nhận điểm xuất phát của phép đọc, chưa xác nhận một chức vụ.", [1]),
          ("Tử Bình Chân Thuyên tiếp tục đặt vấn đề thành bại và cứu ứng sau khi tìm dụng theo tháng. Một cấu trúc có yếu tố thuận vẫn có thể kèm điều kiện làm giảm hiệu lực; muốn nói có giải cứu cũng phải có yếu tố phối hợp cụ thể. Phần này chưa được xét đủ nên trạng thái ứng viên cần giữ nguyên.", [1,2]),
          ("Liên hệ với câu hỏi nghề nghiệp, điều còn thiếu không chỉ là tên cách cục mà là bằng chứng bạn thực hiện vai trò quản lý thế nào. Có thể dùng chủ đề Quan như một gợi ý để suy ngẫm về trách nhiệm và tổ chức, nhưng khả năng phân công, xử lý xung đột và theo dõi kết quả phải được quan sát thực tế. Chưa có cơ sở suy từ một nhãn sang lời khuyên chọn nghề.", [1,2,3])],
         ("Bạn có thể thử điều phối một nhiệm vụ nhỏ và xin phản hồi về cách giao việc, theo dõi tiến độ; dùng kết quả đó để đánh giá lựa chọn quản lý.", [1,3]),
         "Chưa xác nhận thành cách, khả năng nghề nghiệp hoặc thời điểm thăng tiến.")
    case("bazi-05-climate", b, "GENERAL", ["CLIMATE_CONFLICT", "NATAL_ONLY"], "Vì sao một đoạn cần Hỏa, đoạn khác lại cần Thủy?",
         ["Hướng phù ức tạm ưu tiên Thủy, CONDITIONAL.", "Điều hậu sơ bộ theo mùa gợi ý Hỏa; climate_conflict=true.",
          "Chưa có bảng Điều hậu đầy đủ theo Can và tháng, chưa hợp nhất hai nhánh."], ["dtt:climate", "ziping:climate"],
         ("Hai đề xuất khác hướng vì đang xét hai vấn đề: điều tiết quan hệ sinh trợ và điều hòa nóng lạnh. Phần phân tích đã nhận diện sự khác biệt nhưng chưa đủ dữ kiện để quyết định nhánh nào cần ưu tiên.", [1,2,3]),
         [("Thủy ở đây thuộc nhánh phù ức, tức tìm hướng điều tiết phần sinh trợ và tiết hao trong mệnh cục. Đề xuất có điều kiện nên chỉ có giá trị trong phạm vi ấy. Nó chưa nói rằng mọi mặt của lá số đều cần thêm Thủy.", [1]),
          ("Hỏa lại được gợi ý ở nhánh Điều hậu, tức xem điều kiện nóng lạnh theo mùa. Tử Bình Chân Thuyên yêu cầu phối khí hậu với phép đọc theo tháng, nên không thể bỏ nhánh này chỉ vì đã có đề xuất phù ức. Tuy vậy, gợi ý mùa của ứng dụng chưa phải một kết luận Điều hậu đầy đủ.", [1,2,3]),
          ("Đọc gộp lại, sự khác hướng chính là điểm phải làm rõ trước khi chốt một hành chung. Muốn đi xa hơn cần đánh giá Điều hậu cụ thể và quan hệ với cấu trúc lá số, rồi mới so thứ tự ưu tiên. Hiện chưa có cơ sở tự lấy một bên làm đúng hoặc lấy cả hai làm đơn thuốc áp dụng ngoài đời.", [1,2,3])],
         ("Bạn có thể giữ riêng hai nhận định khi đọc lại lá số và yêu cầu làm rõ điều kiện của từng nhánh trước khi cân nhắc một ứng dụng theo hành.", [1,2,3]),
         "Điều hậu mới là gợi ý mùa; chưa chốt hành ưu tiên dùng chung.")
    case("bazi-06-wealth", b, "WEALTH", ["NATAL_ONLY", "WEALTH_EXPOSED"], "Có Tài lộ là tôi dễ có tiền không?",
         ["Chính Tài xuất hiện trên can năm.", "Thực Thương chưa lộ trên can nhưng có trong tàng can.",
          "Khí thế MIXED; hướng phù ức UNRESOLVED, chưa có dữ kiện thu nhập hoặc vận."], ["dtt:strength", "ziping:formation"],
         ("Chính Tài lộ cho biết nhóm quan hệ về Tài có mặt rõ trên can, chưa cho biết kiếm tiền dễ hay khó. Vì sức Nhật chủ và sự phối hợp còn để mở, chưa thể chuyển sự hiện diện này thành kết luận tài chính.", [1,2,3]),
         [("Tài là nhóm bị Nhật chủ khắc trong quan hệ ngũ hành; Chính Tài ở đây xuất hiện trên can năm. Điều đó xác nhận vị trí của một nhóm trong lá số. Chữ Tài tự nó không chứa số tiền, mức ổn định hoặc chi phí để có được thu nhập.", [1,3]),
          ("Khi đọc Tài cần đặt nó cạnh khả năng phối hợp của toàn cục, thay vì lấy một nhãn làm đáp án. Phần sinh trợ đang có dấu trái chiều nên chưa chốt mạnh yếu; Thực Thương vẫn tồn tại trong tàng can dù không lộ trên can. Không được từ đây kết luận rằng thiếu đường tạo ra thu nhập hoặc chắc đã có chuỗi sinh Tài hữu hiệu.", [1,2,3]),
          ("Như vậy, phần có thể nói là lá số cung cấp một điểm để khảo sát chuyện Tài; phần chưa thể nói là điểm đó vận hành thuận đến đâu. Nếu đem vào câu hỏi đời sống, nên đối chiếu cách tạo giá trị, điều kiện nhận tiền và khoản phải bỏ ra. Các thông tin này cần được hỏi hoặc kiểm tra, không nằm sẵn trong tên Chính Tài.", [1,2,3])],
         ("Bạn có thể mô tả một nguồn thu cụ thể: việc tạo ra giá trị, điều kiện được trả và chi phí đi kèm; đối chiếu từng khâu bằng số liệu đang có.", [1,2,3]),
         "Chưa có Đại vận/Lưu niên và dữ liệu tài chính thực tế để bàn một thời kỳ thu nhập.")
    case("bazi-07-study", b, "STUDY", ["NATAL_ONLY", "RESOURCE_EXPOSED"], "Tôi nên thay đổi cách học thế nào?",
         ["Nhật chủ Canh Kim; Chính Ấn Thổ lộ trên can tháng và có trong tàng can.",
          "Thực Thương Thủy có trong tàng can, chưa lộ trên can.",
          "Assessment=MIXED, balance=UNRESOLVED; chưa đánh giá năng lực hay thói quen học."], ["dtt:month", "dtt:strength"],
         ("Điểm có thể đem đối chiếu là cách nối phần tiếp nhận kiến thức với phần tự diễn đạt và thực hành. Lá số có cả hai nhóm quan hệ này; vị trí lộ hay tàng chưa xác định bạn học theo cách nào hiệu quả nhất.", [1,2,3]),
         [("Canh Kim là điểm quy chiếu; Thổ sinh Kim nên nhóm Ấn thuộc phía sinh trợ. Ấn xuất hiện trên can tháng khiến nó là một dữ kiện liên quan khi bàn chủ đề học. Có thể dùng hình ảnh này để suy ngẫm về phần tiếp nhận kiến thức, nhưng chưa đủ để nói bạn nhớ tốt hoặc dựa nhiều vào sách vở.", [1,3]),
          ("Kim sinh Thủy nên Thực Thương thuộc phía được Nhật chủ sinh ra, khác vai trò sinh trợ của Ấn. Nhóm này có trong tàng can, vì vậy không phải vắng khỏi lá số. Việc chưa lộ chỉ mô tả vị trí; không chứng minh bạn khó diễn đạt, thiếu sáng tạo hoặc ít thực hành.", [1,2,3]),
          ("Nối hai phần lại, câu hỏi hữu ích là điều đã tiếp nhận có được kiểm tra bằng một đầu ra tự làm hay chưa. Đây là cách ứng dụng biểu tượng vào việc học để bạn tự thử, không phải chẩn đoán một điểm yếu. Vì hướng điều tiết của mệnh cục còn để mở, kết quả bài tập và phản hồi thực tế mới giúp chọn cách học phù hợp.", [1,2,3])],
         ("Bạn có thể thử một buổi học gồm phần đọc ngắn rồi tự giải hoặc trình bày lại khi đóng tài liệu; so độ hiểu và lỗi còn mắc với cách học cũ.", [1,2,3]),
         "Những liên hệ với thói quen học là ứng dụng hiện đại; chưa có đánh giá năng lực hoặc vận học tập.")
    case("bazi-08-relations", b, "RELATIONSHIPS", ["NATAL_ONLY", "HAS_RELATIONS"], "Lá số có hình là tình cảm sẽ đổ vỡ à?",
         ["Nhận diện Tý–Mão hình liên quan chi ngày.", "Chưa đánh giá đủ cứu giải hoặc hiệu lực tổ hợp trong toàn cục.",
          "Không có thông tin tương tác thực tế hoặc dữ kiện người còn lại."], ["smt:relations"],
         ("Tổ hợp được nhận diện chưa đủ để kết luận đổ vỡ. Nó là điểm cần khảo sát trong lá số, còn hiệu lực toàn cục và tình trạng mối quan hệ đều chưa được xác định.", [1,2,3]),
         [("Hình là tên một kiểu tổ hợp giữa các Chi, ở đây có liên quan vị trí chi ngày. Tam Mệnh Thông Hội lưu ý không cứ thấy hình là luận hung. Vì vậy, bước nhận diện tổ hợp và bước kết luận sự kiện cần được giữ tách biệt.", [1,2]),
          ("Muốn nói tổ hợp ấy tác động thế nào còn phải xét sự phối hợp và khả năng giải trong toàn cục. Phần dữ kiện hiện tại chưa hoàn tất bước đó, nên không thể tự thêm một tai họa hay một lời giải cứu. Cũng không được dùng một lá số để xác định ý định hoặc sự chung thủy của người khác.", [1,2,3]),
          ("Với câu hỏi tình cảm, phần hữu ích là đưa việc đối chiếu về tình huống hai người thực sự đang gặp. Một bất đồng cụ thể có thể được làm rõ bằng thông tin trao đổi; tên tổ hợp không cho biết bất đồng đó là gì. Như vậy, lá số chưa trả lời được kết cục nhưng cũng không tạo căn cứ để mặc định một kết cục xấu.", [1,2,3])],
         ("Nếu đang có việc vướng, bạn có thể nêu một tình huống và điều hai người muốn thống nhất, rồi kiểm tra mức đồng thuận qua cuộc trao đổi thực tế.", [2,3]),
         "Chưa luận hợp hai lá số, cứu giải toàn cục hoặc thời điểm hôn nhân.")

    case("maihoa-01-support", m, "WEALTH", ["USE_GENERATES_BODY"], "Việc thu khoản tiền này có thuận không?",
         ["Thể Chấn Mộc, Dụng Khảm Thủy; quan hệ đầu USE_GENERATES_BODY, FAVOURABLE.",
          "Hỗ phía Thể cùng hành Mộc; Hỗ phía Dụng thuộc Thổ bị Thể khắc; quan hệ cuối cùng hành Mộc, FAVOURABLE.",
          "Độ mạnh chưa được cấp; chưa có xác nhận thanh toán hoặc ứng kỳ."], ["mh:roles", "mh:wealth", "mh:phase_priority"],
         ("Các quan hệ được cấp cùng nghiêng về chiều thuận cho việc thu tiền: có sinh trợ ở đầu và cùng hành ở cuối. Điểm chưa thể chốt là mức hiệu lực và lúc nhận, vì thiếu vượng suy cụ thể cùng xác nhận thanh toán.", [1,2,3]),
         [("Thể đại diện phía chủ thể, Dụng đại diện việc đang hỏi. Thủy sinh Mộc nên ở bước đầu, phía việc có chiều sinh trợ cho phía bạn. Trong phép cầu tài đây là dấu tiến ích, nhưng nó chưa phải thông tin khoản tiền đã được duyệt.", [1,3]),
          ("Đặt quan hệ đầu cạnh Hỗ và Biến, chưa thấy một quan hệ khắc Thể trong các phần đã cấp. Hỗ phía Thể cùng hành, Hỗ phía việc được Thể khắc, rồi cuối trở về cùng hành; chúng bổ sung cho cách đọc thuận ban đầu. Những chặng này mô tả cấu trúc diễn tiến, chưa tự xác định các bước xử lý tiền ngoài đời.", [1,2]),
          ("Vì vậy, có cơ sở giữ chiều luận thuận thay vì chỉ dựa vào một dấu đơn lẻ. Tuy nhiên, chưa có độ mạnh thì không biết sinh trợ ấy đủ hiệu lực đến đâu; chưa có ứng kỳ thì không thể hẹn ngày tiền về. Việc đối chiếu cần tập trung vào điều kiện thanh toán đã được xác nhận tới đâu.", [1,2,3])],
         ("Bạn có thể kiểm tra khoản tiền đã được chấp thuận chưa, còn ai phải xác nhận và điều kiện nào còn thiếu trước khi thanh toán.", [1,3]),
         "Thiếu vượng suy cụ thể và ứng kỳ; các chặng quẻ không phải lịch thanh toán.")
    case("maihoa-02-drain", m, "TRADE", ["BODY_GENERATES_USE"], "Tôi nên chú ý gì trước khi nhận đơn hàng này?",
         ["Thể Ly Hỏa, Dụng Khôn Thổ; BODY_GENERATES_USE, chiều hao về phía Thể.",
          "Hỗ phía Thể là Mộc sinh Thể; cuối là Thổ được Thể sinh, vẫn có chiều hao.",
          "Chưa có mức vượng suy, giá vốn hoặc điều khoản đơn hàng."], ["mh:trade", "mh:phase_priority", "mh:reason"],
         ("Điểm xuyên suốt là phía bạn có chiều phải đưa ra, dù ở giữa vẫn có yếu tố sinh trợ. Nên đối chiếu phần phải bỏ ra với phần thực nhận trước khi quyết định; quẻ chưa xác nhận đơn hàng đang lỗ.", [1,2,3]),
         [("Hỏa sinh Thổ nên quan hệ đầu là Thể sinh Dụng: tác động đi từ phía chủ thể sang phía việc. Theo phép giao dịch được trích, đây là chiều cần xét hao tổn. Nó cho một hướng để khảo sát, chưa chỉ rõ hao tiền, thời gian hay công sức.", [1,3]),
          ("Ở giữa có Mộc sinh Hỏa nên không thể nói mọi chặng đều thiếu hỗ trợ. Nhưng phía cuối lại là Thổ được Hỏa sinh, tức điều kiện hao ở đầu chưa được thay bằng một chiều tiến ích về cuối. Sinh trợ ở chặng giữa không tự xóa quan hệ hao ở chặng kết.", [1,2]),
          ("Đọc chung, điều cần làm rõ là phần hỗ trợ có đủ bù phần phải ứng ra hay không. Quẻ chưa có dữ kiện để lượng hóa mức bù đó, còn lợi nhuận cần giá vốn và điều khoản cụ thể. Vì vậy, dùng cách đọc này để soi một câu hỏi về chi phí sẽ sát hơn việc lấy nó làm đáp án nhận hoặc bỏ đơn.", [1,2,3])],
         ("Bạn có thể tính riêng chi phí ứng trước, số giờ làm và khoản thực nhận; kiểm tra cả trường hợp thanh toán chậm trước khi chốt đơn.", [1,2,3]),
         "Chưa đủ vượng suy và số liệu giao dịch để kết luận lãi lỗ hoặc mức hao.")
    case("maihoa-03-control", m, "PLANNING", ["USE_CONTROLS_BODY"], "Việc tôi đang tính có trở ngại gì cần lưu ý?",
         ["Thể Khảm Thủy, Dụng Cấn Thổ; USE_CONTROLS_BODY, CAUTION.",
          "Hỗ phía Thể là Khảm Thủy, SAME, FAVOURABLE; quan hệ cuối Kim sinh Thể, FAVOURABLE.",
          "Chưa có mô tả trở ngại, độ mạnh hoặc ứng kỳ."], ["mh:roles", "mh:planning", "mh:sequence", "mh:phase_priority"],
         ("Quẻ cho một diễn tiến đầu chịu sức ép, về sau có chiều hỗ trợ. Vì thế cần làm rõ điều kiện khởi sự; dấu thuận ở cuối chưa đủ để bảo đảm vượt được điểm khó ở đầu.", [1,2,3]),
         [("Thổ khắc Thủy nên Dụng khắc Thể: phía việc đang hỏi có chiều gây sức ép lên phía chủ thể. Theo phần mưu sự, đây là dấu cần thận trọng ở bước đầu. Dữ kiện chưa gọi tên một người, một thủ tục hay một chi phí cụ thể gây sức ép đó.", [1,3]),
          ("Tuy nhiên, Hỗ phía Thể cùng hành Thủy và phần cuối có Kim sinh Thủy. Tỷ hòa là quan hệ cùng hành được phần phân tích xếp thuận, không có nghĩa trung tính hoặc chủ quan. Hai dữ kiện này khiến bài luận cần giữ khả năng có hỗ trợ về sau thay vì gộp toàn quẻ thành thất bại.", [1,2]),
          ("Nối các chặng lại, điểm cần phân biệt là khó ở điều kiện bắt đầu với chiều hỗ trợ khi đi tiếp. Muốn xem phần thuận sau có đủ hiệu lực hay không vẫn thiếu vượng suy; không thể tự điền một người cứu giúp hoặc mốc chuyển vận. Khi đối chiếu kế hoạch, nên xác minh điều kiện bắt buộc trước rồi mới dựa vào phần hỗ trợ dự kiến.", [1,2,3])],
         ("Bạn có thể liệt kê điều kiện để bắt đầu và điều kiện để hoàn tất, đánh dấu chỗ đã xác nhận với chỗ còn chờ; ưu tiên làm rõ điểm đang chặn bước đầu.", [1,2,3]),
         "Chưa biết trở ngại thực tế hoặc ứng kỳ; diễn tiến thuận sau không phải bảo đảm thành công.")
    case("maihoa-04-sequence", m, "GENERAL", ["MIXED_PHASES"], "Vì sao đầu thuận mà cuối lại có cảnh báo?",
         ["Quan hệ đầu USE_GENERATES_BODY, FAVOURABLE.", "Hỗ phía Thể SAME, FAVOURABLE; Hỗ phía việc USE_CONTROLS_BODY, CAUTION.",
          "Quan hệ cuối USE_CONTROLS_BODY, CAUTION; chưa có vượng suy hoặc ứng kỳ."], ["mh:sequence", "mh:phase_priority"],
         ("Chiều hỗ trợ ở đầu đi kèm sức ép ở giữa và cuối, nên thuận lúc khởi sự chưa đủ nói toàn việc thuận. Phần cần chú ý là điều kiện để duy trì và hoàn tất sau bước đầu.", [1,2,3]),
         [("Dụng sinh Thể ở đầu mô tả việc có chiều hỗ trợ cho chủ thể khi khởi sự. Đây là một dấu thuận thật trong phạm vi phép đọc, không cần phủ nhận vì có cảnh báo về sau. Nhưng nó mới nói một chặng, chưa bao trùm cả quá trình.", [1,3]),
          ("Ở phần giữa, Hỗ phía Thể cùng hành vẫn được xếp thuận, trong khi Hỗ phía việc lại khắc Thể. Hai quan hệ khác nhau cùng hiện diện nên không thể lấy chữ thuận của một bên thay cho toàn chặng. Phần Biến tiếp tục khắc Thể, khiến điểm cần theo dõi chuyển về điều kiện kết thúc.", [1,2,3]),
          ("Đọc chung, nhận định chính là có thể thuận khi bắt đầu nhưng cần kiểm tra sức ép ở đoạn đi tiếp và hoàn tất. Chưa có vượng suy thì chưa so được mức nặng nhẹ; chưa có ứng kỳ thì không gán chặng giữa hoặc cuối thành một ngày cụ thể. Cũng chưa có căn cứ gọi tên sự cố sẽ xảy ra.", [1,2,3])],
         ("Bạn có thể rà riêng điều kiện bàn giao, duy trì và hoàn tất, thay vì chỉ kiểm tra việc có bắt đầu được hay không.", [1,2,3]),
         "Chưa có vượng suy, ứng kỳ hoặc ngữ cảnh để xác định mức độ và sự kiện cụ thể.")

    case("liuyao-01-money", l, "WEALTH", ["SELECTED_USE", "DAY_MONTH_MIXED"], "Người kia có trả khoản đang nợ không?",
         ["Engine đã chọn Thê tài làm Dụng thần cho khoản tiền.", "Dụng được tháng sinh nhưng bị ngày khắc, tendency=MIXED.",
          "Nguyên thần có mặt nhưng còn tĩnh, hiệu lực sinh trợ chưa được xác nhận.", "Chưa có ứng kỳ hoặc cam kết thanh toán."], ["ly:wealth", "ly:month", "ly:effective"],
         ("Khoản tiền đang có cả nền nâng đỡ lẫn sức ép, còn nguồn trợ chưa được xác nhận đủ hiệu lực. Vì vậy, phần luận chưa nghiêng thành một kết luận chắc về trả hoặc không trả.", [1,2,3]),
         [("Thê tài được chọn làm hào đại diện khoản tiền, nên mọi sinh khắc ở đây phải quay về đối tượng đó. Tháng sinh Dụng là một nền hỗ trợ, còn ngày khắc Dụng là điều kiện gây sức ép. Hai mặt cùng tồn tại, không được lấy một mặt để xóa mặt còn lại.", [1,2]),
          ("Nguyên thần là nhóm sinh Dụng, nhưng có tên trong quẻ chưa đồng nghĩa đã sinh trợ hữu hiệu. Ở lát cắt này, nhóm ấy còn tĩnh và phần phân tích chưa xác nhận tác dụng. Theo Tăng San, phải xét sức và điều kiện hoạt động, nên chưa thể dùng sự hiện diện này để kết luận đã được cứu.", [1,2,3]),
          ("Như vậy, kết luận để mở xuất phát từ điều kiện trợ lực chưa rõ, chứ không phải quẻ không có gì để đọc. Ngoài đời, điều cần đối chiếu là khoản trả đã có xác nhận và điều kiện thực hiện hay mới chỉ là dự định. Quẻ chưa xác định thiện chí của người nợ hoặc ngày tiền về.", [1,2,3,4])],
         ("Bạn có thể xin một lịch trả được xác nhận, gồm khoản trả và điều kiện còn chờ; dùng thông tin ấy để kiểm tra khả năng thu tiền thực tế.", [2,3,4]),
         "Chưa có ứng kỳ, cam kết trả tiền và đánh giá đầy đủ hiệu lực trợ lực.")
    case("liuyao-02-selection", l, "DOCUMENT", ["AMBIGUOUS_USE"], "Hồ sơ của tôi có được duyệt không?",
         ["Chủ đề hồ sơ lấy Phụ mẫu làm trọng tâm.", "Có hai hào Phụ mẫu, selection=AMBIGUOUS.",
          "Ứng viên thứ nhất được tháng sinh nhưng tĩnh; ứng viên thứ hai động và bị ngày khắc; chưa chọn một hào."], ["ly:document", "ly:effective"],
         ("Vướng mắc chính là chưa khóa được hào đại diện hồ sơ, nên chưa thể gộp thành một kết luận được duyệt hay không. Hai ứng viên phải được giữ riêng vì điều kiện hỗ trợ và động tĩnh khác nhau.", [1,2,3]),
         [("Phụ mẫu ở câu hỏi này đại diện văn thư, không phải cha mẹ. Cả hai hào đều thuộc nhóm ấy, còn phần phân tích chưa xác định hào nào sát đối tượng cần xét. Bước chọn trọng tâm chưa xong thì nhận định về kết quả cũng phải giữ mở.", [1,2]),
          ("Ứng viên thứ nhất có tháng sinh nhưng đang tĩnh; ứng viên thứ hai có động nhưng gặp sức ép từ ngày. Không được ghép tháng sinh của hào đầu với động của hào sau để tạo một hào vừa vượng vừa động. Cũng chưa có căn cứ tự chọn hào có vẻ thuận hơn.", [2,3]),
          ("Phần có thể đọc lúc này là hai hướng khảo sát khác nhau: một bên có nền trợ, một bên có tác động nhưng kèm điều kiện cản. Muốn đi tiếp cần xác định đối tượng hoặc khâu hồ sơ và lựa chọn trọng tâm trên cùng quẻ. Bổ sung ngữ cảnh giúp làm rõ việc hỏi, chưa tự tạo bằng chứng hồ sơ đã được duyệt.", [1,2,3])],
         ("Bạn có thể xác định đang hỏi về văn bản đã nộp hay một khâu xử lý cụ thể, rồi đối chiếu riêng từng ứng viên trước khi chọn hào trọng tâm.", [1,2,3]),
         "Dụng thần chưa được chọn; chưa luận được kết quả chung hoặc ngày duyệt.")
    case("liuyao-03-day-clash", l, "CAREER", ["SELECTED_USE", "DAY_CLASH_STRONG_STATIC"], "Hào bị ngày xung là hỏng việc sao?",
         ["Quan quỷ đã được chọn cho câu hỏi về vị trí công việc.", "Hào gốc tĩnh, được tháng sinh, gặp ngày xung.",
          "Phân tích ghi DARK_ACTIVE sơ bộ, không ghi Nhật phá; chưa có động biến hoặc ứng kỳ đầy đủ."], ["ly:day", "ly:month"],
         ("Ở dữ kiện này, ngày xung chưa được đọc thành hỏng việc: hào có tháng sinh nên đang được xét theo hướng ám động. Đó là một trạng thái tác động có điều kiện, chưa phải kết luận công việc thành hay bại.", [1,2,3]),
         [("Quan quỷ là hào trọng tâm cho vị trí đang hỏi, còn tháng sinh cung cấp nền nâng đỡ cho hào. Khi hào vốn tĩnh gặp ngày xung trên nền đó, phần phân tích ghi nhận ám động, tức có tác động nổi lên dù không phải hào động từ lúc gieo. Cách đọc này giữ cả nền sức lẫn tác động của ngày.", [1,2,3]),
          ("Tăng San phân biệt xung hào tĩnh có sức với xung hào tĩnh suy yếu. Vì vậy, cùng chữ xung nhưng điều kiện của hào khác nhau thì ý nghĩa không giống nhau. Không được bỏ phần được tháng sinh rồi gọi đây là Nhật phá, cũng không được lật thêm hào để tạo quẻ biến.", [2,3]),
          ("Đọc gộp lại, dữ kiện hiện tại bác cách kết luận chỉ từ một chữ xung; nó chưa xác định kết quả tuyển chọn hay quyết định nhân sự. Phần tiếp theo cần là các điều kiện sinh khắc và động biến đã được phân tích thêm, cùng tình trạng thực tế của vị trí. Không nên lấy ám động làm lời hẹn chắc chắn có biến chuyển tốt.", [1,2,3])],
         ("Bạn có thể xác nhận vị trí đang ở bước nào và điều kiện xét chọn còn thiếu, rồi đối chiếu với phần trợ lực và cản trở đã được ghi nhận.", [1,2,3]),
         "Ám động còn ở mức sơ bộ; chưa đủ động biến và ứng kỳ để chốt kết quả công việc.")
    case("liuyao-04-document", l, "DOCUMENT", ["SELECTED_USE", "DAY_MONTH_MIXED"], "Bản kế hoạch xin phê duyệt nên rà soát gì?",
         ["Phụ mẫu ở hào 2 Mộc được chọn làm Dụng, được tháng Thủy sinh và ngày Mộc đồng hành.",
          "Thế ở hào 5 Hỏa, MOVING, có RETURN_CONTROLS; tendency=MIXED.",
          "Quan hệ Dụng → Thế là GENERATES: Mộc sinh Hỏa, Dụng sinh Thế; chiều ngược là Thế được Dụng sinh.",
          "Nguyên thần có mặt nhưng tĩnh; chưa xác nhận cứu giải. Chưa có nội dung văn bản hoặc ứng kỳ."], ["ly:document", "ly:month", "ly:effective"],
         ("Quẻ có nền hỗ trợ cho hào đại diện văn bản, nhưng điều kiện của người hỏi còn bị động biến gây sức ép. Điểm cần đối chiếu là khả năng theo việc đến cùng; quẻ chưa chứng minh bản kế hoạch đã đúng hoặc sẽ được duyệt.", [1,2,3,4]),
         [("Phụ mẫu đại diện bản kế hoạch, ở đây là Mộc được tháng sinh và ngày cùng hành. Hai điều kiện đó cùng nâng đỡ Dụng trong phép luận, nên không thể nói đối tượng hoàn toàn thiếu nền. Tuy vậy, sức hào không phải kết quả đọc và kiểm tra nội dung văn bản.", [1,4]),
          ("Dụng Mộc sinh Thế Hỏa, tức chiều sinh trợ hướng từ đối tượng về phía người hỏi. Nhưng Thế đang động và bị hồi đầu khắc, nghĩa là hào biến khắc lại hào gốc. Vì thế, Dụng có hỗ trợ và Thế có điều kiện bất lợi vẫn cùng tồn tại; không được đảo thành Thế sinh Dụng hoặc nói người hỏi đang hao lực nuôi văn bản.", [1,2,3]),
          ("Nối hai phần lại, chưa thể lấy Dụng được sinh phù để bỏ qua sức tiếp nhận ở Thế. Nguyên thần có mặt nhưng còn tĩnh cũng chưa đủ xác nhận đã giải được sức ép. Khi đối chiếu thực tế, có thể kiểm tra phần việc và điều kiện cần duy trì cho tới bước hoàn tất, nhưng chưa được kết luận chắc đang quá tải hoặc thiếu người hỗ trợ.", [1,2,3,4])],
         ("Bạn có thể rà yêu cầu phê duyệt bằng văn bản, phần việc mình phải theo tới cùng và thời gian có thể cam kết; kiểm tra từng mục thay vì mặc định nội dung đã đạt.", [1,2,4]),
         "Chưa có nội dung văn bản, cứu giải đầy đủ hoặc ứng kỳ để kết luận chất lượng và ngày được duyệt.")

    case("zhouyi-01-qian", z, "PLANNING", ["LINE_1"], "Hào đầu quẻ Càn khuyên gì khi khởi sự?",
         ["Đã truy xuất đúng quẻ Càn hào 1, nguồn 潛龍勿用。", "Không có Nạp Giáp, điều kiện dự án hoặc ứng kỳ."], ["zy:qian1"],
         ("Hình ảnh hào đầu gợi việc giữ sức và chuẩn bị khi chưa đến lúc bộc lộ đầy đủ. Nó chưa phải lệnh bỏ việc hoặc một mốc khởi sự đã được xác định.", [1,2]),
         [("Rồng còn ẩn được đặt ở vị trí đầu của quẻ Càn, nên ý chưa dùng gắn với một bước mở đầu. Trọng tâm là mức bộc lộ và điều kiện của bước ấy, không phải giá trị của toàn bộ kế hoạch. Cách đọc cần giữ hình ảnh với vị trí hào thay vì tách hai chữ thành phán quyết cho mọi tình huống.", [1]),
          ("Với câu hỏi khởi sự, có thể đem ý này đối chiếu phần chuẩn bị trước khi công bố hoặc mở rộng. Nhưng context chưa cho biết dự án thiếu điều gì, nên không tự thêm chuyện thiếu tiền hoặc chưa gặp người giúp. Muốn chọn thời điểm cụ thể cần thêm dữ kiện, còn hiện tại chỉ đang giải nghĩa hào.", [1,2])],
         ("Nếu đang chuẩn bị dự án, bạn có thể làm một bản nhỏ và lấy phản hồi về điều kiện còn thiếu trước khi mở rộng.", [1,2]),
         "Chỉ có kinh văn hào; không dùng thay kết luận Nạp Giáp hoặc dự đoán ngày bắt đầu.")
    case("zhouyi-02-jiji", z, "GENERAL", ["HEXAGRAM_63"], "Ký Tế nghĩa là mọi việc đã xong và sẽ tốt hết à?",
         ["Quẻ được xác định Ký Tế số 63; quẻ từ có 初吉終亂。", "Không có kinh văn hào, hào động hoặc ứng kỳ."], ["zy:jiji"],
         ("Ký Tế gợi thế đã vào hoàn tất, nhưng quẻ từ đặt ngay điều kiện phải giữ gìn sau khởi đầu tốt. Hoàn thành một bước chưa có nghĩa mọi bước sau tự ổn.", [1]),
         [("Mệnh đề đầu tốt, cuối rối nối hai thời điểm trong chính quẻ từ. Vậy nên ý hoàn tất phải đọc cùng khả năng trật tự bị xáo trộn về sau. Nếu chỉ lấy tên quẻ để kết luận mọi việc đều tốt, bài đọc sẽ bỏ mất điều kiện được nêu ngay trong văn bản.", [1]),
          ("Với câu hỏi này, điều có thể đối chiếu là cách duy trì sau một mốc hoàn thành. Context chưa có hào cụ thể nên chưa xác định một chỗ hỏng hay một sự cố sẽ xảy ra. Cũng không được đổi chữ cuối thành ngày hoặc tháng đã biết.", [1,2])],
         ("Bạn có thể rà việc bàn giao, người theo dõi và dấu hiệu sai sót cần kiểm tra sau mốc hoàn thành.", [1,2]),
         "Thiếu hào và ứng kỳ; đang giải nghĩa quẻ từ, chưa luận một sự kiện cụ thể.")

    guides = {
        "BAZI_NATAL_V1": {"source_ids": ["dtt:month", "dtt:strength", "ziping:use", "ziping:formation", "ziping:rescue", "ziping:climate"],
            "instruction": "BÁT TỰ: Lấy Nhật chủ và nguyệt lệnh làm nền, đặt mùa sinh cạnh căn khí và can sinh trợ/khắc tiết đã được cung cấp. Sau đó mới nối nhóm Thập Thần sát câu hỏi vào bức tranh ấy. Phân biệt vị trí hiện diện với hiệu lực: lộ không tự mạnh, tàng không tự yếu hoặc khó bộc lộ; số lượng không quyết định vượng suy. Nếu MIXED, giải thích các dấu trái chiều cụ thể và giữ hướng phù ức UNRESOLVED. Cách cục ứng viên chưa thành cách; không tự dựng Sát Ấn tương sinh, Thực Thương sinh Tài hoặc cứu ứng chỉ vì thấy các nhãn cùng có mặt. Nguyệt lệnh/cách cục, phù ức và Điều hậu là các nhánh khác nhau, chỉ nối khi findings đã cung cấp kết luận. Với câu hỏi học/việc, tổng hợp nền sinh trợ rồi nêu một liên hệ có điều kiện; không viết từng đoạn thành một định nghĩa Thập Thần. Không đoán tính cách, bệnh, thu nhập hoặc thời điểm khi chỉ có mệnh cục."},
        "MAIHOA_INTERNAL": {"source_ids": ["mh:roles", "mh:sequence", "mh:reason", "mh:phase_priority"],
            "instruction": "MAI HOA: Giữ Thể cố định làm chủ thể, Dụng là việc. Nối quan hệ đầu, Hỗ phía Thể, Hỗ phía Dụng và Biến thành một diễn tiến; so dấu đầu/cuối và điểm làm thay đổi cách đọc ở giữa. Không đổi hai Hỗ thành hai quẻ chủ, không đếm nhãn để bỏ cảnh báo của một chặng. Phần thuận có thể đi cùng phần cần thận trọng, cần nói rõ chúng thuộc chặng nào. SAME/tỷ hòa là quan hệ cùng hành theo finding, không tự đổi thành trung tính, trì trệ hoặc chủ quan. BODY_CONTROLS_USE khác USE_CONTROLS_BODY; nói rõ chiều. Vượng suy chỉ dùng mức được cấp; NOT_SPECIFIED là chưa xác định, không phải yếu hoặc thiếu sức bền của người hỏi. Khi chưa có nguyên văn quẻ/hào trong evidence, không tự lấy tên Độn/Bĩ/Ký Tế làm kết luận đảo ngược Thể Dụng. Thiếu ngoại ứng hoặc ứng kỳ thì không bịa; đầu–giữa–cuối là chặng trong phép đọc, chưa phải lịch. Dịch sang vấn đề thực tế bằng khả năng để đối chiếu, không suy từ quái sang một sự kiện đã xảy ra."},
        "LIUYAO_NAJIA": {"source_ids": ["ly:roles", "ly:month", "ly:day", "ly:effective"],
            "instruction": "LỤC HÀO: Bắt đầu đúng Dụng đã chọn; Phụ mẫu/Thê tài/Quan quỷ phải hiểu theo đối tượng của câu hỏi. selection AMBIGUOUS giữ riêng từng ứng viên, không ghép dữ kiện của hai hào; PROVISIONAL vẫn tạm chọn. Sau đó đặt Nhật–Nguyệt của Dụng cạnh động/tĩnh, Không/Phá và biến hóa đã được tính; xét thêm điều kiện Thế khi nó giới hạn chiều thuận của Dụng. reading:anchors xác định đúng Thế/Ứng; relation:use_world ghi chiều nguồn→đích từ mã quan hệ đã lưu, ưu tiên cách diễn đạt rõ chiều này. GENERATES: nguồn sinh đích; DRAINS: nguồn được đích sinh; CONTROLS: nguồn khắc đích; CONSUMES: nguồn bị đích khắc. Không đảo chiều hoặc xem có Nguyên thần là đã được cứu: phải có lực/hoạt động và đánh giá hiệu lực được cấp. Nguyên/Kỵ cùng có mặt chưa đủ tự giải chuỗi tham sinh quên khắc. Sinh phù của Dụng không xóa điều kiện xấu của Thế; Không/Phá không tự xóa hào hoặc tự thành thất bại. Tendency=MIXED phải giữ cả phần nâng đỡ và điều kiện cản. Hào văn thư vượng chưa chứng minh nội dung đúng; Thế bị khắc chưa chứng minh người hỏi quá tải. Chỉ nêu điều kiện ứng kỳ đã có, không biến nó thành ngày chắc có kết quả."},
        "ZHOUYI_TEXT": {"source_ids": ["zy:qian1", "zy:jiji"],
            "instruction": "KINH VĂN: Chỉ đọc quẻ từ hoặc hào từ thực sự được truy xuất. Nối hình ảnh, vị trí và điều kiện trong văn bản thành một ý nghĩa sát câu hỏi. Không thêm kinh văn từ trí nhớ, không coi nghĩa quẻ là kết luận Nạp Giáp và không gán chặng biểu tượng thành thời gian chắc chắn."},
    }
    guides[b]["instruction"] += " Điểm mở bài phải bắt nguồn từ bức tranh mệnh cục được findings xác nhận, không mở bằng một khoảng cách tiếp nhận–thực hành suy từ lộ/tàng. Không coi vị trí can năm là xa nên ít tác dụng nếu chưa có finding đánh giá khoảng cách. Chỉ nói Quý Thủy khắc Đinh Hỏa theo nhóm Quan Sát đã cấp, không gọi cùng quan hệ ấy là vừa khắc vừa tiết. Sự có mặt của một nhóm chỉ cho phép nêu vai trò, không kết luận nó khó hoặc dễ hoạt động."
    guides[m]["instruction"] += " Mỗi finding có phase và quy tắc riêng: quy tắc mưu sự cho Dụng ban đầu không tự áp vào Hỗ. Nếu Hỗ Thể khắc Hỗ Dụng chỉ được finding AUX đánh giá thuận, giữ đúng chiều thuận đó; không thêm thành chậm, chướng ngại hoặc phải siết tiến độ từ một trích đoạn khác. Có thể đề xuất kiểm tra tiến độ như ứng dụng hiện đại, nhưng không viết thành điều quẻ đã kết luận."
    guides[l]["instruction"] += " Không tự xếp hào nào mạnh nhất toàn quẻ hoặc kết luận Cừu/Kỵ không gây sức ép khi findings chưa so hiệu lực. Điều kiện bất lợi của Thế chỉ giới hạn kết luận thuận cho người hỏi; không chỉ ra người hỏi thiếu sức, khó theo việc hoặc dễ dừng. Nêu tách biệt tác động của hào với chuyện thực tế cần kiểm tra."
    guides[l]["instruction"] += " roles đã gán tên và hành từng vai: chỉ Kỵ thần là nhóm khắc Dụng; Cừu thần là nhóm khắc Nguyên, sinh Kỵ, không phải tên khác của hào khắc Dụng. Không tự gán lại vai. Ví dụ Dụng Kim thì Kỵ là Hỏa, Nguyên là Thổ, Cừu là Mộc; không viết Mộc khắc Kim. Đó là ví dụ giải thích hướng, không phải dữ kiện bổ sung cho phiên."
    base.write(ROOT / GUIDES_PATH, guides)
    evals = deepcopy(json.loads((ROOT / "data/interpretation/plain_v2/evals.json").read_text()))
    for item in evals:
        item["required_review_checks"] += ["Các đoạn cùng làm rõ một nhận định chính, có căn cứ và điều kiện giới hạn cụ thể.",
                                           "Ứng dụng đời sống được nêu như lựa chọn kiểm tra, không phải sự thật từ nhãn."]
    for key, base_id, question, facts, checks, forbidden in [
        ("holdout-09-synthesis", "bazi-07-study", "Tôi nên chuẩn bị gì để học một chuyên môn mới?",
         ["Nhật chủ Mậu Thổ sinh tháng Dần, mùa không sinh trợ; có căn Thổ trong chi và Bính Hỏa Ấn lộ.",
          "Có Giáp Mộc thuộc Quan Sát lộ; Thực Thương Kim nằm trong tàng can.",
          "Assessment=MIXED, balance=UNRESOLVED; chưa biết cách học hoặc năng lực thực tế."],
         ["Nối mùa không trợ với căn và Ấn sinh trợ để giải thích trạng thái đan xen.",
          "Liên hệ phần học với nền ấy, không chia mỗi đoạn thành định nghĩa một nhóm Thập Thần.",
          "Không kết luận ít thực hành hoặc diễn đạt khó vì Thực Thương nằm trong tàng can."],
         ["tàng can nên khó thực hành", "có Ấn nên học giỏi"]),
        ("holdout-10-sequence", "maihoa-01-support", "Kế hoạch bồi dưỡng kỹ năng này cần chuẩn bị gì?",
         ["Thể Khôn Thổ; Dụng Ly Hỏa sinh Thể, FAVOURABLE; Dụng STRONG.",
          "Hỗ phía Thể cùng hành Thổ, SAME/FAVOURABLE; Hỗ phía Dụng là Thủy bị Thể khắc, FAVOURABLE.",
          "Biến là Hỏa sinh Thể, FAVOURABLE; sức Thể NOT_SPECIFIED; chưa có ứng kỳ hoặc thông tin khóa học."],
         ["Nối thuận đầu/cuối với hai quan hệ Hỗ và nêu đúng phạm vi vượng suy đã biết.",
          "Không đổi tỷ hòa thành chủ quan, thụ động hoặc trì trệ.",
          "Không đổi sức Thể chưa xác định thành người hỏi thiếu sức bền."],
         ["tỷ hòa nên dễ chủ quan", "Thể yếu nên không theo nổi"]),
        ("holdout-11-direction", "liuyao-04-document", "Phần đề án tôi đang soạn cần chú ý gì?",
         ["Dụng Phụ mẫu tại L1 Thủy được Nhật–Nguyệt sinh phù, selection=SELECTED.",
          "Thế L4 Mộc đang MOVING, VOID, RETURN_CONTROLS; tendency=MIXED.",
          "Quan hệ đã lưu source_key=L1, target_key=L4, relation=GENERATES: Thủy sinh Mộc, Dụng sinh Thế.",
          "Nguyên thần tĩnh; chưa có đánh giá cứu giải đầy đủ, nội dung đề án hoặc ứng kỳ."],
         ["Đúng chiều Dụng sinh Thế, không diễn đạt rằng Thế hao lực sinh Dụng.",
          "Tổng hợp Dụng có trợ và Thế bị điều kiện động biến, không bỏ một phía.",
          "Không gọi văn bản đã tốt hoặc Nguyên thần đã cứu khi chưa có hiệu lực được xác nhận."],
         ["Thế sinh Dụng", "nội dung đề án chắc đã vững", "có Nguyên thần nên được cứu"]),
    ]:
        ctx = deepcopy(next(c["context"] for c in base.CASES if c["id"] == base_id))
        ctx.update(context_id=key, question=question, analysis_profile="HELDOUT_SYNTHETIC_SLICE")
        ctx["facts"] = [{"id": f"{key}:f{i+1}", "text": text} for i, text in enumerate(facts)]
        ctx["findings"] = [{"id": key + ":finding", "text": "Giữ nguyên các trạng thái và chiều quan hệ đã cung cấp; chưa chốt thành bại.",
                            "status": "CONDITIONAL", "fact_refs": [f["id"] for f in ctx["facts"]],
                            "evidence_refs": ctx["findings"][0]["evidence_refs"]}]
        ctx["limitations"] = [facts[-1]]
        evals.append({"id": key, "context": ctx, "required_review_checks": checks,
                      "forbidden_conclusions": forbidden, "model_evaluation_status": "NOT_RUN"})
    # Reuse the existing runtime examples as *regression* probes, not held-out
    # accuracy benchmarks. Their answers must be reviewed separately.
    for row in base.CASES:
        validate_response(row["response"], row["context"])
    for row in evals:
        Context.model_validate(row["context"])
    base.write(PACK / "sources.json", base.SOURCES)
    base.write(PACK / "cases.json", base.CASES)
    base.write(PACK / "evals.json", evals)
    paths = {ROOT / s["raw_path"] for s in base.SOURCES if s["raw_path"]}
    paths.update([PACK / name for name in ("sources.json", "cases.json", "evals.json")])
    paths.update(ROOT / p for p in (GUIDES_PATH, PROMPT_PATH, "schemas/plain_reading_context.schema.json", "schemas/plain_reading_response.schema.json"))
    paths.update((ROOT / "data/reference/interpretation").glob("*.source.json"))
    base.write(PACK / "manifest.json", {"version": VERSION, "system_prompt": PROMPT_PATH, "method_guides": GUIDES_PATH,
        "model_called": False, "review_status": "EDITORIAL_DRAFT_NOT_EXPERT_REVIEWED", "case_count": len(base.CASES),
        "source_count": len(base.SOURCES), "heldout_count": len(evals),
        "files": [{"path": str(p.relative_to(ROOT)), "sha256": sha256(p.read_bytes()).hexdigest()} for p in sorted(paths)]})
    print(json.dumps({"version": VERSION, "cases": len(base.CASES), "sources": len(base.SOURCES), "model_called": False}))


if __name__ == "__main__":
    build()
