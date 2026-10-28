# Tra ngày theo việc trọng đại — bàn giao 25/10/2026

Đã triển khai **7 nhóm, 18 việc chính** trong bản local. Chọn nhóm → việc cụ thể → nhập hồ sơ người đứng việc → tra ngày → mở popup đánh giá. Rules `mvp2-dates-2026-10-25-v2`, registry `major-events-2026-10-25-v2`, response `date-search-response-v2`, app `0.5.0`.

## Phạm vi đang bật

| Nhóm | Việc | Chế độ |
| --- | --- | --- |
| Hôn nhân, gia thất | Thành hôn | Ngày và giờ, giữ gate v1 |
| Hôn nhân, gia thất | Nạp thái — lễ ngỏ lời; đính ước | Chỉ xét ngày, hai hồ sơ |
| An cư, chỗ ở | Nhập trạch; chuyển nơi cư trú | Ngày và giờ |
| Xây dựng, tu tạo | Tu tạo, sửa chữa lớn | Ngày và giờ |
| Xây dựng, tu tạo | Động thổ; thượng lương | Chỉ xét ngày |
| Kinh doanh, tài sản | Khai trương | Ngày và giờ, giữ gate v1 |
| Kinh doanh, tài sản | Giao dịch tài sản lớn | Ngày và giờ |
| Kinh doanh, tài sản | Lập văn khế; mua nhà đất; nạp tài | Chỉ xét ngày |
| Công danh, học nghiệp | Nhậm chức, nhận nhiệm vụ | Ngày và giờ |
| Công danh, học nghiệp | Nhập học | Chỉ xét ngày |
| Xuất hành trọng yếu | Xuất hành | Ngày và giờ, giữ gate v1 |
| Gia tiên, lễ nghi | Tế lễ gia tiên | Ngày và giờ |
| Gia tiên, lễ nghi | An hương | Chỉ xét ngày |

Tổng **9 việc xét ngày + giờ / 9 việc chỉ xét ngày**. Thành hôn, nạp thái và đính ước cần hai đương sự; các việc khác cần một hồ sơ đúng vai trò. Khai trương gọi **Chủ sự kinh doanh**, nhập trạch gọi **Gia chủ**, các việc khác dùng vai trò tương ứng. Không dùng người đăng nhập/người thao tác thay thế người đứng việc.

An sàng, tháo dỡ và cầu phúc giữ trong registry với `enabled=false`, không xuất hiện trong picker và API tra trả 422. Tang sự/phần mộ, điều trị/sinh nở giữ ngoài tính năng này.

## Quyết định sau bản nghiên cứu

[Nghiên cứu và số đếm](research/mvp2_major_life_events.md) được giữ làm lịch sử. Khi triển khai, giải quyết các mục chưa có mapping giờ bằng **DAY_ONLY**: nạp thái giữ `纳采`, đính ước giữ `订盟`, không thay bằng `订婚`; nạp tài giữ `纳财`, không dùng giờ `求财`. Nhãn nạp thái chưa đại diện mọi hình thức ăn hỏi Việt Nam. An hương giữ tên/phạm vi nghi thức an hương; không mở rộng kết luận sang mọi việc lập/chuyển bàn thờ.

Các mốc nhà đất, văn khế, nhận nhiệm vụ và nhập học được giới hạn trong mô tả của registry. Không suy ngày ký hợp tác/lao động từ văn khế mua bán; không suy lịch thi từ nhập học. Phương vị, bố trí nhà/đất/thờ tự chưa được tính. Những giới hạn giúp xác định việc người dùng đang chọn, được ghi ngay cạnh lựa chọn.

Registry và các profile mới là **quyết định sản phẩm**, `review_status=PRODUCT_POLICY`. Kiểm thử phần mềm, hash nguồn và token trực tiếp không phải hiệu đính chuyên môn hoặc xác nhận hiệu quả dự đoán.

## Bộ luật v2

