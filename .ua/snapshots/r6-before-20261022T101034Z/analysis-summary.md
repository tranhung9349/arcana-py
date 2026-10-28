# Kết quả refresh knowledge graph — R5

Ứng dụng local Python/FastAPI gồm gieo sáu số theo MVP 1 và tra ngày/khung giờ cho cưới hỏi, khai trương, xuất hành theo hồ sơ sinh trong MVP 2. Runtime dùng lịch Bắc Kinh UTC+8, corpus Yi/Ji đã ghim và policy sản phẩm v1.

Đã phủ **123/123 tệp**, dựng **382 node**, **1245 cạnh**, **10 tầng** và **15 bước tour**. Core schema, inventory, 71 imports, tham chiếu, phân tầng, source snapshot và fingerprint đều pass. Không có issue; hai warning orphan thuộc package initializer rỗng.

## File theo loại

- code: 49
- config: 49
- docs: 20
- infra: 0
- data: 0
- script: 1
- markup: 4

## Node theo loại

- file: 53
- class: 57
- function: 176
- table: 1
- config: 43
- document: 20
- schema: 14
- concept: 6
- module: 3
- endpoint: 8
- resource: 1

## Cạnh theo loại

- imports: 71
- contains: 326
- exports: 159
- tested_by: 19
- configures: 12
- reads_from: 39
- writes_to: 26
- calls: 108
- related: 185
- depends_on: 96
- inherits: 27
- documents: 129
- defines_schema: 21
- validates: 27

## Các tầng

- Giao diện gieo và tra ngày: 4 node file-level
- API cục bộ và SQLite: 13 node file-level
- Lịch Bắc Kinh, Bát Tự và Mai Hoa: 3 node file-level
- Điều phối gieo, trọng số và nghiệm thu: 2 node file-level
- Tra ngày theo việc và hồ sơ: 12 node file-level
- Giải thích chỉ đọc và hợp đồng LLM: 21 node file-level
- Hai nguồn tham chiếu đã ghim: 12 node file-level
- Luật, tài liệu và môi trường chạy: 12 node file-level
- Kiểm thử, thí nghiệm và bằng chứng: 37 node file-level
- Lịch Việt, vị trí và nghiên cứu lưu trữ: 24 node file-level

## Guided tour

1. Tổng quan ứng dụng
2. Điểm vào API
3. Hợp đồng hai luồng
4. Lịch và lá số
5. Gieo bộ sáu số
6. Lưu phiên, đọc lời giải
7. Corpus và ranh ngày
8. Luật ứng viên v1
9. Dựng hồ sơ một lần
10. Gate trước điểm số
11. Lịch và chi tiết giờ
12. Kiểm thử và HTTP
13. Phạm vi bằng chứng
14. Ranh giới bản lưu
15. Hợp đồng LLM dự kiến

## Phạm vi và giới hạn

- Không có Git; giữ ngôn ngữ Việt, autoUpdate=false và snapshot SHA256 để xác định freshness.
- Tái dùng phân tích của 89 tệp có hash không đổi; phân tích lại 29 tệp mới và 5 tệp sửa.
- Parser không cung cấp mọi method/range trong Python hoặc function trong JavaScript IIFE; không bịa range. Markup và gzip được đọc source/metadata, corpus chỉ giữ metadata trong graph.
- Hai initializer rỗng không có quan hệ; đây là warning không chặn lưu graph.
- Tam Nương tắt; áp bảng Sát Chủ/Thọ Tử vào tháng ứng viên và điểm/ngưỡng là policy v1 chưa được chuyên gia hiệu đính độc lập.
- Không mở lại dashboard trong refresh này. Kết quả chi tiết ở validation-report.json; bản cũ được giữ trong snapshots/r5-before-20261012T125758Z/.

Graph: .ua/knowledge-graph.json. Snapshot: 4434be3a79bba589cdd293665257a536c50bb21c7abcd53f1358511564a659ec.
