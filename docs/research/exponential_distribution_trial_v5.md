# Thử phân bố trọng số hàm mũ — MVP 1

Bể **00–99**, trần quota **4**; runtime dùng **beta = 2**. Core Mai Hoa Y/M/D/H và lớp lịch không bị thay đổi trong kiểm chứng này.

Thử `b(n) = exp(beta × (S_i − max_allowed_S) / 100)`, sau đó ×3 hành giải sát và cộng các delta đã khóa. Beta lớn hơn ưu tiên mạnh hơn số có S_i cao. Trừ max là ổn định số học; mọi bộ có sáu số nên không đổi phân bố tương đối.

Xác suất một bộ hợp lệ tỷ lệ tích trọng số của sáu số, cùng luật sampling của runtime. Dùng đa thức đối xứng để tính chính xác khối lượng từng cấu hình và bốc tập không hoàn lại; khác cách bốc tuần tự rồi xóa số. Các profile delta dưới đây chỉ là dữ liệu tổng hợp.

125 tổ hợp P/Thể/Dụng có trọng số bằng nhau. Hai profile: không có delta phụ; và delta tổng hợp minh họa (tháng Dần, hào 2, Kim +30%/Thủy +20% Thần Sát, danh sách dân gian đã chốt). Profile minh họa không phải lá số thật, không suy ra tần suất sao hoặc các KPI thực tế.

| Profile | Beta | Đạt ngưỡng mode lượt 1 | Điểm ≥75 lượt 1 | Điểm trung bình |
|---|---:|---:|---:|---:|
| Không delta phụ | 2 | 70.24% | 73.04% | 80.45 |
| Delta minh họa | 2 | 70.03% | 72.83% | 80.37 |

Các tỷ lệ bảng trên tính từ toàn bộ cấu hình, không phải ước lượng từ Monte Carlo. JSON có phân bố chẵn/lẻ, số lượng kỳ vọng từng hành, kết quả từng ngữ cảnh và số bộ trùng trong lượt lấy mẫu. Trùng bộ giữa các phiên/lượt độc lập vẫn có thể xảy ra, khác việc trùng số bên trong bộ.

Retry trong thử nghiệm chọn trực tiếp từ cấu hình 3–3 đạt ngưỡng, giữ G_cap/ngưỡng/quẻ cũ. Trong Đại Hung thêm lọc số khắc Thể như phương án retry hiện có. Tỷ lệ đạt sau bước đó đến từ điều kiện bộ sinh; không chứng minh ×3 hoặc phép gieo ngẫu nhiên bất kỳ chắc chắn đạt.

Monte Carlo seed **20261026**, **50 bộ/ngữ cảnh/profile/beta**: 12,500 bộ đầu và 3,669 bộ retry; lỗi luật cứng **0**.

**Runtime giữ beta = 2.** Kiểm chứng này không thay đổi beta; cần corpus hồ sơ/thời gian đại diện để đánh giá tỷ lệ đạt và độ đa dạng thực tế. Điểm phong thủy nội bộ không đo xác suất trúng thưởng hay hiệu quả cải vận.
