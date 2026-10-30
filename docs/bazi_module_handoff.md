# Luận Giải Bát Tự — bản natal v1

Cập nhật **28/10/2026**: phần tóm tắt theo chủ đề dùng lời thường ngày, bảng lá số và giải thích thuật ngữ mở thêm. AI Bát Tự sinh mới dùng hai tầng **Structural Analyst → Life Interpreter** với prompt người dùng cung cấp; [thiết kế hiện hành](bazi_two_stage_handoff.md). Narrative v2, quy tắc và dữ kiện lá số giữ nguyên; [bố cục và định dạng cũ](bazi_plain_reading_handoff.md). Các mô tả lưu phiên dưới đây thuộc giai đoạn cũ; runtime hiện dùng RAM như README.

Triển khai ngày **26/10/2026**, rules `bazi-natal-2026-10-26-v1`, profile `bazi_natal_v1`, corpus `bazi-corpus-2026-10-26-v1`.

## Người dùng có thể làm gì

Menu **Luận Giải Bát Tự** là chức năng thứ tư, cùng cấp với Luận Giải Kinh Dịch. Nhập tên tùy chọn, ngày giờ sinh dương lịch **1950–2026, Giờ Việt Nam**, chọn chủ đề trước ô ghi chú rồi lập lá số. Không có giờ sinh mặc định. Chủ đề: Tổng quan, Công việc, Tài chính, Học tập, Quan hệ.

Kết quả gồm tổng quan, bàn Tứ Trụ, tàng can và Thập Thần đầy đủ, gốc khí, sinh trợ, khí thế, trục nguyệt lệnh, hướng phù ức, gợi ý hàn noãn và tương tác Can Chi. Mỗi phần mở được căn cứ. Đếm can lộ/tàng can nằm trong mục mở thêm, không biểu diễn thành phần trăm sức mạnh. Ghi chú được lưu nguyên, chưa được phân tích ngữ nghĩa để trả lời sự kiện hoặc thời điểm.

Người dùng mở lại lá số trong lịch sử, luận thêm chủ đề từ cùng snapshot, hoặc mở lại một bài luận đã lưu. Hồ sơ mới đang sửa không thay dữ liệu kết quả đã hiển thị. Retry lỗi mạng giữ UUID/payload; sửa form hủy retry cũ. State, lịch sử và API Bát Tự tách riêng khỏi các chức năng khác.

## Lõi và phương pháp

- `bazi_facts.py` dựng facts từ Tứ Trụ của `time_engine.pillars()` đúng một lần khi không khai sai số. Bảng Thập Thần phân biệt đầy đủ Thiên Tài/Chính Tài và mọi cặp cực tính; Nhật chủ mang nhãn riêng. Root cùng hành được phân biệt bản khí/khí khác, không cộng thành điểm.
- `bazi_rules.py` ghim và kiểm nguồn, tạo findings có `fact_refs` và `evidence_refs`. Trạng thái là độ đủ căn cứ, không phải xác suất. Các nhánh vượng/nhược dùng điều kiện định tính hẹp đã ghi ở `policy:strength`; phần chưa phân định giữ MIXED. Không tự coi MIXED là cân bằng, không suy tòng cách chỉ từ điểm cực trị.
- Phần nguyệt lệnh xét bản khí cùng tàng can thấu đúng Can ở năm/tháng/giờ. Tên Kiến Lộc/Dương Nhận là dấu hiệu để khảo sát; mọi cách cục giữ ở mức ứng viên, chưa xác nhận thành cách/phá cách/hóa cách.
- Hướng phù ức và Điều hậu tách riêng. Mùa lạnh có gợi ý khảo sát Hỏa, mùa nóng khảo sát Thủy; đây chưa phải dụng Điều hậu hoàn chỉnh. Xung đột với hướng phù ức được giữ rõ. Nghi thuận thế không tự áp dụng cách bổ thân của nội cách.
- `bazi_narrative.py` chỉ biên soạn từ facts/findings. Các chủ đề đọc cặp lực liên quan và hiện diện thực tế ở từng trụ, cùng khí thế và quan hệ chi ngày khi thích hợp. Không gọi LLM hoặc RNG.
- `bazi_service.py` điều phối và validate response. Nếu sai số đã khai làm đổi Tứ Trụ ở đầu/cuối khoảng, trả 422 `BIRTH_BOUNDARY_UNSTABLE`; không dựng lá số giả để thay thế. Không sinh thông báo thiếu sai số mặc định.

Nhận diện hợp Can, lục hợp/xung, tam hợp/tam hội đủ ba chi khác nhau, hại, Tý–Mão hình, tam hình đủ bộ và tự hình. Một bộ chi ghi một lần, giữ vị trí chi lặp; quan hệ hợp không tự suy hóa. Chưa xét phá, bán hình và toàn bộ chế hóa/cứu giải.

