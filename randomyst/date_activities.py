"""Explicit product activity policy; raw tokens keep their literal scope.

This registry is reviewed as product policy, not a certified traditional method.
The research proposal remains an immutable historical artifact.
"""
from typing import Literal

Activity = Literal[
    "MARRIAGE", "BUSINESS_OPENING", "TRAVEL", "HOME_ENTRY", "RELOCATION",
    "RENOVATION", "TRADE", "LAND_BREAKING", "ROOF_BEAM", "CONTRACT_RITE",
    "PROPERTY_ACQUISITION", "RECEIVE_ASSETS", "START_EDUCATION", "START_JOB",
    "ANCESTOR_RITE", "BETROTHAL_NACAI", "BETROTHAL_COVENANT",
    "INCENSE_INSTALLATION", "BED_SETUP", "DEMOLITION", "PRAYER",
]
REGISTRY_VERSION = "major-events-2026-10-25-v2"
GROUPS = [
    {"group_id": "MARRIAGE_FAMILY", "name": "Hôn nhân, gia thất"},
    {"group_id": "HOME_RESIDENCE", "name": "An cư, chỗ ở"},
    {"group_id": "BUILDING_RENOVATION", "name": "Xây dựng, tu tạo"},
    {"group_id": "BUSINESS_ASSETS", "name": "Kinh doanh, tài sản"},
    {"group_id": "CAREER_EDUCATION", "name": "Công danh, học nghiệp"},
    {"group_id": "MAJOR_TRAVEL", "name": "Xuất hành trọng yếu"},
    {"group_id": "FAMILY_RITES", "name": "Gia tiên, lễ nghi"},
]


def spec(key, name, group, token, roles, mode, anchor, note,
         profile="CONSTRUCTIVE_V2", enabled=True):
    return {"activity": key, "name": name, "group_id": group,
            "provider_token": token,
            "provider_hour_token": None if mode == "DAY_ONLY" else token,
            "subject_count": len(roles), "subject_roles": roles,
            "hour_evaluation_mode": mode, "rule_profile": profile,
            "event_anchor": anchor, "scope_note": note,
            "enabled": enabled, "tier": "CORE" if enabled else "CONTEXTUAL",
            "review_status": "PRODUCT_POLICY" if enabled else "NOT_ENABLED"}


