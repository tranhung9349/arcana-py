# Nghiên cứu cách tổng hợp lời luận — 27/10/2026

Runtime dùng `plain-vietnamese-2026-10-27-v3.2`. Đây là nâng cấp cách diễn giải trên cùng dữ kiện Bát Tự, Mai Hoa và Lục Hào, không bổ sung phép tính vận hoặc thay các kết luận của lõi.

## Vấn đề thấy trong bài cũ

Đã đọc lại ba bài AI đã lưu của các phiên mẫu, thay vì chỉ kiểm tra văn bản prompt. Bát Tự tách từng nhóm Ấn, Thực Thương và Quan Sát thành các đoạn riêng rồi suy “khó tự thực hành” từ việc tàng can. Mai Hoa chuyển tỷ hòa thành “dễ chủ quan”; chưa phân biệt rõ sức Thể chưa xác định với sức người hỏi. Lục Hào có đoạn đảo Dụng sinh Thế thành Thế sinh Dụng và dùng hào văn thư có trợ để xác nhận nội dung bản thảo tốt.

Vấn đề gồm cả bố cục và bước suy luận: một dẫn chiếu đúng ID vẫn có thể được gắn vào câu không được dữ kiện ấy hỗ trợ. Kiểm schema không phát hiện được toàn bộ lỗi này.

## Nguồn đối chiếu và điều được áp dụng

Ưu tiên nguyên tác và chương cụ thể. “Uy tín” ở đây là nguồn văn bản cho phương pháp truyền thống; không coi cổ thư hay các lời nghiệm trong sách là kiểm chứng khoa học cho khả năng dự báo.