Nguồn, metadata và phần chưa có corpus được ghi trong [README nguồn](../data/reference/bazi/README.md). Đây là engine luận có phạm vi giới hạn, chưa được chuyên gia hiệu đính. Cách cục, vượng nhược và Điều hậu chưa có ground truth độc lập đầy đủ; kiểm thử phần mềm không được trình bày thành độ chính xác dự đoán đời người.

## API và snapshot

| Endpoint | Chức năng |
|---|---|
| `GET /api/v1/bazi/rules` | Chủ đề, version/hash, registry và coverage |
| `POST /api/v1/bazi/consultations` | Tạo snapshot và bài luận đầu tiên |
| `GET /api/v1/bazi/consultations/{request_id}` | Đọc nguyên response đã lưu |
| `GET /api/v1/bazi/history?limit=10` | Lịch sử lá số riêng |
| `POST /api/v1/bazi/consultations/{request_id}/readings` | Biên soạn và lưu bài luận khác trên snapshot |
| `GET /api/v1/bazi/consultations/{request_id}/readings?limit=10` | Bài đầu tiên và tối đa `limit` bài bổ sung gần nhất |

Contract ở `bazi_models.py`; JSON Schema và examples có tiền tố `bazi_consultation_` / `bazi_reading_`. Response có kiểu cho chart, facts, assessment, findings, reading, evidence và coverage; validators kiểm hash đoạn trích và tham chiếu tồn tại. Link nguồn chỉ chấp nhận GitHub/Wikisource; UI dựng nội dung qua `textContent`.

`bazi_store.py` thêm hai bảng `bazi_consultations`, `bazi_readings` trong cùng SQLite. `BEGIN IMMEDIATE` giữ retry đồng thời chỉ tạo một bản ghi. UUID/payload hash quyết định replay; UUID cũ với payload khác trả 409, UUID không tìm thấy trả 404. GET consultation luôn trả bài đầu; luận thêm không đổi consultation. Reading snapshot có UUID riêng, hash chart, version analysis gốc và version narrative riêng.

`BaziService.reinterpret()` dùng chart, facts, assessment và findings đã lưu, không tính lại lịch hoặc áp rules natal mới. Nó tạo lời luận theo narrative hiện hành với version mới trong reading snapshot. Các bài đã lưu được replay nguyên vẹn. Nếu cần đổi schema/profile về sau, phải migration/version riêng.

Lõi `randomyst/bazi.py` và `bazi_reading.py` cũ được giữ cho gieo số/tra ngày/phần đọc sâu. Không thay nhánh số học hoặc viết lại snapshot cũ. Profile mới có thể khác cách đọc cũ vì phương pháp và phạm vi khác nhau; provenance được giữ riêng ở API.

## Kiểm chứng và vận hành

```sh
RANDOMYST_DATABASE=/tmp/randomyst_bazi_tests.sqlite3 .venv/bin/python -m unittest discover -s tests -q
node --check web/bazi.js
node --test tests/test_draw_reading.cjs
.venv/bin/python scripts/smoke_bazi_consultations.py
```

Ca mới kiểm 100 cặp Thập Thần theo công thức ngũ hành/cực tính độc lập với bảng provider, 12 bảng tàng can, 144 cặp chi, các bộ thiếu/đủ và chi lặp, điều kiện vượng/nhược/MIXED/ngoại cách nghi vấn, ứng viên cách cục từ chi tháng, Điều hậu khác hướng phù ức, binding/hash nguồn, một lần dựng chart, luận lại không dựng chart, retry đồng thời, 409, restart và cách ly lịch sử khác. Fixtures lịch là kiểm tích hợp với provider và kế thừa policy đã có; không quảng bá thành kiểm chứng lịch thiên văn độc lập toàn dải.

Kết quả: **162 ca Python + 5 ca JavaScript đạt**, gồm 15 ca mới cho module Bát Tự. Bốn schema/example hợp lệ; khảo sát 308 lá số, bốn mẫu/năm trong 1950–2026, đều validate được. Thời gian khảo sát local trung bình 3,058 ms, tối đa 13,344 ms; đây không phải load test/P95. HTTP tạo/đọc/retry/luận thêm đạt, các lịch sử khác giữ nguyên. UI ở chiều rộng 686px đã kiểm tạo lá số, chọn chủ đề, mở bài cũ, căn cứ và cuộn tới kết quả; console không có warning/error. [Báo cáo](research/bazi_module_validation.json), [HTTP](research/bazi_http_smoke.json), [ảnh](research/bazi_module_ui.png).

Đại vận, Lưu niên, không rõ giờ sinh, nhập ngày âm, múi giờ khác, hợp hai lá số và xuất báo cáo chưa nằm trong bản này. Xem kế hoạch gốc [bazi_module_plan.md](bazi_module_plan.md) cho hướng mở rộng.
