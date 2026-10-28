# Gieo ba đồng theo Lục Hào: lựa chọn phương pháp và phạm vi triển khai

Ngày nghiên cứu: **26/10/2026**, UTC+7. Phương pháp đã chọn: **ba tiền thay cỏ thi, gieo sáu lượt**. Phiên bản: `three-coins-liuyao-2026-10-26-v1`.

## Kết luận

Chọn quy trình ba đồng của **Bốc Phệ Chính Tông**, đối chiếu **Bốc Phệ Toàn Thư**, thay cho cách sáu đồng nhị phân cùng lúc. Hai bản chép cùng mô tả ba đồng cho một hào, ba lượt thành nội quái rồi thêm ba lượt thành ngoại quái; xếp từ dưới lên; phân biệt hào tĩnh và động. Đây là lựa chọn có căn cứ văn bản cho bước gieo Lục Hào, không phải tuyên bố mọi trường phái chỉ có một cách đúng.

Nguồn chính: [Bốc Phệ Chính Tông, quyển 1, mục 以錢代蓍法](https://www.shidianguji.com/book/AMNL0060/chapter/1ma05akk4w74j). Đối chiếu: [Bốc Phệ Toàn Thư, cùng mục](https://www.shidianguji.com/zh/book/HY1394/chapter/1l3wdooougilw). Đây là các bản chép điện tử; OCR của bản Chính Tông có lỗi ở dấu hào và một số chữ. Chưa tuyên bố đã khảo đính bản in gốc.

## Quy trình cho người dùng

1. Ghi rõ một việc đang hỏi; ngày giờ ghi là lúc gieo, không phải ngày dự định làm việc.
2. Dùng ba đồng phân biệt được hai mặt. Với tiền cổ, nhận diện mặt **chữ 字** và mặt **lưng 背**. Với tiền hiện đại, tự chỉ định hai mặt tương ứng **trước khi gieo**, giữ nguyên trong sáu lượt. Tránh dùng nhãn sấp/ngửa mà không định nghĩa.
3. Gieo cả ba đồng cùng một lượt. Mặt lưng tính 3, mặt chữ tính 2. Ghi tổ hợp ba mặt, không chỉ ghi kết quả quẻ cuối cùng.
4. Lượt đầu lập hào 1 dưới cùng. Lượt 2–3 hoàn thành hạ quái; lượt 4–6 hoàn thành thượng quái.
5. Giữ mọi hào có tổng 6 hoặc 9 là động; lật đồng thời tất cả hào ấy để lập quẻ biến. Không ép mỗi phiên có một hào động.
6. Đóng phiên sau đủ sáu lượt. Đọc lại hoặc thử lại yêu cầu bị lỗi mạng phải giữ kết quả đã lưu.

Phần nghi lễ trong cổ thư được mô tả như bối cảnh lịch sử; ứng dụng không bắt buộc nhang, hướng ngồi hoặc lời khấn để tính được quẻ.

### Bốn trạng thái

| Ba đồng | Tổng | Tên | Hào quẻ chủ | Hào quẻ biến | Xác suất |
| --- | ---: | --- | --- | --- | ---: |
| 3 chữ | 6 | Lão âm / giao × | Âm | Dương | 1/8 |
| 1 lưng + 2 chữ | 7 | Thiếu dương / đơn | Dương | Dương | 3/8 |
| 2 lưng + 1 chữ | 8 | Thiếu âm / sách | Âm | Âm | 3/8 |
| 3 lưng | 9 | Lão dương / trùng ○ | Dương | Âm | 1/8 |

Mã hóa `BACK=3`, `INSCRIPTION=2`. Các xác suất được tính bằng cách liệt kê tám tổ hợp của ba đồng công bằng, độc lập; không phải xác suất đúng của lời luận. Trang [I Ching readings của University of Oregon](https://hexadecimal.uoregon.edu/ching/explain.html) xác nhận độc lập cách biểu diễn 6/7/8/9 và thứ tự từ dưới lên; app không dùng thuật toán trộn câu hỏi vào RNG của chương trình ấy.

Không bốc đều bốn tổng 6/7/8/9 vì sẽ làm sai tỷ lệ. Gieo trên app lấy 18 bit độc lập qua `secrets.randbits(1)`, chia thành sáu lượt ba đồng. Câu hỏi, tên và ngày sinh không làm seed; thời điểm chỉ dùng cho lịch và bàn Nạp Giáp. Chế độ gieo tự động tạo đủ sáu lượt trong một lần gửi, không giả lập sáu lần nhấn đã diễn ra ngoài đời. Nhập tay nhận đúng 18 mặt do người dùng đã gieo.

### Vì sao không chọn sáu đồng một lượt?

Sáu đồng nhị phân chỉ xác định 64 mẫu âm/dương, không đủ thông tin phân biệt bốn trạng thái của từng hào. Biến thể có một đồng đánh dấu buộc đúng một hào động. Cả hai đều khác không gian 0–6 hào động của ba tiền sáu lượt. [Clarity mô tả và bình luận biến thể một đồng khác biệt](https://www.onlineclarity.co.uk/learn/ways-to-consult-the-i-ching/other-methods/); đây là tham khảo hiện đại, không được dùng làm căn cứ cổ thư cho runtime.

## Gieo quẻ và luận Lục Hào là hai lớp

Tạo được quẻ chủ/biến mới hoàn thành bước lập hào. Lục Hào Nạp Giáp còn dùng cung quẻ, địa chi/ngũ hành từng hào, Lục thân, Thế–Ứng, nhật nguyệt, Dụng thần và các quan hệ động biến. Việc đọc quẻ từ/hào từ là một lớp tra kinh văn riêng. Không gắn một đoạn nghĩa quẻ chung rồi gọi là đã luận toàn bộ câu hỏi theo Nạp Giáp.

Bản này đã triển khai **bàn Nạp Giáp cơ bản**:

- Đủ tám cung, mỗi cung tám quẻ; thứ tự quẻ đối chiếu mục 六十四卦名 của Chính Tông. Thế lần lượt 6, 1, 2, 3, 4, 5, 4, 3; Ứng cách Thế ba hào.
- Nạp can/chi theo nội và ngoại quái, từ dưới lên. Bảng đối chiếu thêm [納甲裝卦歌](https://changxianyi.com/guji/bushi/wz-20260915/chapter-018/), khắc phục các chữ OCR nhầm của nguồn thứ nhất.
- Lục thân lấy **hành của cung quẻ chủ** làm gốc, kể cả Lục thân hào biến. Chỉ trình bày biến chi/biến thân ở vị trí hào động, không coi hào tĩnh của quẻ biến là một động tác độc lập.
- Lục thú khởi tại hào 1 theo nhật can, đi lên đủ sáu thú. Tuần Không theo tuần Giáp của nhật trụ; Nguyệt Phá ghi khi địa chi hào đối xung nguyệt kiến.
- Dấu Không/Phá chỉ là quan hệ đã tính, không tự diễn giải thành mất hiệu lực/cát hung. Xử lý cứu giải, vượng suy, thật/giả Không/Phá cần một lớp luận riêng.

**Chưa tự động:** chọn Dụng thần theo câu hỏi, Phục thần, ám động, hợp/xung toàn cục, hồi đầu sinh/khắc, tiến/thoái thần và ứng kỳ. Phần UI/API ghi giới hạn này trực tiếp.

### Quy ước lịch

Dùng lại profile lịch đang có của app: đầu vào UTC+7, đổi cùng instant sang Bắc Kinh UTC+8 đúng một lần; nguyệt kiến theo tiết khí; nhật trụ đổi lúc 23:00 Bắc Kinh; Lục thú theo nhật can ấy. Cho nhập thời điểm gieo thật trong 2024–2030. Đây là **quy ước sản phẩm có version**, không gán cho cổ thư một chuẩn múi giờ hiện đại duy nhất. Có kiểm tra ranh 22:00 Việt Nam / 23:00 Bắc Kinh.

## Đọc 64 quẻ

Dùng lại corpus `open-iching` đã kiểm checksum tại commit `4c5f00f8cb62c6e0d2471243d28150b473ef592f` và bản nháp Việt `iching-vi-draft-v1`. Mỗi quẻ có quẻ từ, nghĩa chung, sáu hào từ và Thoán/Tượng nếu nguồn có. Hiển thị riêng các hào động của quẻ chủ, giữ đủ mọi hào động; không đưa phép chọn một hào theo số hào động của cách đọc Chu Dịch vào quy tắc Lục Hào.

Càn/Khôn cả sáu hào động: nguyên văn Dụng Cửu/Dụng Lục có trong nguồn được đưa ra tham khảo, không gán sẵn vai trò kết luận Nạp Giáp; chưa có nghĩa Việt cho hai mục đặc biệt. Thoán truyện quẻ 32 thiếu trong corpus vẫn ghi rõ. Không gọi provider LLM; nghĩa Việt là bản nháp có sẵn, chưa hiệu đính.

## Kiểm chứng

- Liệt kê đủ 4^6 = **4.096** vector tổng, đủ 64 quẻ chủ và 4.096 cặp chủ/biến; bao phủ số hào động 0–6.
- Duyệt đủ 64 quẻ và 384 hào từ; kiểm tra nguồn dịch/hash bằng validator dùng chung.
- Đối chiếu danh sách 64 quẻ của tám cung, vị trí Thế/Ứng; kiểm tra Nạp Giáp Càn và biến Khôn, Lục thân quẻ biến theo cung gốc.
- Kiểm tra Lục thú cho cả mười nhật can, Tuần Không cho 60 ngày Can Chi, đổi ngày theo profile app.
- Retry đồng thời cùng UUID chỉ gieo 18 bit một lần. Mở lại từ database khác instance không lập lại quẻ; đổi payload cùng UUID trả 409.
- API tra cứu không tạo phiên; lịch sử gieo số và Mai Hoa độc lập. Không có bằng chứng kiểm định khả năng dự báo từ các phép thử này.

Lệnh: `.venv/bin/python -m unittest discover -s tests -v`. Các ca chuyên biệt ở `tests/test_coin_consultations.py`; báo cáo chạy thực tế ở `three_coin_validation.json`.
