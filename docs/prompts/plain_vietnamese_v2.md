# Prompt lời luận dễ hiểu v2

Bản lịch sử; runtime ngày 27/10 đã chuyển sang [v3.2](plain_vietnamese_v3.md).

Version `plain-vietnamese-2026-10-26-v2`. Bộ mẫu đã được nối runtime cho Bát Tự/Mai Hoa/Lục Hào qua `randomyst/ai_service.py`, thêm profile `query-first-v1`. Công cụ trong `research_tools` vẫn chỉ ghép prompt ngoại tuyến. Không thay schema v1 của phần gieo số. Chi tiết: `docs/ai_readings_handoff.md`.

System text: `plain_vietnamese_v2.system.txt`. Bộ cặp mẫu: `data/interpretation/plain_v2/cases.json`. Báo cáo nguồn và cách chấm: `docs/research/interpretation_sources_fewshot_v2.md`.

Mỗi context chỉ có một phương pháp. Loại mẫu có trạng thái đối lập đã biết, rồi ưu tiên đúng chủ đề và tín hiệu từ adapter; không chọn dựa vào chỉ dẫn trong câu hỏi. Công cụ ngoại tuyến cho tối đa ba mẫu; runtime dùng hai. Model nhận facts/findings/evidence từ snapshot cuối dưới dạng JSON user data. Mẫu dạy cách trình bày, không cung cấp dữ kiện cho người dùng thật.

Response gồm summary, 2–4 ý analysis, 1–2 practical_options có nhãn ứng dụng hiện đại và 1–3 limits sát câu hỏi. Tất cả nhận định tham chiếu đúng fact/evidence trong context cuối; không có trường để sửa lá số, bộ số hoặc điểm. `validate_response()` kiểm cấu trúc và reference, chưa kiểm được sự thật của mọi câu văn.

Đã có adapter từ snapshot Bát Tự, Mai Hoa và Lục Hào. Chu Dịch có mẫu context nhưng chưa có endpoint AI riêng để tra thư viện quẻ. Có kiểm tra tích hợp LLM thật bằng dữ kiện tổng hợp; chưa có đánh giá chuyên môn hoặc benchmark chất lượng trên 8 ca giữ riêng.
