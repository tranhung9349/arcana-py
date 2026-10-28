# Prompt luận thích ứng v4

Runtime `plain-vietnamese-2026-10-27-v4.1`: 24 mẫu nguyên tác biên tập, 29 trích đoạn/quy ước nguồn, hướng dẫn riêng cho bốn phương pháp và một bộ chọn trọng tâm theo phiên. Tối đa hai few-shot trong mỗi lần gọi runtime.

Trọng tâm phụ thuộc tín hiệu đã lưu, chủ đề đã chọn và gợi ý mục đích câu hỏi. Chỉ điều chỉnh thứ tự/dung lượng giải thích, không suy thêm finding mệnh lý. Có một trọng tâm, tối đa hai điều kiện đi kèm; không nối mọi nhánh vào một bài.

Build offline: `.venv/bin/python -m scripts.build_plain_interpretation_v4`. Giữ nguyên v2/v3, không tải nguồn ngầm hoặc gọi model. Manifest ghim prompt, hướng dẫn, playbook, module định tuyến, dữ liệu và raw nguồn.

Trạng thái `EDITORIAL_DRAFT_NOT_EXPERT_REVIEWED`. 11 ca giữ riêng chưa chạy model; 3 câu hỏi biến thể cùng dữ kiện với mẫu dạy nằm riêng trong `adaptive_probes.json`, chưa chạy model và không phải held-out độc lập. Cổ thư cung cấp phương pháp truyền thống, không chứng minh độ đúng dự báo thực nghiệm.

[Nghiên cứu, nguồn và giới hạn](../../../docs/research/masters_reading_dynamic_v4.md).
