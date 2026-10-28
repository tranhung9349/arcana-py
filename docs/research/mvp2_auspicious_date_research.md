# Nghiên cứu chọn ngày MVP 2

Ngày: **12/10/2026**. Provider khảo sát: **lunar-python 1.4.8**, đúng phiên bản đang dùng trong MVP 1.

## Kết luận khả thi

Có thể xây tính năng chọn ngày theo việc trên nền hiện có. Provider đã cung cấp Can Chi, Thiên Thần/Hoàng-Hắc Đạo, Trực, Yi/Ji ngày và giờ, danh sách cát/hung thần. Logic Bát Tự hiện có đủ dữ liệu để xây lớp đối chiếu chủ thể.

Đề xuất ba bộ lọc của người dùng giúp tổ chức tầng ngày chung. Tuy nhiên cần giữ riêng nhãn lịch, nhãn kết quả theo việc, và kết quả cá nhân hóa. Phần khó chủ yếu là **quy ước và nguồn của luật**, chưa thấy cần đổi stack hoặc thêm dịch vụ lịch.

Kế hoạch: [logic_plan_mvp2.md](../logic_plan_mvp2.md). Bằng chứng máy đọc: [mvp2_auspicious_date_feasibility.json](mvp2_auspicious_date_feasibility.json).

## Những gì đã chạy

```sh
.venv/bin/python -m research_tools.auspicious_date_audit
```

Script khảo sát độ phủ tại **12h UTC+7 mỗi ngày**, không chấm ngày, không đọc/ghi lịch sử hoặc sinh số. Nó lưu hash code provider và nguồn tinix, kiểm ranh 22h/23h, giao Hàn Lộ, phạm vi cuối 2030, hai hệ 12 mục và ba bảng tinix đủ 12 hàng.

| Token việc | Có ở nên, không ở kỵ | Có ở kỵ, không ở nên | Cả hai | Không đề cập |
|---|---:|---:|---:|---:|
| Cưới `嫁娶` | 887 | 967 | 0 | 703 |
| Khai trương `开市` | 560 | 737 | 0 | 1.260 |
| Xuất hành `出行` | 867 | 328 | 0 | 1.362 |

Mỗi hàng cộng đủ **2.557 ngày** trong 2024–2030. Số ngày có token “nên” không phải số ngày sẽ được khuyến nghị sau khi xét cá nhân, giờ và ngày kỵ. Không có mâu thuẫn token chính trong mẫu này không cho phép bỏ handler mâu thuẫn nguồn.

Các mục đặc biệt xuất hiện trong mẫu:

| Mục | Cột nên | Cột kỵ |
|---|---:|---:|
| `馀事勿取` | 613 | 9 |
| `诸事不宜` | 23 | 166 |
| `无` | 1 | 99 |

Có ngày `诸事不宜` nằm cạnh một hoạt động cụ thể ở cột nên. Vì vậy không dùng phép kiểm “token nằm trong list” cho toàn bộ semantics và không hiểu `无` thành thuận mọi việc.

## Hai phát hiện cần khóa trước khi lập trình

