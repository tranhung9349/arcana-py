# Corpus lịch cho MVP 2

`almanac_2024_2030.json.gz` giữ **toàn bộ mảng Yi/Ji nguyên văn theo ngày và giờ**, không chỉ token của ba việc v1, và không chứa kết luận ngày đẹp. Provider là `lunar-python==1.4.8`; manifest khóa hash corpus, nội dung giải nén và ba module nguồn. V2 dùng lại đúng corpus/hash này cho [7 nhóm/18 việc](../../docs/major_events_handoff.md), không thu thập lại lịch.

- Phạm vi truy vấn công khai: 01/01/2024–31/12/2030 theo UTC+7.
- 2.558 ngày dân sự Bắc Kinh: 01/01/2024–01/01/2031. Ngày đệm cuối dùng cho giờ Việt Nam 23:00–24:00 của 31/12/2030.
- 33.254 bản ghi giờ: 13 mốc/ngày Bắc Kinh tại 00h, 01h, 03h…23h; hai mốc giờ Tý đầu/cuối ngày khác nhau.
- 100 mốc tiết `Jie` duy nhất, có đệm để chia khung tại ranh tháng/năm Bát Tự.
- Map việc v1: `嫁娶` → cưới hỏi; `开市` → khai trương; `出行` → xuất hành.

Mỗi ngày giữ `lunar`, `day_gan_zhi`, `month_gan_zhi`, `year_gan_zhi`, `day_officer`, `tian_shen`, `tian_shen_type`, `yi`, `ji`, `hours`. Mỗi giờ giữ mốc Bắc Kinh, chi giờ và mảng nên/kỵ. Xem tên trường thực tế trong corpus; không dùng lịch âm số tháng để thay cho chi tháng tiết khí.

```sh
.venv/bin/python scripts/build_date_data.py
.venv/bin/python -m unittest discover -s tests -p test_auspicious_dates.py -v
```

Builder kiểm version provider và hash `shensha.js` tinix trước khi số hóa. JSON canonical và gzip `mtime=0` cho kết quả tái lập. Builder đồng thời xuất config luật và ba JSON Schema; sửa rule/scoring lâu dài tại builder rồi build lại, tránh sửa config và bị ghi đè ở lần build sau.

Runtime đọc và kiểm hash một lần lúc khởi tạo engine. Ngày/giờ Yi/Ji đọc từ corpus; trụ ứng viên vẫn lấy exact bằng provider ở đầu từng khung. Trụ sinh và Dụng/Hỷ/Kỵ chỉ dựng một lần/chủ thể/request.

`无` là không có mục; `诸事不宜` là nên tránh; `馀事勿取`/`余事勿取` chỉ cho việc đã ghi nên. Việc xuất hiện đồng thời nên/kỵ hoặc được ghi nên cùng `诸事不宜` trả `UNRESOLVED`. Dữ liệu thô luôn được giữ để kiểm tra.

Sát Chủ, Thọ Tử, Nguyệt Phá lấy bảng natal đã ghim từ tinix, nhưng dùng **chi tháng ứng viên exact và chi ngày sect 1** theo quyết định sản phẩm. Ba việc cũ giữ BLOCK v1. Việc mới dùng Sát Chủ/Thọ Tử làm WARN; Nguyệt Phá BLOCK cho profile kiến tạo, WARN cho hai nghi lễ gia tiên/an hương. Hash nguồn xác nhận việc sao chép bảng; không xác nhận đây là phương pháp chọn ngày cổ truyền độc lập. Tam Nương chưa được bật.

Nguồn: [6tail/lunar-python](https://github.com/6tail/lunar-python), [tinix shensha.js ở commit đã ghim](https://github.com/vhphuoc1102/tinix-bazi/blob/80ff4463d0397c1b11db76f38d880255f55558bc/backendjs/src/bazi/shensha.js).
