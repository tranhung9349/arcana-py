# Bài Tổng quan Bát Tự theo toàn mệnh — 29/10/2026

Trước thay đổi, bài Tổng quan bị ràng buộc thành ba khuynh hướng, mỗi khuynh
hướng chỉ có một biểu hiện đời sống; `in_life` luôn rỗng trong khung mà server
đưa cho Interpreter. Phần mở đầu chỉ được 60–80 từ. Vì vậy ngay cả lá số có đủ
Đại vận cũng thường cho ra một bài mô tả cách học/làm việc hoặc phản ứng trước
tình huống mới, chưa thành bức tranh cuộc đời.

## Hành vi mới

Chủ đề `GENERAL` dùng `reading_scope=WHOLE_LIFE`. Các chủ đề chuyên biệt giữ
`FOCUSED` và khung giải đáp theo chủ đề. Phiên bản pipeline tăng thành
`bazi-two-stage-tinix-2026-10-29-v5`; hash prompt, schema, implementation và
context thay đổi nên cache backend không tái sử dụng bài thuộc khung cũ.

Analyst vẫn phân tích ba cơ chế có căn cứ của toàn lá số, đồng thời phải tạo
`whole_life`: một tổng hợp toàn mệnh; ba đánh giá riêng về sự nghiệp, tài chính,
tình cảm/quan hệ/gia đình; và ba chặng vận khi có dữ liệu. Mỗi đánh giá có cơ hội,
điểm nghẽn, điều kiện, giới hạn, ít nhất hai dữ kiện khác nhau và nguồn đối chiếu.
Một lĩnh vực ít căn cứ được đánh dấu `LIMITED`, không thay bằng nhận định tính
cách phổ quát hoặc đoán tình trạng hôn nhân/nghề/thu nhập thực tế.

Context thêm giới tính dùng tính vận, dữ kiện cung ngày, điểm ngũ hành và bản
tóm tắt lời giải từng Đại vận từ snapshot engine. Các chuỗi này là đầu ra quy
tắc truyền thống, không phải dữ kiện xác nhận sự kiện ngoài đời. Các trạng thái
vượng nhược/cân bằng chính vẫn lấy từ nhánh canonical đang dùng. Không gửi tên
hay timestamp ngày giờ sinh đầy đủ vào prompt.

Server gộp các Đại vận đã có thành ba chặng liên tiếp: chỉ số `[0,1]`, `[2,3,4]`,
`[5,6]`. Đây là cách trình bày bảy vận đầu, không tạo ranh giới tuổi tròn mới và
không ấn định tuổi thọ. Năm bắt đầu/kết thúc và tuổi tương ứng lấy nguyên từ
snapshot đã ký; Analyst không được sửa, thêm chặng hay lấy riêng Lưu niên năm
xem để mô tả cả đời. Thiếu Đại vận thì vẫn luận ba lĩnh vực, đồng thời ghi chưa
đủ dữ liệu để chia chặng; không tự dựng thời điểm.

Interpreter chỉ nhận phân tích đã kiểm tra, điền lời văn vào khung cố định:

1. **Bức tranh toàn cảnh**: 120–170 từ, liên kết đường phát triển, sự nghiệp/tài
   chính, các mối gắn bó và sự đổi nhịp giữa các chặng.
2. **Sự nghiệp và đường phát triển**.
3. **Tài chính và tích lũy**.
4. **Tình cảm, quan hệ và gia đình**.
5. **Các chặng đường theo Đại vận**: mốc năm/tuổi không chỉnh sửa được.
6. **Điểm tựa và điều cần cân bằng**: tổng hợp xuyên suốt thay cho lời khuyên
   chung như “thử một bước nhỏ”.

Nhắm 800–1.050 từ, trần 1.400 từ; phần mở đầu tối đa 240 từ. Bài Tổng quan không
còn ba thẻ khuynh hướng độc lập. Điều kiện, mâu thuẫn và giới hạn được giữ trong
các lĩnh vực/chặng liên quan. Các bài chuyên đề vẫn giữ ngân sách và kiểm tra
cũ. Hình thức SSE/tác vụ nền không thay đổi.