| Nguồn | Nội dung đối chiếu | Áp dụng vào prompt | Giới hạn |
|---|---|---|---|
| [Địch Thiên Tủy, Suy vượng](https://zh.wikisource.org/w/index.php?oldid=844360) và [bản tổng hợp, Nguyệt lệnh](https://zh.wikisource.org/wiki/滴天髓) | Mạnh/yếu cần xem phối hợp; trong vượng có thể có suy và ngược lại. Nguyệt lệnh là nền quan trọng. | Đặt mùa sinh cạnh căn và can trợ/khắc đã tính, giải thích dấu trái chiều trước khi chốt. Không đếm số hành hoặc dùng nhãn lộ/tàng làm kết luận hiệu lực. | Bản chép cộng đồng; chỉ áp dụng những đánh giá lõi đã cấp. |
| [Tử Bình Chân Thuyên, Dụng thần](https://donglishuzhai.net/chapter/3721.html), [Thành bại cứu ứng](https://m.donglishuzhai.net/chapter/3722.html), [Phối khí hậu](https://www.donglishuzhai.net/chapter/3727.html) | Dụng theo tháng cần phối bốn trụ; thành bại và cứu ứng là bước tiếp theo, không suy từ một tên nhóm. Khí hậu cần tham chiếu riêng. | Tách cách cục ứng viên, phù ức và Điều hậu. Nêu đúng phần chưa xét; không tự dựng Sát–Ấn, sinh Tài hoặc cứu ứng. | Đối chiếu được các đoạn trong chỉ mục web; truy cập toàn trang nhiều lần timeout. Chưa ghim ấn bản đầy đủ. |
| [Mai Hoa Dịch Số, quyển II](https://zh.wikisource.org/w/index.php?oldid=1441921), “Chiêm bốc luận lý quyết” và phần Thể Dụng | Cần đặt số/tượng trong lý và việc hỏi, tránh áp một hình ảnh cố định cho mọi tình huống. | Giữ nghĩa có điều kiện, phân biệt biểu tượng với tình trạng đời sống. Không suy “tỷ hòa = chủ quan”. | Không nhập ngoại ứng chưa được người hỏi cung cấp. |
| [Mai Hoa Dịch Số, quyển III](https://zh.wikisource.org/w/index.php?oldid=1441927), “Thể Dụng Hỗ Biến chi quyết” | Phân biệt chặng đầu, Hỗ phía Thể, Hỗ phía Dụng và chặng cuối. | Nối thành diễn tiến, giữ cảnh báo của từng chặng. Quy tắc dành cho Dụng ban đầu không tự chuyển sang Hỗ chỉ vì cùng quan hệ ngũ hành. | Chặng trong phép đọc không phải lịch sự kiện. Bản raw đã tải lại và khớp SHA-256 bản ghim hiện có. |
| [Tăng San Bốc Dịch, chương 10](https://zh.wikisource.org/w/index.php?oldid=2100301), “Nguyên thần Kỵ thần suy vượng” | Có Nguyên thần chưa đủ; phải xét sức và điều kiện để sinh được Dụng. | Phân biệt vai trò với hiệu lực. Không tự chốt được cứu khi chỉ thấy nhãn hoặc một hào tĩnh. | Mới ghim nguyên văn chương; chưa bổ sung phép giải cứu toàn cục vào lõi. |
| [Tăng San Bốc Dịch, Nhật thần](https://zh.wikisource.org/w/index.php?oldid=2100338) và Nguyệt tướng trong corpus hiện có | Cùng chữ xung nhưng điều kiện của hào khác nhau có thể có cách đọc khác. | Đọc Nhật–Nguyệt cạnh động/tĩnh, Không/Phá và biến hóa; giữ cả trợ lực và điều kiện cản của Dụng/Thế. | Chỉ dùng trạng thái đã tính, không tự thêm ám động hoặc ứng kỳ. |

Có tìm được bản scan Tử Bình của thư viện trên Wikimedia, nhưng công cụ từ chối tệp 68,8 MB. Không dùng nó như một ấn bản đã đọc hoặc đã kiểm chứng. Không lấy lời bình hiện đại, blog hoặc diễn đàn làm bằng chứng nguyên tác.

## Khung luận được biên soạn

Trình tự của bài: nhận định chính → nền cụ thể của phiên → các quan hệ thuận/nghịch hoặc diễn tiến → tổng hợp điều kiện → việc có thể kiểm tra. Đây là quy ước biên tập hiện đại rút ra từ cách đối chiếu nguồn, không phải một đoạn cổ thư được dịch nguyên văn.

- Bát Tự: bắt đầu Nhật chủ/tháng, đặt căn và can cạnh nhau, rồi chọn nhóm sát chủ đề. Chưa đủ phân định thì giải thích vì sao giữ mở, không biến phần còn thiếu thành một phán đoán tính cách.
- Mai Hoa: Thể giữ nguyên, nối Dụng–hai Hỗ–Biến, chỉ dùng vượng suy đã biết. Phân biệt cảnh báo ở chặng nào, không gom nhãn bằng đa số.
- Lục Hào: đúng Dụng và trạng thái lựa chọn → nền Nhật–Nguyệt → động biến/Không/Phá → điều kiện Thế và hiệu lực trợ lực được cung cấp. Hai ứng viên chưa khóa phải đọc riêng.

System prompt và hướng dẫn theo phương pháp được tách riêng, chỉ hướng dẫn tương ứng được đưa vào phiên. 18 cặp mẫu được soạn mới thành các đoạn nối nhau; thêm mẫu văn thư có Dụng được trợ nhưng Thế bị điều kiện hạn chế. Giữ schema `plain-reading-response-v2` để giao diện và dữ liệu lịch sử tương thích.

Đã thêm các trích đoạn vào context dưới nhãn nguồn thật, để model có thể dẫn ID của phiên. Nguồn không tự tạo một finding mới. Lớp adapter Lục Hào lấy mã quan hệ `USE_WORLD` đã lưu, viết rõ nguồn → đích và thêm vị trí Thế/Ứng; không chạy lại phép tính hoặc ghi đè snapshot.

## Kiểm tra và giới hạn đánh giá

Lượt thử v3 đầu có mạch rõ hơn nhưng vẫn tự thêm “Ấn xa”, áp quy tắc mưu sự của Dụng ban đầu vào Hỗ và suy tình trạng đời sống. Báo cáo kết nối được giữ tại `ai_readings_v3_draft_http_smoke.json`; không xem kết nối thành công là đạt chất lượng. Bản v3.1 bỏ được các bước suy đó trong ca Bát Tự/Mai Hoa nhưng ca Lục Hào vẫn nhầm vai một hào phụ và xác nhận quá mức về nội dung văn bản; báo cáo giữ ở `ai_readings_v3_1_http_smoke.json`.

Bản v3.2 bổ sung ràng buộc findings, ví dụ lỗi, giới hạn chuyển quy tắc giữa các chặng và giữ ngữ cảnh Lục Hào tập trung vào hào được các findings thực sự đề cập, Dụng/ứng viên và Thế–Ứng. Một lượt phản hồi bị nhà cung cấp cắt ở giới hạn 6.000 token đã bị chặn (`AI_RESPONSE_INCOMPLETE`), không lưu prose; giới hạn phản hồi được tăng lên 8.000 token rồi mới kiểm tra lại. Không tự thử lại timeout hoặc chấp nhận JSON dở dang.

Lượt đối chiếu cuối dùng lại ba phiên tổng hợp đã có, cùng model/endpoint. [Báo cáo HTTP](ai_readings_v3_http_smoke.json) kiểm kết nối, cache và snapshot không đổi. [So sánh lời luận](ai_readings_v3_comparison.json) lưu bài cũ/mới và nhận xét biên tập. Đây là ca hồi quy đã được dùng trong phát triển, không phải đánh giá mù hoặc benchmark độc lập.

Lượt cuối cả ba module qua schema/dẫn chiếu ở lần sinh đầu, dùng lại cache giống hệt và không đổi snapshot nghiệp vụ. Khi đọc lại, các lỗi cụ thể về lộ/tàng, tỷ hòa, áp quy tắc sang Hỗ, chiều Dụng–Thế và gán nhầm hào phụ không còn trong ba bài này. Mạch tổng hợp rõ hơn nhưng văn phong chưa đồng đều: vẫn lọt từ `finding`/`MIXED`, một số đoạn kể quan hệ thừa và các liên hệ đời sống cần tiếp tục hiệu đính. Không xem đây là chứng minh đã loại hết suy diễn. [Ảnh trên giao diện](ai_synthesis_v3_ui.png).

Bộ giữ riêng có 11 ca, trong đó ba ca mới kiểm tổng hợp Bát Tự, tỷ hòa/vượng suy Mai Hoa và chiều Dụng–Thế. Các ca này chỉ được kiểm contract; `model_evaluation_status=NOT_RUN`, chưa tính là 11 câu trả lời AI đã được chấm. Không đưa chúng vào few-shot.

Kiểm tự động xác nhận: nguồn và prompt bị sửa phải đổi hash hoặc bị chặn; không trộn hướng dẫn các phương pháp; câu hỏi không trở thành chỉ dẫn system; dữ kiện không tính lại; cache đổi khi chính nội dung messages đổi. Chất lượng mệnh lý và mọi câu liên hệ đời sống vẫn cần chuyên gia hiệu đính; không công bố điểm chính xác hoặc cam kết loại hết suy diễn.