| Profile | Sát Chủ / Thọ Tử từ bảng natal | Nguyệt Phá | Gate việc |
| --- | --- | --- | --- |
| `LEGACY_V1` — ba việc cũ | BLOCK, giữ nguyên | BLOCK, giữ nguyên | Giữ gate/điểm v1 |
| `CONSTRUCTIVE_V2` — 13 việc mới | WARN | BLOCK theo policy kiến tạo | Ngày phải hỗ trợ; nếu xét giờ thì giờ cũng phải hỗ trợ trực tiếp |
| `RITUAL_V2` — tế lễ, an hương | WARN | WARN | Yi/Ji và cá nhân vẫn quyết định trong phạm vi đã chọn |

Các penalty lịch chung kế thừa v1; kỵ việc trực tiếp/kỵ chung và xung cá nhân vẫn chặn. Cát điểm không bù hard block. Dữ liệu mâu thuẫn hoặc hồ sơ sinh bất ổn trả `UNRESOLVED`, không đổi thành ngày thường để tăng số kết quả. Tam Nương tiếp tục tắt. Tất cả các scope nằm trong config được builder tái tạo; không bê nguyên ba luật cấm natal sang 15 việc mới.

`DAY_ONLY` dùng **Can và Chi trụ ngày**, bỏ cả hai yếu tố trụ giờ. Base 100, ngưỡng GOOD **80**, NORMAL **50**; các mức phạt hành vẫn 0/2/5/10, lấy chủ thể có tổng phạt lớn nhất. Đây là ngưỡng sản phẩm riêng cho hai yếu tố thay vì bốn. GOOD cần Yi ngày hỗ trợ, mọi chủ thể `SUPPORTED` và không bị loại; `NOT_LISTED` không tự trở thành bằng chứng nên làm.

`DAY_AND_HOUR` dùng base/ngưỡng 100/75/45 và bốn yếu tố v1. Với sáu việc mới ở chế độ này, `hour_activity_status=SUPPORTED` là gate bắt buộc. Với ba việc cũ, gate v1 vẫn được giữ để không đổi kết quả trước đó.

## Ngày và giờ tách trong contract

Endpoint giữ `POST /api/v2/auspicious-dates/search`; request cũ còn hợp lệ. Response đã sang **v2**, cập nhật schema đi kèm cho client kiểm cấu trúc nghiêm ngặt.

- `GET .../rules` trả bảy `groups`, registry có cờ bật/tắt, vai trò, mốc hành động, scope, mode và profile luật. Dropdown lấy các mục bật từ API.
- Response có `activity_spec` chụp đúng phạm vi/role đã đánh giá, `activity_registry_version`, `evaluation_mode` và `evaluated_periods`.
- Ngày + giờ: giữ `windows` top 3 khi tóm tắt, `recommended_windows` đủ mọi khung GOOD theo thời gian. `hour_evaluation` phân biệt `HAS_RECOMMENDATIONS` và `EVALUATED_NO_MATCH`.
- Chỉ xét ngày: `windows=[]`, `recommended_windows=[]`, `recommended_minutes=0`, `hour_evaluation=NOT_SUPPORTED`; trả `day_periods` và mọi `recommended_day_periods`. Không có `hour_branch`, `hour_activity_status` hay dữ liệu Yi/Ji giờ trong đánh giá ngày.
- Ngày bị lọc thứ trong tuần dùng `NOT_EVALUATED`, không nhầm với thiếu capability giờ.
- DAY_ONLY không nhận bộ lọc giờ khác toàn ngày; API trả 422 thay vì bỏ qua âm thầm. UI ẩn và vô hiệu hóa các trường giờ, không gửi bộ lọc này.

Phạm vi đánh giá ngày cắt ở **22h UTC+7** (ngày Bát Tự sect 1), **23h** (ngày dân sự Bắc Kinh), đúng giây giao Jie và hai đầu ngày. Không lấy 12h làm giờ đại diện, không cắt theo mọi chi giờ. Popup gọi đây là **khoảng hiệu lực đánh giá ngày**, không là giờ đẹp. Không gộp qua ranh lịch; giữ giây lẻ và 24:00 ở cuối ngày.

