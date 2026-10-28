# Phần đọc sâu của phiên gieo số — 26/10/2026

View “Thời điểm và dữ liệu của phiên” đã được bỏ khỏi giao diện. “Đọc sâu quẻ & Bát Tự” có hai tab **Luận Mai Hoa** và **Luận Bát Tự**, hiển thị bài luận tiếng Việt dựa trên đúng snapshot đã lưu. Kinh văn, căn cứ và giới hạn nằm trong các mục đối chiếu tùy chọn.

`GET /api/v1/interpretation/{request_id}` trả `source-explanation-v2`, thêm hai `ModuleReading` trong `readings`. Mỗi module có version, summary, sections, evidence, facts và limitations. Các đoạn luận phải tham chiếu tới căn cứ tồn tại; nhãn phân biệt kinh văn nguyên bản, dữ kiện đã lưu và quy tắc triển khai. Validator vẫn nhận response v1 cũ; v2 bắt buộc đủ hai module. Sinh số giữ rules v6 và ngưỡng 80/85.

- `randomyst/bazi_reading.py`: diễn giải 10 nhánh tính Dụng Thần từ `bazi.reason_code`, Nhật chủ, trợ lực tháng sinh, nội/ngoại cách, 13 tên cách cục có nguồn, Dụng/Hỷ/Kỵ và liên hệ với số đã chọn. Mùa sinh lấy từ trụ tháng sinh; không lấy thời khí lúc gieo để luận lá số. Override chỉ đổi hành dùng cho bộ số, không sửa kết quả lá số. Không có đại vận, lưu niên hoặc luận toàn bộ đời người. Tên cách cục/nhánh chưa hỗ trợ được báo thiếu, không thay tên để tìm lời luận.
- `randomyst/maihoa_service.py`: tách `interpret_chart(core, month, topic)` dùng chung cho consultation và phần đọc sâu. Consultation vẫn lập quẻ theo source profile cũ của nó; phần đọc sâu truyền nguyên quẻ và tháng gieo đã lưu. Lõi xét Thể/Dụng, Thể hỗ/Dụng hỗ, Dụng biến, vượng suy, chuỗi đầu/cuối và căn cứ cổ thư đã ghim.
- `randomyst/maihoa_reading.py`: chuyển findings của lõi Mai Hoa thành bài luận tiếng Việt theo từng chặng. Phiên gieo số không có câu hỏi nên dùng phạm vi GENERAL, không tự chọn cầu tài hoặc dự đoán trúng thưởng. Hỗ và Biến không quay lại thay đổi trọng số hoặc điểm.
- `randomyst/interpretation.py`: kiểm ID/hào của quẻ gốc và quẻ phụ, gọi hai module; từ chối Thể/Dụng không khớp hình quẻ. Thiếu Hỗ/Biến thì nêu rõ phần chưa luận, không lập lại để lấp chỗ trống.
- `web/app.js`: bỏ toàn bộ code render dữ liệu phiên và các ID tương ứng; render bài luận từ API bằng textContent. Code `sourceCard` vẫn được giữ vì tab Mai Hoa riêng dùng nó để đối chiếu nguồn.

Không gọi RNG, tính lại lá số/lịch, tạo consultation mới, ghi lại phiên số hoặc gọi LLM bên ngoài. Các nhãn vượng nhược/cát hung là quy ước của phép đọc truyền thống, không được đổi thành xác suất trúng thưởng hay kết luận chắc chắn về một người.

Kiểm chứng: 147 kiểm thử Python và 5 kiểm thử JavaScript đạt. Các ca mới phủ đủ 64 quẻ × 6 vị trí hào động, 10 nhánh tính Bát Tự, override, tên cách cục thiếu nguồn, mùa sinh khác mùa gieo, quẻ phụ thiếu hoặc không nhất quán, hỗ quẻ Càn/Khôn của profile cũ, lịch v3 và đọc lại không tính lại. HTTP đọc hai lần trả cùng bài luận, giữ nguyên bộ số và lịch sử. Xem `research/draw_deep_reading_validation.json` và `research/draw_deep_reading_http_smoke.json`.
