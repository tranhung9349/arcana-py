# Tra ngày theo việc — danh mục việc trọng đại

Ngày nghiên cứu: **25/10/2026**, UTC+7. Nội dung dưới đây lưu **bản đề xuất trước triển khai**.

**Đã triển khai sau khi người dùng chốt:** đủ 7 nhóm/18 việc chính; nạp thái, đính ước và an hương được giới hạn tên/phạm vi nghi thức và chỉ tra ngày. Xem [quyết định cuối, policy và kiểm chứng](../major_events_handoff.md). JSON nghiên cứu và số đếm giữ nguyên; registry runtime nằm tại `randomyst/date_activities.py`.

Đề xuất tổ chức lại thành **7 nhóm, 18 việc chính**, kèm **3 việc liên quan** chỉ hiện theo ngữ cảnh. Ưu tiên đợt mở rộng đầu: **nhập trạch, chuyển nơi cư trú, tu tạo/sửa chữa lớn, giao dịch tài sản lớn**. Sau đó bổ sung các mốc quan trọng cần chế độ chỉ tra ngày, gồm động thổ và lập văn khế.

Bản này thay **thứ tự ưu tiên và cách phân nhóm** trong [nghiên cứu 14/10](mvp2_activity_expansion.md). Giữ nguyên báo cáo cũ và số đếm lịch sử. Danh mục mới ở [mvp2_major_event_catalog.json](mvp2_major_event_catalog.json), bằng chứng dữ liệu ở [mvp2_major_event_coverage.json](mvp2_major_event_coverage.json).

## 1. Tiêu chí đưa vào nhóm trọng đại

Đây là tiêu chí thiết kế sản phẩm, chưa phải thang đo cổ truyền hoặc kết quả khảo sát nhu cầu:

1. Việc tạo bước chuyển đáng kể trong quan hệ gia đình, chỗ ở, công danh, tài sản hoặc trách nhiệm gia tộc.
2. Người dùng xác định được **một mốc hành động** có thể chủ động chọn ngày: thành hôn, vào ở, khởi công, ký văn khế, nhận chức…
3. Xác định được **người trực tiếp đứng việc/chịu tác động**, thay vì mặc định lấy hồ sơ người đang đăng nhập.
4. Có thể đối chiếu với một mục dụng sự cụ thể; token và luật phải đúng phạm vi của mốc đó trước khi bật tính năng.

Mức độ trọng đại và mức sẵn sàng kỹ thuật là hai trục riêng. Động thổ là việc chính dù chưa có Yi giờ; an sàng có dữ liệu giờ tốt hơn nhưng được xếp thành việc liên quan. Không dùng độ nhiều token để quyết định việc nào quan trọng với con người.

## 2. Căn cứ nghiên cứu

