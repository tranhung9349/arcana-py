# Bát Tự bằng lời thường ngày — 28/10/2026

**Cập nhật tiếp theo cùng ngày:** phần AI sinh mới đã chuyển sang [Bát Tự hai tầng](bazi_two_stage_handoff.md), dùng hai prompt người dùng cung cấp và bài 700–1.000 từ. Prompt một tầng v4.3, 10 mẫu và giới hạn 300 từ dưới đây mô tả lần triển khai trước; giao diện tóm tắt/lá số và các bài theo schema cũ vẫn được hỗ trợ.

Phản hồi: người đọc không hiểu phần Bát Tự vì có quá nhiều tên chuyên môn. Lần sửa trước mới đổi bố cục panel AI; bảng Tứ Trụ vẫn hiện trước lời giải, nội dung theo chủ đề và các ví dụ Bát Tự vẫn dùng cách diễn đạt chuyên môn.

## Thay đổi

- `bazi_narrative.py` v2 viết lại tóm tắt và các phần giải thích. Tóm tắt mô tả mức kết luận của lá số bằng lời thường ngày; một gợi ý để tự thử thay đổi theo 5 chủ đề. Không suy tính cách, năng lực, thu nhập hay tương lai từ tên nhóm ký hiệu. Đây là biên tập nội dung từ facts/assessment/findings đã có, không tính lại lá số.
- Mở kết quả thấy tóm tắt, việc có thể thử và lưu ý trước. Bảng Tứ Trụ/tàng can/Thập Thần nằm trong disclosure có 7 mục giải nghĩa. Căn cứ vẫn giữ đầy đủ văn bản findings và nguồn, bao gồm các finding chỉ được dẫn một lần.
- AI dùng prompt riêng `bazi_plain_language_v1.system.txt`, chỉ nối cho `BAZI_NATAL_V1`. Cả 10 mẫu Bát Tự được viết lại thành hai đoạn ngắn, giữ nguyên context và nguồn; dẫn chiếu của đoạn thứ hai gộp từ các đoạn tương ứng trước đó. Build script tái tạo các mẫu và manifest v4.3 offline, không đổi các pack v2/v3.
- Khi sinh AI Bát Tự mới, bộ kiểm từ vựng chặn các tên chuyên môn phổ biến trong tóm tắt và hành động, hoặc quá hai tên khác nhau trong phân tích. Một từ được giải nghĩa trong phân tích vẫn được phép. Từ “quan sát” dùng như hành động thông thường không bị coi là nhóm “Quan Sát”. Bài cũ vẫn đọc được; retry dùng chung ngân sách tối đa hai lượt sinh với kiểm độ dài/schema/ref.
- Khi AI trả bài hợp lệ, phần tóm tắt ban đầu thu lại để tránh lặp nội dung. Lỗi hoặc kết quả không khớp phiên không làm mất phần tóm tắt đó. Không tự gọi AI.
- Phần Bát Tự giải thích bộ số cũng đổi tiêu đề và lời văn. Nhánh tính cụ thể vẫn có nguyên lời giải trong căn cứ `rules:reason`; cách chấm số và dữ kiện gốc giữ nguyên.

## Kiểm chứng

Các kiểm tra gồm ba trạng thái STRONG/WEAK/MIXED với cả năm chủ đề, không đổi input/facts; đầy đủ dẫn chiếu, 10 mẫu AI qua kiểm độ dài/từ vựng; hash prompt riêng và cách ly phương pháp; từ chuyên môn được viết lại một lần; giao diện có tóm tắt trước bảng và bảng đóng mặc định; đọc lại bài lịch sử đủ nội dung. Xem kết quả chạy trong chat và ảnh trong `docs/research/bazi_plain_reading_ui.png`.

Lần kiểm chứng riêng cho Bát Tự: 66 kiểm tra Python và 42 JavaScript đạt. Một bài AI thực tế với hồ sơ giả lập, chủ đề Học tập và câu hỏi “Tôi nên thay đổi cách học thế nào?” có 199 từ: tóm tắt 37, hai đoạn giải thích 51/50, hành động 27, hai giới hạn 17/17. Phần đọc nhanh không có tên chuyên môn. Kiểm trên 375px không tràn ngang; mở mục thuật ngữ thấy đủ 7 định nghĩa và bảng lá số. Ảnh mobile trong `docs/research/bazi_plain_reading_mobile.png`.

Bộ kiểm từ vựng chỉ chặn một nhóm tên phổ biến, không bảo đảm toàn bài dễ hiểu hoặc đúng ngữ nghĩa. Gợi ý thực tế là việc để tự kiểm tra; chưa có thử nghiệm với người dùng để đo mức hiểu và chưa có chuyên gia hiệu đính.
