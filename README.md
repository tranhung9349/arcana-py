# Randomyst Numbers — MVP 2

**28/10/2026 — bản không lưu phiên:** Không đăng nhập, không cookie/localStorage/sessionStorage, không ghi hồ sơ/kết quả vào database. Trang chỉ giữ dữ liệu tạm trong RAM; tải lại/đóng trang sẽ mất. Nút **Xuất PDF** in snapshot kết quả bằng trình duyệt. [Bảo mật và API hiện tại](docs/security_deployment.md) · [Deploy Dokploy](docs/dokploy.md). Các tài liệu bàn giao cũ bên dưới có thể mô tả giai đoạn lưu SQLite; bản public hiện tại đã thay luồng đó.

Ứng dụng local Python/FastAPI. Mỗi phiên trả **một bộ gồm sáu số khác nhau trong 00–99**, sắp tăng dần và giữ hai chữ số. Các phiên độc lập có thể trùng bộ.

Rules **mvp1-logic-2026-10-26-v5** mở bể số từ 00–45 lên 00–99; giữ cách tính hành theo chữ số cuối, trọng số, ngưỡng và luật giải sát. Phiên cũ vẫn trả đúng kết quả đã lưu. [Đặc tả gieo số](docs/logic_plan_mvp1.md).

Rules hiện tại **mvp1-logic-2026-10-26-v6** nâng ngưỡng lên **80**, riêng Đại Hung **85**. Phần “Vì sao là bộ số này?” giải thích trực tiếp phân bố chẵn/lẻ, ngũ hành, quan hệ từng nhóm số với hồ sơ sinh/quẻ và hai thành phần điểm từ phiên đã lưu. “Đọc sâu” dùng hai module luận: Bát Tự giải thích thế lá số, cách cục và lý do chọn Dụng/Hỷ/Kỵ; Mai Hoa dùng chung lõi Thể–Dụng/Hỗ–Biến, vượng suy với chức năng luận riêng. Đã bỏ view “Thời điểm và dữ liệu của phiên”; dữ liệu kiểm chứng vẫn có trong API. [Phạm vi và cách nối module](docs/draw_deep_reading.md).

**Luận Giải Bát Tự** đã có menu, API riêng: nhập hồ sơ sinh, xem Tứ Trụ/tàng can/Thập Thần, gốc khí, nhận định khí thế, ứng viên cách cục, hướng phù ức, gợi ý hàn noãn và quan hệ Can Chi. Có 5 chủ đề và luận thêm trên cùng lá số đang mở. Phần chưa đủ căn cứ giữ kết luận mở; chưa có Đại vận/Lưu niên. [Bàn giao và phạm vi](docs/bazi_module_handoff.md), [kế hoạch gốc](docs/bazi_module_plan.md).

**Luận giải AI:** Bát Tự, Mai Hoa và Lục Hào dùng chung kết nối tương thích OpenAI qua endpoint cấu hình ở backend, model `deepseek-v4.1-flash`. Prompt v4 chọn trọng tâm theo trạng thái đã lưu, chủ đề và mục đích câu hỏi; một trọng tâm và tối đa hai điều kiện đi kèm, chọn trong 24 cặp few-shot. Luận từ snapshot có chữ ký, kiểm schema/dẫn chiếu; không lưu database. [Kết nối, API và phạm vi](docs/ai_readings_handoff.md), [nghiên cứu cách luận](docs/research/masters_reading_dynamic_v4.md), [bộ mẫu](data/interpretation/plain_v4/README.md).

## Tra ngày theo việc — MVP 2

**27/10/2026:** mở một ngày để đọc **Vì sao ngày này được xếp như vậy?** và chọn **Luận giải AI** để nối các căn cứ với việc đã chọn. Có lời giải thích cho cả ngày đẹp, chưa đạt và chưa đủ dữ liệu; phân biệt chỉ xét ngày với chọn giờ. [API, cách lưu kết quả và giới hạn](docs/date_readings_handoff.md).

