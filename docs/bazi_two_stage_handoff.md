# Bát Tự: phân tích và diễn giải hai tầng — 28/10/2026

Cập nhật 29/10/2026: chủ đề Tổng quan dùng phân tích toàn mệnh với ba lĩnh vực
đời sống và ba chặng Đại vận, thay cho khung ba khuynh hướng. Các bài chuyên đề
giữ khung tập trung. Xem [hợp đồng và kiểm tra toàn mệnh](bazi_whole_life_handoff.md).

Mục tiêu: tìm điểm riêng từ lá số nhưng người đọc thấy những khuynh hướng dễ hình dung trong công việc, học tập, quyết định và các lĩnh vực thực sự được phân tích. Không đưa bản chuyên môn thành bài đọc cho người dùng.

## Hai vai trò tuần tự

Hai prompt người dùng cung cấp được lưu nguyên văn ở [Structural Analyst](prompts/bazi_structural_analyst_v1.system.txt) và [Life Interpreter](prompts/bazi_life_interpreter_v1.system.txt). Runtime nối thêm hợp đồng JSON, quy tắc dẫn chiếu và giới hạn hiển thị; không sửa nội dung gốc.

Theo yêu cầu mới nhất, cấu hình local và hai file môi trường mẫu dùng `claude-sonnet-4-6` qua endpoint hiện có; đã xác nhận đúng ID trong `/models`. Hai tầng cùng dùng model này, timeout 180 giây cho mỗi lượt HTTP. Giữ endpoint và thông tin xác thực; bỏ biến `RANDOMYST_AI_REASONING_EFFORT=low` đã thử cho GPT để không gửi tham số reasoning của GPT sang Claude. Tùy chọn reasoning trong transport vẫn là opt-in và có trong cache key.

Giai đoạn thử trước: DeepSeek bị cắt đầu ra; GPT-5.6 Terra gọi JSON ngắn thành công và hoàn tất Analyst ở cấu hình mặc định, nhưng Interpreter timeout. Không dùng những lần này để kết luận chất lượng bài đọc cuối, không xuất bài một phần.

## Giao diện tinh gọn

Form bỏ Tên gọi và không gửi `display_name`; backend tiếp tục nhận được giá trị mặc định rỗng. Kết quả bỏ ba khối “Đọc thêm trên cùng lá số”, “Các bài luận trong phiên này”, “Phạm vi và phương pháp luận”, cùng luồng tải danh sách/luận lại trong frontend. API và snapshot nghiệp vụ giữ nguyên.

Theo lượt tinh gọn tiếp theo, bỏ cả “Đọc giải thích và căn cứ của từng phần”, các đoạn luận chuyên môn và disclosure căn cứ bên trong. Frontend không còn dựng các khối này cho cả snapshot hiện tại lẫn snapshot cũ; căn cứ vẫn được dùng riêng trong pipeline phân tích. Bảng lá số và dialog thuật ngữ tiếp tục truy cập độc lập.

“Xem lá số” chỉ mở bảng lá số. Nút “Thuật ngữ” đặt cạnh nó mở native dialog có 7 định nghĩa, nhãn và mô tả hỗ trợ đọc màn hình, nút Đóng tối thiểu 44px, Escape, click nền để đóng và trả focus về nút mở. Header của dialog giữ nút Đóng trong tầm nhìn khi cuộn trên màn hình nhỏ. Bài luận không bị ngắt bởi bảng giải nghĩa; cảnh báo/giới hạn thuộc nội dung bài luận vẫn giữ trong schema và câu chữ.

Luồng hiển thị mới: người dùng bấm **Xem luận giải** một lần; sau khi lập lá số, frontend tự tìm bài đã có hoặc chạy hai tầng và hiển thị thẳng bài dành cho người đọc. Bỏ hoàn toàn phần tóm tắt native “Bạn nên hiểu kết quả này thế nào?”, “Bạn có thể làm gì?” và cảnh báo mẫu; không còn nút sinh bài lần hai. Trong lúc chờ chỉ hiện trạng thái đang viết; khi lỗi hiện thông báo và nút thử lại bài luận. Những snapshot cũ cũng không dựng lại đoạn mẫu. Nội dung Analyst không được đưa lên thay thế bài cuối nếu sinh bài thất bại.

