# Lời luận tra ngày v1

Prompt riêng cho `DATE_SELECTION`, dùng cùng transport OpenAICompatible, kiểm tra schema/dẫn chiếu và bộ nhớ đệm của phần luận AI. Không nhập quy tắc Mai Hoa/Lục Hào vào chấm ngày.

Runtime `date-selection-2026-10-28-v1.1` trả kết luận bằng lời thường ngày, đúng hai đoạn giải thích ngắn và 1–2 việc chuẩn bị cụ thể; nhắm 140–220 từ, tối đa 300 từ. [Cách hiển thị và kiểm chứng](../../../docs/plain_reading_handoff.md).

7 ví dụ biên tập từ hồ sơ giả lập, với trạng thái engine thực sự tính: ngày/giờ đẹp, bình thường, bị chặn; chỉ xét ngày với hai người; ngày bị chặn; đầu vào giờ sinh chưa ổn định ở cả hai chế độ. Đây là mẫu dạy cách giải thích phần mềm, **chưa được chuyên gia hiệu đính, không phải chứng cứ nghiệm lý**. Một số trạng thái không có mẫu cùng chế độ sẽ dùng hướng dẫn trực tiếp, không mượn mẫu thuận hoặc mẫu có giờ để điền vào.

`date:policy` là quy tắc sản phẩm đã lưu, không phải lời cổ nhân. Dữ liệu ngày lấy từ engine hiện có (6tail/lunar-python 1.4.8 và các bảng/quy tắc đã ghim của tính năng tra ngày). Không có nguồn mệnh lý mới hoặc luật chấm điểm mới.

Tái tạo offline: `.venv/bin/python -m scripts.build_date_interpretation`. Manifest khóa hash prompt, ví dụ, adapter, phần giải thích và cấu hình luật. Lời luận AI không nhận ngày giờ sinh, vị trí, tên hoặc mã hồ sơ gốc.