Đã có API/UI **7 nhóm, 18 việc trọng đại**: hôn nhân; an cư; xây dựng/tu tạo; kinh doanh/tài sản; công danh/học nghiệp; xuất hành; gia tiên/lễ nghi. Chọn nhóm → việc cụ thể → hồ sơ người đứng việc → khoảng ngày, rồi mở popup đánh giá. Thành hôn/nạp thái/đính ước dùng hai hồ sơ; các việc khác một hồ sơ. Tra tối đa **93 ngày**, trong **2024–2030**; hồ sơ sinh dùng **1950–2026**.

**Chín việc xét ngày + giờ**, gồm ba việc cũ và nhập trạch, chuyển cư, tu tạo, giao dịch, nhậm chức, tế lễ. **Chín việc chỉ xét ngày**, gồm nạp thái, đính ước, động thổ, thượng lương, văn khế, mua nhà đất, nạp tài, nhập học, an hương. UI ghi rõ “đã xét ngày; chưa khuyến nghị giờ” và trả khoảng hiệu lực của đánh giá ngày; không suy giờ đẹp từ dữ liệu thiếu.

Ô ngày giữ chiều cao 160px; popup liệt kê đủ giờ theo mẫu **“Giờ Tuất - Từ 18:00 đến 20:00”** hoặc phạm vi đánh giá ngày, cùng lý do tải khi mở thêm. Đóng bằng nút Đóng, Esc hoặc bấm ngoài. Khoảng giờ UTC+7, tên giờ theo lịch Bắc Kinh UTC+8. Nhãn hồ sơ theo vai trò: Gia chủ, Chủ sự kinh doanh, Người xuất hành, Người chủ lễ, hai Đương sự… Kết quả cũ giữ role của lượt tra dù đổi form.

Rules **mvp2-dates-2026-10-25-v2** giữ cách chấm của ba việc cũ; việc mới có scope luật riêng, Sát Chủ/Thọ Tử từ bảng natal chỉ cảnh báo. **Tam Nương chưa bật**. Mỗi hồ sơ dựng lá số một lần/request. Điểm/ngưỡng và scope là policy sản phẩm, chưa được chuyên gia chọn ngày hiệu đính độc lập.

[Bàn giao v2 và kiểm chứng](docs/major_events_handoff.md), [nghiên cứu danh mục](docs/research/mvp2_major_life_events.md), [policy v1](docs/logic_plan_mvp2.md), [corpus/rebuild](data/date_calendar/README.md).

## Chạy