**12 Thiên Thần khác 12 Trực.** Trong code provider, Thiên Thần là chu kỳ Thanh Long…Câu Trần có offset theo chi tháng. Trực là Kiến…Bế tính từ hiệu chi ngày/tháng. Mảng tên static chỉ là dữ liệu, vẫn cần phép tra đúng tháng. Bằng chứng triển khai: code cài đặt được ghim/hash trong JSON; nguồn upstream tham khảo là [Lunar.py](https://github.com/6tail/lunar-python/blob/master/lunar_python/Lunar.py) và [LunarUtil.py](https://github.com/6tail/lunar-python/blob/master/lunar_python/util/LunarUtil.py). Các link master không thay thế hash bản 1.4.8 đã khảo sát.

**Quy ước tháng khác nhau cho kết quả khác nhau.** `getMonthZhi()` dùng tháng theo ngày chứa tiết, `getMonthZhiExact()` dùng đúng instant tiết; cả hai khác số tháng âm. `getDayYi(sect=1)` dùng month không exact và ngày dân sự; sect 2 chỉ đổi month sang exact, không đổi day sang ngày Bát Tự 23h. Tầng cá nhân hiện dùng EightChar sect 1. Không đổi tham số theo tên sect mà mặc định nó có cùng ý nghĩa ở hai API.

## Đối chiếu các link người dùng đưa

Đã đọc trực tiếp ngày 12/10/2026. Đây là tài liệu tham khảo quan niệm và các ví dụ lịch; chưa phải một đặc tả thống nhất đủ bảng/phiên bản để triển khai toàn bộ luật.

- [Chinese Culture Studio](https://www.culture-of-china.com/guide/auspicious-dates) nói về **12 Day Officers** và chọn theo hoạt động/chủ thể. Không nên dùng đoạn đó làm định nghĩa cho chu kỳ 6 Hoàng/6 Hắc của 12 Thiên Thần.
- [SKĐS ngày 10/8/2026](https://suckhoedoisong.vn/am-lich-hom-nay-10-8-lich-am-10-8-lich-van-nien-ngay-10-8-2026-169260809161539163.htm) vừa ghi Bạch Hổ Hắc Đạo, vừa gọi quan hệ Can sinh Chi là đại cát. Điều này cho thấy các nhãn phản ánh các góc luận khác nhau; không đủ để lấy một nhãn duy nhất làm kết quả tổng.
- [Bài Lâm Đồng qua Báo Mới](https://baomoi.com/lich-am-duong-ngay-10-08-2026-xem-gio-hoang-dao-huong-xuat-hanh-va-cac-luu-y-cat-hung-c55796272.epi) cùng ngày ghi tháng Ất Mùi và nói Sát Chủ Dương với các việc nên tránh cụ thể, không cung cấp đủ bảng toàn tháng cho Sát Chủ/Thọ Tử/Tam Nương.
- [Liugems](https://liu.com.vn/bai-viet/ngay-tot-thang-8-am-lich-2020) hiện là bài **2026**, dù slug còn `2020`. Bài phân biệt ngày chung với đối chiếu tuổi; không phải nguồn version ổn định cho engine.
- [BKNS](https://tools.bkns.vn/en/tools/lunar-calendar) là công cụ lịch Việt Nam tham khảo; trang đã đọc không cho thấy đặc tả thuật toán đủ để dùng làm oracle cho lịch Trung Quốc UTC+8 của dự án.

Trong runtime đang ghim, tại **10/08/2026 12h UTC+7**: ngày **Bính Thìn**, tháng provider **Bính Thân**, Trực **Thành**, **Kim Quỹ Hoàng Đạo**; nên có cưới/khai trương, kỵ có xuất hành. Các bài Việt Nam trên ghi tháng Mùi/Bạch Hổ. **Suy luận cần kiểm thêm:** khác hệ tháng góp phần tạo khác biệt; chưa xác nhận toàn bộ thuật toán của các trang. Không tuyên bố provider hoặc bài báo đúng tuyệt đối.

## Nguồn cho các ngày kỵ

`data/reference/tinix-bazi/shensha.js`, commit `80ff4463d0397c1b11db76f38d880255f55558bc`, có bảng **Sát Chủ, Thọ Tử, Nguyệt Phá**, mỗi bảng 12 hàng theo chi tháng. SHA256 xác nhận với manifest. Nhưng hàm gốc áp dụng tháng sinh cho các trụ sinh; chưa phải phép chọn ngày ứng viên.

Provider có `月破` trong corpus hung thần. Corpus đã khảo sát không có tên trực tiếp `Sát Chủ`, `Thọ Tử`, `Tam Nương`; không được lấy tên có chữ chết/sát khác làm alias thay thế. Tam Nương còn cần nguồn đầy đủ riêng. Chi tiết bảng tinix và mục chưa bật nằm trong JSON nghiên cứu.

Chưa tìm được trong các link đã đọc một hệ thống điểm phạt/ngưỡng chuẩn. Bất kỳ bảng điểm nào đưa vào sản phẩm phải được ghi là policy đề xuất và hiệu chỉnh trên corpus, không gắn cho nguồn truyền thống.

## Ranh và hiệu năng

Fixtures xác nhận tại 12/10/2026: Bát Tự đổi Kỷ Mùi → Canh Thân ở **22h UTC+7**; ngày dân sự vẫn Kỷ Mùi đến **23h UTC+7**. Hàn Lộ 2026 đổi tháng Bát Tự ở **08/10/2026 13:29:17 UTC+7** theo provider.

Benchmark khảo sát 13 đoạn cơ bản/ngày cho 31 và 93 ngày đã hoàn tất; thời gian thực của lần chạy nằm trong JSON. Đây là phép đo facts provider trong cùng process đã chạy khảo sát, có tác động cache. Chưa có split giao tiết đầy đủ, chấm cá nhân, ranking, HTTP/UI hoặc cold-start. Không suy ra SLA sản phẩm từ số này.

Chưa chạy lại toàn bộ test ứng dụng vì đợt này thêm nghiên cứu/tài liệu, không đổi runtime. Sau khi bắt đầu triển khai engine/API sẽ chạy test mới và regressions MVP 1, đồng thời cập nhật graph.
