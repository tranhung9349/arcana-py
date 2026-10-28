# Hồ sơ mẫu kiểm tra

Bản public hiện tại không lưu phiên. Các request AI/luận thêm cần snapshot có chữ ký từ response thật, thay vì chỉ UUID trong ví dụ cũ. Xem [hợp đồng API hiện tại](../docs/security_deployment.md).

Mẫu tra ngày v2: [nhập trạch](home_entry_date_request.json) / [response](home_entry_date_response.json), [động thổ chỉ xét ngày](day_only_date_request.json) / [response](day_only_date_response.json). Dùng hồ sơ tổng hợp và ngày giao Jie 08/10/2026; chỉ xét ngày trả khoảng hiệu lực, không trả giờ đẹp. Sinh lại bằng `scripts/smoke_major_dates.py` khi preview local đang chạy; xem [bàn giao](../docs/major_events_handoff.md).

`draw_request.json` là input tổng hợp dùng kiểm tra, không phải dữ liệu sinh của người dùng. `draw_response.json` là phản hồi HTTP thật của server local với input ấy; không có seed được truyền vào API. Đây là một kết quả mẫu, không phải bộ số được khuyến nghị riêng.

Mã request cố định giúp thử idempotency: chạy lại cùng file nhận đúng kết quả cũ. Muốn phiên mới, đổi request_id thành UUID mới.

Mẫu hiện hành dùng rules v4: 10:00 UTC+7 → 11:00 Bắc Kinh UTC+8; không có tọa độ. Phiên v3 trước được lưu trong `docs/archive/`; đổi UUID giúp mẫu mới không trả lại cache của quy tắc cũ.
# Giải thích nguồn

`source_explanation.json` là response đọc từ phiên thực tế trong `draw_response.json`, qua `GET /api/v1/interpretation/{request_id}`. Nội dung gồm nguyên văn Hán open-iching, bản nháp nghĩa Việt có nhãn AI, lời giải Việt từ tinix-bazi và nghĩa Hổ/Biến chỉ để xem. Không có lời gọi provider LLM; không gieo lại hay sửa bộ số đã lưu. Schema tại `schemas/source_explanation.schema.json`.
