> Calendar runtime hiện dùng 6tail UTC+8 (rules v4). `legacy_time_engine.py` và `calendar_adapter/` chỉ phục vụ báo cáo nghiên cứu v3; không tham gia gieo số hiện tại.

## Khảo sát phương pháp lập và luận quẻ

```sh
.venv/bin/python -m research_tools.audit_iching_methods
```

Đọc corpus Kinh Dịch và lõi Mai Hoa hiện hành; liệt kê không gian hào 6/7/8/9, xác suất ba đồng tiền theo giả định công bằng/độc lập, độ phủ tuple Mai Hoa và hai ví dụ số học từ cổ thư. Xuất `docs/research/iching_methods_audit.json`, không tạo phiên gieo, không gọi API hoặc đọc lịch sử SQLite. Mô hình xác suất thi thảo chỉ được khai báo để so sánh, chưa mô phỏng thao tác chia cọng. [Bản nghiên cứu và lộ trình](../docs/research/iching_casting_interpretation_research.md) phân biệt nguồn cổ, quy ước sản phẩm và phần chưa đủ căn cứ để triển khai.

Sau triển khai ngày 25/10, dùng `.venv/bin/python -m research_tools.maihoa_source_audit` để kiểm nguồn/52 trích đoạn đã ghim, đủ 51.840 tuple, ngoại lệ hỗ Càn/Khôn và 1.152 bài luận đại diện thời gian thực. Xuất `docs/research/maihoa_source_validation.json`, không truy cập SQLite hay tạo phiên qua API. Audit ngày 24/10 giữ nguyên là bản trước triển khai; xem [bàn giao Mai Hoa](../docs/maihoa_source_handoff.md).

## Khảo sát chọn ngày MVP 2

```sh
.venv/bin/python -m research_tools.auspicious_date_audit
```

Khảo sát provider đã ghim, độ phủ Yi/Ji 2024–2030 cho cưới/khai trương/xuất hành, ranh UTC+7/UTC+8, hai hệ 12 mục và bảng nguồn cho ngày kỵ. Lưu `docs/research/mvp2_auspicious_date_feasibility.json`. Đây là bằng chứng khả thi phần mềm; script không chấm ngày, không sinh số hoặc truy cập lịch sử SQLite. Kế hoạch: `docs/logic_plan_mvp2.md`.

MVP 2 đã triển khai tại `randomyst/date_*`; build corpus/config/schema bằng `.venv/bin/python scripts/build_date_data.py`, kiểm HTTP bằng `.venv/bin/python scripts/smoke_dates.py`. Khảo sát trên vẫn giữ vai trò nghiên cứu trước R1; corpus runtime đầy đủ có ngày đệm, không chỉ mẫu tại 12h. Xem `MVP2_HANDOFF.md`.

Nghiên cứu mở rộng category: `.venv/bin/python research_tools/audit_activity_categories.py`. Script chỉ đọc corpus đã ghim, audit 23 category dự kiến trên 2.557 ngày Bắc Kinh / 33.241 mốc giờ của 2024–2030, bỏ ngày đệm 2031; giữ token ngày/giờ riêng, trạng thái và ngày mâu thuẫn, cùng thống kê từng năm. Xuất `docs/research/mvp2_activity_token_coverage.json`; đề xuất triển khai trong `docs/research/mvp2_activity_expansion.md`. Không bật category, chấm GOOD hay truy cập lịch sử gieo số.

## Audit danh mục việc trọng đại — 25/10/2026

```sh
.venv/bin/python -m research_tools.audit_major_event_catalog
```

Đọc `docs/research/mvp2_major_event_catalog.json`, kiểm nhóm/role/token/capability và ba việc live tại thời điểm nghiên cứu (profile LEGACY_V1), quét corpus đã ghim 2024–2030; xuất `docs/research/mvp2_major_event_coverage.json`. Báo cáo có số đếm từng năm, xung đột, token giờ ứng viên chưa được duyệt và đối chiếu số đếm với báo cáo 14/10. Chỉ phục vụ nghiên cứu; không bật category, chấm điểm hoặc sửa luật runtime. [Runtime v2 đã triển khai](../docs/major_events_handoff.md) dùng registry riêng; kiểm bằng `scripts/smoke_major_dates.py` với preview local đang chạy. Báo cáo nghiên cứu cũ giữ lịch sử trước triển khai.

# Các script kiểm chứng logic MVP 1

