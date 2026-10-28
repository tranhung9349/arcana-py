# MVP 2 — Bản bàn giao local

**Cập nhật 25/10/2026:** đã có **7 nhóm/18 việc**, 9 việc xét ngày + giờ và 9 việc chỉ xét ngày. Bản hiện hành là `mvp2-dates-2026-10-25-v2` / `date-search-response-v2`; xem [bàn giao việc trọng đại](docs/major_events_handoff.md). Nội dung dưới đây lưu phạm vi và kiểm chứng v1 ngày 12–15/10.

Ngày: 12/10/2026. Rules: `mvp2-dates-2026-10-12-v1`. API: `date-search-response-v1`.

Đã có tra ngày cho **cưới hỏi (hai người), khai trương và xuất hành (một người)**; tối đa 93 ngày trong 2024–2030. Giao diện có lịch kết quả và chi tiết khung giờ, điểm, loại trừ, đối chiếu từng chủ thể và nguồn.

Cập nhật hiển thị 15/10/2026: ô ngày có chiều cao cố định, hiện số khung giờ đẹp và mở popup liệt kê đủ khung bằng **tên giờ + khoảng giờ**. Popup dùng `recommended_windows` sẵn có; chỉ tải chi tiết khi mở phần lý do. Đóng bằng nút Đóng/Esc/bấm ngoài, giữ focus trong popup rồi trả về card. `recommended_windows` không giới hạn top 3; có `hour_branch` ở cả tóm tắt gọn và chi tiết. Ranh giờ/Jie/ngày được giữ, cuối ngày 24:00, giây lẻ được hiển thị. Role client: Gia chủ / Người xuất hành / Đương sự thứ nhất-thứ hai; ID API giữ nguyên.

Đã audit **23 category dự kiến**: đề xuất ưu tiên nhập trạch, chuyển chỗ ở, an sàng, sửa chữa và giao dịch. Category mới **chưa bật**; [bản nghiên cứu](docs/research/mvp2_activity_expansion.md) và [độ phủ token](docs/research/mvp2_activity_token_coverage.json) ghi mapping, thiếu dữ liệu giờ, xung đột nguồn và việc cần làm trước khi triển khai. Chạy lại bằng `.venv/bin/python research_tools/audit_activity_categories.py`.

```sh
./scripts/run_mvp.sh
# Mở http://127.0.0.1:8765 và chọn “Tra ngày theo việc”
```

API tra ngày:

```sh
curl --fail http://127.0.0.1:8765/api/v2/auspicious-dates/search \
  -H 'Content-Type: application/json' \
  --data-binary @examples/date_search_request.json
```

- Đặc tả: [logic_plan_mvp2.md](docs/logic_plan_mvp2.md).
- Rules: [mvp2_date_rules.json](config/mvp2_date_rules.json); schema: [mvp2_date_rules.schema.json](schemas/mvp2_date_rules.schema.json).
- Contract: [request](schemas/date_search_request.schema.json), [response](schemas/date_search_response.schema.json); ví dụ [cưới hỏi 93 ngày](examples/marriage_date_search_request.json).
- Corpus thô: [manifest](data/date_calendar/manifest.json), [quy ước và rebuild](data/date_calendar/README.md).
- Engine: `randomyst/date_calendar.py`, `date_rules.py`, `date_engine.py`; models riêng tại `date_models.py`.
- Kiểm chứng HTTP: [mvp2_runtime_validation.json](docs/research/mvp2_runtime_validation.json), [cold 93 ngày riêng](docs/research/mvp2_cold_93_runtime_validation.json); UI: [mvp2_ui_smoke.json](docs/research/mvp2_ui_smoke.json).
- Kiểm chứng thay đổi hiển thị: [HTTP](docs/research/mvp2_display_runtime_validation.json), [UI và tên chủ thể](docs/research/mvp2_display_ui_validation.json); 66 tests đã pass.
- Kiểm chứng popup ngày 15/10: [UI, chiều cao card và bàn phím](docs/research/mvp2_popup_ui_validation.json); [ảnh card](docs/research/mvp2_popup_cards.jpg), [ảnh popup](docs/research/mvp2_popup_ui.jpg). Thay đổi client; kiểm tra cú pháp JS và thao tác trình duyệt, không chạy lại bộ test backend.
- Graph kiến trúc: `.ua/knowledge-graph.json` là snapshot R5 ngày 12/10/2026; chưa phản ánh field khung giờ và nghiên cứu category bổ sung. `autoUpdate=false` được giữ; đọc source hiện hành khi sửa phần này. Chỉ số của snapshot trong `.ua/validation-report.json`.

Chạy lại kiểm chứng:

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/smoke_dates.py
.venv/bin/python scripts/smoke_dates.py --cold-marriage-first --output docs/research/mvp2_cold_93_runtime_validation.json
node --check web/dates.js
```

`smoke_dates.py` tự mở server localhost mới, dùng SQLite tạm và hồ sơ mẫu, rồi dừng server. Không gọi gieo số. Kết quả đo là các request trên máy phát triển, chưa là benchmark tải đồng thời.

Luật lớn có bảng ghim được bật `BLOCK`; **Tam Nương tắt** và xuất hiện trong `disabled_rules`. Có dữ liệu thật sự mâu thuẫn hoặc sai số sinh đã biết vượt ranh đổi trụ thì khung trả `UNRESOLVED`. Điểm phạt/ngưỡng và cách áp bảng natal vào ngày ứng viên là policy sản phẩm v1, chưa được chuyên gia chọn ngày hiệu đính độc lập.

Mỗi chủ thể chỉ gọi `pillars` và `analyze` một lần/request. Cặp đôi xét chung một khung và dùng mức phạt cá nhân lớn nhất; xung thuộc policy của một người loại trừ khung chung. “Ngày Đẹp cho [việc]” chỉ áp dụng các khung đủ điều kiện, dùng làm giờ bắt đầu.
