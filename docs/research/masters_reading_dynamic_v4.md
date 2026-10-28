# Từ cách đọc cổ điển đến prompt thích ứng v4

Ngày nghiên cứu: 27/10/2026. Runtime: `plain-vietnamese-2026-10-27-v4.1`.

Mục tiêu là học cách đặt vấn đề và cân điều kiện từ các bản nguyên tác/chú giải có thể truy nguồn. Không giả làm một bậc thầy, không dùng danh tiếng tác giả để chứng nhận độ đúng dự báo. Các quy tắc định tuyến dưới đây là lựa chọn biên tập của sản phẩm, không phải thuật toán nguyên xi có trong cổ thư.

## Những cách luận đáng học

| Văn bản / truyền thống | Phần đã đối chiếu | Cách tư duy có ích | Cách đưa vào sản phẩm |
|---|---|---|---|
| Nhậm Thiết Tiều, *Địch Thiên Tủy Xiển Vi* | Tri mệnh; Nguyên lưu; Tuế vận | Phản đối lấy một nhãn Tài/Quan/Ấn làm tốt xấu cố định; xem nền mạnh yếu, chiều quan hệ và chỗ lưu thông/bị chặn. Bàn thời kỳ có thêm tầng vận, không chỉ mệnh cục. | Khi có dấu trái chiều, đặt chúng cạnh nhau và chỉ ra điều chưa phân định; chỉ nối chuỗi tương tác nếu findings đã xác nhận. Câu hỏi chứa một năm không tự tạo Lưu niên. |
| *Tử Bình Chân Thuyên*, truyền thống Thẩm Hiếu Chiêm | Dụng thần biến hóa; Thành bại cứu ứng; Tướng thần khẩn yếu | Tên cách cục mới là đầu mối; phối hợp có thể thay đổi cách đọc, một yếu tố phụ trợ có thể giữ vai trò then chốt. | Nhánh ứng viên cách cục giải thích khoảng cách tới thành cách; chỉ gọi nút thắt/cứu ứng khi đã có kết luận tương ứng. Không tự phong Tướng thần từ danh sách can. |
| *Mai Hoa Dịch Số*, truyền thống gắn với Thiệu Ung | Mượn vật ban đêm, quyển I; luận lý và Thể Dụng; Thể Dụng Hỗ Biến | Ví dụ mượn rìu/cuốc cho thấy cùng tượng chưa đủ phân biệt việc; phải xét hoàn cảnh đã biết. Các chặng Dụng/Hỗ/Biến có vị trí riêng. | Bám việc thực sự được hỏi, tìm chặng làm đổi chiều; không gán Hỗ/Biến của phương án A cho B, không bịa ngoại ứng. Không coi giai thoại là kiểm chứng lịch sử về tác giả hoặc hiệu quả dự báo. |
| *Tăng San Bốc Dịch*, truyền thống Dã Hạc / Lý Văn Huy | Nguyên/Kỵ thần suy vượng; Nhật/Nguyệt; Lưỡng hiện | Có vai trò chưa đồng nghĩa có hiệu lực. Chương Lưỡng hiện nêu ngoại lệ đối với cách máy móc bỏ hào Không/Phá để chọn hào thuận hơn. | Lựa chọn Dụng chưa rõ hoặc mới tạm chọn phải được xử lý trước; giữ từng ứng viên riêng, không tự đổi Dụng hoặc ghép ưu điểm hai hào. |

Đây là các phép đọc khác nhau. “Dụng” theo nguyệt lệnh Bát Tự không đồng nghĩa Dụng thần Lục Hào; Tướng thần không phải mọi can sinh Nhật chủ; Thể/Dụng Mai Hoa không thay thế Thế/Ứng. V4 giữ hướng dẫn từng phương pháp của v3.2 và thêm một lớp chọn trọng tâm riêng.

## Nguồn và mức xác minh

