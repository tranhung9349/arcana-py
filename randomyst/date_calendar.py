"""Shared, immutable raw almanac; request-local interval facts.

Natal analysis is deliberately absent from this module.
"""
from datetime import datetime, timedelta, timezone
import gzip
import hashlib
import inspect
import importlib
import json
from pathlib import Path

from lunar_python import Lunar, Solar

from .time_engine import BEIJING, STEMS_ZH, BRANCHES_ZH, check_provider

ROOT = Path(__file__).resolve().parents[1]
VN = timezone(timedelta(hours=7))


class DateDataError(RuntimeError):
    pass


class DateCalendar:
    def __init__(self):
        check_provider()
        manifest = json.loads((ROOT / "data/date_calendar/manifest.json").read_text())
        path = ROOT / manifest["corpus_path"]
        packed = path.read_bytes()
        if hashlib.sha256(packed).hexdigest() != manifest["sha256"]:
            raise DateDataError("Hash corpus ngày không khớp; cần build lại dữ liệu.")
        raw = gzip.decompress(packed)
        if hashlib.sha256(raw).hexdigest() != manifest["uncompressed_sha256"]:
            raise DateDataError("Hash dữ liệu thô không khớp.")
        for row in manifest["provider_sources"]:
            path = Path(inspect.getfile(importlib.import_module(row["module"])))
            if hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
                raise DateDataError("Mã provider khác bản đã xây corpus.")
        self.data = json.loads(raw)
        if self.data["provider_version"] != "1.4.8" or len(self.data["days"]) != manifest["day_count"]:
            raise DateDataError("Metadata corpus không đúng.")
        self.manifest = manifest
        self.jie = tuple(sorted(datetime.fromisoformat(x) for x in self.data["jie_instants"]))

    def intervals(self, civil_date, allowed_hours):
        start = datetime.combine(civil_date, allowed_hours.start, VN)
        midnight = datetime.combine(civil_date, datetime.min.time(), VN)
        end = datetime.combine(civil_date, allowed_hours.end, VN) if allowed_hours.end else midnight + timedelta(days=1)
        cuts = {start, end}
        for hour in (*range(0, 24, 2), 23):
            edge = midnight + timedelta(hours=hour)
            if start < edge < end:
                cuts.add(edge)
        cuts.update(point.astimezone(VN) for point in self.jie if start < point < end)
        ordered = sorted(cuts)
        return list(zip(ordered, ordered[1:]))

    def day_intervals(self, civil_date):
        """Day validity changes only at sect1 day, civil day and exact Jie.

        Hour pillars cannot split or influence a DAY_ONLY assessment.
        """
        midnight = datetime.combine(civil_date, datetime.min.time(), VN)
        end = midnight + timedelta(days=1)
        cuts = {midnight, midnight + timedelta(hours=22), midnight + timedelta(hours=23), end}
        cuts.update(point.astimezone(VN) for point in self.jie if midnight < point < end)
        ordered = sorted(cuts)
        return list(zip(ordered, ordered[1:]))

    def at(self, instant):
        bj = instant.astimezone(BEIJING)
        row = self.data["days"][bj.date().isoformat()]
        hour_index = 0 if bj.hour == 0 else (bj.hour + 1) // 2
        hour = row["hours"][hour_index]
        lunar = Solar.fromYmdHms(bj.year, bj.month, bj.day, bj.hour, bj.minute, bj.second).getLunar()
        chart = lunar.getEightChar()
        chart.setSect(1)
        pairs = (chart.getYear(), chart.getMonth(), chart.getDay(), chart.getTime())
        return {"civil_day": row, "civil_hour": hour, "beijing_date": bj.date().isoformat(),
                "gans": tuple(STEMS_ZH.index(x[0]) for x in pairs), "zhis": tuple(BRANCHES_ZH.index(x[1]) for x in pairs),
                "pillars_zh": pairs, "civil_day_ganzhi": row["day_gan_zhi"], "bazi_day_ganzhi": pairs[2],
                "calendar_class": "HOANG_DAO" if row["tian_shen_type"] == "黄道" else "HAC_DAO"}

    def birth_boundary_warning(self, birth):
        bound = birth.clock_uncertainty_seconds
        if bound is None:
            return "UNDETERMINED"
        if bound == 0:
            return "CLEAR_WITHIN_BOUND"
        lo, hi = birth.civil_datetime - timedelta(seconds=bound), birth.civil_datetime + timedelta(seconds=bound)
        # All chart-changing boundaries: branch hours, sect1 day and exact Jie.
        seconds = birth.civil_datetime.hour * 3600 + birth.civil_datetime.minute * 60 + birth.civil_datetime.second + birth.civil_datetime.microsecond/1e6
        distance = min(abs(seconds - edge) for edge in range(0, 86401, 7200))
        bj = birth.civil_datetime.astimezone(BEIJING)
        lunar = Solar.fromYmdHms(bj.year, bj.month, bj.day, bj.hour, bj.minute, bj.second).getLunar()
        jie = lunar.getJieQiTable()
        for name in Lunar.JIE_QI_IN_USE[::2]:
            point = jie[name]
            edge = datetime(point.getYear(), point.getMonth(), point.getDay(), point.getHour(), point.getMinute(), point.getSecond(), tzinfo=BEIJING)
            if lo <= edge <= hi:
                return "UNSTABLE"
        return "UNSTABLE" if bound > 0 and distance <= bound else "CLEAR_WITHIN_BOUND"
