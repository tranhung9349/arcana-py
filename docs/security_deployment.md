# Security và phiên không lưu — 28/10/2026

Ứng dụng không có tài khoản, cookie phiên, localStorage, sessionStorage hay IndexedDB. Không ghi hồ sơ, câu hỏi, kết quả hoặc bài luận vào database. Dữ liệu hiện tại chỉ nằm trong RAM của trang; tải lại, đóng trang hoặc trở lại một trang từ back/forward cache sẽ bắt đầu trang mới. Nút **Xuất PDF** mở hộp thoại in của trình duyệt; chọn **Save as PDF / Lưu dưới dạng PDF** để chủ động giữ bản chụp kết quả. Bản PDF dùng CSS/font của app, có nội dung luận AI đã hoàn tất tại thời điểm xuất. Không tải HTML và không gửi nội dung sang dịch vụ tạo PDF.

## Các lỗi đã sửa

| Rủi ro | Cách xử lý |
| --- | --- |
| API liệt kê lịch sử chung, tra kết quả bằng UUID | Bỏ toàn bộ endpoint lịch sử/đọc bản ghi trên server và bỏ UI lịch sử. Server không mở database cá nhân cũ. |
| Client tự sửa lá số/kết quả trước khi nhờ AI luận | HMAC-SHA256 ký snapshot theo loại; backend xác minh nội dung, UUID và liên kết chart/analysis trước khi tạo prompt hoặc tiêu hạn mức. Chữ ký không chứa dữ liệu ẩn hay cấp quyền đọc dữ liệu khác. |
| API AI ẩn danh bị dùng để tiêu tiền | Tối đa 10 yêu cầu tạo AI/IP/giờ, 2 lượt AI đồng thời, mặc định 100 HTTP attempt AI/ngày UTC. Tính cả retry upstream và lần sửa định dạng; cache RAM tránh gọi trùng. Không tự tạo AI khi người dùng vừa lập quẻ/lá số. |
| Quá tải API hoặc body lớn/chậm | 120 API request/IP/phút, 30 POST/IP/phút, 600 request tổng/phút; tối đa 16 request API đang xử lý, body 1 MiB, thời gian nhận body 10 giây. Health probe riêng. |
| Giả X-Forwarded-For để né giới hạn | Chỉ đọc chuỗi IP khi peer là proxy nằm trong allowlist cấu hình. Mặc định không tin header chuyển tiếp. |
| Website khác gọi API bằng trình duyệt | Kiểm Origin, Sec-Fetch-Site, Host và JSON Content-Type; không bật CORS. Frontend chỉ gửi đến các API cùng origin, không gửi cookie và từ chối redirect. |
| XSS/clickjacking và rò dữ liệu qua cache/referrer | CSP chỉ chạy script/style/font cùng origin, cấm inline script/eval/frame/object; nosniff, no-referrer, Permissions-Policy, no-store cho HTML/API, HSTS khi cấu hình HTTPS. Renderer dùng textContent; bản in loại bỏ active content. |
| Exception lộ hồ sơ, upstream response hoặc key | Lỗi trả thông báo chung, validation không phản chiếu input; log lỗi chỉ ghi tên loại exception. API key giữ ở server, không nằm trong snapshot hoặc PDF. |
| Secret bị bake vào image | Docker build allowlist, không copy .env/database; runtime không root, filesystem chỉ đọc. Production từ chối khởi động nếu thiếu signing key hoặc HTTPS public origin. |

Không lưu database không có nghĩa là không dùng RAM: server có cache AI tạm, tối đa 32 kết quả, chỉ được tra lại trong 15 phút bằng đúng signed snapshot; cache mất khi tiến trình dừng. Hạn mức và trạng thái đang chạy cũng chỉ ở RAM. Không có API tìm kiếm/liệt kê cache.

## Giới hạn vận hành còn lại

- Chạy **1 worker, 1 replica**. Restart/redeploy làm reset bộ đếm giới hạn; cần đặt trần chi phí/tín dụng tại nhà cung cấp AI để có giới hạn độc lập với tiến trình. Không có đăng nhập/CAPTCHA nên bot vẫn có thể tiêu hết hạn mức chung; ứng dụng từ chối AI khi đạt trần, phần tính toán vẫn dùng được.
- AI được gọi khi người dùng bấm nút, và dữ kiện cần thiết được chuyển cho nhà cung cấp đã cấu hình. Chính sách lưu dữ liệu của nhà cung cấp nằm ngoài ứng dụng này.
- Nếu HTTP response của lần gieo bị mất trước khi trình duyệt nhận, backend không có bản ghi để phục hồi. Thử lại có thể sinh kết quả mới. Kết quả nhận thành công được dùng lại trong trang đang mở.
- Key ký nên giữ ổn định trong Environment của deployment; không commit. Đổi key khiến snapshot đang mở không còn dùng được để luận thêm, nhưng không ảnh hưởng PDF đã xuất.
- Database SQLite cũ có thể vẫn tồn tại ở máy phát triển/VPS từ bản trước. Bản mới không đọc hoặc xóa chúng; nếu không còn cần, người quản trị chủ động xử lý bản cũ và backup. Không gắn volume dữ liệu cũ vào bản mới.

## API hiện tại

Các endpoint POST tạo kết quả giữ nguyên đường dẫn: `/api/v1/draw`, `/api/v1/bazi/consultations`, `/api/v1/maihoa/consultations`, `/api/v1/coins/consultations`, `/api/v2/auspicious-dates/consultations`. Response có header `X-Arcana-Signature`.

Snapshot gửi lại có dạng `{kind, data, signature}`. Không gửi key ký cho client.

- `POST /api/v1/interpretation`: `{consultation: snapshot DRAW}`.
- `POST /api/v1/bazi/readings`: `{consultation: snapshot BAZI, reading: payload BaziReadingRequest}`.
- `POST /api/v1/coins/analysis`: `{consultation: snapshot COINS, context: AnalysisContext}`.
- AI request thêm `consultation`; Bát Tự chủ đề khác thêm `bazi_reading`, Lục Hào thêm `analysis`. Mỗi thành phần là snapshot có chữ ký và phải khớp bản gốc.
- Endpoint rules, catalog, tra ngày, nhận diện câu hỏi và health vẫn là các phép tính/tra cứu không có trạng thái. Swagger/ReDoc/OpenAPI public đã tắt.

## Kiểm chứng

- **218 test Python và 39 test JavaScript đạt**; test raw API riêng kiểm sửa chữ ký, đổi loại, trộn analysis/chart cùng UUID, không tạo database, CSRF/Host/body/rate limits và không log secret.
- Chrome headless chạy đủ 5 chức năng, tạo PDF thật cho từng phần (gồm lịch và popup ngày), kiểm CSS/CSP, không cookie/storage/history, không tự gọi AI, reload mất phiên, nút Xuất PDF và PDF A4 thật.
- `pip-audit --disable-pip --no-deps -r requirements-runtime.lock` và `npm audit`: không báo lỗ hổng đã biết tại thời điểm kiểm tra. Không đồng nghĩa với bảo đảm không có lỗ hổng chưa công bố.
- Không gọi AI trả phí trong kiểm thử, chưa deploy hoặc pentest VPS thật.

Tham chiếu: [OWASP REST Security](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html), [OWASP HTML5 Security](https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html), [Dokploy Applications](https://docs.dokploy.com/docs/core/applications).
