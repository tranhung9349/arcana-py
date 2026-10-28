# Plain Vietnamese v2

Bản lịch sử ngày 26/10/2026. Runtime hiện dùng [v3.2](../plain_v3/README.md); các mô tả v2 dưới đây được giữ để tra lại.

17 cặp few-shot biên soạn mới, 8 context đánh giá riêng, 20 trích đoạn/quy ước nguồn. Trạng thái `EDITORIAL_DRAFT_NOT_EXPERT_REVIEWED`. Runtime mới chọn tối đa hai cặp để diễn giải Bát Tự/Mai Hoa/Lục Hào; công cụ nghiên cứu vẫn chạy ngoại tuyến. Tích hợp tại `randomyst/ai_service.py`, phạm vi tại `docs/ai_readings_handoff.md`.

Các ví dụ là lát cắt giả định, không phải lá số đầy đủ, mệnh lệ cổ hay kết quả tiên đoán đã nghiệm. Facts/trạng thái của từng ví dụ là đầu vào được cung cấp, không dùng để kiểm thử ngược thuật toán lập quẻ/lá số.

`PRIMARY_TEXT` chỉ nói trích nguyên tác; `source_state` phân biệt bản chép ghim revision với đoạn Tử Bình mới đối chiếu qua web, chưa ghim ấn bản. `AI_INTERPRETATION` là prose soạn mới; `MODERN_APPLICATION` là gợi ý đời sống, không phải lời cổ thư.

Build: `.venv/bin/python -m scripts.build_plain_interpretation_data`. Manifest khóa prompt, schema, examples và nguồn raw được dùng. Không cập nhật nguồn ngầm. Các kiểm tra trong `tests/test_interpretation_prompt.py` chỉ xác nhận contract và ràng buộc dữ liệu.

Nguồn, ví dụ dễ đọc và giới hạn: [báo cáo nghiên cứu](../../../docs/research/interpretation_sources_fewshot_v2.md). Công cụ: `research_tools/interpretation_prompt.py`. Prompt: `docs/prompts/plain_vietnamese_v2.system.txt`.
