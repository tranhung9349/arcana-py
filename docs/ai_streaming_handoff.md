# Streaming bài luận và tác vụ nền — 29/10/2026

**30/10:** cả `/start` và endpoint JSON đồng bộ đều gọi provider với `stream=True`; endpoint JSON vẫn trả một bài đã kiểm tra. Đã kiểm thật Lục Hào với `Content-Type: text/event-stream`. Lỗi UI tái hiện do bài vượt ngân sách độ dài, xử lý bằng lượt biên tập chính bản nháp đã qua kiểm tra; [chi tiết và luồng UI mới](liuyao_plain_reading_handoff.md).

Giao diện đọc bài qua SSE bằng `fetch`, gửi nguyên snapshot có chữ ký trong POST.
Khóa LLM và phần phân tích Bát Tự trung gian vẫn chỉ ở backend. Không đưa bản
nháp hoặc token chưa kiểm tra ra giao diện.

## Luồng chạy

- `POST /api/v1/ai/readings/stream`: chỉ theo dõi tác vụ đã có hoặc đọc lại kết
  quả hợp lệ trong cache; trả `missing` nếu chưa có. Endpoint này không tạo lượt gọi LLM.
- `POST /api/v1/ai/readings/start`: tạo tác vụ nếu cần; tham gia tác vụ đang chạy
  hoặc đọc cache nếu cùng dữ kiện. Một lần bấm thử lại sau lỗi có thể tạo tác vụ mới.
- Cả hai nhận `AIReadingRequest` hiện có, kiểm chữ ký và ràng buộc context trước
  khi đọc kết quả. Không có đường GET theo ID để đọc bài luận của người khác.
- SSE gồm `progress`, `result`, `error`, `missing`; bình luận keep-alive mỗi 10
  giây. Header `X-Accel-Buffering: no` hỗ trợ proxy chuyển dữ liệu ngay.
- Các trạng thái công khai là `QUEUED`, `ANALYZING`, `WRITING`, `CHECKING`.
  Giao diện chỉ hiển thị câu tiếng Việt cố định tương ứng, không hiển thị dữ liệu
  kỹ thuật hoặc chuỗi lỗi do nhà cung cấp gửi về.
- Backend dùng `stream: true` trên Chat Completions, ghép `delta.content` riêng
  với reasoning, đợi `finish_reason=stop` và `[DONE]`, sau đó kiểm JSON/schema/căn
  cứ như trước. Usage lấy từ sự kiện usage cuối, không cộng lặp từng chunk.
  Nếu gateway trả `application/json` dù đã yêu cầu stream, backend đọc phản hồi
  đó một lần; không tự gửi thêm request để đổi chế độ.

## Ngắt và nối lại

Worker chạy trong thread riêng, dùng cùng giới hạn đồng thời (mặc định 2 tác vụ)
và ngân sách lượt gọi đang có. Ngắt HTTP, đổi menu, hủy panel hoặc mất mạng chỉ
đóng observer. Browser nối lại bằng endpoint `/stream`, không phát lại `/start`.
Watchdog phía browser chờ 45 giây không có dữ liệu rồi kết nối lại, tối đa 3 lần,
với khoảng nghỉ 1/2/4 giây. Nếu không biết request tạo tác vụ đã tới máy chủ hay
chưa, browser chỉ thăm dò lại; không tự khởi tạo một tác vụ trả phí mới.

Lỗi EOF, timeout hoặc thiếu tín hiệu hoàn tất từ LLM không lưu bài một phần và
không tự thử lại một lời gọi có khả năng đã bị tính phí. Giữ chính sách cũ: tối
đa một lần thử lại cho HTTP 429/502/503/504 nhận trước khi bắt đầu đọc nội dung;
mỗi lần outbound đều tính vào ngân sách. Mỗi tầng vẫn chỉ sửa tối đa một lần khi
nội dung chưa qua kiểm tra. HTTP API đồng bộ cũ và lookup vẫn dùng được và chia
sẻ cùng cơ chế chống gọi trùng/cache với tác vụ SSE.

## Giới hạn vận hành

`RANDOMYST_AI_TIMEOUT_SECONDS` là timeout kết nối/đọc im lặng của socket (local
hiện tại 180 giây). Một phản hồi streaming có trần tổng 600 giây; tác vụ có ngân
sách thời gian 1.500 giây cho toàn bộ các tầng. Deadline được kiểm giữa các lần
đọc, còn lần đọc đang bị treo chịu timeout socket. Heartbeat chỉ giữ kết nối tới
browser, không che lỗi timeout của upstream. Proxy có giới hạn tổng thời gian
cứng vẫn có thể đóng kết nối; browser sẽ nối lại vào cùng worker.

Cache và registry tối đa 32 tác vụ, giữ kết quả/lỗi tối đa 15 phút từ khi xong;
không đẩy tác vụ đang chạy ra khỏi registry để nhận thêm việc. Tất cả ở RAM một
process. Docker đã chạy một worker Uvicorn: tiếp tục giữ cấu hình này; muốn chạy
nhiều process/replica phải dùng kho job chung trước. Restart server làm mất job
và cache. Reload toàn bộ trang vẫn xóa snapshot/lịch sử theo chính sách hiện tại;
kết nối lại hoạt động khi trang còn snapshot hoặc mở lại lá số trong lịch sử RAM.

## Kiểm chứng

`tests/test_ai_streaming.py` kiểm parser upstream, hai tầng dùng streaming,
snapshot/chữ ký, chống gọi trùng, worker sống sau khi observer ngắt, kiểm lại
cache, lỗi kín, giới hạn đồng thời và hạn mức tạo tác vụ. `tests/test_ai_streaming.cjs`
kiểm UTF-8/CRLF bị chia chunk, heartbeat, watchdog, nối lại không trả phí thêm,
hủy observer, lỗi giữa luồng và cache trong trang. `tests/test_ai_reading.cjs`
kiểm tiến trình và việc chỉ hiển thị bài hoàn chỉnh.

Tham chiếu giao thức:
[Chat Completions](https://developers.openai.com/api/reference/resources/chat),
[SSE framing và keep-alive](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events).
