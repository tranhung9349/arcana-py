# Cấu trúc prompt v4

1. `plain_vietnamese_v4.system.txt`: phạm vi dữ kiện, mức kết luận, tổng hợp liền mạch, cách viết thích ứng và hợp đồng JSON.
2. `interpretation_method_guides_v3.json`: chỉ lấy hướng dẫn đúng method của phiên, giữ các kiểm soát chuyên môn đã bổ sung ở v3.2.
3. `reading_playbook_v4.json` + `research_tools/reading_strategy.py`: chọn một trọng tâm, tối đa hai điều kiện, một gợi ý mục đích câu hỏi và góc nhìn theo chủ đề đã chọn. Chỉ chuỗi cố định đã ghim hash được nối vào system; câu hỏi/facts/evidence không được chép thành chỉ dẫn.
   Với Bát Tự, `bazi_plain_language_v1.system.txt` nối thêm yêu cầu dùng lời thường ngày; 10 mẫu Bát Tự dùng lời văn trong `bazi_plain_examples_v1.json`, giữ context và nguồn.
4. Tối đa hai cặp mẫu runtime: cùng phương pháp, loại trạng thái đối lập, xếp theo chủ đề/trọng tâm/mục đích/tín hiệu. Ví dụ chỉ dạy cách viết.
5. Context cuối là dữ liệu của phiên, giữ nguyên schema và dẫn chiếu; không thêm trường mệnh lý hoặc ghi đè kết quả gốc.

Mục đích câu hỏi được nhận diện bằng các mẫu từ tiếng Việt hữu hạn, không phải suy luận tự do về chủ đề/Dụng thần. Nếu không nhận diện được thì dùng gợi ý mở. Các định tuyến như hỏi thời điểm/so sánh không cấp phép tự tạo vận, ứng kỳ hoặc phần phân tích cho phương án thứ hai.

`build_messages` trả thêm `reading_plan` phục vụ kiểm tra nội bộ. Cache vẫn dựa trên hash actual messages và manifest, nên đổi trọng tâm hoặc prompt làm thay khóa. Đầu ra người dùng giữ `plain-reading-response-v2`; bài mới dùng summary, đúng 2 analysis ngắn, practical_options và limits. Schema vẫn nhận 2–4 analysis để đọc bài lịch sử. Không thêm dàn ý/mã định tuyến vào bài luận.

[Pack](../../data/interpretation/plain_v4/README.md) · [Nguồn và quyết định biên tập](../research/masters_reading_dynamic_v4.md).