[Hiệp Kỷ Biện Phương Thư, quyển 11 — Dụng sự, revision 787353](https://zh.wikisource.org/w/index.php?oldid=787353) liệt kê từng việc cùng mục nên/kỵ, trong đó có hôn lễ, di chuyển, xây dựng, mở chợ, văn khế/giao dịch, nhậm chức và nhập học. Điều này hỗ trợ cách thiết kế **chọn nhóm rồi chọn việc cụ thể**. Bản chép có các mục được đối chiếu chung; không suy rằng mọi token provider đều tương ứng một mục cổ độc lập hoặc đều phải dùng bộ luật riêng hoàn toàn.

Đối chiếu nghĩa thuật ngữ bằng các nguồn do Bộ Giáo dục Đài Loan cung cấp: [nạp thái](https://dict.revised.moe.edu.tw/dictView.jsp?ID=56243&la=0&powerMode=0), [lập khoán giao dịch](https://pedia.cloud.edu.tw/Entry/Detail/?title=%E7%AB%8B%E5%88%B8%E4%BA%A4%E6%98%93), [điền sản](https://dict.revised.moe.edu.tw/dictView.jsp?ID=114528), [nạp tài](https://dict.revised.moe.edu.tw/dictView.jsp?ID=56242&la=1&powerMode=0). Đây là căn cứ về nghĩa từ, không xác nhận toàn bộ ánh xạ sang nghi lễ Việt Nam hoặc nghiệp vụ hiện đại.

[Tài liệu tác giả provider](https://6tail.cn/calendar/lunar.yiji.html) mô tả contract Yi/Ji và sự khác biệt có thể có giữa các lịch. Audit dùng **corpus local đã ghim `lunar-python==1.4.8`**, không dùng phiên bản mới nhất để thay bảng hiện hành. Bản chép cổ chỉ dùng nghiên cứu danh mục; không biến các bảng natal/điểm sản phẩm hiện tại thành phương pháp cổ đã hiệu đính.

## 3. Bảy nhóm đề xuất

| Nhóm trên giao diện | Việc chính | Mốc phải chọn rõ |
| --- | --- | --- |
| **Hôn nhân, gia thất** | Thành hôn; nạp thái — lễ ngỏ lời; đính ước | Bắt đầu đúng nghi thức đang tra |
| **An cư, chỗ ở** | Nhập trạch; chuyển nơi cư trú | Nghi thức vào ở hoặc mốc chuyển cư |
| **Xây dựng, tu tạo** | Động thổ xây dựng; tu tạo/sửa chữa lớn; thượng lương | Khởi công từng hạng mục hoặc gác đòn nóc |
| **Kinh doanh, tài sản** | Khai trương; lập văn khế/ký kết mua bán; giao dịch tài sản lớn; mua nhà đất; nạp tài | Mở bán, giao kết, mua/giao nhận hoặc thu tài vật |
| **Công danh, học nghiệp** | Nhậm chức/nhận nhiệm vụ; nhập học | Bắt đầu nhận chức trách hoặc nhập học |
| **Xuất hành trọng yếu** | Xuất hành | Bắt đầu chuyến đi công việc, học tập hoặc xuất ngoại đã xác định |
| **Gia tiên, lễ nghi** | Tế lễ gia tiên; an hương/an vị thờ tự | Bắt đầu nghi lễ trọng yếu có thể chọn ngày |

Tên nhóm mang văn phong Hán Việt vừa đủ; cách phân nhóm là quyết định UX. Không gọi toàn bộ danh mục hoặc phương pháp hiện hành là quy chuẩn Nho giáo.

Ba việc liên quan: **an sàng** trong an cư/hôn lễ; **tháo dỡ** trong xây dựng; **cầu phúc** trong nghi lễ. Vẫn giữ category/token độc lập khi đánh giá, chỉ giảm độ ưu tiên hiển thị. Mỗi việc có một nhóm chính; dùng liên kết ngữ cảnh để tránh tạo bản sao category.

## 4. Danh mục, chủ thể và mức sẵn sàng

`LIVE`: đang chạy. `P1`: ưu tiên duyệt luật để mở rộng ngày + giờ. `P2`: cần contract chỉ tra ngày và duyệt phạm vi. `P3`: cần xử lý ánh xạ nghi lễ, dữ liệu thưa hoặc xung đột. Đây là **cổng công việc**, chưa là cam kết lịch phát hành.

| Khóa | Tên đề xuất | Token ngày | Token giờ/capability | Chủ thể đề xuất | Đợt |
| --- | --- | --- | --- | --- | --- |
| `MARRIAGE` | Thành hôn | `嫁娶` | `嫁娶`; giữ v1 | Hai đương sự | LIVE |
| `BETROTHAL_NACAI` | Nạp thái — lễ ngỏ lời | `纳采` | `订婚` mới là ứng viên | Hai đương sự | P3 |
| `BETROTHAL_COVENANT` | Đính ước | `订盟` | `订婚` mới là ứng viên | Hai đương sự | P3 |
| `HOME_ENTRY` | Nhập trạch | `入宅` | Trực tiếp `入宅` | Gia chủ | P1 |
| `RELOCATION` | Chuyển nơi cư trú | `移徙` | Trực tiếp `移徙` | Người chủ trì chuyển cư | P1 |
| `LAND_BREAKING` | Động thổ xây dựng | `动土` | Chỉ có Ji giờ | Chủ sự xây dựng | P2 |
| `RENOVATION` | Tu tạo, sửa chữa lớn | `修造` | Trực tiếp `修造` | Chủ sự tu tạo | P1 |
| `ROOF_BEAM` | Thượng lương | `上梁` | Chỉ có Ji giờ | Chủ sự xây dựng | P2 |
| `BUSINESS_OPENING` | Khai trương | `开市` | `开市`; giữ v1 | Chủ sự kinh doanh | LIVE |
| `CONTRACT_RITE` | Lập văn khế — ký kết mua bán | `立券` | Chỉ tra ngày | Người đứng giao kết | P2 |
| `TRADE` | Giao dịch tài sản lớn | `交易` | Trực tiếp `交易` | Người đứng giao dịch | P1 |
| `PROPERTY_ACQUISITION` | Mua nhà đất — điền sản | `置产` | Chỉ tra ngày | Người tạo lập điền sản | P2 |
| `RECEIVE_ASSETS` | Nạp tài — thu nhận tài vật | `纳财` | Chỉ tra ngày | Người thu nhận tài vật | P2 |
| `START_JOB` | Nhậm chức, nhận nhiệm vụ | `赴任` | Trực tiếp `赴任` | Người nhậm chức | P3 |
| `START_EDUCATION` | Nhập học | `入学` | Chỉ tra ngày | Người nhập học | P2 |
| `TRAVEL` | Xuất hành | `出行` | `出行`; giữ v1 | Người xuất hành | LIVE |
| `ANCESTOR_RITE` | Tế lễ gia tiên | `祭祀` | Trực tiếp `祭祀` | Người chủ lễ | P3 |
| `INCENSE_INSTALLATION` | An hương — an vị thờ tự | `安香` | Chỉ tra ngày | Người chủ lễ | P2 |

Hai hồ sơ hôn lễ là policy dự kiến kế thừa cách cá nhân hóa cặp đôi; cần duyệt riêng cho nạp thái/đính ước. Các việc còn lại dự kiến một người đứng việc. Kết quả của một hồ sơ không đại diện mọi người cư trú, mọi người trong đoàn hoặc cả hai phía giao kết.

Mục nhậm chức chưa tự bao gồm mọi ngày đầu đi làm; nhập học chưa bao gồm thi tuyển, phỏng vấn hay bái sư. Nạp thái/đính ước chưa tự đồng nghĩa toàn bộ lễ ăn hỏi Việt Nam. An hương là nhãn ứng viên, phải xác định việc lập mới, chuyển vị hay nghi thức nào trước khi ánh xạ. Những phạm vi này đã ghi từng mục trong JSON.

## 5. Độ phủ dữ liệu kiểm lại ngày 25/10

Đã quét **2.557 ngày dân sự Bắc Kinh và 33.241 mốc giờ** từ 2024–2030, mỗi ngày có 13 mốc kể cả hai mốc Tý; bỏ ngày đệm 01/01/2031. Có **114 token ngày và 34 token giờ**, tính cả token điều khiển như không có mục/kỵ chung. Đây không phải số ngày/khung đẹp ở Việt Nam sau cá nhân hóa.

| Việc | Yi ngày trực tiếp | Ji ngày trực tiếp | Yi giờ trực tiếp | Ji giờ trực tiếp | Ngày UNRESOLVED |
| --- | ---: | ---: | ---: | ---: | ---: |
| Nhập trạch | 650 | 873 | 12.563 | 0 | 0 |
| Chuyển nơi cư trú | 719 | 347 | 10.519 | 1.792 | 0 |
| Tu tạo, sửa chữa lớn | 663 | 115 | 11.501 | 9.678 | 0 |
| Giao dịch tài sản lớn | 561 | 86 | 11.678 | 0 | 4 |
| Động thổ | 824 | 577 | 0 | 4.858 | 0 |
| Thượng lương | 453 | 225 | 0 | 3.196 | 5 |
| Lập văn khế | 586 | 41 | 0 | 0 | 4 |
| Mua nhà đất | 76 | 124 | 0 | 0 | 3 |
| Nạp tài | 397 | 27 | 0 | 0 | 4 |
| Nhập học | 101 | 8 | 0 | 0 | 0 |
| An hương | 222 | 13 | 0 | 0 | 0 |
| Nhậm chức | 39 | 39 | 7.292 | 14.910 | 2 |
| Tế lễ | 1.696 | 178 | 8.917 | 9.158 | 82 |

Số token trực tiếp và trạng thái sau kỵ chung là hai phép đếm khác nhau. `UNRESOLVED` dùng hàm hiện hành: token nên đồng thời bị kỵ hoặc gặp kỵ chung. Không có Ji trực tiếp vẫn có thể bị kỵ chung. `NOT_LISTED` không phải mất dữ liệu.

Các điểm cần đưa vào cổng phát hành:

- Giao dịch có bốn ngày nguồn mâu thuẫn: **20/02/2024, 14/02/2025, 09/02/2026, 04/02/2027**. Giữ nguyên mâu thuẫn tại khung chịu ảnh hưởng.
- Nhậm chức chỉ có **một ngày Yi trong 2026**, trước cả lọc luật/cá nhân. Không được nới nghĩa hoặc đổi `NOT_LISTED` thành `SUPPORTED` để có thêm kết quả.
- `纳财` có **397 Yi ngày, 0 Yi giờ**; `求财` có **0 Yi ngày, 21.402 Yi giờ**. Có dữ liệu cả hai không tạo ra căn cứ tự ghép chúng thành cùng việc.
- Hai token `纳采`, `订盟` đều không có giờ cùng tên; `订婚` có 19.216 mốc Yi giờ. Đây là ứng viên cần duyệt nghĩa, chưa là mapping được chấp nhận.
- Tế lễ có 82 ngày nguồn mâu thuẫn. Mục này nhiều dữ liệu nhưng không phù hợp mở bằng cách thêm enum rồi dùng nguyên policy v1.

JSON bằng chứng giữ thống kê từng năm, toàn bộ ngày/mốc giờ mâu thuẫn và các token của miền chuyên biệt để nghiên cứu tiếp. Audit đối chiếu **42 bảng thống kê ngày/giờ** với báo cáo 14/10 và tất cả khớp.

```sh
.venv/bin/python -m research_tools.audit_major_event_catalog
```

## 6. Các ranh nghiệp vụ phải giữ

**Mua nhà** có thể gồm ký văn khế, thanh toán/nhận tài vật, nhận chuyển giao, nhập trạch và chuyển cư. Giao diện yêu cầu chọn mốc; mỗi mốc là một kết quả. Chọn nhập trạch không tự cho phép kết luận ngày ký mua nhà đẹp. Nếu triển khai chuỗi nhiều mốc sau này, từng mốc vẫn có scope riêng.

**Lập văn khế** tập trung ký kết mua bán theo nghĩa đã đối chiếu. Hợp đồng lao động, góp vốn và hợp tác hiện đại chưa tự kế thừa mục này. **Giao dịch tài sản lớn** là phạm vi sản phẩm cho `交易`; chữ lớn không có ngưỡng tiền cổ truyền.

**Xuất hành** giữ một category. Công tác, du học và xuất ngoại là mục đích chuyến đi để định hướng mô tả, không phải ba bộ token mới. Định cư có thể cần thêm mốc chuyển cư; chưa chọn hướng hoặc đánh giá thời điểm đến.

**Tu tạo/thượng lương/động thổ** phân biệt hành động. Nguồn cổ có trường hợp đối chiếu chung, nhưng provider có mảng Yi/Ji riêng nên cần giữ từng token. Nhà cửa, đất và thờ tự còn có bối cảnh địa điểm/phương vị; bản lịch + hồ sơ sinh phải nêu rõ phần chưa xét trước khi gọi là tư vấn đầy đủ.

## 7. Đề xuất luồng giao diện

1. Chọn **Nhóm việc trọng đại** từ bảy nhóm; hiển thị các việc chính của nhóm đã có capability được bật.
2. Chọn **Việc cụ thể**, đọc mô tả mốc được tra. Ví dụ nhóm kinh doanh/tài sản có lựa chọn lập văn khế và giao dịch riêng.
3. Nhập đúng hồ sơ người đứng việc. Nhãn theo vai trò; `user_1` chỉ là định danh API. Người thao tác hộ không bị dùng nhầm làm chủ thể.
4. Chọn khoảng ngày và, nếu có hỗ trợ, khung giờ tổ chức. Giới hạn 93 ngày và một lần dựng natal/người/request tiếp tục áp dụng.
5. Card ngày giữ chiều cao gọn. Popup hiển thị kết luận, phạm vi và giờ phù hợp nếu đã đánh giá được giờ.

Các mục nghiên cứu chưa bật không xuất hiện như lựa chọn có thể tra. Có thể có trang phạm vi/giải thích riêng; không tạo danh sách dài toàn lựa chọn bị khóa.

Với `DAY_ONLY`, card/popup ghi **“Đã xét ngày; chưa khuyến nghị giờ”** và lý do capability. `recommended_windows` trống không đủ biểu đạt, vì còn có thể mang nghĩa đã xét mà không tìm được giờ đẹp. Contract cần tách rõ `hour_evaluation = NOT_SUPPORTED` với `EVALUATED_NO_MATCH` và `HAS_RECOMMENDATIONS`. Đây là thiết kế dự kiến, chưa là trường API hiện hành.

Đánh giá ngày của `DAY_ONLY` phải là chế độ riêng: dùng facts và đối chiếu cá nhân theo **trụ ngày**, loại phần hành của trụ giờ; duyệt ngưỡng mới. Không gọi engine v1 lúc 12 giờ hoặc lấy điểm ngày + giờ v1 rồi chỉ giấu giờ trên client. Chia khoảng hiệu lực theo ranh ngày dân sự Bắc Kinh, ngày Bát Tự và giao Jie; một ngày Việt Nam có thể chứa nhiều đoạn khác nhau. Các đoạn này là phạm vi của đánh giá ngày, không gắn nhãn giờ đẹp. Với việc có Ji giờ như động thổ, có thể trình bày cảnh báo nguồn theo giờ riêng, nhưng không suy giờ nên từ phần giờ còn lại.

Với category mới có dữ liệu giờ trực tiếp, chỉ khuyến nghị khi **ngày và giờ cùng hỗ trợ đúng việc**, qua profile luật và xét cá nhân. Policy v1 của ba việc đang chạy vẫn giữ nguyên cho đến một thay đổi có version riêng.

## 8. Các miền trọng đại cần luồng chuyên biệt

**Tang sự, phần mộ** có an táng, phá thổ và cải táng. Đưa vào nhánh nghiên cứu riêng: xác định người mất, tang chủ/chủ lễ, nghi thức, bối cảnh phần mộ và phương pháp tương ứng. Corpus có token liên quan nhưng không đủ để dùng natal người đang thao tác làm đầu vào thay thế. Không gộp phá thổ phần mộ vào động thổ xây nhà; token `启钻` của provider cũng cần duyệt trước khi đại diện bước cải táng nào.

**Sức khỏe, sinh nở** là biến cố lớn nhưng token `求医`, `治病`, `针灸`, `求嗣` không tạo mapping trực tiếp cho phẫu thuật hoặc lịch sinh. Giữ ngoài danh mục tự động khuyến nghị ngày hiện tại; không tạo category kiểu “ngày mổ tốt”, “chọn ngày sinh” từ các token này.

Các việc sinh hoạt như cắt tóc, tắm gội và gặp bạn bè giữ ngoài màn chọn việc trọng đại. Đầu tư sinh lời, cơ may tiền bạc, thi cử, phỏng vấn và việc chung chung chưa có mapping trực tiếp đã duyệt. Mai Hoa tiếp tục là luồng hỏi/luận riêng; không dùng quẻ thay dữ liệu thiếu của bộ tra ngày.

## 9. Thứ tự triển khai cụ thể

| Đợt | Kết quả phải đạt | Cổng trước khi bật |
| --- | --- | --- |
| Nền tảng registry | Nhóm, việc, tên, role, token ngày/giờ, capability, mốc hành động, nguồn và review status | Đồng bộ builder, validator, schema và dropdown; registry chưa bật không lọt runtime |
| P1 — bốn việc mới | Nhập trạch, chuyển cư, tu tạo, giao dịch; tổng bảy việc đang dùng nếu đạt cổng | Duyệt scope luật/nghĩa/role; kiểm giờ trực tiếp, mâu thuẫn; giữ natal một lần/người |
| P2 — bảy việc chỉ tra ngày | Động thổ, thượng lương, văn khế, điền sản, nạp tài, nhập học, an hương | Contract ngày/capability, score ngày riêng, ranh hiệu lực; duyệt phạm vi hiện đại và bối cảnh địa điểm |
| P3 — bốn việc chính còn lại | Nạp thái, đính ước, nhậm chức, tế lễ; thêm ba việc liên quan khi đạt cổng | Duyệt mapping nghi thức/giờ, ca thưa và xung đột; không làm đẹp dữ liệu bằng điểm |

Không sao chép nguyên `SAT_CHU/THO_TU/NGUYET_PHA` sang mọi category mới. Phải duyệt từng scope; ngay trong bản chép dụng sự, mục phá nhà có cách dùng Nguyệt Phá khác các việc xây dựng. Điều này chưa tự chứng minh token `拆卸` đồng nhất mục phá nhà, nhưng đủ để bác bỏ cách mở rộng một luật cấm toàn bộ một cách máy móc.

Mỗi đợt cần kiểm ánh xạ từng việc, kỵ chung, Yi/Ji mâu thuẫn, không có giờ, giới hạn năm sinh, vai trò một/hai người, ranh UTC+8/UTC+7/Jie và replay/version. Nghiên cứu này đã kiểm danh mục/độ phủ và các số đếm lịch sử; chưa chạy đánh giá hiệu quả dự đoán hoặc hiệu đính chuyên gia.