PAIR = ["Đương sự thứ nhất", "Đương sự thứ hai"]
ACTIVITIES = [
    spec("MARRIAGE", "Thành hôn", "MARRIAGE_FAMILY", "嫁娶", PAIR, "LEGACY_V1",
         "Bắt đầu nghi thức thành hôn.", "Nhập hồ sơ hai đương sự; lễ ngỏ lời và đính ước được tra riêng.", "LEGACY_V1"),
    spec("BETROTHAL_NACAI", "Nạp thái — lễ ngỏ lời", "MARRIAGE_FAMILY", "纳采", PAIR, "DAY_ONLY",
         "Bắt đầu lễ nạp thái, ngỏ lời kết hôn.", "Chọn khi gia đình thực hiện lễ nạp thái; phạm vi này chưa bao gồm mọi nghi thức ăn hỏi."),
    spec("BETROTHAL_COVENANT", "Đính ước", "MARRIAGE_FAMILY", "订盟", PAIR, "DAY_ONLY",
         "Bắt đầu nghi thức xác lập đính ước.", "Xét lễ đính ước của hai đương sự; chọn Thành hôn cho nghi thức cưới."),
    spec("HOME_ENTRY", "Nhập trạch", "HOME_RESIDENCE", "入宅", ["Gia chủ"], "DIRECT_YI_JI",
         "Bắt đầu nghi thức vào ở tại nơi cư trú mới.", "Xét lịch và hồ sơ gia chủ; phương vị và bố trí nhà chưa được đánh giá."),
    spec("RELOCATION", "Chuyển nơi cư trú", "HOME_RESIDENCE", "移徙", ["Người chủ trì chuyển cư"], "DIRECT_YI_JI",
         "Bắt đầu chuyển cư theo mốc đã chọn.", "Nhập người đứng việc chuyển cư. Kết quả áp dụng hồ sơ này; nghi thức nhập trạch tra riêng."),
    spec("LAND_BREAKING", "Động thổ xây dựng", "BUILDING_RENOVATION", "动土", ["Chủ sự xây dựng"], "DAY_ONLY",
         "Bắt đầu động thổ công trình.", "Xét ngày khởi công động thổ xây dựng; phương vị, thế đất và phần mộ nằm ngoài phạm vi."),
    spec("RENOVATION", "Tu tạo, sửa chữa lớn", "BUILDING_RENOVATION", "修造", ["Chủ sự tu tạo"], "DIRECT_YI_JI",
         "Khởi công hạng mục tu tạo đã xác định.", "Xét hạng mục sửa chữa lớn; động thổ tra riêng. Phương vị công trình chưa được đánh giá."),
    spec("ROOF_BEAM", "Thượng lương — gác đòn nóc", "BUILDING_RENOVATION", "上梁", ["Chủ sự xây dựng"], "DAY_ONLY",
         "Đặt đòn nóc hoặc dầm nóc theo nghi thức thượng lương.", "Áp dụng mốc gác đòn nóc; các hình thức cất nóc khác cần xác định nghi thức tương ứng."),
    spec("BUSINESS_OPENING", "Khai trương", "BUSINESS_ASSETS", "开市", ["Chủ sự kinh doanh"], "LEGACY_V1",
         "Bắt đầu khai trương hoặc mở bán.", "Nhập người đứng việc kinh doanh; ký văn khế và giao dịch được tra riêng.", "LEGACY_V1"),
    spec("CONTRACT_RITE", "Lập văn khế — ký kết mua bán", "BUSINESS_ASSETS", "立券", ["Người đứng giao kết"], "DAY_ONLY",
         "Xác lập văn khế mua bán.", "Xét mốc giao kết mua bán và hồ sơ phía đương sự đã nhập; hợp đồng lao động hoặc hợp tác khác chưa được xét."),
    spec("TRADE", "Giao dịch tài sản lớn", "BUSINESS_ASSETS", "交易", ["Người đứng giao dịch"], "DIRECT_YI_JI",
         "Bắt đầu bước mua bán hoặc giao nhận được chọn.", "Chọn một bước cụ thể; mốc ký văn khế và nhập trạch được tra riêng. Kết quả áp dụng đương sự đã nhập."),
    spec("PROPERTY_ACQUISITION", "Mua nhà đất — điền sản", "BUSINESS_ASSETS", "置产", ["Người tạo lập điền sản"], "DAY_ONLY",
         "Mua hoặc nhận chuyển giao nhà đất trong giao dịch mua bán.", "Chọn Lập văn khế khi tra mốc ký kết, hoặc Nhập trạch khi tra mốc vào ở."),
    spec("RECEIVE_ASSETS", "Nạp tài — thu nhận tài vật", "BUSINESS_ASSETS", "纳财", ["Người thu nhận tài vật"], "DAY_ONLY",
         "Thu nhận tài vật quan trọng theo mốc đã chọn.", "Xét mốc thu tài vật; chưa đánh giá đầu tư, vay vốn hoặc cơ may tiền bạc nói chung."),
    spec("START_JOB", "Nhậm chức, nhận nhiệm vụ", "CAREER_EDUCATION", "赴任", ["Người nhậm chức"], "DIRECT_YI_JI",
         "Bắt đầu nhận chức trách hoặc nhiệm vụ được bổ nhiệm.", "Phạm vi là nhậm chức; lịch nguồn có ít ngày đề cập việc này. Chưa mở rộng sang mọi ngày đầu đi làm."),
    spec("START_EDUCATION", "Nhập học", "CAREER_EDUCATION", "入学", ["Người nhập học"], "DAY_ONLY",
         "Bắt đầu nhập học tại mốc có thể chủ động chọn.", "Nhập hồ sơ người học, kể cả khi người thao tác là phụ huynh; thi tuyển và phỏng vấn nằm ngoài phạm vi."),
    spec("TRAVEL", "Xuất hành", "MAJOR_TRAVEL", "出行", ["Người xuất hành"], "LEGACY_V1",
         "Bắt đầu chuyến đi trọng yếu.", "Áp dụng thời điểm khởi hành và hồ sơ người đi; hướng xuất hành chưa được xét.", "LEGACY_V1"),
    spec("ANCESTOR_RITE", "Tế lễ gia tiên", "FAMILY_RITES", "祭祀", ["Người chủ lễ"], "DIRECT_YI_JI",
         "Bắt đầu lễ gia tiên có thể chủ động chọn ngày.", "Nhập người chủ lễ. Các ngày giỗ cố định tiếp tục theo lệ gia đình.", "RITUAL_V2"),
    spec("INCENSE_INSTALLATION", "An hương", "FAMILY_RITES", "安香", ["Người chủ lễ"], "DAY_ONLY",
         "Bắt đầu nghi thức an hương đã xác định.", "Xét lịch và hồ sơ người chủ lễ cho nghi thức an hương; cách an vị, phương hướng và bố trí thờ tự chưa được đánh giá.", "RITUAL_V2"),
    spec("BED_SETUP", "An sàng — đặt giường", "HOME_RESIDENCE", "安床", ["Gia chủ"], "DIRECT_YI_JI",
         "Đặt giường theo nghi thức.", "Chưa bật: cần tách vai trò an sàng trong an cư và trong hôn lễ.", "DEFERRED", False),
    spec("DEMOLITION", "Tháo dỡ", "BUILDING_RENOVATION", "拆卸", ["Chủ sự công trình"], "DAY_ONLY",
         "Khởi công tháo dỡ.", "Chưa bật: cần bộ luật riêng và duyệt phạm vi phá nhà/tháo dỡ.", "DEFERRED", False),
    spec("PRAYER", "Cầu phúc", "FAMILY_RITES", "祈福", ["Người chủ lễ"], "DIRECT_YI_JI",
         "Bắt đầu lễ cầu phúc.", "Chưa bật: cần xác định nghi thức và phạm vi luật riêng.", "DEFERRED", False),
]
BY_ACTIVITY = {row["activity"]: row for row in ACTIVITIES}
