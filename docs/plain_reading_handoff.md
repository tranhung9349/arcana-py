# Lời giải dễ hiểu — 28/10/2026

**30/10/2026:** Lục Hào dùng hướng dẫn riêng ở pack v4.4, hiển thị luôn hai đoạn giải thích ngắn và thu gọn toàn bộ kinh văn/bảng quẻ. [Cách trả lời nhiều ý, phạm vi thời gian và kiểm tra](liuyao_plain_reading_handoff.md).

Phản hồi cần giải quyết: người dùng đọc kết quả vẫn không hiểu vì dài và trừu tượng. Thay đổi áp dụng cho panel AI dùng chung của Bát Tự, Mai Hoa, Lục Hào và Tra ngày.

## Cách đọc mới

- **Ý chính:** trả lời thẳng câu hỏi bằng 1–2 câu, dùng lời thường ngày.
- **Bạn có thể làm gì?:** 1–2 việc cụ thể, có thứ để kiểm tra ngoài đời; đặt ngay sau câu trả lời.
- **Cần lưu ý:** hiển thị các giới hạn liên quan ngay trong phần đọc nhanh.
- **Vì sao có kết luận này?:** đóng mặc định, chứa đủ phân tích và căn cứ của từng nhận định, gồm cả căn cứ câu tóm tắt. Không cắt câu hoặc bỏ đoạn của bài đã có.

Giữ hệ giao diện Arcana, font và màu hiện có; nội dung chính rộng tối đa 65ch, các gợi ý/lưu ý dùng chữ 16px. Tra cứu skill `ui-ux-pro-max` không cho kết quả khớp riêng về progressive disclosure; áp dụng nguyên tắc mặc định của skill về giảm nội dung ban đầu, chữ dễ đọc và control native.

## Đầu ra mới

Prompt `plain-vietnamese-2026-10-28-v4.3` và `date-selection-2026-10-28-v1.1` yêu cầu trả lời trước, giải thích sau, không đưa thuật ngữ chuyên môn vào tóm tắt, không biến biểu tượng thành sự kiện thật. V4.3 bổ sung hướng dẫn và lời văn mẫu riêng cho Bát Tự; xem [kiểm chứng bổ sung](bazi_plain_reading_handoff.md). Độ dài ví dụ không phải chuẩn cho đầu ra mới.

Máy chủ kiểm tra từ theo khoảng trắng: tóm tắt ≤50; đúng 2 đoạn phân tích, mỗi đoạn ≤70; mỗi hành động ≤35; mỗi giới hạn ≤30; tổng bài ≤300. Mục tiêu biên tập là 140–220 từ, không ép viết cho đủ. Nếu vượt ngân sách, cho viết lại một lần kèm trường vượt và giới hạn; lần hai vẫn lỗi thì không hiển thị hoặc cache. Cơ chế retry dùng chung với kiểm schema/dẫn chiếu, tổng cộng tối đa hai lượt sinh.

Ngân sách áp dụng khi sinh mới; bài hợp lệ có sẵn vẫn đọc đủ nội dung. Không đổi schema API hoặc tính lại lá số, quẻ, điểm/ngày khuyến nghị. Manifest và build script đã cập nhật để cache mới dùng đúng prompt mới.

## Kiểm chứng

- `npm test`: 40 kiểm tra JavaScript đạt, gồm thứ tự đọc nhanh và phân tích đóng mặc định cho cả bốn phương pháp, nội dung không mất và snapshot không bị sửa.
- `.venv/bin/python -m unittest tests.test_reading_display tests.test_interpretation_prompt tests.test_ai_readings tests.test_date_readings -q`: 46 kiểm tra Python đạt, gồm biên độ dài từng phần/tổng bài, retry, không cache bài dài bị loại và đọc lại bài cũ.
- `npm run build:css`: thành công; hai bộ prompt tái tạo offline thành công và kiểm hash qua bộ test.
- Một bài Mai Hoa tạo bằng model thật qua UI, với câu hỏi mẫu “Tôi cần chuẩn bị gì trước khi triển khai một kế hoạch mới?”: tóm tắt 30 từ; hai đoạn phân tích 52 và 54 từ; hai hành động 26 và 21 từ; ba lưu ý 13, 12 và 14 từ. Tổng 222 từ, phần đọc nhanh 116 từ. Mở phần giải thích xem đủ nội dung và đóng lại được.
- Kiểm tra responsive ở 375px và chiều ngang; phần đọc nhanh không tràn ngang. Ảnh trong `docs/research/plain_reading_ui.png` và `docs/research/plain_reading_mobile.png`.

Đây là một mẫu thử model thật và kiểm chứng hành vi hiển thị/độ dài. Chưa có thử nghiệm với người dùng để xác nhận mức độ hiểu, chưa đánh giá diện rộng chất lượng diễn đạt của model ở cả bốn phương pháp. Bộ kiểm độ dài không thay thế kiểm chứng ngữ nghĩa hoặc chuyên gia hiệu đính.
