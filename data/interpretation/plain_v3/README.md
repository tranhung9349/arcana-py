# Lời luận tổng hợp v3.2

Bản lịch sử. Runtime hiện tại dùng [prompt thích ứng v4.1](../plain_v4/README.md); dữ liệu v3.2 giữ nguyên để đối chiếu.

Runtime `plain-vietnamese-2026-10-27-v3.2`: 18 cặp mẫu nguyên tác biên tập, 24 trích đoạn/quy ước nguồn, 11 ca giữ riêng. Trạng thái `EDITORIAL_DRAFT_NOT_EXPERT_REVIEWED`. Cổ thư là nguồn phương pháp truyền thống, không phải bằng chứng dự báo thực nghiệm.

Các case là lát cắt giả định, không phải mệnh lệ lịch sử. Trạng thái mạnh/yếu và các quan hệ được cung cấp sẵn cho ví dụ, không dùng để suy ngược hoặc kiểm chứng thuật toán lập lá số/quẻ. Gợi ý hiện đại mang nhãn `MODERN_APPLICATION`.

Build ngoại tuyến: `.venv/bin/python -m scripts.build_plain_interpretation_v3`. Kế thừa danh mục nguồn và ca giữ riêng v2, soạn lại toàn bộ mẫu, thêm mẫu Lục Hào văn thư. V2 giữ nguyên để tra lại. Manifest ghim prompt, hướng dẫn từng phương pháp, schema, case và raw nguồn; không tải hoặc cập nhật nguồn ngầm.

Runtime chọn tối đa hai mẫu đúng phương pháp, loại trạng thái đối lập đã biết rồi ưu tiên chủ đề/tín hiệu. Hướng dẫn tương ứng method được nối vào system; các method khác không được nối vào. Cache gồm hash của chính messages, ngoài manifest/model/endpoint/context.

11 ca giữ riêng có tiêu chí review nhưng chưa chạy model (`NOT_RUN`). Ba phiên HTTP thực tế là ca hồi quy tổng hợp đã dùng trong phát triển. Kiểm schema và dẫn chiếu không thay hiệu đính ngữ nghĩa/chuyên môn.

[Nghiên cứu và giới hạn](../../../docs/research/interpretation_synthesis_v3.md). [Cấu trúc prompt](../../../docs/prompts/plain_vietnamese_v3.md).