Các script phục vụ nghiên cứu; chưa phải API hoặc bộ sinh số sản phẩm. Python 3.10 trở lên.

## Phân bố trọng số hàm mũ

Chạy tại thư mục dự án; không cần cài package:

```sh
python3 -m unittest discover -s tests -v
python3 -m research_tools.exponential_audit --output-dir docs/research --samples-per-context 100 --seed 20261011
```

Đổi danh sách beta để thử thêm:

```sh
python3 -m research_tools.exponential_audit --betas 0.5 1 2 3 4 --samples-per-context 200 --output-dir /tmp/randomyst-beta-test
```

Input là cấu hình đã chốt `config/mvp1_rules.json` và `dan_gian_config.json`. Thử beta 0/0,25/0,5/1/2/4/8 mặc định, bể 00–99 theo rules v6, quota 3–4 ở Đại Hung, ngưỡng 80/85. Cột điểm ≥75 được giữ để đối chiếu, không phải ngưỡng dừng hiện tại.

Script kiểm tra các giả định bể/luật/ngưỡng trước khi chạy; đổi chính sách đó cần một phiên bản kiểm chứng mới. Miền beta cho phép ở bản thử số học này là **0–20**, tránh nhận tham số NaN/vô hạn hoặc độ tập trung cực đoan làm trọng số underflow.

Output:

- `remediation_feasibility_v6.json`: kiểm tra đủ 25 trường hợp Đại Hung trên bể 00–99, xếp hạng hành giải sát theo điểm thô khả thi; so sánh với quota cũ 3–5 bằng phép tính riêng. Không sửa báo cáo các phiên bản cũ.
- `exponential_distribution_trial_v6.json`: xác suất tính chính xác theo cấu hình, kết quả từng ngữ cảnh và kiểm tra Monte Carlo; ghi seed, hash cấu hình và phạm vi bể số.
- `exponential_distribution_trial_v6.md`: bảng dễ đọc và giới hạn của phép thử. Tên file lấy hậu tố phiên bản rules hiện tại để không ghi đè báo cáo cũ.

Phân bố thử tỷ lệ **tích trọng số các số trong bộ**, có điều kiện luật cứng. Nó khác phân bố lấy mẫu tuần tự rồi xóa số. Beta là **độ tập trung**, không phải temperature: tăng beta làm ưu tiên điểm cao mạnh hơn. Beta 0 vẫn có ×3/quota và các delta, nên không gọi toàn bộ engine là ngẫu nhiên đều.

Ngữ cảnh và delta minh họa không phải hồ sơ thực. Trung bình đều 125 tổ hợp không đại diện tự động cho tần suất quẻ/người dùng; phải dùng corpus thực/đại diện trước khi chốt beta/KPI. Quẻ Hổ/Quẻ Biến không được đưa vào thử nghiệm trọng số hay điểm.

## Kiểm tra schema/prompt

Bộ mẫu lời luận dễ hiểu v2 có 17 cặp, 8 ca đánh giá riêng, nguồn có hash và adapter đọc snapshot Bát Tự. Chưa gọi model hoặc nối runtime. Chi tiết: `docs/research/interpretation_sources_fewshot_v2.md`.

```sh
.venv/bin/python -m research_tools.interpretation_prompt \
  examples/bazi_consultation_response.json --bazi-snapshot \
  --output /tmp/arcana_plain_prompt_preview.json
```

Kiểm tra JSON Schema 2020-12 và ví dụ bằng `jsonschema==4.25.1` trong môi trường phát triển riêng:

```sh
python3 -m research_tools.validate_interpretation_examples
```

Thư viện validator này chỉ dùng kiểm định schema; adapter và script phân bố vẫn dùng thư viện chuẩn. Schema giới hạn cấu trúc/nhãn nhưng chưa thay kiểm định dữ kiện chéo và chất lượng dịch thuật. Mẫu response được viết để minh họa, chưa phải output từ LLM đã gọi.

## Sau khi chốt bản chạy

Người dùng đã chọn β = 2 và phân bố tích trọng số cho runtime `randomyst/`. Báo cáo phân bố v2 giữ trạng thái lịch sử trước lựa chọn; không phải KPI của ứng dụng. Runtime lấy delta thật từ hồ sơ/tháng gieo thay cho profile tổng hợp. Cấu hình hiện hành là `config/mvp1_rules.json` v6 với bể 00–99 và ngưỡng 80/85.

