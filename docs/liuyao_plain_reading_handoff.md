# Luận Lục Hào bằng lời thường ngày — 30/10/2026

## Kiểm tra lỗi hiển thị và streaming

Sau đó đã tái hiện lỗi ngay trên UI với quẻ thử: cả hai lượt bị `READING_TOO_LONG`, cuối cùng `AI_RESPONSE_UNBOUND` dù upstream dùng `stream=True`. Một quẻ thử khác gặp lỗi dẫn chiếu ở lượt đầu, thuật ngữ ở lượt sau: kiểm từng bước làm lượt sửa không thấy hết các vấn đề. Đã sửa: `validate_liuyao_candidate` gom lỗi dẫn chiếu/lời văn/từ vựng/độ dài cùng lúc; cấp danh mục ID rõ trong prompt; đưa bản nháp có cấu trúc hợp lệ và đúng context_id vào `editorial_draft` trong user data để biên tập cùng tất cả gợi ý kiểm tra. Bản bị từ chối không được xem là facts/evidence. Bỏ few-shot trong lượt biên tập, yêu cầu rút còn 150–190 từ, giữ điều kiện và sửa dẫn chiếu theo catalog; kiểm lại toàn bộ, vẫn tối đa hai lượt và không cắt câu tự động. Log độ dài chỉ có tên trường và số đếm, không có nội dung.

UI mới theo yêu cầu tiếp theo: chỉ chọn chủ đề/nhập câu hỏi, **Gieo và lập quẻ** tự gieo bằng giờ hiện tại. Kết quả mở sẵn sáu lượt tiền và quẻ chủ/biến trước AI. Hai mục “Xem căn cứ của lời giải” và “Thông tin bài luận” đã gỡ khỏi bài Lục Hào; metadata bài cũng gỡ ở các bài AI khác. Dữ kiện nguồn trong request không bị cắt. Chi tiết kỹ thuật chung nằm trong một mục tham khảo đóng mặc định.

Đo riêng ca quẻ thử #54 → #32: lượt đầu 261 từ (summary 52, đoạn đầu 81), lượt sửa 222 từ (đoạn đầu 76). Cả hai bị trần từng phần 50/70 chặn dù tổng đã dưới 300. Giữ mục tiêu prompt ngắn, nhưng validator Lục Hào cho khoảng dư 1,5 lần ở từng phần, vẫn giữ cứng tổng 300 từ và đúng hai đoạn. Phương pháp khác giữ ngân sách cũ. Không cắt nội dung tự động hoặc bỏ kiểm dẫn chiếu/từ vựng.

Kiểm cuối: toàn bộ 294 Python đạt trước lần thêm khoảng dư; sau thay đổi cuối 30 kiểm thử lời văn/streaming đạt, có ca bảo đảm khoảng dư vẫn chặn tổng trên 300. 76 JavaScript đạt; build CSS và manifest/hash đạt. Browser xác nhận form chỉ có `coins-topic`/`coins-question`, đủ 6 lượt/18 mặt tiền đứng trước hai quẻ và AI, không còn details trong bài AI. 1440px và 375px không tràn ngang, khôi phục viewport mặc định.

Bài live cuối qua đúng UI gieo tự động: tổng tiền `7,7,8,7,9,8`, Thuần Đoài #58 → Quy Muội #54, hào động 5; bài AI hiển thị thành công, khoảng 236 từ nếu tính cả tiêu đề UI. Đây là quẻ thử của agent, không phải kết luận về công việc thực tế. Ảnh `liuyao-simple-flow-desktop.jpg` trong artifact; ba tab thử trước đã xuất kết quả DOM thành JSON quyền 0600 rồi dọn, giữ tab người dùng và tab bản hoàn thiện. Backend local đang chạy bản cuối. Restart local dùng khóa phát triển mới nên snapshot của trang cũ có thể không xác thực được; tránh thử lại các tab cũ sau restart.

Người dùng báo UI hiện “Bài luận chưa thể hiển thị. Bạn có thể thử lại phần luận.” Ở bản cũ, câu này dùng chung cho `AI_RESPONSE_INVALID` và `AI_RESPONSE_UNBOUND`, nên ảnh không đủ phân biệt lỗi JSON/transport với lỗi schema/dẫn chiếu/lời văn. Không kết luận nguyên nhân lần lỗi ấy là timeout hoặc đã sửa được chính xác lần lỗi đó khi chưa có mã tương ứng.

