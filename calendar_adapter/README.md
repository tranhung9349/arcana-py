> **Đã ngừng sử dụng trong ứng dụng từ rules v4 (11/10/2026).** Mã và báo cáo dưới đây chỉ giữ để tái lập nghiên cứu v3. Runtime hiện dùng `randomyst/time_engine.py` + `lunar-python==1.4.8`, lịch Trung Quốc UTC+8; không import adapter này.

# Adapter lịch Việt Nam UTC+7 — bản thử nghiệm

Adapter Python dùng thư viện chuẩn, không phụ thuộc 6tail, `lunardate` hoặc timezone hệ thống. Offset lịch cố định **420 phút**. Công thức thiên văn giản lược và quy tắc lịch tham khảo [Hồ Ngọc Đức](https://honguyenviet.com/amlich/calrules.html); nguồn cũng nêu giới hạn độ chính xác của bản giản lược.

**Lựa chọn triển khai đã chốt ngày 11/10/2026:** người dùng chọn adapter này cho MVP 1. Phiên bản thuật toán được chọn là `hnd-simplified-vn-utc7-v0.1`. Việc chọn adapter không thay kết quả kiểm chứng: trạng thái độ chính xác vẫn là `EXPERIMENTAL` cho đến khi hoàn thành các mục nghiệm thu còn lại. Nguồn EoT và tiết khí chính xác là các thành phần riêng, chưa được chọn bằng quyết định này.

## Chạy thử

Chạy tại thư mục dự án bằng Python 3.10 trở lên:

```sh
python3 -m calendar_adapter date 2026-10-11
```

Kết quả: năm âm 2026, tháng 9, ngày 2, không nhuận; chi năm Ngọ = 7.

Ánh xạ Mai Hoa khi module thời gian đã cung cấp TST:

```sh
python3 -m calendar_adapter maihoa --civil 2024-02-09T23:00:00+07:00 --tst 2024-02-09T23:00:00
```

Ví dụ này **giả định TST đã được tính và bằng giờ đầu vào**. Adapter không tự tính kinh độ/EoT. TST là biểu diễn đồng hồ mặt trời không gắn timezone; thời điểm UTC thật vẫn lấy từ `--civil`. Đến 23h TST, ngày hiệu lực sang 10/02/2024: âm lịch 01/01/2024, nên `Y=5, M=1, D=1, H=1`.

## Giao diện Python

```python
from datetime import date, datetime
from calendar_adapter import LunarDate, VietnameseCalendar, resolve_maihoa

calendar = VietnameseCalendar()
lunar = calendar.to_lunar(date(2004, 3, 21))
assert lunar == LunarDate(2004, 2, 1, True)
assert calendar.to_solar(lunar) == date(2004, 3, 21)

result = resolve_maihoa(
    civil_datetime=datetime.fromisoformat("2030-12-31T23:55:00+07:00"),
    true_solar_datetime=datetime(2031, 1, 1, 0, 5),
    kind="casting",
)
```

- `to_lunar(date)` trả `LunarDate(year, month, day, is_leap_month)`.
- `to_solar(LunarDate)` trả ngày dương; từ chối tháng nhuận không tồn tại hoặc ngày 30 trong tháng 29 ngày.
- `describe(date)` trả JSON chứa nguồn, phiên bản, offset và trạng thái thử nghiệm.
- `resolve_maihoa(civil_datetime, true_solar_datetime, kind)` kiểm tra biên đầu vào trước hiệu chỉnh, chuyển đồng bộ Y/M/D theo `date(TST + 1 giờ)`, lấy H từ TST chưa dịch. `kind` là `birth` hoặc `casting`.

Phạm vi tra cứu nội bộ: **01/12/1949–31/01/2031**. Phạm vi đầu vào: sinh **1950–2026**, gieo **2024–2030**, theo giờ đồng hồ có offset `+07:00`. Không đổi quy tắc này thành giờ hành chính lịch sử bằng tên zone IANA.

Các lỗi có `CalendarError.code`; CLI trả `success=false`, `error_code` và mã thoát 2. Không ép ngày vượt biên về năm cũ. Kiểm tra TST đầu vào dùng một khoảng độ dịch rộng tương ứng kinh độ hợp lệ và EoT dưới 30 phút để bắt lỗi truyền nhầm ngày/năm; đây không phải độ chính xác thiên văn hoặc vùng cảnh báo giáp ranh.

## Kiểm tra đã chạy

```sh
python3 -m unittest discover -s tests -v
python3 -m calendar_adapter.audit --nasa-1901 docs/research/calendar_sources/nasa-phases1901.html --nasa-2001 docs/research/calendar_sources/nasa-phases2001.html --output docs/research/calendar_adapter_trial.json
```

Kết quả lần thử 11/10/2026:

| Kiểm tra | Kết quả |
|---|---|
| Ca kiểm thử tháng nhuận, giờ Tý, Tết, kiểu dữ liệu và biên | 12/12 qua |
| Đổi hai chiều và kiểm tra nối ngày/tháng trong vùng nội bộ | 29.647 ngày, không lỗi |
| Ngày Sóc từ bảng NASA sau quy đổi UT + 7 giờ | 1.004/1.004 khớp ngày đầu tháng |
| Ngày Sóc khác nhau giữa UTC+7 và UTC+8 trong tập trên | 32 sự kiện |
| Chênh lệch thời điểm Sóc lớn nhất quan sát được so với bảng | Khoảng 3,5127 phút |
| Sóc trong vòng 5 phút quanh nửa đêm của bảng tham chiếu | 6 ca cần xem xét thêm |

Bảng nguồn: [1901–2000](https://eclipse.gsfc.nasa.gov/phase/phases1901.html), [2001–2100](https://eclipse.gsfc.nasa.gov/phase/phases2001.html), tính bởi **Fred Espenak, GSFC Planetary Systems Laboratory**. Bản tải được lưu cùng SHA-256 trong báo cáo. Phép kiểm tra chỉ dùng cột New Moon; parser kiểm tra mỗi thế kỷ đủ 100 năm, mỗi năm 12 hoặc 13 Sóc, thứ tự và trùng lặp.

Các bảng ghi **UT**, có độ phân giải phút và mô hình ΔT; không mặc định chúng là thời điểm UTC chính xác đến giây. Cả hai họ công thức có tham khảo Meeus, nên đây là đối chiếu với dữ liệu công bố bên ngoài, không phải phép đo vật lý độc lập hoàn toàn. Cửa sổ 5 phút trong báo cáo chỉ ưu tiên xem xét nguồn tham chiếu, không dịch thời gian hoặc thay quy tắc gieo.

## Giới hạn để ghép vào hệ thống

Trạng thái trả về vẫn là `EXPERIMENTAL`, biên sai số thiên văn là `null`. Khớp ngày Sóc và đổi hai chiều chưa chứng minh mọi nhãn năm/tháng/nhuận đúng theo corpus Việt Nam độc lập. Cực đại sai số quan sát được không phải biên sai số được bảo đảm.

Adapter chưa cung cấp nguồn tiết khí chính xác, thời điểm Lập Xuân, EoT, định vị, độ bất định TST, lập bốn trụ hay phân tích Dụng Thần. Hàm chia kinh độ Mặt Trời thành 12 cung chỉ phục vụ quy tắc tháng/nhuận giản lược. Khi ghép Bát Tự, vẫn cần provider tiết khí theo thời điểm UTC thật và adapter riêng cho bốn trụ; không dùng hàm này như bộ tính Lập Xuân đến giây.