Giới hạn vẫn 2024–2030, tối đa 93 ngày; sinh 1950–2026. Dựng natal đúng một lần/người/request, dùng chung corpus đã kiểm hash. Ngày + giờ 93 ngày có 1.212 khung trong fixture qua Jie; chỉ xét ngày có 282 đoạn. Không gọi gieo số, Mai Hoa hoặc ghi lịch sử cho việc tra ngày.

## Tệp và chạy lại

- Registry: [date_activities.py](../randomyst/date_activities.py).
- Builder: [build_date_data.py](../scripts/build_date_data.py); config: [mvp2_date_rules.json](../config/mvp2_date_rules.json).
- Contract/engine: [date_models.py](../randomyst/date_models.py), [date_calendar.py](../randomyst/date_calendar.py), [date_engine.py](../randomyst/date_engine.py).
- UI: [dates.js](../web/dates.js), [index.html](../web/index.html), [style.css](../web/style.css).
- Mẫu nhập trạch: [request](../examples/home_entry_date_request.json), [response](../examples/home_entry_date_response.json).
- Mẫu chỉ xét ngày: [request](../examples/day_only_date_request.json), [response](../examples/day_only_date_response.json).

```sh
.venv/bin/python scripts/build_date_data.py
RANDOMYST_DATABASE=/private/tmp/randomyst_date_test_import.sqlite3 .venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/smoke_major_dates.py --base-url http://127.0.0.1:8766
.venv/bin/python scripts/smoke_dates.py --cold-marriage-first --output docs/research/mvp2_major_events_cold_validation.json
node --check web/dates.js
```

Builder vẫn tái tạo đúng corpus cũ, SHA256 **a046dbf8187bd7bd6b8e3208118f6b584f5d9f3541e663422d69c30ff586ef28**. Không thu thập lại hoặc thay provider.

## Bằng chứng kiểm chứng

- **93 tests PASS**, gồm 13 test mới cho registry, tất cả việc bật, schema, gate giờ trực tiếp, scope luật, trụ ngày độc lập trụ giờ, ranh Jie/nửa đêm, hai người/93 ngày, giữ đủ đoạn tóm tắt, mâu thuẫn và API không có tác dụng phụ.
- [HTTP 29 ca](research/mvp2_major_events_runtime_validation.json): đủ 18 việc, lượt 93 ngày, padding cuối 2030, phản hồi/schema, lặp xác định và lỗi capability. Thời gian lớn nhất trong các ca đã đo khoảng **0,995 giây**.
- Sáu response v1 đầy đủ được chụp vào file tạm trước khi sửa, sau đó đối chiếu mọi điểm, grade, loại trừ và giờ/đoạn gợi ý: **khớp**. Chỉ tên hiển thị/metadata v2 thay đổi; file tạm không là fixture dài hạn của repo.
- [Tiến trình lạnh riêng](research/mvp2_major_events_cold_validation.json): lượt cưới hỏi 93 ngày đầu **0,902 giây**, 1.212 khung/2.424 đối chiếu; natal hai lần. Đây là đo trên máy phát triển, chưa là P95 hay kiểm tải.
- [Kiểm UI](research/mvp2_major_events_ui_validation.json): bảy nhóm/18 mục, một/hai role, ẩn/vô hiệu hóa giờ, kết quả cũ giữ role khi đổi form, popup ngày/giờ, Esc trả focus, card 160px và không tràn ngang ở viewport tự nhiên 686×979. Không mô phỏng lỗi mạng hoặc riêng viewport 390px.

UI dùng dữ liệu mẫu 1994/1990. Ca có kết quả GOOD trong ảnh nhập trạch/động thổ dùng Dụng Thần nhập đè Thổ để kiểm nhãn và popup; đây là fixture phần mềm.

Ảnh: [danh mục](research/mvp2_major_event_groups_ui.jpg), [card nhập trạch](research/mvp2_major_events_ui.jpg), [popup chỉ xét ngày](research/mvp2_major_events_day_only_ui.jpg).
