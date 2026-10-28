# Arcana trên VPS/OCI bằng Docker — bản không lưu phiên

Với Dokploy, dùng [hướng dẫn Dokploy](dokploy.md). Các bước dưới dành cho Docker Compose trực tiếp, một instance Ubuntu ARM64 hoặc x86_64.

## Chuẩn bị

Cài Docker Engine, Buildx và Compose theo [tài liệu chính thức](https://docs.docker.com/engine/install/ubuntu/). Đóng gói source trên máy phát triển:

```sh
python3 scripts/package_oci.py /tmp/arcana-vps.tar.gz
scp -i /path/to/key /tmp/arcana-vps.tar.gz ubuntu@YOUR_PUBLIC_IP:~/
```

Archive không chứa `.env.local`, database, node_modules hoặc khóa. Trên VPS, giải nén vào thư mục nguồn, tạo `.env.production` từ mẫu, quyền 600 và cấu hình **RANDOMYST_SIGNING_KEY**, **RANDOMYST_PUBLIC_ORIGIN**, AI nếu dùng. Public origin phải là HTTPS production. Không commit file thật.

```sh
tar -xzf ~/arcana-vps.tar.gz -C ~
cd ~/arcana
umask 077
cp -n .env.production.example .env.production
chmod 600 .env.production
# Dùng editor để điền signing key ngẫu nhiên và HTTPS origin thực tế.
docker compose build --pull
docker compose up -d --wait --wait-timeout 120
python3 scripts/smoke_docker.py http://127.0.0.1:8765
```

Cổng chỉ bind localhost. Có thể mở SSH tunnel để kiểm trước khi cấu hình HTTPS. Smoke test không gọi AI hoặc ghi lịch sử.

## HTTPS trực tiếp bằng Caddy

Trỏ DNS về VPS, mở TCP 80/443 ở firewall nhà cung cấp/host theo thiết lập thực tế. Với OCI Ubuntu, kiểm NSG/security list và đường Docker FORWARD; không tự bật UFW, xóa iptables hoặc đổi firewall hàng loạt. [Docker firewall](https://docs.docker.com/engine/network/packet-filtering-firewalls/), [OCI security rules](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/securityrules.htm).

```sh
cp -n deploy/.env.https.example deploy/.env.https
# Điền domain/email; không cần tài khoản hoặc mật khẩu truy cập app.
docker compose -f compose.yaml -f compose.https.yaml config --quiet
docker compose -f compose.yaml -f compose.https.yaml up -d --wait --wait-timeout 120
```

Caddy dùng volume riêng cho chứng chỉ, không lưu hồ sơ app. Cấu hình trusted proxy nếu muốn giới hạn theo IP thật. Không dùng Caddy nếu Traefik/Dokploy đang xử lý domain.

## Cập nhật và dữ liệu

```sh
docker compose build --pull
docker compose up -d --wait --wait-timeout 120
docker compose logs --tail=100 app
```

Không cần backup/restore phiên hoặc database: app không lưu chúng. PDF do người dùng tự xuất là bản họ giữ. Không xóa tự động các database/volume cũ khi nâng cấp. Quota AI ở RAM reset khi app restart; cấu hình trần chi phí phía nhà cung cấp. Xem [báo cáo security](security_deployment.md).
