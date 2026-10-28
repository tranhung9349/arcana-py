# Module luận Lục Hào theo câu hỏi

Ngày 26/10/2026. [Cơ sở nghiên cứu và lựa chọn phương pháp](research/liuyao_analysis_research.md).

## Dùng trên giao diện

Trong tab **Gieo 3 đồng · Lục Hào**, chọn chủ đề và viết câu hỏi. App đối chiếu cụm từ trong câu hỏi với chủ đề: hiển thị ý nhận diện và tín hiệu đã dùng, gợi ý đổi chủ đề khi không khớp. Câu hỏi nhiều nhóm ý hoặc khác chủ đề cần chọn gợi ý hoặc bấm **Giữ chủ đề** trước khi gieo/luận. Kết quả có lời luận trước phần kinh văn. Mở một phiên cũ cũng có thể lập lời luận; không sửa sáu lượt tiền hoặc thời điểm đã lưu.

**Đổi chủ đề hoặc chọn Dụng thần** cho phép đổi chủ đề, chỉ định Lục thân và chọn một hào thuộc nhóm ứng viên. Khi đổi nhóm, luận lại để lấy danh sách ứng viên mới. Chọn hào rồi bấm luận lại nếu đối tượng thực tế đã xác định. Bản phân tích gần nhất được mở lại cùng phiên.

## API

- `GET /api/v1/coins/analysis-rules`: chủ đề, nguồn, phạm vi, phiên bản/hash quy tắc.
- `POST /api/v1/coins/question-intent`: nhận diện và đối chiếu `{question, topic}`; chỉ đọc, không tạo quẻ hoặc bản luận.
- `POST /api/v1/coins/consultations/{request_id}/analysis`: phân tích snapshot quẻ đã lưu.
- `GET /api/v1/coins/consultations/{request_id}/analysis`: bản phân tích được mở gần nhất; `null` khi chưa có; phiên không tồn tại trả 404.

```json
{"topic":"CAREER","use_relative":null,"focus_line":null,"intent_mode":"COMBINED","intent_acknowledged":false}
```

`topic`: `GENERAL`, `WEALTH`, `CAREER`, `DOCUMENT`, `PARENTS`, `CHILDREN`, `SIBLINGS`, `PARTNERSHIP`.

`use_relative` nhận đúng một trong năm Lục thân tiếng Việt hoặc `null`. `focus_line` là số nguyên 1–6 hoặc `null`; phải thuộc nhóm Dụng. Hào Phục chọn theo vị trí bị phủ; một nhóm không trộn hào hiện với Phục. Payload sai hoặc hào không thuộc nhóm trả 422.

`intent_mode=COMBINED` bật kết hợp câu hỏi và chủ đề. `TOPIC_ONLY` là mặc định cho client cũ, giữ cách luận cũ. Nhận diện không tự đổi `topic`, `use_relative` hoặc `focus_line`. Thứ tự quyết định: Lục thân chỉ định → chủ đề đã chọn → tín hiệu câu hỏi dùng để gợi ý/làm rõ. Nếu cần xem lại mà chưa có `intent_acknowledged=true`, API trả 422 `INTENT_REVIEW_REQUIRED` và không lưu bản luận mới. Khi người dùng chọn gợi ý, UI đổi chủ đề rõ ràng; với câu nhiều ý, lựa chọn đó cũng xác nhận phạm vi chính.

Response thêm `intent` (nullable để đọc bản cũ), gồm phiên bản nhận diện, hash câu hỏi, chủ đề chọn/gợi ý, trạng thái `MATCH/CONFLICT/MULTIPLE/UNRECOGNIZED`, ứng viên, cụm từ và nhóm ý. `SPECIFIC_PHRASE/KEYWORD` mô tả loại bằng chứng, không phải xác suất chính xác. Những ý cụ thể như khoản nợ, ứng tuyển, hợp đồng bổ sung câu hỏi kiểm chứng thực tế phù hợp trong lời luận.

