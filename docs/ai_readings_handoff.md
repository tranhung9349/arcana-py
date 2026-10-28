# Luận giải AI dùng chung — 26/10/2026

Cập nhật 27/10/2026: runtime dùng `plain-vietnamese-2026-10-27-v4.1`, 24 cặp mẫu, 29 trích đoạn/quy ước và bộ chọn trọng tâm theo trạng thái, chủ đề, mục đích câu hỏi. [Nghiên cứu mới và giới hạn đánh giá](research/masters_reading_dynamic_v4.md), [prompt](prompts/plain_vietnamese_v4.md). Kiểm thử hiện tại: 193 Python và 10 JavaScript đạt. Các số liệu cuối tài liệu về lần chạy 26/10 được giữ như lịch sử kiểm chứng.

Kiểm tra thật và hiệu đính v4: [báo cáo](research/ai_readings_v4_http_smoke.json), [nhận xét biên tập và điểm còn yếu](research/ai_readings_v4_editorial_review.json). Adapter Lục Hào chỉ đưa các hào liên quan tới bài phân tích vào context, viết rõ chiều quan hệ đã lưu và thêm tín hiệu tóm tắt trạng thái Thế/điều kiện ứng kỳ để chọn cách trình bày. Giới hạn trả lời 12.000 token sau một ca v4 bị cắt ở 8.000; phản hồi bị cắt vẫn bị chặn, không hiển thị hoặc tự gọi lại.

Đã nối Bát Tự, Mai Hoa và Lục Hào qua giao thức Chat Completions tương thích OpenAI. Backend dùng endpoint `https://rexapf.com/v1`, model yêu cầu `deepseek-v4.1-flash`; model trả về ở lần kiểm tra là `deepseek-v4.1-flash:1017`. Không qua OpenRouter. Mã HTTP được viết riêng bằng thư viện chuẩn Python, tham khảo cách phân tách kết nối/ngữ cảnh của tinix; không nhập nguyên dịch vụ Node.js hoặc prompt nhân vật.

## Cấu hình backend

`.env.local` được đọc lúc khởi động, nằm trong `.gitignore`, quyền file 600. Các biến môi trường cùng tên ưu tiên hơn file này. `.env.example` chứa tên biến và giá trị công khai, không có khóa thật.

- `RANDOMYST_AI_BASE_URL`: địa chỉ tới `/v1`, chưa gồm `/chat/completions`.
- `RANDOMYST_AI_MODEL`: model do người dùng chọn.
- `RANDOMYST_AI_API_KEY`: chỉ ở backend.
- `RANDOMYST_AI_TIMEOUT_SECONDS`: mặc định 55, cho phép 5–90 giây.

Chạy như trước bằng `./scripts/run_mvp.sh`. Cấu hình đổi cần khởi động lại. Không ghi khóa vào JavaScript, HTML, SQLite, kết quả API hoặc tài liệu. Kết nối HTTPS kiểm chứng chứng chỉ; không chuyển tiếp Authorization theo redirect. Không có endpoint cho trình duyệt đổi URL hoặc gửi API key.

## Luồng và giao diện

Lập/lưu phiên bằng engine hiện hành → adapter đọc snapshot → lấy nguồn và tối đa hai cặp few-shot → model viết lời luận → kiểm schema và dẫn chiếu → lưu bài luận riêng → hiển thị.

Phiên mới và thao tác luận lại chủ đề/Dụng thần tự viết bài luận AI. Khi mở lịch sử, giao diện tra bài đã lưu trước; nếu chưa có thì hiện nút **Luận giải AI**. Phân tích quy tắc và nguyên văn nằm trong phần mở rộng bên dưới. Không render HTML từ model.

- Bát Tự lấy đúng bài luận chủ đề đã lưu theo `bazi_reading_id`, kiểm tra nó thuộc lá số đang mở. Tên và ngày giờ sinh không được đưa vào payload AI; giữ dữ kiện Tứ Trụ và nhận định cần luận. Câu hỏi tự nhập vẫn được gửi làm ngữ cảnh.
- Mai Hoa giữ quẻ, hào động, Thể/Dụng/Hỗ/Biến, thời khí và những quan hệ đã tính; không lập quẻ mới. Mốc giao tiết đã dẫn xuất vẫn có thể nằm trong dữ kiện mùa; không gửi toàn bộ hồ sơ nhập.
- Lục Hào lấy đúng analysis đã lưu theo chủ đề/Lục thân/hào chọn và hash quy tắc. Không chọn Dụng khác. Nguồn cổ văn bổ sung có bản ghim; lời giải của engine được ghi **PRODUCT_POLICY**, không biến thư mục liên kết nguồn thành trích nguyên tác.

Few-shot ưu tiên đúng phương pháp, loại ví dụ có trạng thái đối lập đã biết, rồi xếp theo chủ đề, trọng tâm, mục đích và tín hiệu. Runtime v4 có 24 cặp, chỉ nối hướng dẫn method đang xem và một trọng tâm cùng tối đa hai điều kiện đi kèm. Bộ nhận diện mục đích câu hỏi chỉ chọn chỉ dẫn viết từ danh sách cố định, không đổi chủ đề/Dụng hoặc thêm kết luận mệnh lý. Bài luận ghi chính xác phiên bản và các mẫu được dùng; v2/v3 giữ làm lịch sử.

