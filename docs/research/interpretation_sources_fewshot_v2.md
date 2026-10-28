# Nguồn lời luận và bộ mẫu Việt ngữ v2

Ngày nghiên cứu: 26/10/2026. Đã kiểm tra mã tại commit đang dùng, đối chiếu nguyên tác và biên soạn **17 cặp mẫu + 8 ca đánh giá riêng**. Đây là bộ chuẩn bị prompt chạy ngoại tuyến, chưa gọi model, chưa thay lời luận trên giao diện. Không dùng kết quả kiểm tra schema như chứng nhận chất lượng mệnh lý.

**Cập nhật triển khai sau nghiên cứu:** bộ mẫu đã được nối vào runtime Bát Tự/Mai Hoa/Lục Hào, kiểm tra bằng các phiên tổng hợp với model thật. [Bàn giao tích hợp](../ai_readings_handoff.md). Các phát biểu “chưa nối runtime” bên dưới mô tả mốc nghiên cứu ban đầu; chưa chạy benchmark chất lượng hoặc hiệu đính chuyên gia. Selector hiện loại trạng thái đối lập rồi ưu tiên chủ đề và tín hiệu phân tích.

## Hai repo GitHub có gì?

| Nguồn | Nội dung đã xác minh | Project đang dùng đến đâu? |
|---|---|---|
| [tinix-bazi, commit 80ff446](https://github.com/vhphuoc1102/tinix-bazi/tree/80ff4463d0397c1b11db76f38d880255f55558bc) | Có lời Việt theo Nhật chủ/mùa và cách cục. Ngoài ra có [dịch vụ tư vấn AI](https://github.com/vhphuoc1102/tinix-bazi/blob/80ff4463d0397c1b11db76f38d880255f55558bc/backendjs/src/services/openrouter.service.js), với `buildSystemPrompt`/`buildUserPrompt`, dữ kiện lá số và câu hỏi. | Đã nhập các bảng và một phần logic cũ. Chưa nhập dịch vụ AI. Module Bát Tự độc lập mới dùng profile riêng, không gọi prompt trong repo này. |
| [open-iching, commit 4c5f00f](https://github.com/john-walks-slow/open-iching/tree/4c5f00f8cb62c6e0d2471243d28150b473ef592f) | Chủ yếu là dữ liệu Hán về quẻ/hào và các truyện. README có dự kiến thêm bản dịch/chú giải, không đồng nghĩa corpus hiện có đã có lời luận Việt theo câu hỏi. | Dùng quẻ từ, hào từ, Thoán và Tượng. Nghĩa Việt hiện là bản nháp AI do project biên soạn riêng. |

Prompt tư vấn của tinix dùng vai nhân vật, yêu cầu các đoạn trả lời và câu hỏi tiếp nối. Đây là ví dụ triển khai tư vấn AI, chưa phải bộ mệnh lệ được kiểm chứng hay bộ mẫu buộc từng nhận định dẫn đúng nguồn. Không chép các khẳng định tính cách/nghề nghiệp/giàu nghèo từ bảng của repo thành sự thật của người dùng.

Đã tải trực tiếp file tư vấn ở commit ghim và ghi SHA-256 `8e00b76ce6aebd1111df1d4b4d7581028359ebdd6b8c76e41f5947e470549323`. Không gọi API tư vấn của repo, không dùng API key và không gửi hồ sơ sinh ra ngoài.

Lưu ý văn bản: ở corpus open-iching đã ghim, hào 2 quẻ Càn có `见龙再田`, trong khi [bản Chu Dịch đối chiếu](https://zh.wikisource.org/w/index.php?oldid=2404991) ghi `見龍在田`. Đây là sai khác một chữ cần hiệu đính; giữ nguyên snapshot cũ, không âm thầm sửa nguồn đã khóa. Quẻ 32 vẫn thiếu Thoán ở corpus hiện hành. Nguồn GitHub là dữ liệu tham khảo, không tự trở thành bản khảo đính.

Về thông tin tái sử dụng: README tinix ở commit ghim tự ghi MIT nhưng đường dẫn `LICENSE` tại commit này trả 404; README open-iching ghi giới hạn học tập, phi thương mại. Bộ mẫu mới được viết mới từ nguyên tác và không sao chép prose hiện đại của hai repo. Thông tin này được ghi để tránh gọi cả hai corpus là dữ liệu có giấy phép MIT đã xác nhận.

## Nguồn chọn làm căn cứ

“Nguồn uy tín” trong nghiên cứu này là nguồn nguyên tác có chương và đoạn đối chiếu được, thay vì một bài SEO hoặc lời AI không dẫn nguồn. Bản chép điện tử vẫn có thể sai chữ; chưa coi là ấn bản phê bình hoặc chứng minh độ chính xác dự báo.

| Phạm vi | Nguồn và đoạn đã kiểm tra | Điều lấy vào bộ mẫu |
|---|---|---|
| Suy vượng Bát Tự | [Địch Thiên Tủy · Suy vượng](https://zh.wikisource.org/w/index.php?oldid=844360) | Sinh trợ/tiết hao phải đọc theo điều kiện, không đếm một hành rồi kết luận toàn cục. Thân nhược không phải chẩn đoán sức khỏe. |
| Mùa và cách cục | [Địch Thiên Tủy · Nguyệt lệnh](https://zh.wikisource.org/w/index.php?oldid=844366), [Tử Bình Chân Thuyên · Luận Dụng thần](https://www.donglishuzhai.net/chapter/3721.html), [Thành bại cứu ứng](https://www.donglishuzhai.net/chapter/3722.html) | Tên ứng viên cách cục chưa đủ thành cách. Giữ riêng Dụng theo cách cục và hướng phù ức mà sản phẩm đang tính. |
| Điều hậu | [Địch Thiên Tủy · Hàn noãn](https://zh.wikisource.org/w/index.php?oldid=844365), [Tử Bình Chân Thuyên · Phối khí hậu](https://www.donglishuzhai.net/chapter/3727.html) | Nóng lạnh là một lớp xét riêng. Không ép một gợi ý mùa thành hành duy nhất hoặc lời khuyên màu sắc/vật phẩm. |
| Quan hệ Chi | [Tam Mệnh Thông Hội · Quyển II](https://zh.wikisource.org/w/index.php?oldid=2292392) | Chữ hình/hợp/xung không tự xác định một sự kiện tình cảm hoặc tai họa. Bộ mẫu dùng đoạn cảnh báo không thấy hình là lập tức luận hung; không tự mở rộng thành thuật toán cứu giải. |
| Mai Hoa | [Mai Hoa Dịch Số · Quyển II](https://zh.wikisource.org/w/index.php?oldid=1441921) | Thể/Dụng, diễn tiến Hỗ/Biến và đoạn riêng cầu tài/giao dịch/mưu sự. Giải thích chiều nhận/cho/hỗ trợ/sức ép, giữ đúng chủ đề. |
| Lục Hào | [Tăng San Bốc Dịch · Dụng thần](https://zh.wikisource.org/w/index.php?oldid=2100700), [Nguyên/Kỵ](https://zh.wikisource.org/w/index.php?oldid=2100299), [Nguyệt tướng](https://zh.wikisource.org/w/index.php?oldid=2100331), [Nhật thần](https://zh.wikisource.org/w/index.php?oldid=2100338) | Dụng thần là đối tượng đang hỏi; Nhật–Nguyệt có thể khác chiều. Nhật xung hào tĩnh có sức khác Nhật phá hào suy. Không tự đổi hào trọng tâm. |
| Nghĩa kinh văn | [Chu Dịch · Càn](https://zh.wikisource.org/w/index.php?oldid=2404991), [Ký Tế](https://zh.wikisource.org/w/index.php?oldid=2572417); đối chiếu thêm [CTP · Ký Tế](https://ctext.org/book-of-changes/ji-ji/zh) | Giải nghĩa hình ảnh theo vị trí quẻ/hào; không lấy nghĩa hào thay phép Nạp Giáp. |

Các bản Wikisource được giữ raw + revision + hash; một số trang Tăng San tự đánh dấu chất lượng chép 50%, cần hiệu đính trước khi quảng bá là bản chuẩn. Ba đoạn Tử Bình đã xác minh được qua chỉ mục nội dung web; máy chủ timeout khi tải trực tiếp. Vì vậy chỉ lưu trích đoạn ngắn cùng URL và hash, trạng thái **WEB_EXCERPT_NOT_EDITION_PINNED**; không tuyên bố đã ghim toàn bộ ấn bản hoặc triển khai phương pháp đầy đủ từ sách.

Không chép bài diễn giải hiện đại, bản dịch thương mại hoặc mệnh lệ trên blog thành mẫu của project. Các ví dụ đời sống bên dưới là nội dung biên soạn mới.

## Vì sao lời luận hiện tại khó đọc?

1. Module mới trả chính xác tên bảng và trạng thái nội bộ nhưng chưa dịch chúng thành một câu trả lời gắn việc đang hỏi.
2. Nhiều câu lặp những từ trừu tượng như “trục”, “sinh xuất”, “nguồn lực”, “cầu nối”; người đọc không biết quan sát điều gì trong đời sống.
3. Một phần engine còn sơ bộ: cách cục là ứng viên; Điều hậu là gợi ý mùa; Bát Tự chưa có Đại vận/Lưu niên và chưa hiểu ngữ nghĩa câu hỏi. Prompt không thể tạo các phép tính còn thiếu.
4. Hiện không có model ở runtime. Thêm file few-shot chỉ chuẩn bị cách viết cho lớp diễn giải sau này; không tự sửa các template đang hiển thị.

Hướng viết: **dữ kiện của phiên → nghĩa đơn giản → liên hệ có điều kiện → việc có thể tự kiểm tra**. Mỗi nhận định cần căn cứ; mỗi ứng dụng đời sống có nhãn biên tập riêng. Giới hạn kỹ thuật đặt trong phần căn cứ, chỉ nhắc ở câu trả lời khi nó thực sự ngăn việc kết luận.

## Ví dụ cách thay lời

Các ví dụ này là lát cắt giả định để dạy văn phong, không phải kết quả của một người dùng thật hoặc mệnh lệ cổ.

| Cách viết khó hiểu | Cách diễn giải mới |
|---|---|
| “Tài lộ nhưng đường sinh xuất chưa lộ.” | “Có Chính Tài trên can năm, nhưng nhãn này chưa cho biết bạn kiếm được bao nhiêu. Có thể đối chiếu bằng việc bạn tạo ra sản phẩm gì, ai trả tiền cho nó và tiền về theo cách nào.” |
| “Nhật chủ nhược, hỷ Ấn Tỷ.” | “Trong cách tính này, Nhật chủ ít được sinh trợ. Khi suy ngẫm về việc nhận thêm việc, hãy xem điều kiện hỗ trợ trước. Nhãn này chưa nói bạn kém năng lực hoặc yếu sức.” |
| “Dụng sinh Thể, chủ tiến ích.” | “Quan hệ đầu có chiều hỗ trợ từ phía việc đang hỏi về phía bạn. Nếu hỏi một khoản tiền, hãy kiểm tra nó đã được xác nhận tới bước nào; dấu hiệu này chưa có nghĩa tiền chắc chắn về.” |
| “Phụ mẫu lưỡng hiện, dụng chưa định.” | “Quẻ đang có hai hào đại diện hồ sơ, với điều kiện khác nhau. Chưa chọn được hào trọng tâm nên cần giữ hai khả năng riêng; chưa thể kết luận hồ sơ được duyệt.” |

Các bước kiểm tra công việc/học tập/thanh toán là **MODERN_APPLICATION**, không gán cho cổ thư. Một nhãn kỹ thuật không đủ để suy ra tính cách, nghề nghiệp, bệnh, mức giàu nghèo hoặc hành vi của người khác.

## Nội dung đã tạo và cách sử dụng

- `data/interpretation/plain_v2/cases.json`: 8 Bát Tự, 4 Mai Hoa, 3 Lục Hào, 2 Chu Dịch. Có đủ nhánh thuận, áp lực, trái chiều, chưa chọn được Dụng và thiếu dữ kiện.
- `sources.json`: 20 trích đoạn/quy ước có hash, URL, phạm vi phương pháp và tình trạng chụp nguồn.
- `evals.json`: 8 câu hỏi khác dùng để đánh giá; không được bơm vào prompt như ví dụ mẫu.
- `docs/prompts/plain_vietnamese_v2.system.txt`: chỉ dẫn trình bày và giới hạn suy diễn.
- `research_tools/interpretation_prompt.py`: chọn tối đa 3 cặp theo **phương pháp → tín hiệu phân tích → chủ đề**; câu hỏi không điều khiển selector. Ghép thành system + user/assistant examples + context cuối.
- `schemas/plain_reading_*.schema.json`: contract mới, không thay contract v1 của phần gieo bộ số.

Adapter Bát Tự đọc một `BaziResponse` đã lưu, giữ nguyên facts/findings/evidence/trạng thái, không tính lịch hoặc phân tích lại. Bỏ tên và thời điểm sinh khỏi payload prompt; giữ các dữ kiện lá số cần luận. Câu hỏi tự do vẫn cần được xem là dữ liệu có thể chứa thông tin người dùng tự nhập. Adapter cho Mai Hoa/Lục Hào hiện chưa nối API runtime; các mẫu đã có context riêng để nghiên cứu.

```sh
.venv/bin/python -m scripts.build_plain_interpretation_data
.venv/bin/python -m research_tools.interpretation_prompt \
  examples/bazi_consultation_response.json --bazi-snapshot \
  --output /tmp/arcana_plain_prompt_preview.json
.venv/bin/python -m unittest tests.test_interpretation_prompt -v
```

Đầu ra công cụ có `model_called=false`. Các file này không tạo cuộc gọi mạng, không cấu hình provider/model, không thay snapshot và không làm lời luận đang hiển thị mang nhãn AI đã được kiểm chứng.

## Kiểm định nội dung trước khi nối vào giao diện

Đã kiểm tra tự động: schema, hash nguồn, nguồn đúng phương pháp, ref không lẫn giữa ví dụ và phiên thật, JSON không được ghi đè facts/điểm/số, câu hỏi chứa chỉ dẫn vẫn ở user data, adapter không tính lại lá số. Kiểm tra này không chứng minh prose đúng nghĩa, chống prompt injection tuyệt đối hoặc dễ hiểu với người bình thường.

Khi chạy model, so cùng 8 context đánh giá với/không có few-shot. Chấm riêng 5 tiêu chí, mỗi tiêu chí 0–2: bám câu hỏi, dùng dữ kiện cụ thể, giải nghĩa thuật ngữ, ứng dụng đời thường phù hợp, giữ đúng mức chắc chắn. Một câu bịa dữ kiện, trái finding, trích nguồn thiếu hoặc đổi Dụng là lỗi loại ngay, dù văn phong hay. Mục tiêu biên tập là ít nhất 8/10 và không có lỗi loại; chưa có điểm thực nghiệm nào được báo ở đây. Nên thêm lượt đọc của người chưa học lý số và hiệu đính chuyên môn trước khi đổi trạng thái review.

**Trạng thái:** bộ mẫu biên tập và công cụ ghép prompt đã có; đánh giá chất lượng từ model/người dùng/chuyên gia **chưa chạy**. Lời luận runtime vẫn là template hiện hành.
