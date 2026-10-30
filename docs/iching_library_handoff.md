# Thư viện 64 quẻ — submenu Kinh Dịch

28/10/2026: chuyển danh sách 64 quẻ khỏi phần dưới form/kết quả Lục Hào sang submenu **Thư viện 64 quẻ**, cùng cấp **Mai Hoa** và **Gieo 3 đồng · Lục Hào**.

`library-workspace` chứa danh sách có tìm kiếm và màn hình kinh văn riêng. Chọn quẻ mở `library-result`; nút trở lại danh sách giữ nguyên từ khóa. Mục đang chọn được giữ khi chuyển sang chức năng khác rồi quay về Kinh Dịch. Bảng 64 quẻ không còn là phần con của `coins-workspace`.

Tra cứu dùng GET các endpoint kinh văn hiện có. Request/abort/revision, trạng thái lỗi và vùng kết quả của thư viện tách khỏi phiên gieo: không hủy request lập quẻ, không reset phần luận Lục Hào hoặc ghi đè kết quả đã gieo. Không gọi AI khi tra cứu. Kinh văn, sáu hào và nút xuất PDF tiếp tục dùng được. Catalog bị lỗi/malformed có thể tải lại; rời chi tiết trong lúc đang tải không làm kết quả cũ xuất hiện lại.

Kiểm chứng sau thay đổi này:

- `npm test`: 47 ca đạt, có 5 ca thư viện về chuyển menu, giữ bộ lọc, đọc quẻ riêng, hủy/đọc lại, giữ request gieo đang chạy và retry lỗi.
- `.venv/bin/python -m unittest tests.test_coin_consultations tests.test_bazi_consultations tests.test_interpretation_prompt tests.test_reading_display tests.test_ai_readings tests.test_deep_readings -q`: 80 ca đạt. Có kiểm cấu trúc HTML để danh sách và kết quả thư viện nằm ngoài workspace gieo.
- `npm run build:css` và `git diff --check`: đạt.
- Trình duyệt thật: mở Kinh Dịch chỉ thấy form/luận; mở submenu thư viện tải đủ 64 quẻ; tìm `thuan can`, đọc quẻ 1, trở lại giữ bộ lọc; chuyển qua Bát Tự rồi về Kinh Dịch giữ mục thư viện. Trên 375px không tràn ngang, submenu ba mục vẫn đủ nhãn. Console không có warning/error.

Ảnh: `docs/research/iching_library_menu.png` và `docs/research/iching_library_mobile.png`.