Từ v4, tầng viết dùng prompt riêng `bazi_whole_life_interpreter_v1.system.txt`
và chỉ trả `bazi-whole-life-prose-v1`: phần mở đầu, lời văn cho từng lĩnh vực/
chặng, kết luận và một giới hạn chung. Máy chủ ghép chúng vào khung đã kiểm tra,
tự gắn hash, tham chiếu và các mốc năm/tuổi. LLM không còn phải chép lại toàn bộ
metadata bất biến để xuất một bài hoàn chỉnh. Bỏ lĩnh vực/chặng, trùng mã hoặc
thêm trường năm/tuổi ngoài giao thức vẫn bị chặn. Lỗi kiểm tra được log bằng mã
loại lỗi và tên tầng/lượt; không log dữ kiện, bản nháp, response hay khóa API.

Chú thích thời gian công khai cũng do máy chủ tạo bằng lời thường, không sao
chép `timing_note` kỹ thuật từ Analyst. Nhờ đó mã chặng/thuật ngữ nội bộ không
lọt vào bộ kiểm văn xuôi và gây lỗi mà Interpreter không thể sửa. Gợi ý sửa văn
được gắn vị trí trường, số từ thực tế/trần, và danh sách thuật ngữ lấy từ danh
mục cố định; không đưa bản nháp bị từ chối vào làm căn cứ cho lượt sau.

## Kiểm tra và giới hạn

`randomyst/bazi_portrait.py` kiểm đủ ba lĩnh vực theo đúng thứ tự, nguồn dữ kiện,
bản kế hoạch năm/tuổi và ràng buộc các phần công khai vào phân tích. Các trường
`whole_life` là phần mở rộng tùy chọn của schema hiện tại để giữ khả năng đọc
bài chuyên đề theo khung cũ. Riêng bài Tổng quan sinh mới bắt buộc có chúng.

`tests/test_bazi_portrait.py` phủ việc thiếu lĩnh vực, nguồn bịa/thiếu, tuổi/năm
không có trong engine, thiếu Đại vận, writer sửa tham chiếu, thêm lại thẻ tính
cách ngoài kế hoạch, và đường API streaming. Kiểm thử giao diện xác nhận đủ
lĩnh vực, thứ tự, mốc thời gian và không hiện mã tham chiếu hoặc phân tích kỹ thuật.

Các kiểm tra cấu trúc này không chứng minh mọi câu diễn giải được nguồn hỗ trợ
về ngữ nghĩa. Việc rà chất lượng một bài do LLM thật viết cần được thực hiện
riêng; không coi fixture giả lập là ví dụ mệnh lý đã được thẩm định.

V5 bổ sung `verified_structure` do máy chủ gắn: vị trí can lộ/tàng và từng cặp
xung riêng biệt. Analyst không được tự sửa bảng này. Tầng viết nhận phần
`whole_life`, bảng đối chiếu và giới hạn từ phân tích đã kiểm tra; không cần
nhận lại các mô thức kỹ thuật không được hiển thị trong bài Tổng quan. Nhãn
thuật ngữ và ẩn dụ như “kênh xuất lực” được chặn trong lời văn Tổng quan; phần
kỹ thuật vẫn có ở các mục lá số riêng. Các bài chuyên đề giữ giới hạn cũ.

Đã kiểm tra bằng LLM thật sau khi người dùng cho phép gửi mẫu tới provider đang
cấu hình. Bản đọc được chấp nhận có khoảng 1.000 từ, đủ ba lĩnh vực và ba chặng
khớp engine. Quá trình QA tái sử dụng phân tích hợp lệ trong RAM để sửa riêng
tầng viết, không phát sinh lại Analyst ở mỗi lượt biên tập. Đây là kiểm chứng
thành phần với provider thật; các kiểm thử API tự động vẫn dùng LLM giả lập.
Provider có một lần ngắt streaming giữa chừng trong QA; không chấp nhận bản
thiếu đó làm bài hoàn chỉnh. Nội dung dự báo vẫn là diễn giải truyền thống,
không được bộ kiểm cấu trúc xác nhận là diễn biến thật của cuộc đời.
