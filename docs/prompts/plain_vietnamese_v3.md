# Prompt lời luận tổng hợp v3.2

Phiên bản `plain-vietnamese-2026-10-27-v3.2`; dùng cho Bát Tự, Mai Hoa và Lục Hào qua dịch vụ AI đã cấu hình. Chu Dịch có mẫu nghiên cứu, chưa có endpoint AI riêng.

`plain_vietnamese_v3.system.txt` quy định bài có một nhận định trung tâm và các đoạn phát triển liên tiếp. `interpretation_method_guides_v3.json` chỉ cung cấp hướng dẫn đúng phương pháp của phiên. Các cặp trong `data/interpretation/plain_v3/cases.json` minh họa nền → phối hợp → điều kiện → tổng hợp, thay cách viết mỗi nhãn một đoạn.

Facts xác nhận dữ kiện; findings giới hạn kết luận đã tính; evidence giải thích căn cứ. Không dùng việc nguồn có một quy tắc để tự áp thêm phép luận mà lõi chưa thực hiện. Giữ đúng chiều sinh khắc, tách vị trí với hiệu lực, tách biểu tượng với tình trạng đời sống. Các ví dụ lỗi cụ thể trong system/guide ngăn việc lặp một câu phủ định rồi vẫn suy ra chính điều vừa phủ định.

Giữ contract `plain-reading-response-v2`: summary, 2–4 analysis, 1–2 practical_options và 1–3 limits. Thông thường 3–4 đoạn phân tích khi dữ kiện đủ, không ép dài với lát cắt ít dữ kiện. Dẫn chiếu phải thuộc context cuối, mẫu không cấp dữ kiện cho phiên thật.

Cache thay khi manifest hoặc chính messages thay. Bài cũ được giữ trong DB; mở lại phiên sẽ tra bản khớp prompt hiện tại, nếu chưa có thì dùng nút Luận giải AI. Không tự gọi trả phí khi chỉ mở lịch sử.

[Nghiên cứu nguồn, ca lỗi và cách kiểm tra](../research/interpretation_synthesis_v3.md). Chưa có chuyên gia hiệu đính hoặc benchmark độc lập; không coi schema/reference là xác nhận đúng mọi câu.
