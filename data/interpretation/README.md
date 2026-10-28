# Corpus hiển thị v1

Bộ mẫu prompt mới: `plain_v2/README.md` (17 cặp mẫu + 8 ca đánh giá), đã nối lớp AI của Bát Tự/Mai Hoa/Lục Hào. Không thay các corpus hiển thị của phần gieo số bên dưới.

- `iching_vi_draft.json`: nghĩa quẻ từ, 384 hào và tổng quan 64 quẻ do trợ lý AI soạn trực tiếp từ văn bản open-iching đã khóa. Nhãn AI_TRANSLATION/AI_INTERPRETATION; chưa được chuyên gia hiệu đính. Không phải bản dịch từ tinix-bazi hay một học giả.
- `tinix_vi.json`: giữ nguyên bảng Nhật Chủ (10 can × 4 mùa, verse/detail) và 13 cách cục từ tinix-bazi. Nhãn SOURCE_ORIGINAL chỉ xác nhận nguồn repo. Không cung cấp bản chữ Hán của Địch Thiên Tủy/Tử Bình.
- Mỗi nghĩa Việt quẻ/hào ràng buộc SHA-256 của đúng nguyên văn và vị trí. Runtime từ chối corpus khác commit hoặc khác text hash. URL dẫn tới file tại commit đã khóa.
- Thoán truyện và Tượng truyện hiện chỉ có nguyên văn Hán. Không dựng bản dịch để lấp nguồn thiếu.
- `scripts/build_explanation_data.py` kiểm manifest raw, build bảng tinix bằng Node rồi gắn/kiểm hash bản dịch. Node không thuộc runtime Python. Sau khi hiệu đính bản nghĩa Việt cần tăng corpus version và lưu người/nguồn review trước khi đổi trạng thái.

Module này đọc phiên đã lưu; không tham gia chọn số, G_cap, trọng số, quota, số lượt hay đổi quy tắc lịch. Tập kiểm thử kiểm chứng việc khớp dữ liệu, không chứng nhận ngữ nghĩa dịch thuật.
