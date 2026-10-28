# Nguồn được khóa cho MVP 1

- `tinix-bazi`: https://github.com/vhphuoc1102/tinix-bazi/tree/80ff4463d0397c1b11db76f38d880255f55558bc
- `open-iching`: https://github.com/john-walks-slow/open-iching/tree/4c5f00f8cb62c6e0d2471243d28150b473ef592f

Các file được giữ nguyên để tra cứu và đối chiếu trong workspace cá nhân. `manifest.json` lưu SHA-256. Runtime đọc dữ liệu open-iching và kiểm tra hash khi khởi động. Mã JS tinix chỉ được chạy bằng Node ở script đối chiếu, không phải dependency runtime của ứng dụng Python.

`randomyst/bazi.py` chuyển các nhánh điểm/cường nhược/cách cục/chọn Dụng-Hỷ-Kỵ/Điều Hầu từ `phan_tich/ngu_hanh.js` và `geju.js`. Không nhập các lời khuyên nghề nghiệp/sức khỏe của nguồn. Tứ trụ hiện được cấp bởi 6tail theo đồng hồ Bắc Kinh UTC+8, sect 1; không dùng calculator nguồn nguyên trạng và lỗi `hour || 12`.

Source lookup: quẻ từ/hào từ từ `iching.json`; Thoán/Tượng truyện từ dictionary `tuan.json`/`xiang.json`. Quẻ 32 thiếu Thoán truyện ở commit này và được ghi `source_gaps`. Nội dung Hán là `SOURCE_ORIGINAL`. Bản nháp nghĩa Việt 64 quẻ/384 hào do trợ lý AI soạn nằm riêng tại `data/interpretation/iching_vi_draft.json`, có nhãn AI và hash nguyên văn.

Lời giải Bát Tự hiển thị được build từ hai bảng `STEM_ESSENCE` trong `phan_tich/data/dich_thien_tuy_data.js` và `STRUCTURE_ANALYSIS` trong `phan_tich/data/ngu_hanh_data.js`, giữ nguyên nội dung Việt của repo. Các câu verse là Hán Việt theo nguồn; không được quảng bá như chữ Hán cổ đã khảo chứng. File mới Địch Thiên Tủy đã đối chiếu Git blob SHA-1 `4b8b5d2ce2f2cae7a7c537832416a1bfce7211c7` ở commit đã khóa; SHA-256 được thêm vào manifest. Runtime đọc JSON đã build, không chạy mã JS này.
