# Graph kiến thức — Randomyst Numbers

Graph này mô tả snapshot mã nguồn hiện tại để tìm thành phần cần sửa, lần theo luồng dữ liệu và chọn kiểm chứng phù hợp. Mở dashboard Understand Anything, tìm file hoặc khái niệm rồi xem các cạnh import, gọi hàm, đọc dữ liệu và `tested_by`.

## Các đường đi chính

- Gieo số: `web/app.js` → `randomyst/api.py` → `DrawStore.execute` → `NumberEngine.draw` → lịch UTC+8, Bát Tự, Mai Hoa và sampling → lưu kết quả SQLite.
- Tra ngày: `web/dates.js` → `POST /api/v2/auspicious-dates/search` → `DateEngine.search` → dựng hồ sơ sinh một lần/chủ thể → chia khung UTC+7 → facts corpus UTC+8, rule ngày và đối chiếu cá nhân → gate, penalty và xếp lịch. Luồng này không ghi bảng `draws`.
- Corpus ngày: `scripts/build_date_data.py` → config/schema cùng manifest và gzip tái lập → `DateCalendar` kiểm hash dữ liệu/mã provider khi khởi tạo. Graph giữ gzip như resource metadata, không đưa 2.558 ngày và 33.254 bản ghi giờ thành các node.
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
| Contract/rule chọn ngày | `randomyst/date_models.py`, `config/mvp2_date_rules.json`, `schemas/` | `tests/test_auspicious_dates.py`; đồng bộ builder và version rules |
| Corpus, chia khung và ranh sinh | `randomyst/date_calendar.py`, `scripts/build_date_data.py`, `data/date_calendar/` | Tests 22h/23h UTC+7, giao Jie exact, giờ clip, ngày đệm 2031 và hash corpus/provider |
| Loại trừ, penalty và hai chủ thể | `randomyst/date_rules.py`, `randomyst/date_engine.py` | Hard gate, special token, Tam Hợp đủ ba chi, dedupe, override, đảo chủ thể và số lần phân tích natal |
| UI tra ngày/API v2 | `web/dates.js`, `web/index.html`, `randomyst/api.py` | `scripts/smoke_dates.py`, `tests/test_auspicious_dates.py`, báo cáo HTTP/UI tại `docs/research/` |

## Ranh giới cần giữ

Runtime dùng lịch Bắc Kinh UTC+8. `calendar_adapter/`, `research_tools/legacy_time_engine.py`, `randomyst/geolocation.py` và đặc tả v3 phục vụ nghiên cứu/tương thích cũ, không phải luồng lịch hiện hành. Đồ thị dùng nhãn và tầng riêng để tránh lẫn hai hệ quy chiếu.

Một phần luật được ghi trong JSON nhưng vẫn triển khai bằng constant/code tại `time_engine.py`, `maihoa.py` và `sampling.py`; engine chỉ đọc hoặc kiểm một số mục cấu hình. Khi đổi luật, kiểm cả JSON lẫn module thực thi, không giả định sửa JSON sẽ đổi mọi hành vi.

Các quan hệ `related`/`documents` biểu thị đối chiếu hoặc giải thích; chúng không có nghĩa code được thực thi trong runtime. Graph mô tả kiến trúc và code, không xác nhận đúng đắn mọi lý luận huyền học hoặc chất lượng dịch nghĩa.

Trong MVP2, bảng Sát Chủ/Thọ Tử áp chi tháng ứng viên là policy sản phẩm v1, không phải xác nhận tương đương một truyền thống chọn ngày đã được hiệu đính. Tam Nương đang tắt. Điểm/nhãn đẹp chỉ áp vào việc, chủ thể và khung giờ được nhập; hard exclusion không được điểm cộng bù lại. `docs/logic_plan_mvp2.md` là đặc tả final, còn `docs/archive/logic_plan_mvp2_pre_r1.md` là proposal đã lưu.

## Cập nhật graph

Thư mục hiện chưa có Git. `source-snapshot.json` ghi SHA256 của từng file đã phân tích, còn `gitCommitHash` được ghi là `unversioned`. Không bật cập nhật theo commit. Sau khi thay code, gọi skill **understand-anything:understand** với `--full` để dựng lại graph từ file hiện tại; không suy ra graph còn mới chỉ từ giá trị `unversioned`.

`config.json` giữ ngôn ngữ tiếng Việt và `autoUpdate: false`. `fingerprints.json` là baseline cấu trúc do công cụ Understand Anything tạo; `validation-report.json` lưu kết quả kiểm tra của lần dựng này.

Refresh R5 dùng canonical scan/import/structure/fingerprint helpers cho toàn inventory, đối chiếu SHA256 để tái dùng phần phân tích của các file không đổi và phân tích lại đầy đủ file mới/đổi. Helper incremental theo commit không dùng được khi không có Git; không suy ra freshness từ `unversioned`. Bản graph trước R5 cùng fingerprint/meta/scan được giữ trong `snapshots/r5-before-20261012T125758Z/` để phục hồi. Dashboard không được tự mở trong lần refresh này vì ứng dụng sản phẩm đang được kiểm tra UI.
