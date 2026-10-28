# Mai Hoa theo nguồn — bàn giao 25/10/2026

## Đã triển khai

Chức năng **Luận Mai Hoa** lập quẻ theo thời điểm hỏi, cho sáu nhóm: nhân sự nói chung, cầu tài, giao dịch, mưu sự, hôn nhân, xuất hành. Mỗi nhóm có năm quan hệ Thể–Dụng dẫn đúng mục nguồn. Không dùng ngày sinh để thay đổi quẻ thời điểm.

- Nguồn: ba quyển *Mai Hoa Dịch Số*, bản chép Wikisource ở revision cố định; kiểm SHA-256 raw và ràng buộc trích đoạn với mục văn bản.
- Lập quẻ: số Tiên Thiên; Y/M/D/H; một hào động từ dưới lên; quái động làm Dụng, quái tĩnh làm Thể.
- Hỗ: lấy 2–3–4 và 3–4–5; nếu quẻ chủ thuần Càn/Khôn thì lấy hỗ từ quẻ biến một lần, theo câu “乾坤無互，互其變卦” của bản nguồn.
- Luận: Dụng ở phần đầu, Thể hỗ/Dụng hỗ ở trung gian, Dụng biến ở phần cuối; giữ Thể gốc để xét sinh/khắc/tỷ hòa. Đối chiếu quẻ/hào từ và lời truyện đã ghim.
- Vượng suy: chỉ gán các hành vượng/suy được đoạn nguồn nêu; không tự điền thêm bảng vượng/tướng/hưu/tù/tử.
- Lưu phiên: SQLite riêng `maihoa_sessions`; đọc lại trả nguyên response đã lưu, không tính lại bằng luật mới. Cùng mã + cùng payload trả cùng kết quả; đổi payload trả 409; retry đồng thời chỉ lưu một phiên.

Quy tắc source profile: `maihoa-ymdh-source-v2`. Rules: `maihoa-source-2026-10-25-v1`. Corpus: `maihoa-wikisource-2026-10-25-v1`.

## Quy ước cần ghi đúng tên

Đầu vào UTC+7 đổi cùng instant sang UTC+8. Ngày âm đổi 00:00 Bắc Kinh, năm chi đổi theo Tết âm; tháng nhuận giữ số tháng. Vượng suy dùng chi tháng tiết khí, ưu tiên nhóm Thìn/Tuất/Sửu/Mùi là tháng Thổ trước phân mùa. Các lựa chọn xác định lịch này được ghi `PRODUCT_CONVENTION`, không gán cho cổ thư như quy định về múi giờ hiện đại.

Tóm tắt “các quan hệ thuận/trở ngại/hỗn hợp” là `PRODUCT_DERIVED`, chỉ đếm sự xuất hiện hai chiều để mô tả. Không phải phép cân trọng số của cổ thư, không thay thứ tự Dụng → Thể hỗ → Dụng hỗ → biến, và không phải kết luận đại cát toàn diện. Vượng suy và cảnh báo hiển thị riêng để không bị tóm tắt che mất.

Ngoại ứng, động tĩnh thực tế, ứng kỳ thành một ngày cụ thể còn cần người luận/ngữ cảnh. Phần tự động không dựng ngoại ứng, không dò từ khóa cát/hung để chấm lời hào, không dự báo số tiền hoặc xác suất thành công. Lời Việt là bản nháp AI **chưa hiệu đính**; hash chứng minh đối chiếu văn bản, không chứng minh nghĩa dịch đúng hoặc dự báo chính xác.

## Tương thích

`IchingRepository.calculate()` vẫn là profile MVP 1 đã khóa, để phát lại các phiên sinh số. `calculate_source()` là profile của chức năng luận mới; khác biệt có chủ đích ở hỗ Càn/Khôn, có version riêng. Không đổi `state_of`, sampling, trọng số bộ số, Bát Tự hoặc điểm ngày MVP 2. Hai profile có cùng quẻ chủ, hào động, Thể–Dụng và quẻ biến cho cùng bốn số.

Phiên sinh số cũ vẫn dùng trace/corpus vốn đã lưu. Giao diện đã sửa cách viết “Quẻ Hỗ”. Tên “Đại cát” của quan hệ MVP 1 không được dùng làm kết luận cầu tài trong chức năng mới.

