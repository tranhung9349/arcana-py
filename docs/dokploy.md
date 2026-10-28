# Deploy Arcana bằng Dokploy

Bản hiện tại không có đăng nhập hoặc dữ liệu phiên lưu trên server. Không cần database, volume dữ liệu hay Redis. PDF được in tại trình duyệt.

## Docker Compose

Với dịch vụ Docker Compose trong Dokploy, chọn:

- **Compose Type:** Docker Compose.
- **Compose Path:** `./compose.yml`.
- **Service** trong Domains: `app`.
- **Container Port:** `8765`; Path `/`; bật HTTPS/Let's Encrypt.

File `compose.yml` dành riêng cho Dokploy, nhận biến trực tiếp từ Environment của dịch vụ (Dokploy lưu thành `.env`). Không cần tạo hoặc upload `.env.production`. Không publish port, không gắn volume và không chạy thêm Caddy. Dokploy tự thêm nhãn Traefik/network khi cấu hình domain trong UI.

Điền Environment theo `.env.production.example`. Bắt buộc có:

```dotenv
RANDOMYST_SIGNING_KEY=<64 ký tự hex ngẫu nhiên>
RANDOMYST_PUBLIC_ORIGIN=https://ten-mien-thuc-te
```

Tạo key bằng `python3 -c 'import secrets; print(secrets.token_hex(32))'`. Nhập trực tiếp trong Environment; không commit. API key AI có thể để trống.

Sau khi push bản sửa lên repository, giữ Compose Path `./compose.yml`, lưu Environment/Domain rồi Deploy lại. Nếu thấy `Compose file not found`, kiểm tra tên file và branch đã chọn; `compose.yaml` là cấu hình Docker chạy trực tiếp trên VPS, còn `compose.yml` là cấu hình Dokploy.

## Application dùng Dockerfile

1. Đưa source lên Git repository, tạo **Application** trong Dokploy và kết nối repository.
2. Chọn **Dockerfile** tại thư mục gốc, build context `.`. Image phục vụ cả web và API.
3. Tại Environment, điền các biến trong `.env.production.example`. `RANDOMYST_ENV=production` đã có trong image.
4. Tạo signing key tại máy quản trị: `python3 -c 'import secrets; print(secrets.token_hex(32))'`. Giữ key trong Environment, không đưa vào Git hoặc frontend.
5. Đặt `RANDOMYST_PUBLIC_ORIGIN=https://ten-mien-thuc-te` (không path), tạo domain HTTPS/Let's Encrypt với **Container Port 8765**, Path `/`.
6. Giữ **1 replica**, không override lệnh chạy của image; không publish cổng 8765 ra Internet. Traefik chuyển tiếp nội bộ đến container. Không dùng `compose.https.yaml`/Caddy cùng Dokploy.
7. Cấu hình `RANDOMYST_TRUSTED_PROXIES` bằng IP/CIDR của proxy Traefik thực tế để giới hạn đúng IP người dùng. Chỉ tin proxy trực tiếp, không dùng `0.0.0.0/0` hoặc `::/0`. Nếu để trống, các request đi qua proxy chia sẻ giới hạn IP bảo thủ.
8. Chọn hạn mức `RANDOMYST_AI_DAILY_LIMIT` phù hợp và đặt trần chi phí ở tài khoản nhà cung cấp. Bộ đếm trong app reset khi restart/redeploy.
9. Deploy, kiểm Logs và `GET /api/v1/health`. Image có healthcheck không gọi AI. Thử lập phiên, mở lời luận, xuất PDF và tải lại trang để kiểm kết quả đã biến mất.

Nếu chưa dùng AI, để API key trống; các chức năng tính toán vẫn chạy. Cấu hình Origin và signing key vẫn bắt buộc cho production.

[Dokploy Domains](https://docs.dokploy.com/docs/core/domains) mô tả Container Port là cổng định tuyến nội bộ, không phải cổng publish. [Chi tiết thay đổi bảo mật, kiểm thử và giới hạn](security_deployment.md).

[Dokploy Compose](https://docs.dokploy.com/docs/core/docker-compose) mô tả cách truyền biến Environment; [Compose Domains](https://docs.dokploy.com/docs/core/docker-compose/domains) mô tả service, nhãn và network do Dokploy quản lý.
