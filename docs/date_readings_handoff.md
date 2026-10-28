# Luận giải Tra ngày theo việc — 27/10/2026

Trước thay đổi này popup chỉ liệt kê trạng thái, điểm trừ, Hoàng/Hắc Đạo và chi tiết từng khung. Có dữ liệu giải thích nhưng chưa có bài luận tổng hợp và chưa nối dịch vụ AI.

Khi mở một ngày, giao diện lưu một bản kết quả đầy đủ của đúng việc, hồ sơ và bộ lọc. Phần **Vì sao ngày này được xếp như vậy?** xuất hiện ngay: nên/kỵ của việc, đối chiếu từng hồ sơ, yếu tố trừ điểm, điều kiện loại trừ và phạm vi áp dụng. Nút **Luận giải AI** đọc bản đã lưu, dùng kết nối/model đang cấu hình. Mở popup chỉ tìm bài luận đã lưu; không tự gọi model trả phí.

## Hợp đồng và lưu trữ

- `POST /api/v2/auspicious-dates/consultations`: `{request_id, search}`; search chỉ được chứa một ngày thuộc bộ lọc thứ. Backend tính đầy đủ các khoảng và lưu kết quả, bảng điểm và hash bộ luật cùng lời giải thích v1.
- `GET /api/v2/auspicious-dates/consultations/{id}`: đọc nguyên bản đã lưu.
- `POST /api/v1/ai/readings` hoặc `/lookup`: `{method: "DATE", consultation_id: "..."}`. Không nhận facts/điểm số từ client.
- Bảng SQLite riêng `date_consultations`; không ghi lịch sử gieo số. UUID lặp với dữ liệu khác trả 409. Luận/đọc lại snapshot không tính lại ngày, Bát Tự hay gieo quẻ.
- UI tái dùng UUID khi mở lại cùng ngày/hồ sơ/bộ lọc trong cùng lần tải trang; đổi dữ liệu tạo bản mới. Chưa có lịch sử tra ngày trên UI; tải lại trang chưa tự khôi phục bản đã mở. AI cache vẫn bền theo ID snapshot, prompt, dữ liệu, model và endpoint.

## Phạm vi lời luận

- Chọn khoảng trọng tâm bằng cùng thứ tự với engine: nhãn → điểm → độ dài → giờ sớm nếu bằng nhau. Phân tích sâu chỉ khoảng này; các khoảng được khuyến nghị khác chỉ liệt kê.
- Giữ nguyên điểm và luật hiện có: ngưỡng Ngày Đẹp là 75 khi xét ngày/giờ, 80 khi chỉ xét ngày. Không thay ngưỡng gieo bộ số.
- DAY_ONLY không xét giờ, dù khoảng hiệu lực vẫn có mốc giờ để thể hiện ranh lịch. DAY_AND_HOUR chỉ nói giờ bắt đầu.
- Hai người xét riêng; dùng mức trừ hành lớn hơn, không lấy trung bình. Trạng thái cá nhân SUPPORTED không chứng minh toàn bộ mệnh cục thuận.
- AI chỉ nhận vai trò, hành/band đã tính và các kết luận có sẵn. Không chuyển ngày giờ sinh, vị trí, tên hay ID hồ sơ lên provider.
- Dùng `DateReadingContext` riêng mở rộng kiểu context; pack Bát Tự/Mai Hoa/Lục Hào v4.1 và schema nghiên cứu bốn phương pháp vẫn giữ nguyên. Kết quả API AI thêm phương pháp DATE và context DATE_SELECTION.
- Prompt date v1 có 7 mẫu giả lập chưa chuyên gia hiệu đính; chọn mẫu cùng trạng thái/chế độ. Không tự thêm Tam Nương, Đại vận, Lưu niên, quẻ Dịch hoặc phong thủy vào kết quả tra ngày.

## Kiểm tra

200 kiểm thử Python và 15 kiểm thử JavaScript đạt. Các ca mới kiểm tra tính nhất quán với search, nhãn bị chặn/chưa rõ, hai người, DAY_ONLY, idempotency, lưu và đọc lại AI sau restart, không tính lại snapshot, không truyền giờ sinh, chặn context/ID lạ, chọn ví dụ đúng chế độ và bỏ kết quả UI cũ khi đóng popup.

Script live: `scripts/smoke_date_readings.py`; fixture và kết quả lưu tại `docs/research/date_readings_smoke_requests.json` và `docs/research/date_readings_http_smoke.json`. Đây là kiểm tra tích hợp và hiệu đính nội bộ trên dữ liệu giả lập; schema/dẫn chiếu đúng không bảo đảm ý nghĩa lời luận đã được chuyên gia xác nhận.
