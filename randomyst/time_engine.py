"""Beijing civil calendar via 6tail; no custom astronomical calculations.

Convert the aware input instant to UTC+8 before supplying wall-clock fields.
Mai Hoa uses the civil lunar date (midnight); Bazi uses exact Jie boundaries
and sect 1 (day pillar changes at 23:00 Beijing time).
"""
from datetime import datetime, timedelta, timezone
from importlib.metadata import version

from lunar_python import Solar

BEIJING = timezone(timedelta(hours=8))
LIBRARY_VERSION = "1.4.8"
ALGORITHM_ID = "6tail-chinese-utc8-v1"
SOURCE = "https://github.com/6tail/lunar-python"
STEMS = ("Giáp", "Ất", "Bính", "Đinh", "Mậu", "Kỷ", "Canh", "Tân", "Nhâm", "Quý")
BRANCHES = ("Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi")
STEMS_ZH = tuple("甲乙丙丁戊己庚辛壬癸")
BRANCHES_ZH = tuple("子丑寅卯辰巳午未申酉戌亥")
BRANCH_ELEMENTS = ("Thủy", "Thổ", "Mộc", "Mộc", "Thổ", "Hỏa", "Hỏa", "Thổ", "Kim", "Kim", "Thổ", "Thủy")
JIE_NAMES = dict(zip(
    ("小寒", "立春", "惊蛰", "清明", "立夏", "芒种", "小暑", "立秋", "白露", "寒露", "立冬", "大雪"),
    ("Tiểu Hàn", "Lập Xuân", "Kinh Trập", "Thanh Minh", "Lập Hạ", "Mang Chủng", "Tiểu Thử", "Lập Thu", "Bạch Lộ", "Hàn Lộ", "Lập Đông", "Đại Tuyết")))


class CalendarError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def check_provider():
    if version("lunar-python") != LIBRARY_VERSION:
        raise RuntimeError(f"Calendar provider requires lunar-python=={LIBRARY_VERSION}")


def _lunar(civil):
    if civil.utcoffset() is None:
        raise CalendarError("TIMEZONE_REQUIRED", "Ngày giờ phải có múi giờ.")
    beijing = civil.astimezone(BEIJING)
    lunar = Solar.fromYmdHms(beijing.year, beijing.month, beijing.day,
                            beijing.hour, beijing.minute, beijing.second).getLunar()
    return beijing, lunar


def beijing_clock(civil, clock_uncertainty_seconds=None):
    beijing, _ = _lunar(civil)
    seconds = beijing.hour*3600 + beijing.minute*60 + beijing.second + beijing.microsecond/1e6
    hour_distance = min(abs(seconds - edge) for edge in range(-3600, 93601, 7200))
    day_distance = min(seconds, 86400-seconds)
    known = clock_uncertainty_seconds
    distance = min(hour_distance, day_distance)
    return {"civil_datetime": civil.isoformat(),
            "utc_instant": civil.astimezone(timezone.utc).isoformat(),
            "beijing_datetime": beijing.isoformat(), "clock_basis": "BEIJING_CIVIL_UTC8",
            "timezone_offset_minutes": 480, "conversion_offset_minutes": (BEIJING.utcoffset(None)-civil.utcoffset()).total_seconds()/60,
            "true_solar_time_applied": False, "location_affects_calculation": False,
            "calculation_resolution_seconds": 1,
            "boundary": {"status": "UNDETERMINED" if known is None else ("BOUNDARY" if distance <= known else "CLEAR_WITHIN_BOUND"),
                         "delta_t_seconds": known,
                         "missing_components": ["clock_uncertainty"] if known is None else [],
                         "distance_to_hour_boundary_seconds": hour_distance,
                         "distance_to_calendar_day_boundary_seconds": day_distance,
                         "crosses_boundary_with_known_components": known is not None and distance <= known},
            "provider": f"lunar-python-{LIBRARY_VERSION}", "validation_status": "INTEGRATION_TESTED"}


def resolve_maihoa(civil, kind="casting"):
    ranges = {"birth": (1950, 2026), "casting": (2024, 2030)}
    if kind not in ranges:
        raise CalendarError("INVALID_CONTEXT", "Loại thời gian không hợp lệ.")
    lower, upper = ranges[kind]
    if civil.utcoffset() != timedelta(hours=7) or not lower <= civil.year <= upper:
        raise CalendarError("CIVIL_RANGE_INVALID", "Ngày giờ đầu vào UTC+7 nằm ngoài phạm vi MVP.")
    beijing, lunar = _lunar(civil)
    return {"algorithm_id": ALGORITHM_ID, "calendar": "CHINESE_LUNAR",
            "offset_minutes": 480, "provider": f"lunar-python-{LIBRARY_VERSION}",
            "source_url": SOURCE, "validation_status": "INTEGRATION_TESTED",
            "civil_datetime": civil.isoformat(), "beijing_datetime": beijing.isoformat(),
            "effective_date": beijing.date().isoformat(), "day_boundary": "00:00_BEIJING",
            "lunar": {"year": lunar.getYear(), "month": abs(lunar.getMonth()),
                      "day": lunar.getDay(), "is_leap_month": lunar.getMonth() < 0,
                      "year_branch": BRANCHES[lunar.getYearZhiIndex()], "hour_branch": BRANCHES[lunar.getTimeZhiIndex()]},
            "maihoa_inputs": {"Y": lunar.getYearZhiIndex()+1, "M": abs(lunar.getMonth()),
                              "D": lunar.getDay(), "H": lunar.getTimeZhiIndex()+1}}


def solar_month(civil):
    _, lunar = _lunar(civil)
    previous = lunar.getPrevJie(False)
    start = previous.getSolar()
    start_beijing = datetime(start.getYear(), start.getMonth(), start.getDay(),
                             start.getHour(), start.getMinute(), start.getSecond(), tzinfo=BEIJING)
    branch = lunar.getMonthZhiIndexExact()
    return {"year_ganzhi_zh": lunar.getYearInGanZhiExact(),
            "month_branch_index": branch, "month_branch": BRANCHES[branch],
            "jie_name": JIE_NAMES[previous.getName()], "jie_name_zh": previous.getName(),
            "jie_start_utc": start_beijing.astimezone(timezone.utc).isoformat(),
            "jie_start_beijing": start_beijing.isoformat(),
            "provider": f"lunar-python-{LIBRARY_VERSION}", "validation_status": "INTEGRATION_TESTED"}


def pillars(civil):
    beijing, lunar = _lunar(civil)
    chart = lunar.getEightChar()
    chart.setSect(1)
    pairs = (chart.getYear(), chart.getMonth(), chart.getDay(), chart.getTime())
    gans = [STEMS_ZH.index(pair[0]) for pair in pairs]
    zhis = [BRANCHES_ZH.index(pair[1]) for pair in pairs]
    return {"gans": gans, "zhis": zhis, "solar_month": solar_month(civil),
            "beijing_datetime": beijing.isoformat(), "day_boundary": "23:00_BEIJING", "sect": 1,
            "effective_date": (beijing + timedelta(hours=1)).date().isoformat(),
            "provider": f"lunar-python-{LIBRARY_VERSION}",
            "pillars": [{"pillar": label, "stem": STEMS[g], "branch": BRANCHES[z],
                         "stem_zh": STEMS_ZH[g], "branch_zh": BRANCHES_ZH[z]}
                        for label, g, z in zip(("year", "month", "day", "hour"), gans, zhis)]}