## Mã và dữ liệu

| Tệp | Vai trò |
| --- | --- |
| `data/reference/maihoa/manifest.json` và ba `.wikitext` | Revision, timestamp, URL và hash nguồn raw |
| `data/reference/maihoa/compiled.json` | 52 trích đoạn đã kiểm nằm trong mục nguồn |
| `config/maihoa_rules.json` | 30 nhánh theo việc, 5 nhánh quan hệ bổ trợ và quy ước lịch |
| `scripts/build_maihoa_data.py` | Build offline, không tải mới/ghi đè nguồn |
| `randomyst/maihoa.py` | Lõi lập quẻ và profile hỗ theo nguồn |
| `randomyst/maihoa_service.py` | Kiểm nguồn, luận theo việc, lưu/đọc phiên độc lập |
| `randomyst/maihoa_models.py` | Request/response, hash và tham chiếu evidence |
| `web/maihoa.js` | Form hỏi việc, bảng quẻ, các phần luận và căn cứ |
| `tests/test_maihoa_consultations.py` | 14 ca kiểm thử mới |

API:

```text
GET  /api/v1/maihoa/rules
POST /api/v1/maihoa/consultations
GET  /api/v1/maihoa/consultations/{request_id}
GET  /api/v1/maihoa/history?limit=10
```

Schema nằm tại `schemas/maihoa_consultation_request.schema.json` và `schemas/maihoa_consultation_response.schema.json`. Không nhận kiểu gieo ba đồng tiền hoặc topic Lục Hào trong API này.

Ví dụ request:

```json
{
  "request_id": "5c018c64-13f7-43fc-89a4-74783898a672",
  "question": "Việc giao dịch mẫu trong tháng tới có những điểm thuận và trở ngại gì?",
  "topic": "TRADE",
  "casting": {"mode": "CUSTOM", "custom_timestamp": "2026-10-25T09:00:00+07:00"}
}
```

## Kiểm chứng

```sh
.venv/bin/python scripts/build_maihoa_data.py
.venv/bin/python -m research_tools.maihoa_source_audit
RANDOMYST_DATABASE=/private/tmp/randomyst_maihoa_test_import.sqlite3 .venv/bin/python -m unittest discover -s tests -v
node --check web/maihoa.js
node --check web/dates.js
node --check web/app.js
```

Toàn bộ **80 tests** đã qua, gồm 14 ca mới. Các ca nguồn cổ kiểm số học Quan Mai/Mẫu Đơn; ca Càn/Khôn kiểm ngoại lệ hỗ; các ca khác kiểm chiều sinh khắc, vị trí Thể trên/dưới, 30 nhánh dẫn nguồn, lỗi nguồn, ranh tiết/giờ/ngày, đọc lại sau restart, đồng thời/idempotency và lịch sử sinh số không đổi.

[Audit nguồn và độ phủ](research/maihoa_source_validation.json) kiểm toàn bộ 51.840 tuple Y/M/D/H, 192 trạng thái quẻ/hào của phép thời gian, và 1.152 bài luận trên đại diện thời gian thực cho sáu topic. Đây là kiểm chứng số học và phần mềm, không phải hiệu đính học thuật hoặc kiểm nghiệm dự báo.

[Kiểm tra giao diện](research/maihoa_ui_validation.json) ghi phạm vi kiểm trên trình duyệt. [Nghiên cứu ngày 24/10](research/iching_casting_interpretation_research.md) và audit cũ giữ nguyên như bằng chứng trước triển khai; hash đầu vào của audit cũ đương nhiên khác source hiện tại. Graph `.ua` cũng là snapshot trước tính năng này; đọc source hiện hành khi sửa.

## Tính năng sau, theo quyết định của người dùng

1. **Lục Hào Nạp Giáp**: corpus/bảng an và bộ luận riêng, có version riêng.
2. **Ba đồng tiền, sáu lượt**: kiểu lập quẻ riêng, cần lưu 0–6 hào động và chính sách đọc tương ứng.

Hai mục được ghi `FUTURE_FEATURE` trong rule summary, chưa có nút hoặc endpoint thực thi. Không tự động nối phần luận Mai Hoa vào điểm chọn ngày; kết nối đó cần một đặc tả riêng nếu phát triển tiếp.
