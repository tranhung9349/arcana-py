# Nghiên cứu lập và luận quẻ cho cầu tài, giao dịch và thời điểm

Ngày nghiên cứu: **24/10/2026**, UTC+7. Trạng thái: **đề xuất phương pháp, chưa bật tính năng mới**.

**Cập nhật 25/10:** người dùng đã chọn hoàn thiện Mai Hoa trước, để Lục Hào Nạp Giáp và ba đồng tiền sáu lượt thành tính năng sau. Phần Mai Hoa đã được triển khai theo [bản bàn giao](../maihoa_source_handoff.md); nội dung bên dưới giữ bối cảnh nghiên cứu trước triển khai.

## Kết luận để phát triển sản phẩm

Đề xuất hoàn thiện **Mai Hoa theo câu hỏi và loại việc** trước, vì app đã có lõi lập quẻ tương ứng. Sau đó nghiên cứu **Lục Hào Nạp Giáp** nếu cần luận sâu về cầu tài và ứng kỳ. Phép gieo ba đồng tiền nên là lựa chọn lập quẻ riêng, với cách đọc được ghi rõ; không tự động thay thế lõi Mai Hoa đã chốt.

Chức năng tra ngày hiện tại tiếp tục có kết quả lịch pháp/Bát Tự riêng. Chưa có cơ sở từ nghiên cứu này để cộng một “điểm Kinh Dịch” vào điểm ngày hoặc gọi ngày đứng đầu là “đại cát tiền bạc”. Tính đúng công thức, khớp kinh văn và khả năng dự báo kết quả thực tế là ba câu hỏi khác nhau.

## 1. Tách cách lập quẻ khỏi cách luận quẻ

| Thành phần | Trả lời câu hỏi | Ví dụ |
| --- | --- | --- |
| Lập quẻ | Sáu hào được tạo thế nào? | Thi thảo, ba đồng tiền, số hoặc thời gian Mai Hoa |
| Luận quẻ | Đọc những dấu hiệu nào, theo truyền thống nào? | Quẻ/hào từ; Thể–Dụng; Nạp Giáp/Lục thân |
| Luận ứng kỳ | Nếu phương pháp có cho phép, dấu hiệu được quy về thời điểm thế nào? | Quan hệ ngày/tháng với dụng thần trong Lục Hào |
| Trạch nhật | So sánh các thời điểm dự định để chọn lịch thực hiện | Engine chọn ngày hiện có |

Một kết quả gieo đồng tiền có thể được đọc theo quẻ/hào từ hoặc được dùng để lập bàn Lục Hào. Hai cách đọc có cấu trúc khác nhau. “Lục Hào” ở tài liệu này chỉ hệ **Lục Hào Nạp Giáp**, không chỉ việc mọi quẻ đều có sáu hào.

