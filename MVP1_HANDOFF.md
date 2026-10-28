# Bàn giao MVP 1 → MVP 2

Ngày chốt: **12/10/2026**. Người dùng kết thúc MVP 1 tại phiên hiện tại; MVP 2 sẽ bắt đầu trong phiên mới. Không tiếp tục mở rộng chức năng trong phiên này.

## Baseline giữ lại

- Mỗi phiên xuất **một bộ sáu số khác nhau trong 00–45**, sắp tăng dần, định dạng hai chữ số. Các phiên độc lập có thể trùng bộ.
- Runtime Python/FastAPI, SQLite local; khởi động bằng `./scripts/run_mvp.sh`, giao diện tại `http://127.0.0.1:8765/`.
- Quy tắc hiện tại: **v4**. Nhập thời gian UTC+7, chuyển cùng thời điểm sang Bắc Kinh UTC+8; provider `lunar-python==1.4.8`. Adapter lịch Việt Nam/TST/vị trí chỉ còn trong phần nghiên cứu lưu trữ.
- Mai Hoa khóa công thức Y/M/D/H; ngày âm dân sự đổi lúc 00:00 Bắc Kinh. Bát Tự dùng sect 1, đổi trụ ngày lúc 23:00 và năm/tháng theo giao tiết. Hổ/Biến phục vụ hiển thị.
- Dụng Thần lấy hành đầu tiên theo bản chuyển logic tinix-bazi hoặc override. Nguồn đã ghim được ghi trong `data/reference/manifest.json`.
- Sampling β = 2; điểm 40% Âm Dương + 60% Ngũ Hành. Khóa ngữ cảnh, G_cap và delta qua tối đa năm lượt tổng cộng. Giải sát chỉ khi Đại Hung, quota **3–4**, cấm hành khắc Dụng Thần từ lượt đầu.
- Đọc lịch sử và giải thích không gieo lại. Kinh Dịch dùng nguyên văn open-iching; nghĩa Việt là bản nháp AI có nhãn UNREVIEWED. Bát Tự trích bảng văn bản tinix-bazi. Chưa nối provider/model LLM.

## Bằng chứng và tài liệu

- `README.md`: cách chạy, hành vi hiện hành, lệnh kiểm chứng và giới hạn.
- `docs/logic_plan_mvp1.md`: đặc tả logic.
- `docs/research/beijing_calendar_migration_validation.json`: bằng chứng chuyển lịch.
- `.ua/knowledge-graph.json`: graph đã dựng **94 file, 284 node, 840 cạnh, 10 tầng, 15 bước tour**.
- `.ua/validation-report.json`: kiểm định graph thành công; dashboard đã được kiểm tra tải dữ liệu.
- `.ua/README.md`: hướng dẫn dùng graph để bảo trì và mở rộng.

Các số liệu trên lấy từ tài liệu/báo cáo đã lưu; không chạy lại bộ kiểm thử ứng dụng khi chốt phiên. Knowledge graph đã hoàn tất, không còn bước kiểm định/dashboard dang dở.

## Điểm cần mang sang phiên MVP 2

- Đọc baseline và graph trước khi thay đổi; phạm vi MVP 2 sẽ do người dùng chốt trong phiên mới.
- Nhiều luật vẫn nằm trong constant của code; sửa JSON cấu hình chưa đủ để thay đổi mọi hành vi.
- Biên sai số đồng hồ chưa cung cấp được hiển thị UNDETERMINED; không tự mặc định thành sai số bằng không.
- Bản dịch Việt cần được rà soát nếu muốn nâng mức bảo đảm nội dung. Điểm nội bộ không phải xác suất trúng thưởng.
- Project hiện chưa có Git; graph dùng SHA256 snapshot và autoUpdate=false. Sau thay đổi MVP 2, dựng/cập nhật graph và chạy kiểm chứng phù hợp với phần thay đổi.
- Giữ nguyên lịch sử đã lưu, quy tắc phiên cũ và tính idempotency khi nâng cấp.

Không có phạm vi tính năng MVP 2 nào được mặc định triển khai trong bàn giao này.
