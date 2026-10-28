# Bản nguồn Mai Hoa đã ghim

Ba bản wikitext được tải từ API Wikisource ngày **25/10/2026**, theo đúng revision trong `manifest.json`. SHA-256 kiểm nguyên byte UTF-8. Đây là **bản chép điện tử**, chưa phải một bản khảo đính từ ảnh sách; giữ nguyên chữ nghi vấn, không tự sửa cổ văn.

- [Quyển một, revision 2690596](https://zh.wikisource.org/w/index.php?oldid=2690596).
- [Quyển hai, revision 1441921](https://zh.wikisource.org/w/index.php?oldid=1441921).
- [Quyển ba, revision 1441927](https://zh.wikisource.org/w/index.php?oldid=1441927).

Ghi nhận Wikisource và các tác giả đóng góp bản chép; xem lịch sử trang theo revision. Cổ văn thuộc truyền thống *Mai Hoa Dịch Số*; không xác nhận mọi nội dung là do chính Thiệu Ung viết. Văn bản/biên tập trên Wikisource được công bố theo [CC BY-SA](https://creativecommons.org/licenses/by-sa/4.0/) với các điều khoản bổ sung theo trang nguồn. Tệp raw được giữ để đối chiếu trong workspace cá nhân.

`compiled.json` chỉ chứa trích đoạn có thể kiểm lại trong raw, với hash, tên mục và URL phiên bản cố định. Tạo lại offline:

```sh
.venv/bin/python scripts/build_maihoa_data.py
```

`config/maihoa_rules.json` phân biệt câu Hán được trích nguyên văn, lời Việt do AI soạn chưa hiệu đính, và quy ước lịch/tổng hợp của sản phẩm. Không nhập các kết luận bệnh tật, tính cách theo giới, nhân tướng hoặc những chi tiết ứng kỳ chưa chuẩn hóa vào luật tự động.
