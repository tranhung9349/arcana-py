# Kiểm tra bài Bát Tự — 28/10/2026

Kết luận ở các mẫu đã đọc: **chưa đạt để dùng làm bài luận cho người đọc**. Dữ liệu sinh và câu hỏi trong phép thử là giả lập. Không dùng fixture của unit test để kết luận về chất lượng model.

## Vấn đề đã quan sát trực tiếp

- Bản phân tích thật của `claude-sonnet-4-6` mất 259 giây, gồm 5 quy luật và khoảng 5.404 từ tính toàn bộ giá trị chuỗi. Có lỗi nền: ghi “Kim khắc Hỏa”; gọi Kim là hành sinh xuất của Hỏa; có đoạn vừa nêu khả năng Đinh–Quý hợp vừa phủ nhận ở phần giới hạn. Bảng engine xác định Hỏa khắc Kim, Hỏa sinh Thổ, Kim khắc Mộc, và Đinh–Nhâm mới là cặp hợp. Vì vậy không thể duyệt nội dung chỉ dựa vào fact/source ID hợp lệ.
- Mẫu kiểm riêng Interpreter Claude từ Analyst GPT thật của lượt thử trước dài **1.610 từ**, lặp chủ đề chuẩn bị–hành động, có từ trừu tượng như “căng kéo cấu trúc”, và gán một lĩnh vực không được các biểu hiện dẫn chiếu hỗ trợ. Đây là kiểm riêng tầng viết, không phải bằng chứng luồng Claude ở cả hai tầng đã hoàn tất.
- Mẫu Interpreter Claude từ bản Analyst Claude nói trên vẫn dài **1.451 từ** ở lượt đầu; chọn cả 5 quy luật, có dẫn chiếu sai và thiếu quan hệ cần giữ. Lượt sửa tiếp vẫn không qua kiểm tra độ dài, thuật ngữ và quan hệ. Các văn bản này không được xuất thành bài cuối cho người dùng.
- Luồng có timeout 180 giây không hoàn tất bản phân tích ở lần đầu. Lượt kiểm riêng với timeout 480 giây nhận được Analyst sau hơn 4 phút; lần sinh lại mất thêm 264 giây và sai độ dài một trường. Đây là thời gian QA, không phải thay đổi timeout production.
- Ở lượt kiểm lại sau khi cấp bảng quy tắc, Analyst hoàn tất sau 172 giây nhưng nhầm mã finding `group:OUTPUT`/`group:WEALTH` thành fact ID. Lượt sửa 159 giây qua kiểm tra cấu trúc. Bản này dùng đúng chiều sinh–khắc đã cấp nhưng vẫn ghi sai quan hệ Âm Dương của Thất Sát/Thiên Tài và có câu tự đính chính trong conditions. Đây tiếp tục là lỗi nội dung do kiểm tra thủ công phát hiện. Interpreter từ bản đó trả sau 75 giây, dài **1.396 từ**, để lộ P02/P03 trong lời văn, còn thuật ngữ và thiếu một quan hệ cần giữ; bị chặn trước khi xuất bài.

## Điều chỉnh sau khi đọc output thật

1. Bỏ khối “Đọc giải thích và căn cứ của từng phần” cùng nội dung con trong UI, kể cả khi dựng snapshot cũ.
2. Cung cấp cho Analyst bảng sinh–khắc, phân biệt sinh xuất/Tài, các cặp thiên can hợp và thứ tự trụ từ engine; yêu cầu kiểm lại cơ chế và sửa mâu thuẫn trước khi xuất.
3. Yêu cầu ưu tiên 3 quy luật có cơ chế riêng, ngân sách ngắn cho từng trường; chia ngân sách từ cho từng phần của bài cuối, bỏ phần chỉ nhắc lại, không tự suy chiều ngược từ một điều kiện thuận lợi.
4. Thu thập đồng thời các lỗi độc lập của bài đọc để lượt sửa duy nhất nhận đủ lỗi dẫn chiếu, lĩnh vực, độ dài và thuật ngữ.
5. Giữ nguyên toàn bộ giới hạn nguồn gốc và thứ tự của chúng; cho phép Analyst nối thêm cảnh báo thận trọng. Việc thêm hai cảnh báo đúng về thiếu Đại vận/MIXED không còn buộc sinh lại toàn bộ phân tích. Không cho sửa hoặc xóa giới hạn gốc.
6. Cấp danh mục fact/source ID rõ ràng và nhắc mã finding không phải mã fact; lượt sửa Analyst nhận lại danh mục ID được phép dẫn.

Các bảng đầu vào và kiểm tra tự động không chứng minh lời luận chuyên môn đúng. Lỗi ngũ hành nêu trên được phát hiện bằng đọc và đối chiếu thủ công, không phải bởi bộ kiểm ID. Cần tiếp tục đánh giá trên output thật; chưa có tập mệnh lệ được chuyên gia thẩm định hoặc thử nghiệm mức hiểu của người dùng.

## Kiểm tra kỹ thuật

242 kiểm tra Python và 51 kiểm tra JavaScript đạt. CSS build và `git diff --check` đạt. UI thật ở 375px và 1280px không có khối căn cứ đã bỏ và không tràn ngang. Ảnh xác nhận UI: `bazi_final_quality_ui.png`.

Lượt kiểm chứng dùng timeout production kết thúc sau **473 giây**, gồm hai lượt Analyst và hai lượt Interpreter, với lỗi `AI_RESPONSE_UNBOUND`. Bản viết lần cuối còn **1.291 từ**, có hai liên hệ lĩnh vực không được các biểu hiện dẫn chiếu hỗ trợ và vẫn thiếu một quan hệ cần giữ. Lời văn còn thêm “giải pháp sáng tạo hơn” dù bản Analyst tương ứng không có nội dung này. Kết luận sau lượt sửa vẫn là **chưa đạt**; không có bài hoàn chỉnh hợp lệ được cache hoặc xuất cho người dùng từ phép thử này.