1. `prepare_analyst()` nhận context từ snapshot lá số đã xác minh: Tứ Trụ, nhận định/quy tắc và nguồn hiện có, chủ đề/câu hỏi. Tên, thời điểm sinh và nơi sinh không được thêm vào payload. Chưa có Đại vận, gửi rõ `NOT_AVAILABLE`; không dựng chu kỳ hay thời điểm sự kiện.
2. Analyst chọn 3 quy luật cốt lõi phù hợp chủ đề, mỗi quy luật có ít nhất hai dữ kiện khác nhau, căn cứ quy tắc, cơ chế, một biểu hiện giả thuyết và tình huống, mặt thuận/bất lợi, điều kiện, giới hạn, dấu trái chiều và cách hiểu thay thế. Nếu căn cứ mỏng, cho ít quy luật hơn với `LIMITED`/`INSUFFICIENT`. Bảng chuẩn còn bao gồm cùng/khác Âm Dương và nhắc nguyệt lệnh là chi tháng. Mức HIGH/MEDIUM/LOW là độ nhất quán trong cách luận, không phải xác suất đúng.
3. Máy chủ kiểm schema, phiên/chủ đề/câu hỏi, phần giới hạn nguồn gốc bất biến, ID dữ kiện/nguồn và liên kết giữa các quy luật. Analyst được nối thêm cảnh báo ở cuối nhưng không sửa/xóa/đổi thứ tự giới hạn gốc. Analyst sai thì sửa một lần từ cùng dữ liệu; vẫn sai thì dừng, không gọi Interpreter. Danh mục fact/evidence ID được cấp rõ để không nhầm mã finding như `group:OUTPUT` thành mã fact.
4. Interpreter chỉ nhận **toàn bộ JSON Analyst đã kiểm tra** và hash của nó. Không nhận lại context/lá số thô hay truy xuất nguồn độc lập. Tầng này chọn nội dung và diễn đạt; không được tự luận thêm.
5. Bài dành cho người đọc ưu tiên 500–700 từ theo yêu cầu mới nhất về sự ngắn gọn: bức tranh chung 60–80 từ, tối đa 3 khuynh hướng có tình huống đời thường, điểm tưởng như trái nhau khi cần và một điều đáng thử. Runtime tạo `output_outline` từ bản Analyst hợp lệ, gồm các ID và dẫn chiếu cố định; Interpreter chỉ điền lời văn/tiêu đề. Phần liên hệ đời sống không dựng thêm nếu chỉ lặp ý. Máy chủ vẫn chặn trên 1.000 từ hoặc phần chung trên 150 từ, đếm bằng khoảng trắng; không ép kéo dài cho đủ.

Mỗi đoạn có dẫn chiếu ẩn về quy luật/biểu hiện/điều kiện/giới hạn. Một khuynh hướng phải dẫn một quy luật có biểu hiện và đủ điều kiện/giới hạn của nó. Liên hệ lĩnh vực chỉ được dẫn biểu hiện đã có; mâu thuẫn phải có quan hệ tương ứng từ tầng 1. Những quan hệ căng kéo/tiết chế giữa các quy luật được chọn phải được giữ lại. Không hiển thị ID, JSON hay bản phân tích chuyên môn trong bài. Chặn một nhóm từ chuyên môn phổ biến nếu toàn bài dùng quá hai tên khác nhau.

## API, ngân sách và cache

- Request `/api/v1/ai/readings` và `/lookup` giữ nguyên. Hai vai trò dùng cùng provider/model backend đang cấu hình, thực hiện tuần tự. Bình thường hai lượt, tối đa bốn nếu mỗi tầng cần sửa một lần; mọi lần gọi HTTP thực tế đều tính vào ngân sách hiện có. Sửa Interpreter dùng nguyên bản Analyst hợp lệ, không gọi lại Analyst. Analyst có ngân sách đầu ra 24.000 token, Interpreter giữ 12.000; các phương pháp khác giữ 12.000. Đây là trần đầu ra provider, tách với giới hạn 1.000 từ của bài đọc. Bản tổng hợp Analyst nhắm 900–1.200 từ, ưu tiên cơ chế/căn cứ hơn liệt kê dài.
- Response ngoài vẫn `ai-reading-v1`; `reading.schema_version` mới là `bazi-life-reading-v1`. Trường `pipeline` ghi phiên bản, hash phân tích, số lượt và model của từng tầng. `usage` cộng toàn bộ lượt sinh. Các bài `plain-reading-response-v2` cũ và các phương pháp khác giữ được khả năng đọc.
- Bản phân tích kỹ thuật ở envelope cache **riêng trong RAM** cùng kết quả cuối, TTL 900 giây, tối đa 32 mục. Mỗi lần lookup kiểm lại cả hai tầng rồi chỉ trả kết quả công khai. API không trả trung gian. Cache key gồm context, provider/model, cả hai prompt, schema và mã pipeline; đổi một trong hai prompt làm mất hiệu lực cache. Hai prompt được chụp một lần trước khi chạy để không trộn phiên bản giữa hai tầng.
- Chỉ cache bài hoàn chỉnh hợp lệ. Lỗi provider/định dạng trả lỗi kiểm soát; không xuất bài một phần, không lưu văn bản bị loại. Khóa pending/chống gọi trùng và giới hạn đồng thời tiếp tục dùng dịch vụ chung.
- UI cho luồng Bát Tự tối đa 1.500 giây để nhận kết quả; bài được tách thành đoạn và tiêu đề, giới hạn và thông tin bài luận mở thêm. Bài cuối tự chạy sau khi người dùng gửi form; không hiển thị bản tóm tắt native. Kiểm phiên và hash trước khi render hoặc gọi `onLoad`; chuỗi không an toàn bị loại trước khi vẽ bất kỳ phần bài nào.