Nhận diện hiện là quy tắc cụm từ cục bộ: hỗ trợ có/không dấu, giữ dấu đã nhập để tránh nhầm “ưu tiên” với “tiền”, ranh giới từ, một số phủ định rõ và người được nhắc làm bối cảnh. Chưa hiểu mọi ngữ nghĩa, phủ định phức tạp hoặc vai trò của mọi nhân vật. Trường hợp không nhận ra ý vẫn dùng chủ đề đã chọn. Không gọi LLM, không gửi câu hỏi tới dịch vụ ngoài.

[Request mẫu](../examples/liuyao_analysis_request.json), [response mẫu](../examples/liuyao_analysis_response.json), [schema request](../schemas/liuyao_analysis_request.schema.json), [schema response](../schemas/liuyao_analysis_response.schema.json).

Nhận diện riêng: [request](../examples/liuyao_intent_request.json), [response](../examples/liuyao_intent_response.json), [schema request](../schemas/liuyao_intent_request.schema.json), [schema response](../schemas/liuyao_intent_response.schema.json). [Kiểm chứng luồng kết hợp](research/liuyao_intent_validation.json).

## Lưu trữ và tái lập

Không thêm trường vào `CoinRequest` v1, giữ tương thích hash của request gieo cũ. Bản quẻ và bản luận là hai snapshot độc lập.

`coin_analyses` lưu theo phiên và khóa hash `(snapshot quẻ, context, rules_sha256)`. `coin_analysis_latest` giữ bản được mở gần nhất. Cùng context/hash trả đúng snapshot; đổi chủ đề hoặc quy tắc tạo bản khác. Quay lại context cũ có thể mở bản đã lưu. Giao dịch SQLite tuần tự hóa retry đồng thời, không gọi lại RNG.

Hash quy tắc bao gồm JSON, mã engine, model và phụ thuộc Nạp Giáp/lịch. GET giữ bản đã lưu kể cả khi code đổi; POST mới dùng engine hiện tại. Khi thay quy tắc cần đổi `version` và cập nhật fixtures/nghiên cứu. Dữ liệu bản trước không bị ghi đè.

## Thành phần

- `randomyst/liuyao_analysis.py`: quy tắc, nhận định có căn cứ, tổng hợp lời văn.
- `randomyst/liuyao_models.py`: hợp đồng request/response và kiểm khóa tham chiếu.
- `randomyst/liuyao_intent.py`, `config/liuyao_intent_rules.json`: nhận diện cụm từ có căn cứ và đối chiếu chủ đề.
- `randomyst/liuyao_store.py`: snapshot phân tích và bản gần nhất.
- `config/liuyao_analysis_rules.json`: chủ đề, cặp hợp/tiến, nguồn, giới hạn.
- `web/liuyao.js`: đọc/lưu lời luận, đổi context, chống kết quả đến muộn và retry riêng phần luận.
- `web/coin_intent.js`: xem trước ý hỏi, chọn gợi ý/giữ chủ đề, chống kết quả nhận diện cũ; dùng cả trước gieo và khi luận lại.
- `tests/test_liuyao_analysis.py`: fixtures nguồn, tính chất toàn không gian quẻ, API và độ bền snapshot.
- `tests/test_liuyao_intent.py`: 8 chủ đề, có/không dấu, Unicode, phủ định, nhiều ý, xung đột, quyền ưu tiên và snapshot kết hợp.

Chạy kiểm thử: `RANDOMYST_DATABASE=/tmp/randomyst_tests.sqlite3 .venv/bin/python -m unittest discover -s tests -v`. Các bài API tự tạo database tạm riêng.

Phần tự động là luận theo quy tắc có điều kiện; chưa giải toàn bộ Lục Hào hoặc dự báo ngày ứng nghiệm. Kinh văn Việt có sẵn vẫn mang nhãn bản nháp AI; lời luận mới dùng mẫu diễn đạt được dựng từ dữ kiện, chưa được chuyên gia hiệu đính.