- [Địch Thiên Tủy Xiển Vi, revision 2600158](https://zh.wikisource.org/w/index.php?oldid=2600158): đã đọc văn bản và tải raw đúng revision, 401.801 byte, SHA-256 `1d1a3d61c1b9a26618b41b8ead857a6b966992fdf2adabdc607a0c6cb4c8f04d`. File `data/reference/interpretation/dtt_chanwei.wikitext` và metadata đi kèm. Bản số hóa có lỗi chữ/dấu, chưa đối chiếu trọn với bản in; dùng hai trích đoạn ngắn khớp raw. Phân biệt lời nguyên chú và lời “Nhậm thị viết”, không gán toàn bộ nội dung cho một tác giả duy nhất.
- [Tử Bình Chân Thuyên, chương 3723](https://caipu.donglishuzhai.net/chapter/3723.html), [chương 3728](https://www.donglishuzhai.net/chapter/3728.html): chỉ xác minh phần nguyên văn được chỉ mục web trả lại; truy cập trực tiếp tiếp tục timeout. Nguồn mới `ziping:assistant` được đánh dấu `WEB_EXCERPT_NOT_EDITION_PINNED`, không có raw toàn chương. Chương biến hóa được dùng trong ghi chú nghiên cứu, không thêm quy tắc biến cách vào core.
- Đã mở [bản scan NLC, quyển II](https://upload.wikimedia.org/wikipedia/commons/d/d5/NLC416-13jh002326-46443_%E6%B7%B5%E6%B5%B7%E5%AD%90%E5%B9%B3_%E5%AD%90%E5%B9%B3%E7%9C%9F%E8%A9%AE_%E7%AC%AC2%E5%8D%B7.pdf), nhưng công cụ không trích được chữ và kết quả ảnh không đủ để đối chiếu đáng tin cậy; không coi là đã hiệu khảo với scan.
- [Mai Hoa Dịch Số quyển I, revision 2690596](https://zh.wikisource.org/w/index.php?oldid=2690596): dùng raw đã ghim trong project; trích đoạn `mh:context` khớp file. Kết quả tìm kiếm nguyên văn trên [bản chép tại Dịch Học Võng](https://www.eee-learning.com/book/4080) hỗ trợ đối chiếu ví dụ mượn vật; trang trực tiếp timeout. Không sử dụng bài diễn giải blog làm chuẩn kỹ thuật.
- [Tăng San Bốc Dịch · Lưỡng hiện, Thức Điển Cổ Tịch](https://www.shidianguji.com/zh/book/XYXZSBY/chapter/1lzxsny7db6rt): mở được nguyên văn dạng chép có liên kết ảnh. Có chỗ OCR lẫn bảng quẻ và mất chữ; chỉ lấy câu ngắn đã thấy, gắn `WEB_TRANSCRIPTION_NOT_EDITION_PINNED`. Chưa đối chiếu từng chữ với ảnh scan, không dùng bảng quẻ OCR làm ví dụ tính toán hoặc lịch sử kết quả.
- Các nguồn v2/v3 vẫn giữ đúng giới hạn và metadata cũ. Tổng 29 mục trong pack là **trích đoạn/quy ước**, không phải 29 cuốn sách.

## Thay đổi cụ thể

`research_tools/reading_strategy.py` chọn từ các chỉ dẫn cố định trong `docs/prompts/reading_playbook_v4.json`. Việc chọn nhánh không tạo finding mệnh lý mới.

1. **Trọng tâm theo trạng thái.** Bát Tự ưu tiên xung đột phù ức–Điều hậu, rồi trạng thái đan xen, ứng viên cách cục hoặc nền vượng/nhược. Lục Hào ưu tiên Dụng chưa rõ/tạm chọn, điều kiện Thế hoặc dấu trái chiều Nhật–Nguyệt. Mai Hoa có nhánh diễn tiến đổi chiều và nhánh các chặng cùng hướng. Kinh văn chỉ dùng văn bản đã truy xuất.
2. **Mục đích câu hỏi.** Bộ nhận diện nhỏ có dấu/không dấu tạo một trong sáu nhãn: mở, thời điểm, so sánh, giải thích, chuẩn bị, kết quả. Đây là gợi ý viết, không phải bộ chọn chủ đề/Dụng mới. Câu hỏi có thể bị phân loại chưa đúng; nguyên câu vẫn được cấp làm dữ liệu cuối để model đọc sát ý. Không trích câu hỏi vào system.
3. **Góc nhìn theo chủ đề đã chọn.** Văn thư khác cha mẹ dù cùng Phụ mẫu; chuyện học khác thu nhập dù cùng mệnh cục. Chủ đề được giữ theo phiên đã lưu.
4. **Một trọng tâm và tối đa hai điều kiện đi kèm.** Không nạp toàn bộ các nhánh của mọi trường phái vào một bài. Bố cục 2–4 đoạn thích ứng với chỗ vướng, bỏ số câu cố định và cách mở đầu mặc định bằng toàn bộ nền lá số.
5. **Few-shot theo trọng tâm và mục đích.** Giữ bộ lọc phương pháp và trạng thái đối lập, ưu tiên chủ đề, rồi độ khớp trọng tâm/mục đích/tín hiệu. Runtime tối đa hai mẫu. Không dùng mẫu làm dữ kiện phiên.
6. **24 mẫu biên tập.** Kế thừa 18 mẫu, sửa một liên hệ đời sống quá tay trong mẫu văn thư, thêm 6 mẫu về ưu tiên hai nhánh, thiếu vận khi hỏi thời điểm, chặng đổi chiều, so sánh thiếu một phía, Dụng tạm chọn và điều kiện ứng kỳ chưa quy đổi.

Adapter Lục Hào chỉ thêm nhãn tóm tắt trạng thái Thế và sự hiện diện điều kiện ứng kỳ đã lưu. Không đổi hào, Dụng, kết luận core, lịch hoặc quy tắc. Bản v2/v3 giữ nguyên để kiểm tra lại. Cache dùng phiên bản pack và hash của chính messages nên bài cũ không được dùng nhầm làm v4.

## Kiểm chứng và giới hạn

Các mẫu là nguyên tác tiếng Việt trên dữ kiện giả định; chưa được chuyên gia hiệu đính. 11 ca giữ riêng kế thừa v3 chưa chạy model. Ba câu hỏi biến thể bổ sung nằm ở `adaptive_probes.json`, cùng dữ kiện với mẫu dạy nên được ghi rõ **development probes**, không gọi là held-out độc lập.

Kiểm thử tự động kiểm tra chọn nhánh, giữ nguyên dữ kiện/chủ đề, cách ly phương pháp, hash nguồn/prompt, cache và đầu ra có dẫn chiếu. Chúng không đánh giá được một bài luận đúng chuyên môn đến đâu. Các lần chạy model thật là hồi quy phát triển trên ba hồ sơ mẫu, không phải benchmark mù.

Prompt thích ứng giúp thay đổi cách chọn trọng tâm và trình bày; không bổ sung Đại vận/Lưu niên, thành bại/cứu ứng đầy đủ, ngoại ứng hoặc phép ứng kỳ còn thiếu. Không dùng câu “có thể” để hợp thức hóa việc tự tính những phần đó.

Hướng dẫn kinh văn có trong bộ mẫu ngoại tuyến; lần cập nhật này không thêm endpoint luận AI Chu Dịch độc lập. Runtime vẫn là Bát Tự, Mai Hoa và Lục Hào.

Lượt thử v4 đầu bị cắt ở giới hạn 8.000 token và đã bị chặn, không lưu/hiển thị. Transport được nâng trần lên 12.000 token; không tự gọi lại một phản hồi bị cắt hoặc timeout. Ba lượt v4 tiếp theo hoàn tất. Khi đọc lại, phát hiện câu gượng “được nhận định đã có xếp thuận”, liên hệ sức Thể chưa rõ với khả năng duy trì của người hỏi, và việc dùng điều kiện Thế để gợi phần nội dung hồ sơ cần rà. V4.1 sửa chỉ dẫn văn phong và siết hai bước liên hệ đó. Báo cáo v4 đầu được giữ riêng ở `ai_readings_v4_draft_http_smoke.json`; các báo cáo chính ghi phiên bản cụ thể của lượt cuối. Đây là hiệu đính phát triển, chưa phải kiểm định chuyên gia.

Kết quả chạy thật và nhận xét văn phong: `ai_readings_v4_http_smoke.json`, `ai_readings_v4_editorial_review.json`. Kết quả kiểm thử: `ai_readings_v4_validation.json`.
