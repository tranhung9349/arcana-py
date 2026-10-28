# Thử phân bố trọng số hàm mũ — MVP 1

Trần quota đã chốt: **4**. Core Mai Hoa Y/M/D/H và lớp lịch không bị thay đổi trong thử nghiệm này.

Thử `b(n) = exp(beta × (S_i − max_allowed_S) / 100)`, sau đó ×3 hành giải sát và cộng các delta đã khóa. Beta lớn hơn ưu tiên mạnh hơn số có S_i cao. Trừ max là ổn định số học; mọi bộ có sáu số nên không đổi phân bố tương đối.

**Phân bố thử nghiệm:** xác suất một bộ hợp lệ tỷ lệ tích trọng số của sáu số. Dùng đa thức đối xứng để tính chính xác khối lượng từng cấu hình và bốc tập không hoàn lại. Đây là một ứng viên bộ sinh, chưa phải quyết định phân bố sản phẩm; khác cách bốc tuần tự rồi xóa số.

125 tổ hợp P/Thể/Dụng có trọng số bằng nhau. Hai profile: không có delta phụ; và delta tổng hợp minh họa (tháng Dần, hào 2, Kim +30%/Thủy +20% Thần Sát, danh sách dân gian đã chốt). Profile minh họa không phải lá số thật, không suy ra tần suất sao hoặc các KPI thực tế.

| Profile | Beta | Đạt ngưỡng mode lượt 1 | Điểm ≥75 lượt 1 | Điểm trung bình |
|---|---:|---:|---:|---:|
| Không delta phụ | 0 | 6.20% | 10.35% | 44.34 |
| Không delta phụ | 0.25 | 11.73% | 15.89% | 50.74 |
| Không delta phụ | 0.5 | 19.99% | 23.94% | 57.39 |
| Không delta phụ | 1 | 40.59% | 43.97% | 68.60 |
| Không delta phụ | 2 | 71.37% | 74.20% | 80.72 |
| Không delta phụ | 4 | 85.82% | 87.22% | 87.11 |
| Không delta phụ | 8 | 88.83% | 89.07% | 89.43 |
| Delta minh họa | 0 | 6.24% | 10.39% | 44.35 |
| Delta minh họa | 0.25 | 11.78% | 15.93% | 50.75 |
| Delta minh họa | 0.5 | 20.03% | 23.97% | 57.39 |
| Delta minh họa | 1 | 40.60% | 43.97% | 68.59 |
| Delta minh họa | 2 | 71.32% | 74.14% | 80.70 |
| Delta minh họa | 4 | 85.76% | 87.14% | 87.08 |
| Delta minh họa | 8 | 88.77% | 89.00% | 89.41 |

Các tỷ lệ bảng trên tính từ toàn bộ cấu hình, không phải ước lượng từ Monte Carlo. JSON có phân bố chẵn/lẻ, số lượng kỳ vọng từng hành, kết quả từng ngữ cảnh và số bộ trùng trong lượt lấy mẫu. Trùng bộ giữa các phiên/lượt độc lập vẫn có thể xảy ra, khác việc trùng số bên trong bộ.

Retry trong thử nghiệm chọn trực tiếp từ cấu hình 3–3 đạt ngưỡng, giữ G_cap/ngưỡng/quẻ cũ. Trong Đại Hung thêm lọc số khắc Thể như phương án retry hiện có. Tỷ lệ đạt sau bước đó đến từ điều kiện bộ sinh; không chứng minh ×3 hoặc phép gieo ngẫu nhiên bất kỳ chắc chắn đạt.

Monte Carlo seed **20261011**, **100 bộ/ngữ cảnh/profile/beta**: 175,000 bộ đầu và 93,915 bộ retry; lỗi luật cứng **0**.

**Chưa chọn beta.** Cần cân nhắc tỷ lệ đạt, số lượng kỳ vọng từng hành, tỷ lệ lặp bộ và độ đa dạng trên corpus hồ sơ/thời gian đại diện. Điểm phong thủy nội bộ không đo xác suất trúng thưởng hay hiệu quả cải vận.
