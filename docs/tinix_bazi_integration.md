# Tích hợp engine tinix-bazi — 28/10/2026

Module luận Bát Tự riêng dùng mã nguồn `tinix-bazi` tại commit
`80ff4463d0397c1b11db76f38d880255f55558bc`, trong `vendor/tinix-bazi`.
Luồng mới không gọi bộ đánh giá cũ `BaziRules.evaluate`. Bộ lịch và bảng dữ kiện
hiện có tiếp tục cung cấp Tứ Trụ để kiểm tra chéo với engine.

Các tính năng được giữ:

| Module nguồn | Trong project |
| --- | --- |
| Homepage | Form ngày giờ sinh Việt Nam, nam/nữ, năm xem, chủ đề, câu hỏi, sai số |
| BaziChart | Bảng Tứ Trụ, tàng can, Thập Thần; radar và bảng điểm Ngũ Hành; Nạp Âm, Trường Sinh, Thần sát |
| LuckCycles | 12 Đại vận, 10 Lưu niên mỗi vận, lời giải từng giai đoạn và phân tích năm xem |
| Interpretation | Ma trận Can Chi, cách cục, Dụng/Hỷ/Kỵ, luận tĩnh/động, các phép luận chuyên sâu, điển tích |
| Consultant | Luận theo chủ đề và câu hỏi khi lập lá số; giao diện không có tab Hỏi thêm |
| ConsultationHistory | Tối đa 5 lá số và các câu hỏi trong RAM của trang; mở lại không tự gọi LLM |

Backend `randomyst/bazi_engine.py` gọi `runner.cjs` bằng stdin, có timeout 15 giây.
Kết quả có commit, phiên bản adapter, hash input và output, và toàn bộ kết quả
engine trong `BaziResponse.engine`. Snapshot tiếp tục có chữ ký máy chủ. Không
thêm HTTP service hoặc database; tải lại trang sẽ mất lịch sử.

`birth.gender` nhận `male`/`female`, mặc định `male` theo nguồn; form hiển thị rõ lựa
chọn này. `target_year` nhận 1950–2150; bỏ trống qua API sẽ dùng năm Việt Nam hiện
tại. Dữ liệu cũ thiếu trường `engine` vẫn đọc được; đọc lại snapshot cũ dùng lời
diễn giải cũ, không tính lại thành kết quả của engine mới.

LLM dùng nguyên `AIReadingService` + `CompatibleAIClient` và cấu hình
`RANDOMYST_AI_BASE_URL`, `RANDOMYST_AI_MODEL`, `RANDOMYST_AI_API_KEY`, timeout và
reasoning effort hiện có. Không có khóa hay endpoint OpenRouter riêng. Hai vai
phân tích/diễn giải tiếp tục kiểm schema, dẫn chiếu, cache tạm và hạn mức gọi.
Ngữ cảnh nhận dữ kiện engine và vận đã tính, không gửi tên hoặc ngày giờ sinh.

Giao diện theo dõi bài luận bằng SSE; tác vụ nền tiếp tục khi kết nối bị ngắt
và cho phép tham gia lại cùng tác vụ. Xem [luồng streaming và giới hạn vận hành](ai_streaming_handoff.md).

Mệnh năm sinh (nạp âm trụ năm) và Nhật chủ (Thiên can ngày sinh) được hiển thị
riêng trước bài luận. Ví dụ 01/09/1994 dương lịch, 07:00 giờ Việt Nam có năm
Giáp Tuất — Sơn Đầu Hỏa và ngày Canh Dần — Nhật chủ Canh Kim. Nhãn Kim ở Nhật
chủ không thay thế nạp âm năm sinh. Ngữ cảnh AI nhận riêng hai dữ kiện; prompt
và bộ kiểm bài đọc ngăn cách gọi mơ hồ “mệnh Kim” khi đang nói về Nhật chủ.

Chạy local cần Node.js >=18 bên cạnh Python:

```sh
npm ci
npm run build:css
.venv/bin/python -m uvicorn randomyst.api:app --host 127.0.0.1 --port 8765
```

Dockerfile sao chép Node 22 và dependency runtime `lunar-javascript` vào image
Python, cùng engine đã ghim; không cần chạy server Node riêng.

Xem `vendor/tinix-bazi/README.md` cho các lỗi nguồn đã sửa và cách kiểm hash.
Điểm vận và cách quy đổi tuổi giữ quy ước của repo nguồn; các nhánh chấm sức mạnh
có thể khác nhau. API assessment dùng nhánh cân bằng Ngũ Hành, giao diện ghi rõ
nguồn và phạm vi diễn giải. Không coi lời điển tích sinh tự động là nguyên văn cổ thư.

Kiểm thử: `tests/test_tinix_bazi.py`, `tests/test_tinix_engine.cjs`, kiểm thử lịch,
pipeline LLM, snapshot, lịch sử và giao diện hiện có. LLM giả lập dùng trong kiểm
thử giao diện, không gọi nhà cung cấp thật.