- Xác minh đường web: `ArcanaClient.streamReading` gọi `/stream` để tra cứu, `/start` để sinh; `subscribe` truyền `stream=True` tới worker và provider. Bài live v4.5 trước đó dùng `/api/v1/ai/readings` đồng bộ nên gửi `stream:false`; nó không phải bằng chứng cho luồng streaming.
- Đã chạy riêng đúng `/start` với câu hỏi/quẻ thử được đồng ý: request `stream:true`, provider trả `Content-Type: text/event-stream`, kết thúc `event: result` sau khoảng 20 giây. Proof không có header/khóa: artifact `liuyao-streaming-check.json` trong thư mục chat.
- Endpoint đồng bộ nay cũng dùng upstream `stream=True`, vẫn trả một JSON sau kiểm tra cho client cũ. Lỗi vẫn trả đúng HTTP/code; không bị đổi thành `null` khi worker giữ lỗi. Thêm kiểm thử Lục Hào cho cả hai endpoint và lượt sửa duy nhất.
- Log chỉ ghi phương pháp, mã lỗi, stream flag, loại lỗi kiểm tra hoặc tên lớp lỗi parse; không ghi câu hỏi, request, khóa, lời văn model hoặc dữ kiện cá nhân. UI phân biệt lỗi kết nối, sai định dạng và chưa đạt kiểm tra nội dung/căn cứ; thêm `data-error-code` để tự kiểm trên DOM. Lượt lỗi xóa bài cũ khỏi vùng lời luận để tránh nhầm bản đã hiển thị với kết quả mới.
- Toàn bộ bảng quẻ, kinh văn, phân tích quy tắc và tùy chọn chuyên môn chuyển vào một mục “Chi tiết quẻ và nguồn tham khảo”, đóng mặc định; dữ kiện gửi LLM giữ đầy đủ. Lỗi AI không mở phần kỹ thuật làm bài thay thế. Lỗi chọn phạm vi/phân tích có thể mở tùy chọn tương ứng để sửa. Thư viện 64 quẻ giữ luồng riêng.

## Bổ sung quẻ và nguồn vào request — v4.5

Người dùng yêu cầu LLM nhận đúng quẻ đã gieo và tài liệu nguồn. Adapter cũ đã gửi lựa chọn Dụng, một số trạng thái hào, findings và vài trích đoạn phương pháp chung, nhưng chưa gửi quẻ chủ/biến, sáu lượt gieo, lịch, toàn bàn Nạp Giáp hoặc kinh văn khớp quẻ.

