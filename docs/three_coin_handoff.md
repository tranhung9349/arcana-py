# Bàn giao gieo ba đồng · Lục Hào

**30/10/2026 · giao diện tối giản:** form chỉ còn chủ đề, câu hỏi và nút **Gieo và lập quẻ**. Cố định `RANDOM` + `CURRENT`, thời điểm gửi đúng offset `+07:00`; retry giữ nguyên request ID và thời điểm. Hiển thị đủ 6 lượt tiền, quẻ chủ/biến và hào động trước lời luận AI. Bỏ hai mục “Xem căn cứ của lời giải”/“Thông tin bài luận” khỏi bài Lục Hào; bảng chuyên môn còn trong mục tham khảo đóng mặc định. API/snapshot lịch sử vẫn đọc được dữ kiện gieo tay, không đổi quẻ cũ.

**30/10/2026 · v4.5:** request LLM gửi đủ quẻ đã gieo, lịch/bàn hào và nguyên văn nguồn đúng quẻ; system prompt Lục Hào riêng. Đã kiểm payload HTTP và chạy thật qua rexapf.com. [Chi tiết](liuyao_plain_reading_handoff.md).

**30/10/2026:** bài dễ hiểu tự chạy sau khi lập quẻ, trả lời và giải thích ngắn đứng trước phần chuyên môn; kinh văn/bảng quẻ thu gọn. Prompt Lục Hào v4.4 tách các ý hỏi và giữ rõ giới hạn thời gian. [Chi tiết và kiểm tra](liuyao_plain_reading_handoff.md).

**28/10/2026:** bảng tra cứu 64 quẻ chuyển sang submenu **Thư viện 64 quẻ** trong Kinh Dịch, có trang đọc kinh văn riêng. Tra cứu không thay nội dung phiên gieo đang mở. [Chi tiết và kiểm chứng](iching_library_handoff.md).

Đã chọn phép **3 đồng × 6 lượt**, `BACK=3`, `INSCRIPTION=2`, từ dưới lên; phương pháp duy nhất của tính năng này. [Nghiên cứu và nguồn](research/three_coin_liuyao_research.md).

Tab **Gieo 3 đồng · Lục Hào** có gieo tự động, nhập 18 mặt của sáu lượt gieo thật, thời điểm hiện tại/tùy chọn, quẻ chủ/biến, đủ hào động, bàn Nạp Giáp cơ bản, thư viện 64 quẻ và lịch sử riêng. Mở lại giữ snapshot của cả kinh văn và phần nghĩa Việt.

Bàn quẻ có cung, Thế–Ứng, Lục thân, Lục thú, Tuần Không và Nguyệt Phá. **Đã bổ sung [module luận Lục Hào theo chủ đề](liuyao_analysis_handoff.md)**: chọn Dụng thần, xét Nhật–Nguyệt, động biến và Phi/Phục, có căn cứ từng nhận định. Chưa phải engine giải toàn cục hoặc ấn định ngày ứng nghiệm. Nghĩa quẻ là bản nháp Việt có sẵn chưa hiệu đính; không gọi LLM.

## API

| Endpoint | Chức năng |
| --- | --- |
| `GET /api/v1/coins/hexagrams` | 64 quẻ, quy ước và nguồn |
| `GET /api/v1/coins/hexagrams/{1..64}` | Kinh văn và bản nghĩa Việt, không lưu phiên |
| `POST /api/v1/coins/consultations` | Gieo đủ sáu lượt hoặc nhận kết quả nhập tay và lưu snapshot |
| `GET /api/v1/coins/consultations/{UUID}` | Đọc snapshot, không gieo/tính lại |
| `GET /api/v1/coins/history?limit=10` | Lịch sử riêng, limit 1–100 |

Ví dụ: `examples/coin_consultation_request.json`. API request dùng `source=RANDOM` khi gieo tự động, không gửi `throws_bottom_to_top`. Dùng `source=MANUAL` phải gửi đủ 6 mảng, mỗi mảng đúng ba giá trị `BACK`/`INSCRIPTION`. `casting` dùng cùng cấu trúc CURRENT/CUSTOM và kiểm timezone UTC+7 của app. UUID giữ nguyên để thử lại khi mất kết nối; payload khác cùng UUID trả 409.

Response `coin-consultation-v1`: `original`, `changed` (null khi không có hào động), `moving_lines` theo thứ tự tăng, `casting.throws_bottom_to_top`, `casting.totals_bottom_to_top`, `calendar`, `najia`, nguồn và giới hạn. Mỗi `CoinReading` có `reference_lines` đủ sáu hào; `text.moving_line=null` vì các vị trí động được lưu riêng ở cấp phiên, hỗ trợ 0–6 hào.

SQLite dùng bảng riêng `coin_sessions` trong cùng database cấu hình bằng `RANDOMYST_DATABASE`. Sửa quy ước tương lai cần tăng version; không cập nhật hoặc tính lại các bản ghi cũ. Config bàn Nạp Giáp nằm trong `config/coins_rules.json`; SHA-256 config được lưu trong `calendar.rules_sha256` của từng phiên.

## Kiểm tra và chạy

```sh
.venv/bin/python -m unittest discover -s tests -v
./scripts/run_mvp.sh
```

Mở [app local](http://127.0.0.1:8765), chọn tab gieo ba đồng. [Báo cáo](research/three_coin_validation.json) ghi phạm vi kiểm tra; ảnh UI ở cùng thư mục nghiên cứu.
