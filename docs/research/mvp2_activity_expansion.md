# Mở rộng “Việc dự định” và cách hiển thị hồ sơ, giờ đẹp

Ngày nghiên cứu: **14/10/2026**, UTC+7. Trạng thái tại thời điểm nghiên cứu: **đề xuất phạm vi; category mới chưa bật trong runtime**.

**Bản hiện hành 25/10:** [đã triển khai 7 nhóm/18 việc](../major_events_handoff.md); phần còn lại giữ nội dung nghiên cứu lịch sử.

**Cập nhật 25/10/2026:** [Danh mục việc trọng đại](mvp2_major_life_events.md) tổ chức lại thành 7 nhóm/18 việc chính và thay thứ tự ưu tiên mở rộng dưới đây. An sàng chuyển thành việc liên quan theo ngữ cảnh; bốn việc ưu tiên là nhập trạch, chuyển cư, tu tạo và giao dịch. Báo cáo 14/10 giữ nguyên để đối chiếu lịch sử.

Bro nên mở rộng theo nhóm việc, nhưng giữ mỗi nghi thức thành một category riêng. Đề xuất đợt kế tiếp thêm **nhập trạch, chuyển chỗ ở, an sàng, sửa chữa/tu tạo và giao dịch**. Đây là ưu tiên sản phẩm dựa trên khả năng dữ liệu hiện có và mức sửa engine; chưa có khảo sát nhu cầu người dùng để khẳng định độ phổ biến.

## Căn cứ và giới hạn