Python 3.10+ (đã chạy trên 3.13.2):

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
./scripts/run_mvp.sh
```

Mở **http://127.0.0.1:8765**. Swagger/ReDoc/OpenAPI public đã tắt.

### Deploy OCI bằng Docker

Đã có Docker multi-stage build Tailwind + FastAPI, Compose không lưu dữ liệu phiên và tùy chọn Caddy HTTPS. Phù hợp Ubuntu 22.04 Minimal ARM64 trên OCI. [Hướng dẫn cài đặt, build, HTTPS và cập nhật](docs/oci_docker.md).

```sh
cp -n .env.production.example .env.production
docker compose up -d --build --wait --wait-timeout 120
```

Mặc định chỉ mở `127.0.0.1:8765`; điền signing key, HTTPS public origin và cấu hình AI nếu dùng trong `.env.production`. File môi trường và lịch sử local không được đưa vào image.

### Build giao diện Tailwind CSS

Giao diện dùng **Tailwind CSS 4.3.3**, build thành CSS tĩnh tại `web/style.css`. File đã build được lưu cùng project, nên chạy FastAPI không cần Node hoặc CDN. Khi sửa HTML, class trong JavaScript hoặc CSS nguồn:

```sh
npm ci
npm run build:css
```

`npm run watch:css` theo dõi thay đổi khi phát triển. Nguồn Tailwind: `web/styles/app.css`; thành phần gothic và form: `web/styles/arcana.css`. Không sửa trực tiếp `web/style.css`. `npm test` chạy bộ kiểm thử frontend.

## Gieo 3 đồng · Lục Hào

Tab mới dùng **3 đồng × 6 lượt**, theo phép tiền thay cỏ thi trong *Bốc Phệ Chính Tông*, đối chiếu *Bốc Phệ Toàn Thư*. Mặt **lưng = 3**, mặt **chữ = 2**; xếp hào từ dưới lên. Tổng 6/9 động, 7/8 tĩnh; giữ đủ 0–6 hào động để lập quẻ chủ và quẻ biến.

Có gieo tự động trên app, nhập kết quả gieo thật, thời điểm hiện tại/tùy chọn, thư viện 64 quẻ với 384 hào từ và lịch sử riêng. Bàn **Nạp Giáp** gồm cung, Thế–Ứng, Lục thân, Lục thú, Tuần Không và Nguyệt Phá.

**Module luận theo việc hỏi** có 8 chủ đề, chọn Dụng thần và đối chiếu các ứng viên, Nhật–Nguyệt, Nguyên/Kỵ/Cừu, hồi đầu sinh/khắc, tiến/thoái, ám động sơ bộ, Phi/Phục và điều kiện ứng kỳ. Lời luận nêu điểm hỗ trợ/cản trở cùng dữ kiện và nguồn cho từng nhận định. Có thể luận lại phiên cũ hoặc chỉ định hào mà không gieo lại. Chưa giải toàn cục tam hợp, mộ tuyệt, mọi chuỗi cứu giải hoặc ấn định ngày sự kiện; không chấm xác suất thành công. [Nghiên cứu](docs/research/liuyao_analysis_research.md), [bàn giao/API](docs/liuyao_analysis_handoff.md). Phần tính và chọn Dụng dùng quy tắc cục bộ; lớp AI mới diễn giải kết quả theo câu hỏi. Nghĩa Việt của kinh văn vẫn là bản nháp có sẵn chưa hiệu đính.

**Chọn chủ đề + nhận diện ý hỏi:** câu hỏi được đối chiếu bằng cụm từ tiếng Việt có/không dấu. App nêu ý nhận diện, tín hiệu, gợi ý đổi chủ đề và hỏi chọn phạm vi khi có nhiều ý hoặc không khớp. Lục thân chỉ định và chủ đề bạn xác nhận được giữ nguyên. Cả phiên mới và luận lại đều có bước này; nhận diện không tạo thêm quẻ. [Kiểm chứng](docs/research/liuyao_intent_validation.json).

API bắt đầu ở `GET /api/v1/coins/hexagrams` và `POST /api/v1/coins/consultations`. [Bàn giao/API](docs/three_coin_handoff.md), [nghiên cứu và quy trình](docs/research/three_coin_liuyao_research.md), [request mẫu](examples/coin_consultation_request.json), [kiểm chứng](docs/research/three_coin_validation.json). Mở lại giữ nguyên snapshot, thử lại cùng UUID không gieo lại; không tác động lịch sử gieo số/Mai Hoa.

Giao diện điền dữ liệu mẫu. Nhập ngày giờ sinh và ngày giờ gieo theo **UTC+7**; chọn hiện tại hoặc thời điểm tùy chọn. Không cần tọa độ hoặc quyền định vị.

## Luồng lịch Trung Quốc UTC+8 — rules v4

1. Kiểm tra năm sinh **1950–2026** và năm gieo **2024–2030** theo ngày giờ đầu vào UTC+7.
2. Giữ nguyên thời điểm thật và chuyển bằng `astimezone(UTC+8)`. Ví dụ `2026-10-11T10:00:00+07:00` → `2026-10-11T11:00:00+08:00`. Không chỉ đổi nhãn timezone; không cộng một giờ lần thứ hai.
3. Truyền các trường Bắc Kinh vào **6tail `lunar-python==1.4.8`**, thư viện cùng họ với `lunar-javascript` trong tinix-bazi. Không tự tính Sóc, tháng nhuận, EoT hay kinh độ Mặt Trời trong runtime.
4. Mai Hoa lấy **Y = getYearZhiIndex()+1**, **M = abs(getMonth())**, **D = getDay()**, **H = getTimeZhiIndex()+1**. Năm âm đổi ở Tết; tháng nhuận giữ số tháng. Ngày âm lịch dân sự đổi lúc **00:00 Bắc Kinh**. Giờ Tý vẫn là 23:00–01:00 Bắc Kinh: lúc 23h, H đổi nhưng Y/M/D chưa sang ngày sau.
5. Bát Tự dùng `getEightChar().setSect(1)`: năm/tháng đổi đúng giao tiết của thư viện; trụ ngày đổi lúc **23:00 Bắc Kinh**. Lấy Thiên Thời và Thiên Đức theo tháng tiết khí của thời điểm gieo trong cùng thư viện.
6. Dụng Thần/ngũ hành vẫn dùng bản Python chuyển logic số học từ tinix-bazi; lấy hành đầu tiên hoặc `override_dung_than`. Kinh văn lấy từ open-iching theo khóa chính xác.
7. Lập quẻ bằng core **Y/M/D/H đã khóa**, rồi sinh/chấm bộ sáu số. Hổ/Biến chỉ hiển thị.

Quyết định v4 thay quy ước lịch Việt Nam/TST ở v3. Adapter cũ được giữ trong `calendar_adapter/` để tái lập nghiên cứu, **không còn được import bởi ứng dụng**. `research_tools/legacy_time_engine.py` cũng chỉ dùng tái lập báo cáo thiên văn cũ.

## Luật sinh số

- β = **2**; xác suất bộ tỉ lệ với tích trọng số khi đã điều kiện hóa theo luật cứng.
- Giữ G_cap, quẻ, ngưỡng và bốn delta suốt tối đa **5 lượt tổng cộng**.
- Điểm bộ = 40% Âm Dương + 60% Ngũ Hành; ngưỡng Đại Cát và các nhóm thường **80**, Đại Hung **85**.
- Chỉ Đại Hung bật giải sát: ×3 hành mục tiêu, quota **3–4**, cấm hành khắc Dụng Thần ngay từ lượt 1.
- Retry từ cấu hình 3–3 đạt ngưỡng khi có nghiệm; Đại Hung còn lọc hành khắc Thể. Hết lượt trả bộ hợp lệ tốt nhất `SUB_OPTIMAL`.

Điểm thể hiện mức phù hợp quy tắc nội bộ, không phải xác suất trúng thưởng hay bằng chứng cải vận.

## API và lịch sử

- `POST /api/v2/auspicious-dates/search`: [ví dụ khai trương](examples/date_search_request.json), [cưới hỏi 93 ngày](examples/marriage_date_search_request.json). Không ghi lịch sử gieo số.
- `GET /api/v2/auspicious-dates/rules`: version, nhóm/registry việc, role, capability, scoring, scope luật và nguồn.
- Schema riêng: [request](schemas/date_search_request.schema.json), [response](schemas/date_search_response.schema.json), [rules](schemas/mvp2_date_rules.schema.json).
- Mỗi ngày có `recommended_windows` chứa đủ khung GOOD theo thời gian (`start_at`, `end_at`, `hour_branch`), kể cả khi `windows` chỉ trả top 3. Chi tiết đầy đủ dùng `include_details=true`.
- Response `date-search-response-v2`: DAY_ONLY dùng `day_periods`/`recommended_day_periods`, `hour_evaluation=NOT_SUPPORTED`, không trả giờ đẹp. Mẫu [nhập trạch](examples/home_entry_date_request.json) và [động thổ chỉ xét ngày](examples/day_only_date_request.json).

```sh
curl --fail http://127.0.0.1:8765/api/v2/auspicious-dates/search \
  -H 'Content-Type: application/json' \
  --data-binary @examples/date_search_request.json