Các schema ở `schemas/bazi_structural_analysis.schema.json`, `schemas/bazi_life_reading.schema.json`, `schemas/ai_reading_response.schema.json`. Mã chính: `randomyst/bazi_pipeline.py`, `randomyst/ai_service.py`, `web/ai_reading.js`.

## Giới hạn của kiểm tra

Nguồn chuyên môn đầu vào là quy tắc/nhận định natal từ engine và các trích đoạn được khóa trong `data/interpretation/plain_v4/sources.json`: Địch Thiên Tủy, Địch Thiên Tủy Xiển Vi, Tử Bình Chân Thuyên, Tam Mệnh Thông Hội. Runtime gắn các đoạn này vào context, không đọc toàn bộ sách hoặc truy xuất một kho mệnh lệ theo từng lá số. Phần tổng hợp vẫn dùng tri thức đã học của model; prompt và dẫn chiếu không biến nó thành một chuyên gia đã được thẩm định. Kho few-shot cũ cũng không phải mệnh lệ được xác nhận bằng thực tế.

Kiểm schema/dẫn chiếu xác nhận tính toàn vẹn dữ liệu và phạm vi ID, **không chứng minh từng câu diễn đạt được suy ra đúng từ căn cứ**. Việc giữ điều kiện trong lời văn còn phụ thuộc model; máy kiểm được dẫn chiếu nhưng không chứng minh được nghĩa của câu. Bản luận là giả thuyết theo hệ thống truyền thống, không phải đánh giá tính cách hoặc dự đoán khoa học. Chưa có chuyên gia hiệu đính hoặc thử nghiệm mức hiểu với người dùng.

Không tính lại lịch, không thay quy tắc natal, không thêm Đại vận/Lưu niên. Mai Hoa/Lục Hào/Tra ngày giữ luồng ngắn hiện có. Bộ few-shot Bát Tự v4.3 vẫn là tài liệu cũ; pipeline mới dùng hai prompt trên, không đưa mẫu một tầng vào Analyst/Interpreter.

## Kiểm chứng

`tests/test_bazi_pipeline.py` kiểm cách ly vai trò, ràng buộc đa dữ kiện/nguồn, lĩnh vực và mâu thuẫn, giữ điều kiện/giới hạn, thiếu dữ liệu, giới hạn bài dài, đồng bộ schema, đổi prompt làm đổi cache, luồng hai lượt, lỗi tầng 1 dừng trước tầng 2, tầng 2 sửa từ cùng trung gian và không xuất bài một phần. Fixture là dữ liệu hợp đồng giả lập, không phải ví dụ luận lá số đã được thẩm định.

`tests/test_ai_reading.cjs` kiểm bài mới hiển thị đủ đoạn/tiêu đề, không lộ ID/trung gian, từ chối hash/phiên/phương pháp sai và chuỗi máy trước khi vẽ, đồng thời giữ khả năng đọc bài cũ. Các suite AI/bảo vệ public/Tra ngày tiếp tục kiểm cache, snapshot và ngân sách lượt gọi.


Lần kiểm tra cuối: **242 Python + 51 JavaScript đạt**, CSS build và `git diff --check` đạt. UI thật ở 1280px và 375px xác nhận không có ô Tên gọi, các khối đã bỏ hoặc phần “Đọc giải thích và căn cứ của từng phần”, không tràn ngang; dialog mở/đóng/Escape/trả focus và cuộn mobile đạt. Ảnh: `research/bazi_final_quality_ui.png`, `research/bazi_glossary_mobile.png`.

Đã đọc output thật từ `claude-sonnet-4-6`; các mẫu được duyệt thủ công **chưa đạt chất lượng**. Có lỗi quy tắc nền trong Analyst; Interpreter có bài 1.610 từ, lặp ý, thuật ngữ trừu tượng và dẫn chiếu sai. Đã bổ sung bảng sinh–khắc/cặp can hợp từ engine, ngân sách từ theo trường/phần và thu thập đồng thời lỗi độc lập cho lượt sửa. Những thay đổi này không phải chứng minh nội dung chuyên môn đúng. [Đánh giá output thật](research/bazi_output_quality_review.md), [báo cáo kỹ thuật](research/bazi_two_stage_validation.json). Các mẫu lỗi không được xuất như bài đạt chất lượng.
