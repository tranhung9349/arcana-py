"""Build pinned raw day/hour Yi/Ji corpus and the MVP 2 rule contract.

No draw database or number generation is touched. Node is unnecessary.
"""
import gzip
import hashlib
from importlib.metadata import version
import inspect
import json
from pathlib import Path
import re
import sys
from datetime import date, timedelta

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lunar_python import Lunar, Solar, EightChar
from lunar_python.util import LunarUtil
from randomyst.date_models import DateRules, DateSearchRequest, DateSearchResponse
from randomyst.date_activities import ACTIVITIES, GROUPS, REGISTRY_VERSION
from randomyst.time_engine import BRANCHES, BRANCHES_ZH


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert version("lunar-python") == "1.4.8"
    target = ROOT / "data/date_calendar"
    target.mkdir(parents=True, exist_ok=True)
    sources = []
    for obj in (Lunar, EightChar, LunarUtil):
        path = Path(inspect.getfile(obj))
        sources.append({"module": obj.__module__, "sha256": digest(path)})
    days, jie = {}, set()
    current, end = date(2024, 1, 1), date(2031, 1, 1)
    while current <= end:
        lunar = Solar.fromYmdHms(current.year, current.month, current.day, 12, 0, 0).getLunar()
        hours = []
        for hour in (0, *range(1, 24, 2)):
            clock = Solar.fromYmdHms(current.year, current.month, current.day, hour, 0, 0).getLunar()
            hours.append({"anchor_hour": hour, "gan_zhi": clock.getTimeInGanZhi(),
                          "yi": clock.getTimeYi(), "ji": clock.getTimeJi()})
        days[str(current)] = {"lunar": {"year": lunar.getYear(), "month": lunar.getMonth(), "day": lunar.getDay()},
            "day_gan_zhi": lunar.getDayInGanZhi(), "month_gan_zhi": lunar.getMonthInGanZhi(),
            "year_gan_zhi": lunar.getYearInGanZhiByLiChun(), "day_officer": lunar.getZhiXing(),
            "tian_shen": lunar.getDayTianShen(), "tian_shen_type": lunar.getDayTianShenType(),
            "yi": lunar.getDayYi(1), "ji": lunar.getDayJi(1), "xiong_sha": lunar.getDayXiongSha(), "hours": hours}
        if current.month == 1 and current.day == 1:
            for name in Lunar.JIE_QI_IN_USE[::2]:
                point = lunar.getJieQiTable()[name]
                jie.add(point.toYmdHms().replace(" ", "T") + "+08:00")
        current += timedelta(days=1)
    raw = {"schema_version": "date-almanac-raw-v1", "provider": "lunar-python", "provider_version": "1.4.8",
           "day_basis": "BEIJING_CIVIL_DATE", "month_basis": "JIE_CIVIL_DATE_NON_EXACT", "yi_ji_sect": 1,
           "start": "2024-01-01", "end": "2031-01-01", "internal_padding": "2031-01-01 supports late UTC+7 inputs on 2030-12-31",
           "jie_instants": sorted(jie), "days": days}
    canonical = json.dumps(raw, ensure_ascii=False, separators=(",", ":")).encode()
    path = target / "almanac_2024_2030.json.gz"
    path.write_bytes(gzip.compress(canonical, mtime=0))
    source = ROOT / "data/reference/tinix-bazi/shensha.js"
    manifest = json.loads((ROOT / "data/reference/manifest.json").read_text())
    expected = next(x["sha256"] for x in manifest["files"] if x["path"] == "tinix-bazi/shensha.js")
    assert digest(source) == expected
    tables = {}
    for key, name in (("sat_chu", "Sát Chủ"), ("tho_tu", "Thọ Tử"), ("nguyet_pha", "Nguyệt Phá")):
        section = re.search(r"        '" + re.escape(name) + r"': \{(.*?)\n        \}", source.read_text(), re.S)
        rows = dict(re.findall(r"'([^']+)': '([^']+)'", section.group(1)))
        assert set(rows) == set(BRANCHES_ZH)
        tables[key] = [BRANCHES.index(rows[branch]) for branch in BRANCHES_ZH]
    corpus_source = {"source_id": "6TAIL_CORPUS", "path": str(path.relative_to(ROOT)), "sha256": digest(path),
                     "url": "https://github.com/6tail/lunar-python", "basis": "Pinned 1.4.8 raw Yi/Ji; month on Jie civil date, day at midnight Beijing"}
    tinix_source = {"source_id": "TINIX_MONTH_TABLES", "path": str(source.relative_to(ROOT)), "sha256": expected,
                   "url": "https://github.com/vhphuoc1102/tinix-bazi/blob/80ff4463d0397c1b11db76f38d880255f55558bc/backendjs/src/bazi/shensha.js",
                   "basis": "Pinned natal tables; product explicitly applies candidate exact Jie month / sect1 day, not a validated ancient date-selection method"}
    activity_keys = ["MARRIAGE", "BUSINESS_OPENING", "TRAVEL"]
    def rule(key, fact, equals, effect, points, message, source_id="6TAIL_CORPUS", enabled=True, group=None):
        return {"rule_id": key, "enabled": enabled, "when": {"fact": fact, "equals": equals},
                "activity_scope": activity_keys, "effect": effect, "points": points, "dedupe_group": group or key,
                "message": message, "source_id": source_id,
                "review_status": "PRODUCT_POLICY" if enabled else "NOT_ENABLED"}
    rules = {"schema_version": "date-rules-v1", "rules_version": "mvp2-dates-2026-10-12-v1",
        "provider_version": "1.4.8", "calendar_policy": "BEIJING_CIVIL_UTC8",
        "major_taboo_basis": "CANDIDATE_EXACT_JIE_MONTH_AND_SECT1_DAY", "disabled_rules": ["TAM_NUONG"],
        "sources": [corpus_source, tinix_source, {"source_id": "PRODUCT_PERSONAL_POLICY", "path": "randomyst/bazi.py", "sha256": digest(ROOT / "randomyst/bazi.py"),
                    "url": "https://github.com/vhphuoc1102/tinix-bazi/blob/80ff4463d0397c1b11db76f38d880255f55558bc/backendjs/src/bazi/phan_tich/ngu_hanh.js",
                    "basis": "Numeric natal analysis port; date element penalties and clash policy are product rules v1"}],
        "activities": [{"activity": k, "name": n, "provider_token": t, "subject_count": c} for k,n,t,c in
                       [("MARRIAGE","Cưới hỏi","嫁娶",2),("BUSINESS_OPENING","Khai trương","开市",1),("TRAVEL","Xuất hành","出行",1)]],
        "month_tables": tables,
        "scoring": {"base": 100, "good_threshold": 75, "normal_threshold": 45,
                    "day_not_listed_penalty": 15, "hour_not_listed_penalty": 5,
                    "personal_element_penalties": {"PRIMARY": 0, "HY": 2, "NEUTRAL": 5, "KY": 10}, "personal_clash_blocks": True},
        "rules": [rule("HAC_DAO","calendar_class","HAC_DAO","PENALTY",15,"Ngày thuộc Hắc Đạo theo provider."),
                  *[rule("DAY_"+kind,"day_relation",kind,"PENALTY",p,msg) for kind,p,msg in
                    [("SAME",5,"Can và Chi ngày cùng hành."),("BRANCH_GENERATES_STEM",10,"Chi ngày sinh Can ngày."),
                     ("STEM_CONTROLS_BRANCH",15,"Can ngày khắc Chi ngày."),("BRANCH_CONTROLS_STEM",20,"Chi ngày khắc Can ngày.")]],
                  rule("NO_AMBIENT_SUPPORT","ambient_support","NONE","PENALTY",5,"Chưa gặp hợp chi ngày với tháng/năm."),
                  rule("YEAR_CLASH","year_clash",True,"PENALTY",15,"Chi ngày xung chi năm ứng viên."),
                  rule("SAT_CHU","sat_chu",True,"BLOCK",None,"Trúng Sát Chủ theo bảng và quy ước của sản phẩm.","TINIX_MONTH_TABLES"),
                  rule("THO_TU","tho_tu",True,"BLOCK",None,"Trúng Thọ Tử theo bảng và quy ước của sản phẩm.","TINIX_MONTH_TABLES"),
                  rule("NGUYET_PHA","nguyet_pha",True,"BLOCK",None,"Chi ngày xung chi tháng ứng viên (Nguyệt Phá).","TINIX_MONTH_TABLES",group="MONTH_CLASH"),
                  rule("TAM_NUONG","tam_nuong",True,"WARN",None,"Tam Nương chưa nằm trong phạm vi đánh giá.","",False)]}
    rules.update(schema_version="date-rules-v2", rules_version="mvp2-dates-2026-10-25-v2",
                 activity_registry_version=REGISTRY_VERSION, groups=GROUPS, activities=ACTIVITIES,
                 day_scoring={**rules["scoring"], "good_threshold": 80, "normal_threshold": 50,
                              "hour_not_listed_penalty": 0})
    rules["sources"].append({"source_id": "PRODUCT_ACTIVITY_POLICY", "path": "randomyst/date_activities.py",
                             "sha256": digest(ROOT / "randomyst/date_activities.py"),
                             "url": "/api/v2/auspicious-dates/rules",
                             "basis": "Versioned product activity scope, roles and capability; not expert-certified traditional rules"})
    new = [a["activity"] for a in ACTIVITIES if a["enabled"] and a["rule_profile"] != "LEGACY_V1"]
    constructive = [a["activity"] for a in ACTIVITIES if a["enabled"] and a["rule_profile"] == "CONSTRUCTIVE_V2"]
    ritual = [a["activity"] for a in ACTIVITIES if a["enabled"] and a["rule_profile"] == "RITUAL_V2"]
    for row in rules["rules"]:
        if row["rule_id"] not in ("SAT_CHU", "THO_TU", "NGUYET_PHA"):
            row["activity_scope"] = [*activity_keys, *new]
    # New scopes deliberately do not inherit the natal-table hard exclusions.
    # Month clash is a separate constructive policy; ancestor/incense rites warn.
    for key, fact, message in (("SAT_CHU", "sat_chu", "Sát Chủ"), ("THO_TU", "tho_tu", "Thọ Tử")):
        row = rule(key+"_V2_NOTE", fact, True, "WARN", None,
                   message+" theo bảng tham khảo; dùng cảnh báo cho việc này.", "TINIX_MONTH_TABLES", group=key)
        row["activity_scope"] = new
        rules["rules"].append(row)
    for scope, effect, suffix in ((constructive, "BLOCK", "V2"), (ritual, "WARN", "V2_NOTE")):
        row = rule("NGUYET_PHA_"+suffix, "nguyet_pha", True, effect, None,
                   "Chi ngày xung chi tháng ứng viên; "+("loại theo policy việc kiến tạo." if effect == "BLOCK" else "cảnh báo tham khảo cho nghi lễ."),
                   "PRODUCT_ACTIVITY_POLICY", group="MONTH_CLASH")
        row["activity_scope"] = scope
        rules["rules"].append(row)
    validated = DateRules.model_validate(rules)
    (ROOT / "config/mvp2_date_rules.json").write_text(json.dumps(validated.model_dump(), ensure_ascii=False, indent=2)+"\n")
    (ROOT / "schemas/mvp2_date_rules.schema.json").write_text(json.dumps(DateRules.model_json_schema(), ensure_ascii=False, indent=2)+"\n")
    for name, model in (("date_search_request", DateSearchRequest), ("date_search_response", DateSearchResponse)):
        (ROOT / f"schemas/{name}.schema.json").write_text(json.dumps(model.model_json_schema(), ensure_ascii=False, indent=2)+"\n")
    metadata = {"schema_version": "date-corpus-manifest-v1", "provider": "lunar-python", "provider_version": "1.4.8",
                "corpus_path": str(path.relative_to(ROOT)), "sha256": digest(path), "uncompressed_sha256": hashlib.sha256(canonical).hexdigest(),
                "provider_sources": sources, "day_count": len(days), "hour_count": sum(len(d["hours"]) for d in days.values()),
                "jie_count": len(jie), "public_range_utc7": ["2024-01-01", "2030-12-31"], "raw_tokens": ["嫁娶", "开市", "出行"],
                "coverage_note": "Full raw day/hour arrays, not a noon-only sample or recommendations"}
    (target / "manifest.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
