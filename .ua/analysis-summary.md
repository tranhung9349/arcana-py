# Kết quả dựng lại knowledge graph — R6 (full)

Ứng dụng local Python/FastAPI gồm gieo sáu số theo MVP 1 và tra ngày/khung giờ cho cưới hỏi, khai trương, xuất hành theo hồ sơ sinh trong MVP 2, có popup liệt kê đủ khung giờ đẹp từ `recommended_windows`. Runtime dùng lịch Bắc Kinh UTC+8, corpus Yi/Ji đã ghim và policy sản phẩm v1.

Đã phủ **129/129 tệp**, dựng **328 node**, **972 cạnh**, **10 tầng** và **15 bước tour**. Kiểm định không có issue; hai warning orphan thuộc package initializer rỗng.

## File theo loại

- docs: 21
- code: 50
- config: 53
- markup: 4
- script: 1

## Node theo loại

- file: 54
- function: 108
- class: 57
- document: 21
- config: 47
- schema: 31
- resource: 1
- endpoint: 8
- table: 1

## Cạnh theo loại

- contains: 199
- exports: 149
- imports: 73
- calls: 138
- tested_by: 20
- inherits: 28
- depends_on: 30
- documents: 81
- related: 185
- configures: 21
- defines_schema: 34
- validates: 7
- writes_to: 2
- reads_from: 4
- serves: 1

## Các tầng

- Giao diện gieo và tra ngày: 4 node file-level
- API cục bộ và SQLite: 12 node file-level
- Lịch Bắc Kinh, Bát Tự và Mai Hoa: 3 node file-level
- Điều phối gieo, trọng số và nghiệm thu: 2 node file-level
- Tra ngày theo việc và hồ sơ: 27 node file-level
- Giải thích chỉ đọc và hợp đồng LLM: 23 node file-level
- Hai nguồn tham chiếu đã ghim: 12 node file-level
- Luật, tài liệu và môi trường chạy: 13 node file-level
- Kiểm thử, thí nghiệm và bằng chứng: 47 node file-level
- Lịch Việt, vị trí và nghiên cứu lưu trữ: 20 node file-level

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
13. Mở rộng 23 việc
14. Ranh giới bản lưu
15. Hợp đồng LLM dự kiến

## Thay đổi so với R5

- Dựng lại toàn bộ bằng `--full`, không tái dùng phân tích R5. Thêm 6 tệp mới: nghiên cứu 23 category (`docs/research/mvp2_activity_expansion.md`, `mvp2_activity_token_coverage.json`, `research_tools/audit_activity_categories.py`) và ba báo cáo kiểm chứng hiển thị/popup.
- Phân tích lại 12 tệp đã đổi, trong đó có `randomyst/date_engine.py`, `date_models.py`, `web/dates.js`, `index.html`, `style.css`, schema/ví dụ response tra ngày: graph nay có `RecommendedWindow`, `recommended_windows` và `hour_branch`.
- Có 8 node endpoint của `randomyst/api.py` và bảng SQLite `draws`. Không dựng lại các node concept/module do LLM tổng hợp của R5 (6 concept, 3 module).

## Phạm vi và giới hạn

- Không có Git; giữ ngôn ngữ Việt, autoUpdate=false và snapshot SHA256 để xác định freshness.
- Parser không cung cấp mọi method/range trong Python hoặc function trong JavaScript IIFE; 4 function của `web/dates.js` lấy range đọc từ source. Markup, requirements và gzip được đọc source/metadata; corpus chỉ giữ metadata.
- Tam Nương tắt; áp bảng Sát Chủ/Thọ Tử vào tháng ứng viên và điểm/ngưỡng là policy v1 chưa được chuyên gia hiệu đính độc lập.
- Bản R5 được giữ trong `snapshots/` để phục hồi. Kết quả chi tiết ở validation-report.json.

Graph: .ua/knowledge-graph.json. Snapshot: 92d7ff560aa82fb8086490e1c4ac19ad31fa032ae21764e54b82f6c5ac87e77b.
