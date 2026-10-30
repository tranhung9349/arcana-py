# Prompt luận thích ứng v4

Runtime `plain-vietnamese-2026-10-30-v4.6`: 25 mẫu biên tập, 29 trích đoạn/quy ước nguồn của mẫu, hướng dẫn riêng cho bốn phương pháp và một bộ chọn trọng tâm theo phiên. Tối đa hai few-shot trong mỗi lần gọi runtime.

V4.6 đặt mục tiêu Lục Hào thấp hơn giới hạn cứng (150–190 từ), chặn thêm “hợp trói”, “biến hào” và cấp danh mục ID dẫn chiếu rõ ràng cho phiên. Các lỗi dẫn chiếu, lời văn, thuật ngữ và độ dài được kiểm cùng lúc; lượt sửa nhận toàn bộ lỗi và bản nháp có cấu trúc hợp lệ trong dữ liệu biên tập, cùng context gốc. Bản nháp bị từ chối không trở thành nguồn dữ kiện. Không tự cắt câu hoặc sửa nguồn; bản cuối tiếp tục qua toàn bộ kiểm tra trước khi hiển thị.

Trần toàn bài vẫn 300 từ. Riêng validator Lục Hào cho khoảng dư 1,5 lần ở từng phần để không từ chối một bài ngắn chỉ vì tóm tắt 52 từ hoặc đoạn giải thích 76 từ; mục tiêu prompt vẫn thấp hơn, không tăng độ dài bài. Phương pháp khác giữ trần từng phần cũ.

V4.5 tách system prompt Lục Hào; context thật gửi đủ lần gieo, quẻ chủ/biến, hào động, lịch và bàn Nạp Giáp, kèm kinh văn truy xuất từ corpus khóa theo đúng quẻ và trích Tăng San phù hợp. Số evidence runtime thay theo quẻ/findings, không giới hạn ở 29 nguồn của ví dụ. Nguyên văn, bản nháp AI và nhận định engine có vai trò khác nhau; nguồn chỉ có link được nêu rõ chưa có nội dung. Manifest ghim prompt, adapter, module truy xuất và corpus. [Dữ liệu gửi, thử API thật và giới hạn](../../../docs/liuyao_plain_reading_handoff.md).

V4.4 thêm hướng dẫn Lục Hào: trả lời đủ các ý của câu hỏi, phân biệt ngày/tháng gieo với tháng được hỏi, không tự suy thời hạn công việc. Sáu ví dụ Lục Hào cũ được viết lại bằng lời thường ngày từ cùng dữ kiện/dẫn chiếu, thêm một ví dụ công việc giả định. Máy chủ chặn danh sách thuật ngữ và mã/số hào trong lời văn khi sinh mới; chi tiết vẫn giữ trong căn cứ mở rộng. [Chi tiết](../../../docs/liuyao_plain_reading_handoff.md).

Bài mới ưu tiên câu trả lời bằng lời thường ngày, gợi ý một việc cụ thể và giới hạn cần biết; nhắm 140–220 từ, tối đa 300 từ. Dữ kiện và nguồn của mẫu được giữ nguyên; ví dụ không làm chuẩn độ dài cho đầu ra mới. Máy chủ kiểm tra ngân sách từng phần và cho viết lại tối đa một lần. [Giao diện, kiểm chứng và giới hạn](../../../docs/plain_reading_handoff.md).

Riêng v4.3: viết lại lời văn của cả 10 mẫu Bát Tự từ cùng context/nguồn; thêm hướng dẫn Bát Tự bằng lời thường ngày sau các hướng dẫn phương pháp và trọng tâm. Máy chủ chặn tên chuyên môn trong tóm tắt/hành động và quá hai tên chuyên môn trong phần giải thích khi sinh mới. [Thay đổi riêng cho Bát Tự](../../../docs/bazi_plain_reading_handoff.md).

Trọng tâm phụ thuộc tín hiệu đã lưu, chủ đề đã chọn và gợi ý mục đích câu hỏi. Chỉ điều chỉnh thứ tự/dung lượng giải thích, không suy thêm finding mệnh lý. Có một trọng tâm, tối đa hai điều kiện đi kèm; không nối mọi nhánh vào một bài.

Build offline: `.venv/bin/python -m scripts.build_plain_interpretation_v4`. Giữ nguyên v2/v3, không tải nguồn ngầm hoặc gọi model. Manifest ghim prompt, hướng dẫn, playbook, module định tuyến, dữ liệu và raw nguồn.

Trạng thái `EDITORIAL_DRAFT_NOT_EXPERT_REVIEWED`. 11 ca giữ riêng chưa chạy model; 3 câu hỏi biến thể cùng dữ kiện với mẫu dạy nằm riêng trong `adaptive_probes.json`, chưa chạy model và không phải held-out độc lập. Cổ thư cung cấp phương pháp truyền thống, không chứng minh độ đúng dự báo thực nghiệm.

[Nghiên cứu, nguồn và giới hạn](../../../docs/research/masters_reading_dynamic_v4.md).
