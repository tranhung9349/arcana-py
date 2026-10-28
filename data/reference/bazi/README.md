# Nguồn module Bát Tự độc lập

`manifest.json` ghim bốn văn bản Wikisource bằng revision, timestamp và SHA-256, cùng mã provider `lunar-python==1.4.8`. Các chương Địch Thiên Tủy được tải riêng vì trang mục lục chứa transclusion; không dùng revision mục lục để giả định nội dung chương đã khóa.

- Suy vượng: `滴天髓/12`, revision **844360**.
- Hàn noãn: `滴天髓/16`, revision **844365**.
- Nguyệt lệnh: `滴天髓/17`, revision **844366**.
- Quan hệ Chi: `三命通會/卷二`, revision **2292392**.

Các `.source.json` giữ metadata nhận từ MediaWiki API; `.wikitext` giữ toàn văn raw của revision tương ứng. Runtime chỉ đưa các đoạn đã chọn trong `config/bazi_rules.json` ra API và UI. Nguyên văn là văn bản lịch sử, không phải bằng chứng khoa học cho sự kiện đời người. Nội dung quy định riêng của Arcana được đánh nhãn `PRODUCT_POLICY`, không gán ngược cho cổ thư.

Tàng can, Thập Thần, Can Chi, ngũ hợp Can, lục hợp và lục xung lấy từ 6tail. Manifest kiểm hash `EightChar`, `Lunar` và `LunarUtil` ở bản cài. MIT license của thư viện: https://github.com/6tail/lunar-python/blob/master/LICENSE. Không nâng dependency hoặc thay thế bảng trong một bản đã phát hành mà không đổi version và chạy đối chiếu.

Nguồn Tam Mệnh Thông Hội mô tả các cặp hại, Tý–Mão hình, nhóm tam hình, tự hình, lục hợp và tam hợp. Bản đầu chỉ nhận diện quan hệ, không nhập các lời phán tai họa/giới tính của nguồn. Tam hội được ghi trong bảng quy ước sản phẩm; không gán một câu nguồn không chứa bảng này làm bằng chứng trực tiếp. Nhóm tam hình chỉ báo khi đủ bộ, nên coverage ghi rõ chưa xét bán hình. Phá và toàn bộ chuỗi cứu giải chưa được bật.

**Giới hạn nguồn:** chưa có corpus Tử Bình Chân Thuyên đã đối chiếu. Vì vậy module giữ các tên nguyệt lệnh ở mức ứng viên, không tuyên bố đã triển khai toàn bộ phép lập cách Tử Bình. Tư lệnh theo số ngày sau tiết, thành/bại/cứu ứng, tòng hóa và bảng Điều hậu 10 Can × 12 tháng chưa nằm trong luật kết luận. Trạng thái hiệu đính là `RULES_TESTED_NOT_EXPERT_REVIEWED`.

Rebuild offline, có chủ đích sau khi đối chiếu nội dung nguồn:

```sh
.venv/bin/python scripts/build_bazi_data.py
```

Builder kiểm đoạn trích có mặt trong raw, sinh rules và manifest. Runtime kiểm hash raw, metadata, config, mã provider và binding đoạn trích. Không truy cập web khi người dùng lập lá số.