- `randomyst/ai_context.py` nay giữ đủ `casting:throws`, `chart:original`, `chart:changed` (null khi tĩnh), `chart:moving_lines`, `chart:najia`, `calendar:casting`, toàn bộ sáu hào và Phục nếu có. Không gọi RNG/lịch/phân tích lại. Snapshot quẻ và phân tích vẫn phải khớp hash/chữ ký. `reading:provenance` ghi phiên bản/hash và những hào có vai trò đã được xét; dữ liệu nền không cấp quyền tự thêm kết luận.
- `randomyst/liuyao_sources.py` truy xuất cục bộ đúng hai quẻ tối đa từ open-iching commit `4c5f00f8cb62c6e0d2471243d28150b473ef592f`: quẻ từ, Thoán/Tượng, sáu hào; thêm Tiểu Tượng hào động nếu có và Dụng Cửu/Dụng Lục khi Càn/Khôn cả sáu hào động. Card đã lưu phải khớp văn bản/vị trí/commit. Kiểm hash cả ba file; không tìm nguồn trên web lúc luận.
- Trích Tăng San theo nhóm Dụng thực tế từ chương 8; chọn trích phương pháp hiện có theo nguồn quy tắc đã dùng (Nguyên/Kỵ, hiệu lực, Nguyệt, Nhật). Kiểm raw, revision, URL và hash. Không gửi nghĩa Việt/overview AI chưa hiệu đính như nguyên tác. Các bản chép khóa revision vẫn chưa phải ấn bản khảo đính.
- `sources:documents` gắn nguyên văn với quẻ chủ/biến, vị trí và nguồn; `sources:rule_bindings` nối từng finding với tài liệu. Chương chỉ có thư mục/link được đánh dấu `BIBLIOGRAPHY_ONLY`, không mạo nhận đã truy xuất. `engine:*` vẫn là `PRODUCT_POLICY`; findings nối cả nhận định engine và đoạn phương pháp có sẵn.
- System prompt riêng `docs/prompts/liuyao_interpreter_v1.system.txt` chỉ áp dụng `LIUYAO_NAJIA`, thay prompt hệ thống chung cho phương pháp này; hướng dẫn phương pháp, trọng tâm và quy tắc lời văn ngắn tiếp tục được ghép. Prompt mô tả từng khối dữ liệu, thứ tự nguồn và cách đối chiếu quẻ chủ/động/biến với câu hỏi; không lấy nghĩa quẻ để đảo Nạp Giáp hoặc đổi “ba năm/bảy ngày” trong kinh văn thành thời hạn công việc.
- Pack `plain-vietnamese-2026-10-30-v4.5` ghim prompt riêng, adapter, module truy xuất và corpus quẻ. Cache backend thay khóa theo context/messages/manifest. Bài cũ trong RAM browser vẫn là bài đã sinh trước đó; bài tạo mới dùng đầu vào mới. Không thay model/provider/credential hoặc giao thức streaming.

Kiểm chứng: 290 Python và 72 JavaScript đạt. Sáu kiểm thử grounding kiểm quẻ/lịch/bàn hào được giữ nguyên, nguồn theo đúng hai quẻ, quẻ tĩnh và cả sáu hào động Càn/Khôn, từ chối nguồn sai, bỏ bản nháp AI, ghim prompt và kiểm JSON HTTP thực sự gửi tới client tương thích.

Thử thật qua rexapf.com với đúng câu hỏi đã được đồng ý, quẻ thử tổng tiền `7,8,9,8,7,6`, thời điểm `30/10/2026 09:00 +07:00`: Ký Tế #63 → Ích #42, hào động 3/6; 32 facts, 35 evidence. Claude Sonnet 4.6 trả bài hợp lệ ở lượt sinh đầu, một request ra provider, khoảng 19 giây; usage provider báo 24.259 prompt + 987 completion = 25.246 tokens. Một lần trước đó trong sandbox không phân giải được DNS, chưa kết nối provider; đã kiểm lỗi DNS rồi chạy bằng quyền mạng được duyệt.

Payload thực tế không kèm header/khóa và bài mẫu lưu trong thư mục artifact của chat: `liuyao-grounded-request-example.json`, `liuyao-grounded-reading-example.md` (quyền 0600). Đây là quẻ thử, không thay quẻ riêng của người dùng. Bài vẫn giữ giới hạn chọn Dụng và chưa tính thời hạn công việc; bổ sung nguồn không tự bổ sung engine ứng kỳ. Kiểm schema/nguồn/từ vựng không chứng minh mọi suy luận của LLM đúng ngữ nghĩa.

## Bố cục và lời văn v4.4

Phản hồi: người hỏi về việc tiếp tục công việc trong một tháng cụ thể và thời gian còn lại, nhưng màn hình mở sẵn nhiều kinh văn/bảng chuyên môn, còn lời giải không giữ rõ hai ý cần trả lời.

## Thay đổi

