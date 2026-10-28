# Graph kiến thức — Randomyst Numbers

Graph này mô tả snapshot mã nguồn hiện tại để tìm thành phần cần sửa, lần theo luồng dữ liệu và chọn kiểm chứng phù hợp. Mở dashboard Understand Anything, tìm file hoặc khái niệm rồi xem các cạnh import, gọi hàm, đọc dữ liệu và `tested_by`.

## Các đường đi chính

- Gieo số: `web/app.js` → `randomyst/api.py` → `DrawStore.execute` → `NumberEngine.draw` → lịch UTC+8, Bát Tự, Mai Hoa và sampling → lưu kết quả SQLite.
- Đọc lời giải: UI → GET interpretation theo UUID → phiên đã lưu → `ExplanationRepository` → corpus nguồn và bản nháp Việt. Luồng này không gọi lại engine sinh số.
- Xây corpus: JS nguồn tinix đã ghim + kinh văn open-iching → `scripts/build_explanation_data.py` → JSON cục bộ → API lời giải.
- Kiểm chứng: các cạnh `tested_by` dẫn từ code được kiểm đến file test. Các báo cáo nghiên cứu là bằng chứng của lần chạy được ghi trong file, không thay thế kết quả kiểm thử mới.

## Chọn vùng sửa và kiểm chứng

| Việc cần mở rộng | Bắt đầu đọc | Kiểm chứng phù hợp |
|---|---|---|
| Input/response hoặc API | `randomyst/models.py`, `randomyst/api.py`, `web/app.js` | `tests/test_runtime.py`, `tests/test_source_explanations.py`; cập nhật schema/mẫu liên quan |
| Lịch, múi giờ, ranh năm/ngày/giờ | `randomyst/time_engine.py`, quy tắc lịch trong `config/mvp1_rules.json` | `tests/test_beijing_calendar.py`, `scripts/audit_beijing_calendar.py` |
| Công thức quẻ | `randomyst/maihoa.py` | `tests/test_runtime.py`; giữ thứ tự hào từ dưới lên, Y/M/D/H và Hổ/Biến chỉ hiển thị |
| Trọng số, quota, ngưỡng, bể số | `randomyst/engine.py`, `randomyst/sampling.py` | `tests/test_weighted_sampling.py`, `tests/test_runtime.py`, audit khả thi/phân bố; đổi phiên bản quy tắc |
| Logic Bát Tự | `randomyst/bazi.py`, các file JS tham chiếu tinix | `scripts/compare_bazi_source.py`, `tests/test_runtime.py` |
| Bản nghĩa Việt hoặc nguồn mới | `data/interpretation/`, `data/reference/manifest.json`, `randomyst/interpretation.py` | `scripts/build_explanation_data.py`, `tests/test_source_explanations.py`; giữ hash, khóa quẻ/hào và nhãn chất lượng |
| Kết nối LLM về sau | prompt/schema trong `docs/prompts/`, `schemas/`; `randomyst/interpretation.py` | Giữ luồng đọc phiên đã lưu, chứng cứ nguồn và trạng thái lỗi độc lập với sáu số |
| Retry, lưu lịch sử, UUID | `randomyst/storage.py`, `randomyst/api.py` | Các ca idempotency/concurrency trong `tests/test_runtime.py` |

## Ranh giới cần giữ

Runtime dùng lịch Bắc Kinh UTC+8. `calendar_adapter/`, `research_tools/legacy_time_engine.py`, `randomyst/geolocation.py` và đặc tả v3 phục vụ nghiên cứu/tương thích cũ, không phải luồng lịch hiện hành. Đồ thị dùng nhãn và tầng riêng để tránh lẫn hai hệ quy chiếu.

Một phần luật được ghi trong JSON nhưng vẫn triển khai bằng constant/code tại `time_engine.py`, `maihoa.py` và `sampling.py`; engine chỉ đọc hoặc kiểm một số mục cấu hình. Khi đổi luật, kiểm cả JSON lẫn module thực thi, không giả định sửa JSON sẽ đổi mọi hành vi.

Các quan hệ `related`/`documents` biểu thị đối chiếu hoặc giải thích; chúng không có nghĩa code được thực thi trong runtime. Graph mô tả kiến trúc và code, không xác nhận đúng đắn mọi lý luận huyền học hoặc chất lượng dịch nghĩa.

## Cập nhật graph

Thư mục hiện chưa có Git. `source-snapshot.json` ghi SHA256 của từng file đã phân tích, còn `gitCommitHash` được ghi là `unversioned`. Không bật cập nhật theo commit. Sau khi thay code, gọi skill **understand-anything:understand** với `--full` để dựng lại graph từ file hiện tại; không suy ra graph còn mới chỉ từ giá trị `unversioned`.

`config.json` giữ ngôn ngữ tiếng Việt và `autoUpdate: false`. `fingerprints.json` là baseline cấu trúc do công cụ Understand Anything tạo; `validation-report.json` lưu kết quả kiểm tra của lần dựng này.