```

- `POST /api/v1/draw`: `examples/draw_request.json`. Trả `draw-response-v2`, đúng một mảng `numbers` sáu chuỗi hai chữ số, trạng thái, điểm, cảnh báo và trace.
- `GET /api/v1/health`: phiên bản quy tắc và provider lịch.
- Các endpoint lịch sử/đọc phiên trên server đã bỏ.
- `POST /api/v1/interpretation`: gửi snapshot DRAW có chữ ký để giải thích, không gieo lại. Xem [định dạng và endpoint stateless](docs/security_deployment.md).

```sh
curl --fail http://127.0.0.1:8765/api/v1/draw \
  -H 'Content-Type: application/json' \
  --data-binary @examples/draw_request.json
```

`CURRENT` chụp `clicked_at` ngay khi bấm; `CUSTOM` dùng `custom_timestamp`. Server không thay mốc gieo, cảnh báo chênh giờ nhận trên 30 giây. Trace hiển thị cả UTC+7, UTC thật và giờ Bắc Kinh UTC+8. Thư viện nhận tới giây; microsecond đầu vào được giữ trong trace.

Các trường `birth.location` và `casting.location` của payload cũ được chấp nhận nếu hợp lệ nhưng **không tham gia tính toán**. Giao diện không gọi GPS/IP; endpoint định vị đã bỏ. Biên sai số đồng hồ chưa cung cấp được ghi `UNDETERMINED`, không giả định thành sai số địa lý/thiên văn.

Bản hiện tại không mở database cá nhân hoặc ghi kết quả. Retry trong trang dùng lại kết quả đã nhận; nếu mất HTTP response trước khi nhận, backend không có bản ghi để phục hồi và lần gieo lại có thể khác.

## Kiểm chứng

```sh
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/compare_bazi_source.py
.venv/bin/python scripts/audit_beijing_calendar.py
.venv/bin/python -m research_tools.validate_interpretation_examples
.venv/bin/python scripts/smoke_mvp.py
.venv/bin/python scripts/smoke_dates.py
.venv/bin/python scripts/smoke_dates.py --cold-marriage-first --output docs/research/mvp2_cold_93_runtime_validation.json
```

Node dùng build CSS và đối chiếu JS gốc; runtime vẫn chạy bằng Python và phục vụ CSS đã build. `requirements-lock.txt` là snapshot môi trường dev, có cả thư viện nghiên cứu lưu trữ; dependency runtime nằm ở `requirements.txt`.

MVP 2 đã qua **66 tests** tổng cộng, gồm danh sách giờ đẹp không bị cắt ở top 3 và clipping theo giờ chọn. HTTP 93 ngày/hai người ở lần đo R5 khoảng **0,91–1,23 giây** trên máy phát triển, chỉ hai lần phân tích lá số. [Báo cáo R5](docs/research/mvp2_runtime_validation.json), [cold 93 ngày riêng](docs/research/mvp2_cold_93_runtime_validation.json) và [kiểm chứng sau thay đổi hiển thị](docs/research/mvp2_display_runtime_validation.json) ghi rõ phạm vi đo. Các smoke script ở giai đoạn SQLite được giữ làm tham chiếu; smoke deployment hiện tại dùng `scripts/smoke_docker.py`, không lưu phiên và không gọi AI; chưa là load test.

Các ca tích hợp kiểm tra chuyển timezone một lần, đủ 12 ranh giờ, nửa đêm/Tết, tháng nhuận, Lập Xuân, biên năm nhập, bỏ ảnh hưởng tọa độ, idempotency phiên v3/v4 và luật sáu số. Ca ngày Tết/tháng nhuận đối chiếu các bảng lịch [HKO 2024](https://www.hko.gov.hk/en/gts/time/calendar/pdf/files/2024e.pdf) và [HKO 2025](https://www.hko.gov.hk/en/gts/time/calendar/pdf/files/2025e.pdf). Đối chiếu với chính 6tail kiểm tra việc tích hợp, không phải nguồn thiên văn độc lập.

Bát Tự đã so 1.000 đầu vào bốn trụ với JS tinix gốc, phủ 10 nhánh Dụng Thần và không sai khác các trường đã so. Kiểm tra này xác nhận bản chuyển mã, không chứng minh mọi lý luận Bát Tự hay lịch toàn dải.

Giao diện có hai tab **Kinh Dịch / Bát Tự**. Kinh Dịch hiển thị nguyên văn Hán cạnh bản nháp nghĩa Việt cho **64 quẻ và 384 hào**, cùng phần diễn giải ngắn. Bản nghĩa Việt do trợ lý AI soạn từ văn bản đã khóa, có nhãn `AI_TRANSLATION`/`AI_INTERPRETATION` và `UNREVIEWED`; không phải bản dịch có sẵn trong repo hay của học giả. Thoán/Tượng truyện giữ nguyên văn Hán; thiếu Thoán truyện quẻ 32 được gắn cờ.

[Nghiên cứu lập và luận quẻ ngày 24/10/2026](docs/research/iching_casting_interpretation_research.md) là bản trước triển khai: so sánh Mai Hoa, ba đồng tiền/thi thảo, đọc quẻ-hào từ và Lục Hào Nạp Giáp; đề xuất luận theo việc trước, nghiên cứu ứng kỳ sau. Có audit số học tái lập.

**Cập nhật 25/10/2026:** đã có tab **Luận Mai Hoa** độc lập: lập quẻ theo giờ hỏi, luận sáu nhóm việc với Thể–Dụng, hỗ/biến, vượng suy và căn cứ từ ba quyển Mai Hoa ghim revision/hash. Hỗ Càn/Khôn dùng profile nguồn mới; phiên sinh số cũ giữ profile đã lưu. Phiên luận đọc lại không tính lại. [Bàn giao, API và giới hạn phần tự động](docs/maihoa_source_handoff.md). **26/10:** ba đồng tiền sáu lượt và bàn Nạp Giáp cơ bản đã triển khai ở tab riêng; luận Lục Hào toàn diện vẫn chưa tự động. Chưa thêm điểm Kinh Dịch vào tra ngày.

Tab Bát Tự trích nguyên văn Việt ngữ từ các bảng `STEM_ESSENCE` và `STRUCTURE_ANALYSIS` của tinix-bazi, theo Nhật Chủ, mùa sinh và cách cục đã tính. Lời dẫn Hán Việt của repo được ghi đúng nhãn; không dựng lại cổ văn Hán. Không nhập lời khuyên sức khỏe/nghề nghiệp. Quẻ Hổ/Biến chỉ có nghĩa quẻ phục vụ xem thêm.

Phần giải thích gieo bộ số nằm ngoài vòng sinh số; có thể tải lại hoặc bấm bộ số trong lịch sử để xem cả phiên cũ. Đọc lại giữ nguyên bộ số, điểm, quẻ, dữ liệu và quy tắc đã lưu. Phần đọc sâu của gieo số vẫn dùng corpus và template cục bộ; dịch vụ LLM mới được nối vào ba chức năng luận Bát Tự/Mai Hoa/Lục Hào riêng.

Mã truy xuất: `randomyst/interpretation.py`. Corpus: `data/interpretation/`. Schema API mới: `schemas/source_explanation.schema.json`. Có thể tái tạo bảng Bát Tự và kiểm ràng buộc bản dịch bằng `.venv/bin/python scripts/build_explanation_data.py`; cần Node ở bước build, runtime chỉ đọc JSON.

Quy tắc: `config/mvp1_rules.json`. Đặc tả: `docs/logic_plan_mvp1.md`. Mã lịch: `randomyst/time_engine.py`. Nguồn: `data/reference/manifest.json`. Báo cáo lần chuyển lịch: `docs/research/beijing_calendar_migration_validation.json`. Bản v3 và bằng chứng lịch cũ được lưu nguyên trạng trong `docs/archive/` và `docs/research/`.