- Sau khi lập quẻ mới, tự bắt đầu bài AI qua luồng streaming hiện có. Trước đây `drawReport` bỏ qua `autoGenerate` nên người dùng phải bấm thêm mới có lời giải.
- Bài AI xuất hiện ngay sau câu hỏi. Phần trả lời, hai đoạn giải thích ngắn, hành động và lưu ý hiển thị trực tiếp; căn cứ của từng nhận định đóng mặc định. Không lặp lại hai đoạn giải thích trong căn cứ.
- Quẻ chủ/biến, kinh văn, hào động, bảng Nạp Giáp và nguồn giữ đầy đủ trong mục “Xem quẻ, kinh văn và bảng Lục Hào”, đóng mặc định. Thư viện 64 quẻ giữ cách đọc đầy đủ.
- Điều khiển đổi chủ đề/chọn Dụng thần nằm sau bài luận, đóng mặc định, vẫn thao tác trên đúng quẻ cũ. Trường hợp chưa chọn được hào phải được lời luận nêu rõ, không tự chọn thêm.
- Prompt riêng `docs/prompts/liuyao_plain_language_v1.system.txt` yêu cầu trả lời đủ các ý và bám đúng công việc hiện tại. Ví dụ giả định và lời văn sáu ví dụ cũ cập nhật ở pack v4.4; không thay facts hoặc sources của ví dụ cũ.
- Context thêm nhận định giới hạn `scope:time` và fact `reading:time_scope`: ngày/tháng đang xét là thời điểm gieo; engine chưa tính riêng kỳ tương lai, thời hạn công việc hoặc ngày kết thúc. Không đổi điều kiện địa chi thành số tháng hay ngày nghỉ việc.
- Kiểm thuật ngữ khi sinh mới: toàn bộ lời văn không dùng danh sách nhãn chuyên môn hoặc số/mã hào. Vi phạm dùng lượt sửa duy nhất hiện có, lần hai vẫn sai thì không hiển thị/cache. Không áp quy tắc mới để cắt bài cũ. Không yêu cầu người đọc tự chọn dấu hiệu/hào trong quẻ khi câu hỏi đã rõ đối tượng.

## Kiểm tra

- `npm test`: 72 kiểm thử đạt.
- `.venv/bin/python -m unittest discover -s tests -q`: 284 kiểm thử đạt.
- Build CSS và pack offline thành công; pack kiểm hash cả prompt và ví dụ mới.
- Câu hỏi công việc tháng 12/2026 được thử cục bộ với context CAREER: giữ nguyên câu hỏi và snapshot quẻ/phân tích, nêu rõ phạm vi thời gian, không tính quẻ mới khi giải thích.
- Sau khi người dùng cho phép gửi câu hỏi và quẻ thử tới rexapf.com, chạy hai bài qua UI với cùng sáu tổng tiền `7,8,9,8,7,6`, thời điểm thử `30/10/2026 09:00` giờ Việt Nam. Lần đầu còn số hào/cụm “khí thế vượng” và đề nghị người đọc tự chọn dấu hiệu; đã sửa prompt và kiểm từ vựng, chạy lại. Bài cuối trả lời đủ hai ý, không còn số hào/nhãn chuyên môn ở phần đọc chính, không hẹn ngày/số tháng còn làm và không yêu cầu tự chọn hào. Không dùng quẻ thử làm kết luận về việc thực tế của người dùng.
- Đối chiếu bài cuối với phần phân tích đã lưu: hai ứng viên công việc đều được ngày/tháng gieo nâng đỡ, lựa chọn vẫn AMBIGUOUS; không có phần tính riêng tháng 12/2026 hoặc thời hạn kết thúc. Bộ kiểm chỉ xác nhận phạm vi/định dạng, chưa phải chấm độ đúng dự đoán.
- Browser ở 1440px và 375px không tràn ngang; hai mục chuyên môn đóng mặc định và mở được đủ nội dung. Khôi phục viewport mặc định sau thử. Ảnh bài cuối nằm ở `liuyao-plain-career.png` trong thư mục artifact của cuộc trò chuyện.
- Sau lượt siết từ vựng cuối, chạy lại 47 kiểm thử prompt/service/lời văn và 13 kiểm thử streaming, đều đạt. Một lỗi console cũ ở `web/app.js:6` do thiếu `casting-mode` thuộc luồng Dãy số, không phát sinh từ bản sửa Lục Hào và chưa xử lý trong thay đổi này.

## Giới hạn

Không thêm engine ứng kỳ, mô hình thời hạn công việc hoặc dữ kiện nhân sự. Kiểm độ dài, từ vựng và dẫn chiếu không chứng minh ngữ nghĩa đúng hay khả năng dự đoán ngoài đời. Quẻ thử cố định chỉ dùng kiểm luồng; không thay quẻ người dùng đã gieo trước đó.
