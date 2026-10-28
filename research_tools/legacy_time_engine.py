"""Archived UTC/Jie and TST implementation; not used by the application.

Retained solely to reproduce v3 astronomy research reports.
"""
"""UTC instants, apparent clocks and solar-term boundaries remain distinct."""
from calendar import isleap
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from math import cos, sin, pi, radians, sqrt

import astronomy

VN = timezone(timedelta(hours=7))
STEMS = ("Giáp", "Ất", "Bính", "Đinh", "Mậu", "Kỷ", "Canh", "Tân", "Nhâm", "Quý")
BRANCHES = ("Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi")
STEMS_ZH = tuple("甲乙丙丁戊己庚辛壬癸")
BRANCHES_ZH = tuple("子丑寅卯辰巳午未申酉戌亥")
BRANCH_ELEMENTS = ("Thủy", "Thổ", "Mộc", "Mộc", "Thổ", "Hỏa", "Hỏa", "Thổ", "Kim", "Kim", "Thổ", "Thủy")
JIE_NAMES = ("Tiểu Hàn", "Lập Xuân", "Kinh Trập", "Thanh Minh", "Lập Hạ", "Mang Chủng", "Tiểu Thử", "Lập Thu", "Bạch Lộ", "Hàn Lộ", "Lập Đông", "Đại Tuyết")


def noaa_eot_minutes(instant):
    """NOAA fractional-year approximation; seconds displayed are not an error bound.

    Evaluate at UTC to give one EoT value for the same instant at every longitude.
    https://gml.noaa.gov/grad/solcalc/solareqns.PDF
    """
    utc = instant.astimezone(timezone.utc)
    hours = utc.hour + utc.minute / 60 + (utc.second + utc.microsecond / 1e6) / 3600
    gamma = 2 * pi / (366 if isleap(utc.year) else 365) * (utc.timetuple().tm_yday - 1 + (hours - 12) / 24)
    return 229.18 * (0.000075 + 0.001868*cos(gamma) - 0.032077*sin(gamma) - 0.014615*cos(2*gamma) - 0.040849*sin(2*gamma))


def longitude_error_from_radius(latitude, radius_m):
    """Conservative WGS84 conversion; radius retains its source confidence level."""
    if latitude is None or radius_m is None:
        return None
    worst_lat = abs(latitude) + radius_m / 6356752.314245 * 180 / pi
    if worst_lat >= 89.9:
        return None
    phi = radians(worst_lat)
    normal = 6378137 / sqrt(1 - 0.00669437999014 * sin(phi)**2)
    metres_per_degree = pi / 180 * normal * cos(phi)
    return min(180, radius_m / metres_per_degree)


def solar_clock(civil, location, clock_uncertainty_seconds=None):
    longitude = round(location.longitude, 2)
    longitude_offset = 4 * (longitude - 105)
    eot = noaa_eot_minutes(civil)
    tst = civil.replace(tzinfo=None) + timedelta(minutes=longitude_offset + eot)
    longitude_error = location.longitude_uncertainty_degrees
    if longitude_error is None:
        longitude_error = longitude_error_from_radius(location.latitude, location.accuracy_m)
    missing = []
    if longitude_error is None:
        missing.append("longitude_uncertainty")
    if clock_uncertainty_seconds is None:
        missing.append("clock_uncertainty")
    # The approximation has not been certified on the full supported date range.
    missing.append("eot_error_bound")
    known = abs(longitude - location.longitude) * 240
    if longitude_error is not None:
        known += longitude_error * 240
    if clock_uncertainty_seconds is not None:
        known += clock_uncertainty_seconds
    seconds = (tst.hour*3600 + tst.minute*60 + tst.second + tst.microsecond/1e6)
    distance = min(abs(seconds - edge) for edge in range(-3600, 93601, 7200))
    return tst, {
        "civil_datetime": civil.isoformat(), "utc_instant": civil.astimezone(timezone.utc).isoformat(),
        "true_solar_datetime": tst.isoformat(timespec="seconds"),
        "longitude_used": longitude, "longitude_offset_minutes": longitude_offset,
        "eot_minutes": eot, "total_offset_minutes": longitude_offset + eot,
        "eot_algorithm": "noaa-fractional-year-v1", "eot_source": "https://gml.noaa.gov/grad/solcalc/solareqns.PDF",
        "location": location.model_dump(mode="json"),
        "boundary": {"status": "UNDETERMINED" if missing else ("BOUNDARY" if distance <= known else "CLEAR_WITHIN_BOUND"),
                     "known_component_seconds": known, "delta_t_seconds": None if missing else known,
                     "missing_components": missing, "distance_to_hour_boundary_seconds": distance,
                     "crosses_boundary_with_known_components": distance <= known},
        "validation_status": "EXPERIMENTAL",
    }


@lru_cache(maxsize=90)
def jie_for_year(year):
    events = []
    for month in range(1, 13):
        angle = (285 + 30*(month - 1)) % 360
        found = astronomy.SearchSunLongitude(angle, astronomy.Time.Make(year, month, 1, 0, 0, 0), 10)
        if found is None:
            raise RuntimeError("Solar-term search failed")
        instant = found.Utc().replace(tzinfo=timezone.utc)
        events.append((instant, (month % 12), JIE_NAMES[month-1], angle))
    return tuple(events)


def solar_month(instant):
    utc = instant.astimezone(timezone.utc)
    events = jie_for_year(utc.year-1) + jie_for_year(utc.year)
    start, branch, name, angle = max((e for e in events if e[0] <= utc), key=lambda e: e[0])
    lap_xuan = jie_for_year(utc.year)[1][0]
    bazi_year = utc.year if utc >= lap_xuan else utc.year - 1
    return {"bazi_year": bazi_year, "month_branch_index": branch, "month_branch": BRANCHES[branch],
            "jie_name": name, "jie_start_utc": start.isoformat(), "solar_longitude_degrees": angle,
            "provider": "astronomy-engine-2.1.19", "validation_status": "EXPERIMENTAL"}


def pillars(civil, tst):
    solar = solar_month(civil)
    year_cycle = (solar["bazi_year"] - 4) % 60
    month_branch = solar["month_branch_index"]
    month_order = (month_branch - 2) % 12
    month_stem = ((year_cycle % 10 % 5)*2 + 2 + month_order) % 10
    effective_date = (tst + timedelta(hours=1)).date()
    day_cycle = (effective_date.toordinal() + 1721425 + 49) % 60
    hour_branch = ((tst.hour + 1) // 2) % 12
    hour_stem = ((day_cycle % 10 % 5)*2 + hour_branch) % 10
    gans = (year_cycle%10, month_stem, day_cycle%10, hour_stem)
    zhis = (year_cycle%12, month_branch, day_cycle%12, hour_branch)
    return {"gans": list(gans), "zhis": list(zhis), "solar_month": solar,
            "effective_date": effective_date.isoformat(),
            "pillars": [{"pillar": label, "stem": STEMS[g], "branch": BRANCHES[z],
                         "stem_zh": STEMS_ZH[g], "branch_zh": BRANCHES_ZH[z]}
                        for label, g, z in zip(("year", "month", "day", "hour"), gans, zhis)]}