Đã duyệt [repo của provider 6tail](https://github.com/6tail/lunar-python), [chỉ mục API](https://6tail.cn/calendar/api.html) và [tài liệu Yi/Ji theo giờ](https://6tail.cn/calendar/lunar.timeyiji.html). Provider trả mảng nên/kỵ và dùng `无` khi không có mục. Tài liệu cũng ghi dữ liệu có thể khác các lịch khác, dùng để tham khảo. Chưa coi tên token là bằng chứng phương pháp chọn ngày đã được hiệu đính.

Corpus local đã ghim `lunar-python==1.4.8` lưu **toàn bộ token**, nên không phải thu thập lại lịch 2024–2030 cho các việc mới. Audit dưới đây đọc **2.557 ngày dân sự Bắc Kinh và 33.241 mốc giờ** trong 2024–2030; bỏ ngày đệm 01/01/2031. Mỗi ngày có 13 mốc, gồm hai mốc Tý. Số lượng này không phải số khung ngày Việt Nam, cũng không phải số ngày/giờ đẹp sau cá nhân hóa.

Audit giữ riêng: token xuất hiện trong Yi/Ji; trạng thái `SUPPORTED/AVOID/NOT_LISTED/UNRESOLVED` theo hàm hiện hành; các ngày mâu thuẫn; thống kê mỗi năm. `NOT_LISTED` là không đề cập việc đó, không đồng nghĩa dữ liệu bị mất. Mục kỵ chung vẫn có thể chặn một giờ dù token kỵ riêng có số đếm bằng 0.

Tệp bằng chứng: [mvp2_activity_token_coverage.json](mvp2_activity_token_coverage.json). Mã tái lập: [audit_activity_categories.py](../../research_tools/audit_activity_categories.py).

```sh
.venv/bin/python research_tools/audit_activity_categories.py
```

## Phân nhóm và thứ tự mở rộng

Giữ ba category hiện tại: `MARRIAGE` → `嫁娶`, `BUSINESS_OPENING` → `开市`, `TRAVEL` → `出行`. “Cưới hỏi” hiện dựa vào token thành hôn; khi mở rộng nên đổi tên rõ thành **“Thành hôn”**, tách dạm hỏi/đính ước ở mục riêng.

| Nhóm | Category dự kiến | Token ngày → giờ | Đợt |
| --- | --- | --- | --- |
| Gia thất | Nhập trạch | `入宅` → `入宅` | Kế tiếp |
| Gia thất | Chuyển chỗ ở | `移徙` → `移徙` | Kế tiếp |
| Gia thất | An sàng — đặt giường | `安床` → `安床` | Kế tiếp |
| Nhà cửa | Sửa chữa, tu tạo | `修造` → `修造` | Kế tiếp |
| Kinh doanh | Giao dịch | `交易` → `交易` | Kế tiếp; xử lý 4 ngày mâu thuẫn |
| Hôn lễ | Nạp thái — lễ dạm hỏi | `纳采` → ứng viên `订婚` | Chốt nghĩa và mapping trước |
| Hôn lễ | Đính ước | `订盟` → ứng viên `订婚` | Chốt nghĩa và mapping trước |
| Kinh doanh | Lập văn khế | `立券` → chưa có Yi/Ji giờ | Nghiên cứu chế độ chỉ tra ngày |
| Nhà cửa | Động thổ | `动土` → chỉ có Ji giờ | Nghiên cứu chế độ chỉ tra ngày |
| Nhà cửa | Thượng lương — gác đòn nóc | `上梁` → chỉ có Ji giờ | Nghiên cứu chế độ chỉ tra ngày |
| Nhà cửa | Tháo dỡ | `拆卸` → chưa có Yi/Ji giờ | Duyệt phạm vi luật và chế độ chỉ tra ngày |
| Nghi lễ | Tế lễ | `祭祀` → `祭祀` | Sau; có 82 ngày mâu thuẫn |
| Nghi lễ | Cầu phúc | `祈福` → `祈福` | Sau; có 5 ngày mâu thuẫn |
| Công việc | Nhậm chức | `赴任` → `赴任` | Sau; Yi ngày rất thưa |
| Sinh hoạt | Hội họp thân hữu, cắt tóc | `会亲友`, `理发` → chưa có Yi/Ji giờ | Chỉ tra ngày khi có contract phù hợp |
| Sức khỏe | Cầu y, trị bệnh | `求医`, `治病` → chưa có Yi/Ji giờ | Chưa đưa vào MVP kế tiếp |
| Tang lễ | An táng, phá thổ phần mộ | `安葬`, `破土` | Miền nghiệp vụ riêng |

**Không gộp nhập trạch với chuyển chỗ ở**, dạm hỏi với thành hôn, giao dịch với lập văn khế, hay động thổ xây nhà với phá thổ phần mộ. Các token có nghĩa công việc khác nhau; gộp theo OR có thể che một việc đang bị kỵ. Số chủ thể dự kiến cho nhóm kế tiếp là một; người đó cần được xác định là người đứng việc, không mặc nhiên là người đang đăng nhập.

## Độ phủ nhóm ưu tiên

Các số sau là **số bản ghi có token trực tiếp**. Trạng thái đánh giá đã áp kỵ chung có thể khác; xem JSON để phân biệt.

| Category | Yi ngày | Ji ngày | Yi giờ | Ji giờ | Ngày mâu thuẫn |
| --- | ---: | ---: | ---: | ---: | ---: |
| Nhập trạch | 650 | 873 | 12.563 | 0 | 0 |
| Chuyển chỗ ở | 719 | 347 | 10.519 | 1.792 | 0 |
| An sàng | 759 | 321 | 12.397 | 0 | 0 |
| Sửa chữa, tu tạo | 663 | 115 | 11.501 | 9.678 | 0 |
| Giao dịch | 561 | 86 | 11.678 | 0 | 4 |

Giao dịch có xung đột tại **20/02/2024, 14/02/2025, 09/02/2026, 04/02/2027**. Giữ `UNRESOLVED` tại các khung chịu ảnh hưởng của ngày nguồn ấy, không đổi thành ngày đẹp để tăng tỷ lệ kết quả.

Động thổ có 824 Yi ngày nhưng **0 Yi giờ / 4.858 Ji giờ**; tháo dỡ có 533 Yi ngày nhưng **0 Yi giờ / 0 Ji giờ**. Mức phạt `HOUR_NOT_LISTED` hiện tại có thể vẫn cho một khung đạt GOOD nếu đủ điểm. Vì vậy, việc thêm những category này bằng một token vào engine v1 sẽ tạo giờ đẹp thiếu bằng chứng giờ riêng. Cần chế độ chỉ tra ngày hoặc chính sách giờ được duyệt độc lập trước.

Tế lễ có nhiều dữ liệu nhưng 82/2.557 ngày `UNRESOLVED` (khoảng 3,2%) theo xử lý kỵ chung hiện hành. Nạp thái và đính ước mỗi loại có 5 ngày mâu thuẫn; token giờ `订婚` là **đề xuất cần duyệt**, chưa được coi như đồng nghĩa tự động. Nhậm chức chỉ có 39 Yi ngày trên bảy năm; cần xem UX khi ít ngày đủ điều kiện.

An táng/phá thổ cần xác định người được xét, người đứng lễ, dữ liệu phần mộ và luật chuyên biệt. Không dùng lá số người đăng nhập để thay thế dữ kiện này. Cầu y/trị bệnh chưa có dữ liệu giờ; đề xuất giữ ngoài đợt kế tiếp, chưa thiết kế kết luận về hiệu quả điều trị.

## Các việc cần làm khi triển khai category mới

1. Bổ sung registry có `activity`, `group`, `name_vi`, `subject_roles`, token ngày/giờ riêng, `hour_evaluation_mode`, `enabled`, `review_status` và profile luật. Thêm vào builder để lần rebuild không ghi đè thay đổi.
2. Duyệt phạm vi `BLOCK/PENALTY` cho từng category. Ba luật lớn áp mọi việc hiện nay là policy v1 cho **ba việc hiện tại**; không tự chuyển nguyên sang tháo dỡ/tang lễ.
3. Mở rộng enum `Activity`, validator `DateRules`, schema và API; dropdown lấy registry đã bật. Code hiện khóa chính xác ba việc, chỉ sửa JSON sẽ bị từ chối.
4. Với nhóm kế tiếp: chỉ ghi “giờ được lịch nguồn đề cập nên làm” khi `hour_activity_status=SUPPORTED`. Nếu vẫn dùng GOOD với `NOT_LISTED`, phải tách rõ “phù hợp theo chấm điểm” với “lịch giờ có mục nên”. Chưa thay chính sách chấm điểm ba việc đang chạy trong yêu cầu này.
5. Với category không có Yi giờ: không suy ra giờ đẹp từ đủ điểm. Cần contract riêng cho “đã tra ngày, chưa đánh giá giờ”, không dùng `PARTIAL` để chặn cả API.
6. Kiểm từng năm 2024–2030, xung đột Yi/Ji, kỵ chung, ranh Jie/nửa đêm, một/hai chủ thể và các category có cùng nhóm nhưng khác kết luận. Giữ một lần phân tích lá số/chủ thể/request và giới hạn 93 ngày.

Tiêu chí bật đợt kế tiếp: token và nghĩa đã duyệt; role rõ; luật có scope; schema tái tạo được; mọi giờ đẹp được giải thích đúng mức bằng chứng; các ca mâu thuẫn và không có giờ không bị “làm đẹp” bằng điểm.

## Cách gọi chủ thể trên client

Chọn văn phong Hán Việt vừa đủ để hợp định hướng nghi lễ truyền thống của sản phẩm. Đây là **quyết định UX**, không tuyên bố các tên gọi hoặc toàn bộ thuật toán là quy chuẩn Nho giáo.

| Ngữ cảnh | Cách hiển thị |
| --- | --- |
| Khai trương; tương lai nhập trạch, nhà cửa | Gia chủ — người đứng việc được nhập hồ sơ |
| Xuất hành | Người xuất hành |
| Cưới hỏi, chưa có trường vai trò | Đương sự thứ nhất / Đương sự thứ hai |
| Chủ thể không xác định trong response | Đương sự |
| Tài khoản, thao tác chung của ứng dụng | Người dùng |

“Đương sự” diễn đạt người liên quan trực tiếp đến việc; đối chiếu [mục 當事人 của từ điển Bộ Giáo dục Đài Loan](https://dict.revised.moe.edu.tw/dictView.jsp?ID=44322). Chỉ dùng để hỗ trợ nghĩa từ, không làm chứng cứ cho một danh xưng cổ truyền duy nhất. Chưa gán “Tân lang/Tân nương” vì hồ sơ không có vai trò ấy.

Client ánh xạ `subject_id` từ request đã tạo kết quả; không hiển thị `user_1`, `person_1` hoặc mã API khác trong tóm tắt, cảnh báo hay đối chiếu khung. Khi đổi lựa chọn trên form, kết quả cũ vẫn dùng role của request cũ.

## Hiển thị khung giờ — đã triển khai

Cập nhật UX 15/10/2026: ô ngày có chiều cao cố định và hiện số khung giờ đẹp. Bấm vào mở popup liệt kê **mọi khung GOOD**, theo thời gian, theo mẫu **“Giờ Tuất - Từ 18:00 đến 20:00”**; tránh kéo giãn những card cùng hàng. Phần lý do đánh giá từng khung được tải khi mở thêm trong popup. API có `recommended_windows` chứa `start_at`, `end_at`, `hour_branch`, không giới hạn ba khung. `windows` tóm tắt vẫn giữ top 3 cho đối chiếu; chi tiết vẫn trả toàn bộ khung. `recommended_minutes` giữ cho API, không dùng làm nhãn trên ô ngày.

Lấy chi giờ từ trụ giờ engine, không suy từ đồng hồ client. [Bảng giờ của HKO](https://www.hko.gov.hk/tc/gts/time/stemsandbranches.htm) đối chiếu thứ tự 12 chi và giờ truyền thống. Với policy **lịch Bắc Kinh UTC+8** hiện tại, giờ Tuất 19:00–21:00 Bắc Kinh tương ứng **18:00–20:00 Việt Nam**. Giao diện ghi rõ khoảng giờ UTC+7 và tên giờ theo lịch UTC+8.

Không gộp qua ranh giờ/tiết khí/đổi ngày đã tính. Khung bị cắt dùng đúng khoảng còn lại; có giây lẻ thì hiển thị `hh:mm:ss` để không mở rộng kết luận. Cuối ngày ghi **24:00**. Mọi nhãn chủ thể/giờ ở phần chi tiết dùng cùng quy tắc với danh sách giờ đẹp trong popup.
