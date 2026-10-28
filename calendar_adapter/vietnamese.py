"""Vietnamese civil lunar dates using a fixed UTC+7 calendar.

Astronomical approximation and calendar rules described by Ho Ngoc Duc:
https://honguyenviet.com/amlich/calrules.html
This prototype does not supply precise solar terms or an EoT calculation.
"""

from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from math import floor, isfinite, pi, sin

LOOKUP_START = date(1949, 12, 1)
LOOKUP_END = date(2031, 1, 31)
ALGORITHM_ID = "hnd-simplified-vn-utc7-v0.1"
SOURCE_URL = "https://honguyenviet.com/amlich/calrules.html"
BRANCHES = ("Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi")
_EPOCH = 2415021.076998695
_SYNODIC_MONTH = 29.530588853
_ORDINAL_TO_JDN = 1721425


class CalendarError(ValueError):
    """An input or lookup failure with a stable machine-readable code."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class LunarDate:
    year: int
    month: int
    day: int
    is_leap_month: bool = False

    def __post_init__(self):
        if any(type(v) is not int for v in (self.year, self.month, self.day)):
            raise CalendarError("INVALID_LUNAR_DATE", "Year, month and day must be integers.")
        if not (1 <= self.year <= 9999 and 1 <= self.month <= 12 and 1 <= self.day <= 30):
            raise CalendarError("INVALID_LUNAR_DATE", "Lunar date fields are outside their ranges.")
        if type(self.is_leap_month) is not bool:
            raise CalendarError("INVALID_LUNAR_DATE", "is_leap_month must be a boolean.")

    @property
    def year_branch_index(self) -> int:
        return (self.year + 8) % 12 + 1


def _jdn(value: date) -> int:
    # Only Gregorian dates in the MVP range are exposed by this adapter.
    return value.toordinal() + _ORDINAL_TO_JDN


def _date_from_jdn(value: int) -> date:
    return date.fromordinal(value - _ORDINAL_TO_JDN)


@lru_cache(maxsize=4096)
def _new_moon_jd(k: int) -> float:
    """Approximate new moon Julian day in UT, before calendar-day rounding."""
    t = k / 1236.85
    t2, t3 = t * t, t * t * t
    radians = pi / 180
    mean = 2415020.75933 + 29.53058868 * k + 0.0001178 * t2 - 0.000000155 * t3
    mean += 0.00033 * sin((166.56 + 132.87 * t - 0.009173 * t2) * radians)
    solar_anomaly = (359.2242 + 29.10535608 * k - 0.0000333 * t2 - 0.00000347 * t3) * radians
    lunar_anomaly = (306.0253 + 385.81691806 * k + 0.0107306 * t2 + 0.00001236 * t3) * radians
    latitude_argument = (21.2964 + 390.67050646 * k - 0.0016528 * t2 - 0.00000239 * t3) * radians
    correction = (0.1734 - 0.000393 * t) * sin(solar_anomaly)
    correction += 0.0021 * sin(2 * solar_anomaly)
    correction -= 0.4068 * sin(lunar_anomaly)
    correction += 0.0161 * sin(2 * lunar_anomaly) - 0.0004 * sin(3 * lunar_anomaly)
    correction += 0.0104 * sin(2 * latitude_argument)
    correction -= 0.0051 * sin(solar_anomaly + lunar_anomaly)
    correction -= 0.0074 * sin(solar_anomaly - lunar_anomaly)
    correction += 0.0004 * sin(2 * latitude_argument + solar_anomaly)
    correction -= 0.0004 * sin(2 * latitude_argument - solar_anomaly)
    correction -= 0.0006 * sin(2 * latitude_argument + lunar_anomaly)
    correction += 0.0010 * sin(2 * latitude_argument - lunar_anomaly)
    correction += 0.0005 * sin(2 * lunar_anomaly + solar_anomaly)
    delta_t_days = -0.000278 + 0.000265 * t + 0.000262 * t2
    return mean + correction - delta_t_days


def _new_moon_day(k: int, offset_hours: int) -> int:
    return floor(_new_moon_jd(k) + 0.5 + offset_hours / 24)


def _principal_term_sector(jdn: int, offset_hours: int) -> int:
    """30-degree solar sector at local midnight, not a precise Jie solver."""
    t = (jdn - 2451545.5 - offset_hours / 24) / 36525
    t2 = t * t
    radians = pi / 180
    anomaly = (357.52910 + 35999.05030 * t - 0.0001559 * t2 - 0.00000048 * t * t2) * radians
    longitude = 280.46645 + 36000.76983 * t + 0.0003032 * t2
    longitude += (1.914600 - 0.004817 * t - 0.000014 * t2) * sin(anomaly)
    longitude += (0.019993 - 0.000101 * t) * sin(2 * anomaly) + 0.000290 * sin(3 * anomaly)
    return floor(((longitude * radians) % (2 * pi)) / (pi / 6))


@lru_cache(maxsize=512)
def _month_eleven_start(year: int, offset_hours: int) -> int:
    k = floor((_jdn(date(year, 12, 31)) - 2415021) / _SYNODIC_MONTH)
    start = _new_moon_day(k, offset_hours)
    if _principal_term_sector(start, offset_hours) >= 9:
        start = _new_moon_day(k - 1, offset_hours)
    return start


@lru_cache(maxsize=512)
def _leap_offset(month_eleven_start: int, offset_hours: int) -> int:
    k = floor((month_eleven_start - _EPOCH) / _SYNODIC_MONTH + 0.5)
    previous_sector = _principal_term_sector(_new_moon_day(k + 1, offset_hours), offset_hours)
    for position in range(2, 15):
        sector = _principal_term_sector(_new_moon_day(k + position, offset_hours), offset_hours)
        if sector == previous_sector:
            return position - 1
        previous_sector = sector
    raise CalendarError("CALENDAR_INVARIANT_FAILED", "No leap month found between month-eleven anchors.")


def _solar_to_lunar(value: date, offset_hours: int = 7) -> LunarDate:
    """Internal converter; UTC+8 exists here only for diagnostic comparison."""
    day_number = _jdn(value)
    k = floor((day_number - _EPOCH) / _SYNODIC_MONTH)
    start = _new_moon_day(k + 1, offset_hours)
    if start > day_number:
        start = _new_moon_day(k, offset_hours)
    a11 = _month_eleven_start(value.year, offset_hours)
    b11 = a11
    if a11 >= start:
        lunar_year = value.year
        a11 = _month_eleven_start(value.year - 1, offset_hours)
    else:
        lunar_year = value.year + 1
        b11 = _month_eleven_start(value.year + 1, offset_hours)
    month_position = floor((start - a11) / 29)
    lunar_month = month_position + 11
    leap = False
    if b11 - a11 > 365:
        leap_position = _leap_offset(a11, offset_hours)
        if month_position >= leap_position:
            lunar_month = month_position + 10
            leap = month_position == leap_position
    if lunar_month > 12:
        lunar_month -= 12
    if lunar_month >= 11 and month_position < 4:
        lunar_year -= 1
    return LunarDate(lunar_year, lunar_month, day_number - start + 1, leap)


class VietnameseCalendar:
    """Fixed UTC+7 converter with the approved internal date buffer."""

    __slots__ = ()
    offset_minutes = 420
    algorithm_id = ALGORITHM_ID

    @staticmethod
    def _validate_date(value: date):
        if type(value) is not date:
            raise CalendarError("INVALID_SOLAR_DATE", "Supply a Gregorian date, not a datetime.")
        if not LOOKUP_START <= value <= LOOKUP_END:
            raise CalendarError("CALENDAR_LOOKUP_OUT_OF_RANGE", "Internal lookup covers 1949-12-01 through 2031-01-31.")

    def to_lunar(self, value: date) -> LunarDate:
        self._validate_date(value)
        return _solar_to_lunar(value)

    def to_solar(self, value: LunarDate) -> date:
        if not isinstance(value, LunarDate):
            raise CalendarError("INVALID_LUNAR_DATE", "Supply a LunarDate.")
        if not 1949 <= value.year <= 2031:
            raise CalendarError("CALENDAR_LOOKUP_OUT_OF_RANGE", "Lunar year is outside the internal buffer.")
        if value.month < 11:
            a11 = _month_eleven_start(value.year - 1, 7)
            b11 = _month_eleven_start(value.year, 7)
        else:
            a11 = _month_eleven_start(value.year, 7)
            b11 = _month_eleven_start(value.year + 1, 7)
        k = floor((a11 - _EPOCH) / _SYNODIC_MONTH + 0.5)
        month_position = (value.month - 11) % 12
        if b11 - a11 > 365:
            leap_position = _leap_offset(a11, 7)
            leap_month = (leap_position - 2) % 12 or 12
            if value.is_leap_month and value.month != leap_month:
                raise CalendarError("INVALID_LEAP_MONTH", "This year has no such leap month.")
            if value.is_leap_month or month_position >= leap_position:
                month_position += 1
        elif value.is_leap_month:
            raise CalendarError("INVALID_LEAP_MONTH", "This lunar year is not a leap year.")
        solar = _date_from_jdn(_new_moon_day(k + month_position, 7) + value.day - 1)
        self._validate_date(solar)
        # Reject day 30 in a 29-day month rather than rolling into a new month.
        if self.to_lunar(solar) != value:
            raise CalendarError("INVALID_LUNAR_DATE", "Day does not exist in the requested lunar month.")
        return solar

    def describe(self, value: date) -> dict:
        lunar = self.to_lunar(value)
        return {
            "solar_date": value.isoformat(),
            "lunar": asdict(lunar),
            "year_branch": BRANCHES[lunar.year_branch_index - 1],
            "year_branch_index": lunar.year_branch_index,
            "calendar_offset_minutes": self.offset_minutes,
            "algorithm_id": self.algorithm_id,
            "source": SOURCE_URL,
            "validation_status": "EXPERIMENTAL",
            "astronomical_error_bound_seconds": None,
        }


def resolve_maihoa(civil_datetime: datetime, true_solar_datetime: datetime, kind: str = "casting") -> dict:
    """Convert an upstream TST clock to Mai Hoa variables.

    TST is a naive *clock representation*, not a replacement UTC instant.
    Its longitude/EoT and uncertainty must be supplied by the time module.
    """
    if kind not in ("birth", "casting"):
        raise CalendarError("INVALID_INPUT_KIND", "kind must be birth or casting.")
    if not isinstance(civil_datetime, datetime) or civil_datetime.utcoffset() != timedelta(hours=7):
        raise CalendarError("INVALID_INPUT_TIMEZONE", "Civil input must carry an explicit +07:00 offset.")
    bounds = (1950, 2026) if kind == "birth" else (2024, 2030)
    if not bounds[0] <= civil_datetime.year <= bounds[1]:
        raise CalendarError("INPUT_OUT_OF_RANGE", "Civil input year is outside the approved range.")
    if not isinstance(true_solar_datetime, datetime) or true_solar_datetime.tzinfo is not None:
        raise CalendarError("INVALID_TST_CLOCK", "TST must be a naive apparent-solar clock datetime.")
    # Bound the upstream offset to the physical envelope of valid longitudes
    # [-180, 180] and a conservative |EoT| < 30 minutes for this prototype.
    offset_minutes = (true_solar_datetime - civil_datetime.replace(tzinfo=None)).total_seconds() / 60
    if not isfinite(offset_minutes) or not -1170 <= offset_minutes <= 330:
        raise CalendarError("INVALID_TST_CLOCK", "Upstream solar-clock offset is implausible.")
    effective_date = (true_solar_datetime + timedelta(hours=1)).date()
    calendar = VietnameseCalendar()
    lunar = calendar.to_lunar(effective_date)
    hour_index = ((true_solar_datetime.hour + 1) // 2) % 12 + 1
    return {
        "kind": kind,
        "civil_datetime": civil_datetime.isoformat(),
        "utc_instant": civil_datetime.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "true_solar_clock": true_solar_datetime.isoformat(),
        "effective_date": effective_date.isoformat(),
        "civil_lunar": asdict(calendar.to_lunar(civil_datetime.date())),
        "effective_lunar": asdict(lunar),
        "maihoa_inputs": {"Y": lunar.year_branch_index, "M": lunar.month, "D": lunar.day, "H": hour_index},
        "calendar_offset_minutes": 420,
        "algorithm_id": ALGORITHM_ID,
        "validation_status": "EXPERIMENTAL",
        "TST_calculation": "SUPPLIED_BY_UPSTREAM",
    }