Hệ Từ có mô tả phép thi thảo dùng 49 trong 50 cọng và việc xem lời quẻ, lời hào, biến hóa. Đây là căn cứ về truyền thống văn bản, không phải bằng chứng kiểm nghiệm dự báo. [Hệ Từ thượng](https://ctext.org/book-of-changes/xi-ci-shang).

## 2. Những cách lập quẻ đã khảo sát

### 2.1. Mai Hoa theo năm–tháng–ngày–giờ

Bản truyền của *Mai Hoa Dịch Số*, quyển một, mục **年月日時起例** nêu cách lấy năm chi, tháng âm, ngày âm và chi giờ. Đánh số quái Càn 1, Đoài 2, Ly 3, Chấn 4, Tốn 5, Khảm 6, Cấn 7, Khôn 8. [Nguồn và hai ví dụ Quan Mai, Mẫu Đơn](https://zh.wikisource.org/zh-hant/梅花易數/卷一).

Với `r(n,k) = ((n-1) % k)+1`:

```text
S = Y + M + D
thượng quái = r(S, 8)
hạ quái     = r(S + H, 8)
hào động    = r(S + H, 6)
```

Hào đánh số từ dưới lên. Lật âm/dương ở hào động để được quẻ biến. Lõi hiện tại phù hợp với hai ví dụ số học đã đối chiếu; không kiểm chứng lời tiên đoán trong các câu chuyện ấy.

**Điểm sản phẩm:** cách lập này tất định, mỗi lần có đúng một hào động. Cùng `Y/M/D/H` sẽ cùng quẻ, kể cả hai người khác nhau. Không thêm ngày sinh, phút/giây, mã người dùng hay hash câu hỏi rồi vẫn gọi là công thức nguồn.

**Quy ước lịch của app:** chuyển cùng instant từ UTC+7 sang UTC+8; lấy ngày âm đổi lúc 00:00 Bắc Kinh, chi giờ Bắc Kinh; tháng nhuận giữ số tháng. Đây là profile sản phẩm đang khóa, không phải kết luận rằng cổ thư quy định múi giờ hiện đại hoặc cách xử lý tháng nhuận ấy. Giữ lịch sử và version khi nghiên cứu một profile khác.

Nguồn quyển một còn có câu về cách lấy hỗ đối với Càn/Khôn. Runtime hiện luôn lấy hào 2–3–4 và 3–4–5, kể cả hai quẻ thuần này. Cần chốt ngoại lệ nguồn trước khi quảng bá một bộ luận Mai Hoa đầy đủ; không âm thầm sửa profile cũ.

### 2.2. Ba đồng tiền, sáu lượt

*Bốc Phệ Chính Tông*, quyển một, mục **以錢代蓍法** mô tả gieo ba đồng, xếp từ dưới lên, phân hào tĩnh/động. Bản điện tử có lỗi OCR ở một số chỗ, nên cần đối chiếu ảnh sách trước khi số hóa bảng nguyên văn cho runtime. [Nguồn](https://www.shidianguji.com/book/AMNL0060/chapter/1ma05akk4w74j).

Có thể chuẩn hóa rõ một mặt trị số 2, mặt kia trị số 3. Không dùng nhãn “sấp/ngửa” thiếu hình minh họa. Tổng ba đồng cho một hào:

| Tổng | Trạng thái | Bit quẻ chủ | Bit quẻ biến | Xác suất với ba đồng công bằng, độc lập |
| --- | --- | ---: | ---: | ---: |
| 6 | Lão âm, động | 0 | 1 | 1/8 |
| 7 | Thiếu dương, tĩnh | 1 | 1 | 3/8 |
| 8 | Thiếu âm, tĩnh | 0 | 0 | 3/8 |
| 9 | Lão dương, động | 1 | 0 | 1/8 |

Thứ tự sáu hào và ánh xạ 6/7/8/9 cũng được mô tả trong [tài liệu của chương trình I Ching tại University of Oregon](https://hexadecimal.uoregon.edu/ching/explain.html). Chỉ tham khảo phần biểu diễn; không tiếp nhận cách chương trình ấy trộn câu hỏi vào bộ tạo số.

Xác suất trên được tự tính bằng cách liệt kê tám tổ hợp, không suy ra “độ linh”. Có thể có 0–6 hào động. Nhập sáu tổng do người dùng gieo thật và mô phỏng số là hai chế độ cần lưu provenance khác nhau. Mô phỏng phải lưu kết quả một lần theo phiên, không gieo lại khi xem hoặc tải lại.

### 2.3. Thi thảo

Phù hợp khi muốn trải nghiệm thao tác cổ điển. Hệ Từ mô tả khung thủ tục; một đoạn văn ngắn không đủ để chốt mọi chi tiết triển khai và xác suất của mọi cách chia cọng thực tế.

Báo cáo số học ghi riêng mô hình xác suất quy ước `6:7:8:9 = 1:5:7:3` trên 16. **Đây là mô hình khai báo để so sánh, chưa phải trình mô phỏng thao tác thi thảo đã được xác minh.** Không đổi giao diện của phép ba đồng tiền rồi gọi là thi thảo. Tạm hoãn lựa chọn này đến khi ghim được thủ tục và giả định chia cọng cụ thể.

### 2.4. Báo số, chữ và ngoại ứng

Mai Hoa có nhiều lối lấy số từ sự việc. Phần quan sát ngoại ứng đòi hỏi ngữ cảnh; không có căn cứ trong nghiên cứu này để coi một hash văn bản tiếng Việt là tương đương cách đếm chữ/âm cổ. Chưa ưu tiên tự động hóa nhóm này.

## 3. Ba hướng luận và mức phù hợp

### A. Đọc quẻ từ và hào từ Chu Dịch

Ưu điểm là có thể chỉ rõ câu nào được đọc. Tên quẻ riêng lẻ chưa đủ: cần hào động, quẻ biến, ngữ cảnh và một chính sách chọn lời.

Quy tắc thường dẫn từ *Dịch Học Khải Mông – Khảo biến chiêm* phân trường hợp theo số hào biến: 0 đọc quẻ chủ; 1 đọc hào động; 2 đọc hai hào động, ưu tiên hào trên; 4 đọc hai hào tĩnh ở quẻ biến, ưu tiên hào dưới; 5 đọc hào tĩnh duy nhất ở quẻ biến; 6 dùng Dụng Cửu/Dụng Lục cho Càn/Khôn, các quẻ khác đọc quẻ biến. Trường hợp 3 đọc hai quẻ còn có chi tiết chủ–phụ theo nhóm biến. [Bản điện tử quyển bốn](https://www.shidianguji.com/book/NA00534/chapter/1m2s6izxhwzdn), [bản chú giải cổ](https://ctext.org/wiki.pl?chapter=427773&if=en).

**Mức sẵn sàng: nghiên cứu sơ bộ.** Bản đầu có OCR xấu; bản sau chỉ đọc được đoạn lập chỉ mục, truy cập trang bị 403. Chưa dùng các nguồn này làm bảng luật production. Nếu triển khai, phải ghim bản đọc rõ, kiểm đủ 0–6 hào, đặc biệt quy tắc ba hào; không tự đặt một “hào chủ” khi chưa chốt. Đây cũng là một truyền thống đọc, không phải luật duy nhất mọi trường phái đều dùng.

Hướng này hợp mục tiêu đọc và suy xét một tình huống. Không có một bảng từ kinh văn đã được xác minh ở đây để tự động chuyển mọi câu thành điểm lợi nhuận.

### B. Mai Hoa: Thể–Dụng theo loại việc

**Phát hiện quan trọng:** quyển hai có mục **求財占第十** và **交易占第十一**. Trong mục cầu tài, Thể đại diện phía người hỏi, Dụng đại diện tài; nguồn luận các quan hệ như sau. [Nguyên văn](https://zh.wikisource.org/zh-hant/梅花易數/卷二).

| Quan hệ | Nghĩa theo đoạn cầu tài | Nhãn ứng viên, chưa phải kết luận toàn quẻ |
| --- | --- | --- |
| Dụng sinh Thể | Tiến ích về tài | Có dấu hiệu hỗ trợ |
| Thể khắc Dụng | Có tài | Có dấu hiệu thuận |
| Thể–Dụng cùng hành | Tài lợi thuận ý | Có dấu hiệu thuận |
| Thể sinh Dụng | Lo hao tổn | Có dấu hiệu hao tổn |
| Dụng khắc Thể | Bất lợi cầu tài | Có dấu hiệu trở ngại |

Quan hệ này là một căn cứ, không phải toàn bộ phép luận. Cần xét thêm hỗ/biến, vượng suy và lời hào theo profile đã chọn; khi các căn cứ khác chiều thì hiển thị riêng. Quy tắc ứng kỳ trong đoạn nguồn còn cần làm rõ cách quy đổi ra lịch; chưa cho phép trả ngày thu tiền cụ thể chỉ từ bảng trên.

Các mức “có dấu hiệu…” là **đề xuất diễn đạt sản phẩm**, không phải bản dịch nguyên văn hay xác suất thành công. Mục giao dịch phải có rule/evidence riêng, dù một số quan hệ giống cầu tài. Trong hệ này, Thể không tự động bằng Nhật chủ; Dụng quái không đồng nghĩa Dụng thần Bát Tự.

### C. Lục Hào Nạp Giáp

Đây là ứng viên để nghiên cứu sâu hơn câu hỏi tiền bạc và ứng kỳ, theo đánh giá về cấu trúc nghiệp vụ, **không phải khẳng định độ chính xác cao hơn**. Hệ này cần an quái cung, Nạp Giáp từng hào, Lục thân, Thế/Ứng, chọn dụng thần rồi xét ngày/tháng và động biến.

Mục *Dụng thần* của *Tăng San Bốc Dịch* lấy hào Tài cho nhiều câu hỏi về tiền, hàng hóa; văn khế lại thuộc một nhóm nghĩa khác. Không thể dùng một token “tiền nong” để quyết định mọi câu hỏi. [Nguyên văn được chép lại, tách khỏi bạch thoại và lời “乾按”](https://shuyuan.zhiming.life/read/增删卜易/7).

*Động biến* còn quy định cách an Lục thân cho hào biến theo quẻ chủ. Đây là khác biệt với việc chỉ đọc tên quẻ biến. [Tăng San Bốc Dịch, chương 7](https://zh.wikisource.org/wiki/增刪卜易/7).

Các bảng và phép xét cần số hóa: 64 quẻ/8 cung; Nạp Giáp; Thế/Ứng; Lục thân; nhật thần/nguyệt kiến; tuần không; vượng suy; động–biến, hồi đầu sinh/khắc; phục thần; các điều kiện ứng kỳ. Phải chốt thứ tự xử lý khi nhiều điều kiện cùng xảy ra. Không rút gọn thành “Tài vượng = đại cát” hoặc “không thấy Tài = không có tài”.

**Mức sẵn sàng:** chưa có corpus/bộ luật Lục Hào đã ghim trong repo. Bản toàn văn [Tăng San Bốc Dịch trên Wikisource](https://zh.wikisource.org/zh-hant/增刪卜易) có lời người nhập thừa nhận lỗi và phần “原劍增訂說明” bổ sung hiện đại. Không coi toàn trang là nguyên văn cổ đã khảo chứng. Cần chọn bản nền, tách lời chú, kiểm bảng bằng ảnh sách và các bàn quẻ mẫu trước khi triển khai.

## 4. Đối chiếu với app đang có

Đã đọc trực tiếp các file; graph có metadata ngày 22/10/2026 nhưng `gitCommitHash=unversioned`, workspace không có Git để xác minh drift. Kết luận dưới đây dựa trên source và hash trong audit, không coi graph là bằng chứng cuối cùng.

| Thành phần | Hiện trạng | Hệ quả |
| --- | --- | --- |
| `randomyst/maihoa.py` | Đúng bốn số Y/M/D/H; một hào động; có chủ/hỗ/biến | Dùng lại lõi số học cho profile Mai Hoa hiện tại |
| `randomyst/engine.py` | Lập Mai Hoa từ thời điểm gieo; ngày sinh dùng cho phần Bát Tự riêng | Không gọi quẻ thời điểm là quẻ cá nhân hóa bởi ngày sinh |
| `randomyst/sampling.py::state_of` | Dụng sinh Thể → `DAI_CAT`; cùng hành → `BINH_HOA`; Thể khắc Dụng → `THU_CAT` | Đây là nhãn quan hệ của MVP 1; chưa phải phán đoán cầu tài toàn diện |
| `randomyst/interpretation.py` | Trả quẻ từ, một hào động và bản nghĩa Việt nháp; hỗ/biến để xem thêm | Chưa phải bộ chọn lời cho nhiều hào hoặc luận tài theo việc |
| Corpus Hán | 64 quẻ, 384 hào thông thường, có thêm Dụng Cửu/Dụng Lục | Hai mục đặc biệt chưa được API/bản nháp Việt hiện hành phục vụ đầy đủ |
| `randomyst/date_engine.py` | Luật lịch/Yi-Ji và hồ sơ Bát Tự, không gọi Mai Hoa | Chưa có điểm hoặc kết luận ngày theo Dịch học |

Bản Việt đang là `AI_TRANSLATION/AI_INTERPRETATION`, `UNREVIEWED`; hash đảm bảo ràng buộc văn bản, không chứng nhận nghĩa dịch. Quẻ 32 thiếu Thoán truyện ở nguồn ghim. Không suy diễn phần thiếu hoặc tự nâng nhãn đã hiệu đính.

**Chưa sửa** quy tắc sinh số, nhãn cũ, lịch, điểm ngày, API, UI hay lịch sử trong đợt nghiên cứu này.

## 5. Áp dụng cho “ngày thuận tiền nong” thế nào?

Phải phân biệt ba thời điểm trong dữ liệu: **lúc hỏi/lập quẻ**, **thời hạn câu hỏi**, và **lúc dự định thực hiện việc**. Ghi cả ba khi có; không lấy chúng thay thế nhau.

1. **Hỏi một việc:** “Tôi dự định đàm phán thu hồi khoản công nợ A trong tháng tới; theo phép luận này có những điểm thuận và trở ngại gì?” Lập một quẻ cho câu hỏi, lưu phiên và luận theo loại việc đã xác định.
2. **Tra lịch thực hiện:** chọn loại việc, người đứng việc và khoảng ngày trong engine hiện có. Nếu kèm quẻ tham khảo, trình bày hai kết quả độc lập, ghi khác biệt; không tự cộng điểm.
3. **Luận ứng kỳ:** giữ quẻ gốc, áp dụng một bộ luật ứng kỳ đã chốt để suy xét các thời điểm trong hạn hỏi. Chưa triển khai từ nghiên cứu sơ bộ này.

Thay thời gian hỏi bằng từng giờ tương lai rồi chọn quẻ tốt nhất là một thiết kế khác. Nếu thử nghiệm, phải gọi rõ **“Quẻ tượng theo thời điểm dự kiến”**, ghi `PRODUCT_DERIVED/EXPERIMENTAL`, và không quảng bá là phép trạch nhật cổ đã xác minh. Lặp nhiều lần gieo ngẫu nhiên rồi giữ kết quả đẹp cũng không phải so sánh cùng một quẻ.

Không chia “may mắn tiền nong” theo loại thu nhập để tự động hứa hẹn có tiền. Phạm vi thử ban đầu nên là **cầu tài từ một việc đã nêu** và **giao dịch**; các trường hợp hợp đồng, công nợ, góp vốn cần mapping nghiệp vụ riêng trước khi kích hoạt.

## 6. Đề xuất cấu trúc chức năng mới

Luồng dự kiến: **Nêu việc → Chọn cách lập quẻ → Xác nhận dữ liệu → Xem căn cứ và lời luận → Đọc lại phiên đã lưu**. Tên người phía client: **Người hỏi** hoặc **Đương sự**; “Gia chủ” chỉ dùng khi vai trò gắn với gia trạch/nghi thức thích hợp.

Contract khái niệm, chưa phải JSON Schema production:

```text
consultation_id, question_text, topic, target_period
casting_method, casting_method_version, casting_time
event_time?                        # khác casting_time
calendar_policy_id?                # bắt buộc khi cách lập dùng thời gian
raw_inputs                         # Y/M/D/H hoặc đủ sáu tổng 6..9
lines_bottom_to_top, moving_lines[] # dùng mảng; không ép thành một hào
original_hexagram, changed_hexagram, mutual_hexagram?
reading_school, reading_rules_version, source_corpus_version
findings[]: rule_id, premise, conclusion, evidence_refs, provenance
source_coverage, unresolved_rules[], interpretation_review_status
```

`changed_hexagram` có thể null khi không có hào động; nếu lưu trạng thái đích giống quẻ chủ để tiện toán học, UI vẫn phải nói “không có hào biến”. `source_coverage` nói về độ đủ của nguồn; không gọi là xác suất lời luận đúng.

Đề xuất provenance: `PRIMARY_TEXT`, `TRADITIONAL_COMMENTARY`, `PRODUCT_DERIVED`, `AI_DRAFT`. Lời luận phải trỏ về evidence; mô hình ngôn ngữ chỉ diễn đạt từ facts và phần nguồn đã cung cấp, không tự an quẻ hoặc đặt rule còn thiếu.

Ví dụ kết quả sau khi có đủ rule: “Về quan hệ Thể–Dụng, có dấu hiệu hỗ trợ cho việc giao dịch. Căn cứ khác đang có cảnh báo, nên chưa đủ điều kiện kết luận thuận lợi toàn diện.” Không trả số tiền lời, tỷ lệ thành công hay nhãn đại cát chỉ từ một dấu hiệu. Ngày sinh không bắt buộc cho lõi Mai Hoa/đồng tiền; chỉ lấy thêm nếu có một lớp Bát Tự được ghi riêng.

## 7. Các bước để thành đặc tả có thể triển khai

| Bước | Đầu ra cần có | Điều kiện hoàn thành |
| --- | --- | --- |
| D1 — Ghim nguồn và profile Mai Hoa | Trích đoạn được kiểm, phiên bản nguồn, bảng rule theo việc | Quyết định ngoại lệ Càn/Khôn, hỗ/biến, vượng suy; mỗi rule có evidence và provenance |
| D2 — Bộ luận offline theo việc | Facts/căn cứ/lời luận cho cầu tài và giao dịch | Các ví dụ nguồn, ca xung đột và ca thiếu nguồn được kiểm; chưa nối điểm ngày |
| D3 — Phiên tư vấn trong app | API/UI/lưu phiên, đọc lại ổn định | Lưu thời điểm/phương pháp; không tái lập quẻ khi mở lại; nguyên văn và bản nghĩa phân biệt rõ |
| D4 — Phép ba đồng tiền tùy chọn | Nhập tay/mô phỏng, sáu hào, chính sách đọc riêng | Kiểm đủ 0–6 hào động, Dụng Cửu/Lục; chốt chính sách nhiều hào bằng nguồn đọc rõ |
| D5 — Lục Hào/ứng kỳ | Corpus, an bàn và bộ luật mới | Kiểm đủ 64 quẻ/8 cung, Thế/Ứng/Nạp Giáp/Lục thân; ca biên lịch và bàn quẻ mẫu độc lập |

Đây là thứ tự đề xuất dựa trên khả năng tái sử dụng và độ đầy đủ dữ liệu hiện có, chưa phải cam kết độ chính xác học thuật hoặc thời hạn giao tính năng. Yêu cầu hiện tại là nghiên cứu; chưa coi các quyết định phương pháp mới là đã được người dùng chốt.

## 8. Bằng chứng số học và giới hạn nguồn

Chạy lại:

```sh
.venv/bin/python -m research_tools.audit_iching_methods
```

Kết quả: [iching_methods_audit.json](iching_methods_audit.json). Script chỉ đọc source/corpus, không gọi API gieo, không đọc SQLite và không ghi lại config.

- Liệt kê 4.096 vector sáu hào với giá trị 6/7/8/9; ánh xạ đủ 64 quẻ và 4.096 cặp chủ–đích.
- Với giả định đồng tiền công bằng, độc lập: khoảng **17,80%** không có hào động; **35,60%** có một; **46,61%** có từ hai trở lên. Schema chỉ nhận một hào sẽ bỏ sót nhiều trường hợp hợp lệ.
- Liệt kê 51.840 tuple số nguyên Mai Hoa hợp lệ: đủ 64 quẻ nhưng **192 cặp quẻ/hào động**, ba vị trí động mỗi quẻ; do số hạ quái và hào động luôn cùng chẵn/lẻ. Đây là tính chất công thức, không phải lỗi cần “bù ngẫu nhiên”. Các tuple không phải 51.840 ngày thực, và không dùng như phân bố tần suất theo lịch.
- Hai ví dụ số học: Quan Mai → quẻ 49, động 1, biến 31, hỗ 44; Mẫu Đơn → quẻ 44, động 5, biến 50, hỗ 1. Khớp không xác nhận các sự kiện được kể đã xảy ra.
- Có hai mục Hán Dụng Cửu/Dụng Lục ngoài 384 hào thường; bản Việt hiện mỗi quẻ chỉ có sáu hào.

Nguồn web được đọc ngày 24/10/2026. Wikisource là bản chép điện tử có thể thay đổi; các đoạn được dẫn trong nghiên cứu **chưa được nhập thành corpus production với ảnh trang, revision và checksum**. CText có đoạn đọc được qua chỉ mục nhưng một số trang trả 403. Hai bản OCR đã ghi rõ ở trên không đạt tiêu chuẩn ghim luật. Nghiên cứu hiện đủ để đề xuất phạm vi và thiết kế dữ liệu, chưa đủ để công bố bộ luận đã hiệu đính hoặc có năng lực dự báo được kiểm chứng.