## API

- `GET /api/v1/ai/status`: trạng thái cấu hình, model và host, không có khóa.
- `POST /api/v1/ai/readings/lookup`: đọc cache, không gọi nhà cung cấp.
- `POST /api/v1/ai/readings`: lấy bài đã lưu hoặc viết một bài mới.

Hai POST dùng cùng request:

```json
{"method":"BAZI","consultation_id":"UUID-cua-la-so","bazi_reading_id":"UUID-cua-bai-luan"}
```

`method` nhận `BAZI`, `MAIHOA`, `LIUYAO`. Bát Tự có thể bỏ `bazi_reading_id` để lấy bài đầu. Mai Hoa chỉ cần `consultation_id`. Lục Hào bắt buộc `analysis_context` và `analysis_rules_sha256` từ bài phân tích đang mở. Các trường API key, URL, model, facts hoặc điểm do client gửi đều không được nhận.

Response `ai-reading-v1` có bài luận, context gắn nguồn, model yêu cầu/trả về, phiên bản prompt, thời gian, usage và số lượt sinh `generation_passes`. Các response nghiệp vụ Bát Tự/Mai Hoa/Lục Hào cũ không đổi schema hoặc bị viết đè.

## Cache và lỗi

Bảng SQLite `ai_readings` dùng khóa băm từ context, endpoint/model, manifest prompt, mẫu đã chọn và chính messages gửi model. Cùng yêu cầu đọc lại kết quả đã lưu. Đổi câu hỏi, chủ đề, Dụng thần, phiên bản nguồn, hướng dẫn hoặc model tạo khóa khác. Bản cũ vẫn giữ trong DB; lịch sử tra phiên bản khớp prompt hiện tại. Khóa API không tham gia khóa băm hoặc dữ liệu lưu.

Reservation `RUNNING` ngăn hai tab gọi trùng; commit giao dịch trước khi HTTP chạy để không giữ khóa DB trong lúc đợi AI. Reservation có lease 420 giây. Kết quả hợp lệ lưu `READY`; thất bại lưu mã lỗi, không lưu/hiển thị văn bản bị loại. Không dùng lời luận dự phòng giả khi nhà cung cấp lỗi.

Lỗi HTTP 429/502/503/504 được thử lại tối đa một lần; timeout không tự thử lại vì chưa biết bên cung cấp đã xử lý hay chưa. Nếu JSON trả được nhưng sai schema/ref/context, cho tối đa **một lượt viết lại** với danh sách ID và lỗi máy kiểm tra. Lượt thứ hai vẫn sai thì chặn. Usage cộng các lượt sinh có trả usage; không gọi đây là bản kê chi phí của nhà cung cấp.

Một lần thử Lục Hào đầu tiên đã bị chặn vì dẫn chiếu không khớp; kết quả lỗi không được hiển thị. Đã bổ sung kiểm tra lại có giới hạn và test ca sửa thành công/lặp lỗi. Báo cáo HTTP cuối chỉ ghi những bài đã qua kiểm tra.

## Phạm vi kiểm chứng

Test tự động kiểm tra kết nối giả lập, bảo mật trường cấu hình, cache qua restart, chủ sở hữu bài luận, dữ kiện không tính lại, đồng thời không gọi trùng, DB không bị giữ khóa, giới hạn sửa định dạng và UI không trộn phản hồi cũ.

Kiểm tra thật dùng ba phiên tổng hợp trong DB xem trước, không dùng hồ sơ cá nhân. Chạy thủ công bằng:

```sh
.venv/bin/python -m scripts.smoke_ai_readings
```

Script dùng lại fixture nếu file `docs/research/ai_readings_smoke_requests.json` còn tồn tại; một phiên bản prompt mới có thể tạo lượt gọi tính phí mới. Kết quả: `docs/research/ai_readings_http_smoke.json`. Snapshot lập quẻ/lá số vẫn giữ nguyên, đọc lại AI dùng cache.

Kiểm schema/reference chưa chứng minh mỗi câu diễn giải đúng ngữ nghĩa hoặc đúng phương pháp. Bộ mẫu và kết quả AI chưa được chuyên gia hiệu đính. Lớp AI không bổ sung Đại vận/Lưu niên, cứu giải hoặc các phép tính mà engine chưa có. Chưa có hội thoại tự do nhiều lượt và chưa nối AI vào phần đọc sâu của gieo bộ số theo profile cũ.

Kết quả kiểm tra: **184 kiểm thử Python + 10 JavaScript đạt**. HTTP thật cả ba module đạt; Bát Tự có một lượt sửa reference, Mai Hoa và Lục Hào đạt ở lượt đầu của lần kiểm tra cuối. Mỗi lần mở lại cho kết quả cache giống hệt và snapshot nghiệp vụ giữ nguyên. Ảnh giao diện: [Bát Tự](research/ai_bazi_ui.png), [Mai Hoa](research/ai_maihoa_ui.png), [Lục Hào](research/ai_liuyao_ui.png). Console trình duyệt không có cảnh báo/lỗi trong lượt kiểm tra cuối.
