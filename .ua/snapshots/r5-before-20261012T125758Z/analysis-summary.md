# Kết quả dựng knowledge graph

Ứng dụng local Python/FastAPI sinh một bộ sáu số khác nhau trong 00–45 từ ngữ cảnh Bát Tự, quẻ Mai Hoa và các quy tắc trọng số đã khóa. Runtime dùng lịch Bắc Kinh UTC+8 của 6tail, lưu lịch sử SQLite và đọc kinh văn cùng lời giải tiếng Việt từ corpus cục bộ; adapter lịch Việt Nam chỉ còn phục vụ nghiên cứu lưu trữ.

Đã phân tích **94/94 file**, dựng **284 node**, **840 cạnh**, **10 tầng** và **15 bước tour**. Kiểm định schema, inventory, imports, tham chiếu và phân tầng: pass; không có issues/warnings.

## File theo loại

- code: 39
- config: 36
- docs: 14
- infra: 0
- data: 0
- script: 1
- markup: 4

## Node theo loại

- file: 44
- function: 128
- class: 38
- endpoint: 6
- table: 1
- document: 14
- config: 33
- schema: 11
- concept: 6
- module: 3

## Cạnh theo loại

- imports: 49
- contains: 227
- exports: 126
- tested_by: 17
- calls: 103
- defines_schema: 22
- serves: 1
- configures: 9
- reads_from: 27
- writes_to: 8
- related: 119
- depends_on: 41
- inherits: 13
- documents: 65
- deploys: 1
- validates: 12

## Các tầng

- Giao diện gieo và tra phiên
- API cục bộ và SQLite
- Lịch Bắc Kinh, Bát Tự và Mai Hoa
- Điều phối gieo, trọng số và nghiệm thu
- Giải thích chỉ đọc và corpus hiển thị
- Hai nguồn tham chiếu đã ghim
- Luật, tài liệu và môi trường chạy
- Kiểm thử, thí nghiệm và bằng chứng
- Lịch Việt, vị trí và nghiên cứu lưu trữ
- Hợp đồng LLM dự kiến

## Guided tour

1. Tổng quan dự án
2. Khởi động ứng dụng
3. Giao diện nhập liệu
4. Luật và cấu hình
5. Lịch Bắc Kinh
6. Bát Tự và quẻ
7. Điều phối phiên gieo
8. Lấy mẫu và chấm
9. Lưu phiên bất biến
10. Nguồn đã ghim
11. Chuẩn bị lời giải
12. Giải thích chỉ đọc
13. Kiểm thử bất biến
14. Nghiên cứu lưu trữ
15. Hợp đồng LLM dự kiến

## Ghi chú

- Đồ thị gắn với SHA256 snapshot; project chưa có Git nên autoUpdate giữ false.
- Không bịa lineRange cho method khi parser không cung cấp.

Dashboard dùng graph tiếng Việt tại `.ua/knowledge-graph.json`.

Dashboard đã tải thành công. Banner về freshness xuất hiện vì project chưa có Git HEAD; SHA256 của cả 94 file đã kiểm khớp snapshot.
