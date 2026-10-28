"""Read-only feasibility audit for MVP 2; never ranks dates or generates numbers.

Run: .venv/bin/python -m research_tools.auspicious_date_audit
Evidence comes from the installed, pinned provider, not an independent almanac.
"""
import argparse
from collections import Counter
from datetime import date, datetime, timedelta, timezone
import hashlib
from importlib.metadata import version
import inspect
import json
from pathlib import Path
import re
from time import perf_counter

from lunar_python import EightChar, Lunar, Solar
from lunar_python.util import LunarUtil

from randomyst.bazi import analyze
from randomyst.time_engine import BEIJING, pillars

ROOT = Path(__file__).resolve().parents[1]
VN = timezone(timedelta(hours=7))
ACTIVITIES = {"MARRIAGE": "嫁娶", "BUSINESS_OPENING": "开市", "TRAVEL": "出行"}
SPECIAL_TOKENS = ("无", "诸事不宜", "馀事勿取", "余事勿取")


def lunar_at(civil):
    clock = civil.astimezone(BEIJING)
    return Solar.fromYmdHms(clock.year, clock.month, clock.day,
                            clock.hour, clock.minute, clock.second).getLunar()


def facts(civil):
    lunar = lunar_at(civil)
    chart = lunar.getEightChar()
    chart.setSect(1)
    return {"civil_datetime": civil.isoformat(), "beijing_datetime": civil.astimezone(BEIJING).isoformat(),
            "civil_day_ganzhi": lunar.getDayInGanZhi(), "bazi_day_ganzhi": chart.getDay(),
            "hour_ganzhi": chart.getTime(), "month_ganzhi_exact": chart.getMonth(),
            "lunar_date": {"year": lunar.getYear(), "month": lunar.getMonth(), "day": lunar.getDay()},
            "day_yi": lunar.getDayYi(1), "day_ji": lunar.getDayJi(1),
            "hour_yi": lunar.getTimeYi(), "hour_ji": lunar.getTimeJi(),
            "month_ganzhi_provider_day": lunar.getMonthInGanZhi(),
            "day_officer": lunar.getZhiXing(),
            "day_tian_shen": lunar.getDayTianShen(), "day_tian_shen_type": lunar.getDayTianShenType(),
            "day_xiong_sha": lunar.getDayXiongSha()}


def graph_freshness():
    snapshot = json.loads((ROOT / ".ua/fingerprints.json").read_text())
    changed, missing = [], []
    for relative, entry in snapshot["files"].items():
        path = ROOT / relative
        if not path.is_file():
            missing.append(relative)
        elif hashlib.sha256(path.read_bytes()).hexdigest() != entry["contentHash"]:
            changed.append(relative)
    return {"baseline_file_count": len(snapshot["files"]), "changed_baseline_files": changed,
            "missing_baseline_files": missing,
            "scope": "Existing graph baseline files only; newly added MVP 2 research/docs are not in the graph."}


def scan_days(start, end):
    counts = {key: Counter() for key in ACTIVITIES}
    special, terms, examples = Counter(), Counter(), {}
    n, current = 0, start
    begin = perf_counter()
    while current <= end:
        civil = datetime.combine(current, datetime.min.time(), VN) + timedelta(hours=12)
        lunar = lunar_at(civil)
        yi, ji = set(lunar.getDayYi(1)), set(lunar.getDayJi(1))
        n += 1
        terms.update(yi | ji)
        for token in SPECIAL_TOKENS:
            for kind, values in (("yi", yi), ("ji", ji)):
                if token in values:
                    special[f"{kind}:{token}"] += 1
                    examples.setdefault(f"{kind}:{token}", {"civil_date": str(current), "yi": sorted(yi), "ji": sorted(ji)})
        for key, target in ACTIVITIES.items():
            status = "BOTH" if target in yi and target in ji else "YI_ONLY" if target in yi else "JI_ONLY" if target in ji else "UNMENTIONED"
            counts[key][status] += 1
            examples.setdefault(f"{key}:{status}", {"civil_date": str(current), "target": target,
                                                      "yi": sorted(yi), "ji": sorted(ji)})
        current += timedelta(days=1)
    return {"start": str(start), "end": str(end), "day_count": n,
            "sample_clock": "12:00 UTC+7 = 13:00 Beijing; coverage probe only, not a whole-day recommendation",
            "elapsed_seconds": round(perf_counter() - begin, 6),
            "activity_exact_term_counts": {key: {status: counts[key][status] for status in ("YI_ONLY", "JI_ONLY", "BOTH", "UNMENTIONED")} for key in ACTIVITIES},
            "special_token_counts": dict(special), "observed_terms": sorted(terms), "examples": examples}


def benchmark(days):
    start = datetime(2026, 10, 12, tzinfo=VN)
    begin, checks = perf_counter(), 0
    for d in range(days):
        for hour in (*range(0, 24, 2), 23):
            facts(start + timedelta(days=d, hours=hour))
            checks += 1
    return {"days": days, "segments_checked": checks, "elapsed_seconds": round(perf_counter() - begin, 6),
            "scope": "13 base segments/day: calendar, four pillars and Yi/Ji only; excludes Jie splits, natal rules, ranking, HTTP/UI, caching."}


def static_filter_evidence():
    path = ROOT / "data/reference/tinix-bazi/shensha.js"
    source = path.read_text()
    tables = {}
    branches = tuple("子丑寅卯辰巳午未申酉戌亥")
    for name in ("Sát Chủ", "Thọ Tử", "Nguyệt Phá"):
        section = re.search(r"        '" + re.escape(name) + r"': \{(.*?)\n        \}", source, re.S)
        if section is None:
            raise ValueError(f"Pinned source table not found: {name}")
        rows = dict(re.findall(r"'([^']+)': '([^']+)'", section.group(1)))
        assert set(rows) == set(branches) and len(rows) == 12
        tables[name] = rows
    hoang = sorted(name for name, kind in LunarUtil.TIAN_SHEN_TYPE.items() if kind == "黄道")
    hac = sorted(name for name, kind in LunarUtil.TIAN_SHEN_TYPE.items() if kind == "黑道")
    assert len(hoang) == len(hac) == 6
    assert len(LunarUtil.ZHI_XING[1:]) == 12
    return {"six_hoang_dao": hoang, "six_hac_dao": hac,
            "twelve_day_officers_separate_system": list(LunarUtil.ZHI_XING[1:]),
            "tian_shen_month_branch_offsets": LunarUtil.ZHI_TIAN_SHEN_OFFSET,
            "calculation": "TIAN_SHEN[(civil_day_zhi_index + month_zhi_offset) % 12 + 1]",
            "tinix_month_tables": tables, "tinix_source_path": str(path.relative_to(ROOT)),
            "tinix_source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "tinix_original_scope": "calculateShenSha(ctx): natal month branch against natal pillars",
            "candidate_date_extension": "PROPOSED_NOT_VALIDATED",
            "tam_nuong": "No rule imported or enabled; a full source table and calendar basis still required"}


def audit():
    installed = version("lunar-python")
    if installed != "1.4.8":
        raise RuntimeError(f"Expected pinned lunar-python 1.4.8, got {installed}")
    methods = ("getDayYi", "getDayJi", "getDayTianShen", "getDayChong", "getZhiXing", "getDayJiShen", "getDayXiongSha", "getTimeYi", "getTimeJi", "getTimeTianShen", "getNextJie", "getTimes")
    sources = []
    for obj in (Lunar, EightChar, LunarUtil):
        path = Path(inspect.getfile(obj))
        sources.append({"file": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    boundary_times = ["2026-10-12T21:59:59+07:00", "2026-10-12T22:00:00+07:00",
                      "2026-10-12T22:59:59+07:00", "2026-10-12T23:00:00+07:00",
                      "2030-12-31T23:59:59+07:00"]
    anchor = lunar_at(datetime(2026, 10, 8, 12, tzinfo=VN))
    jie = anchor.getJieQiTable()["寒露"]
    jie_clock = datetime(jie.getYear(), jie.getMonth(), jie.getDay(), jie.getHour(), jie.getMinute(), jie.getSecond(), tzinfo=BEIJING).astimezone(VN)
    boundaries = [facts(datetime.fromisoformat(value)) for value in boundary_times]
    jie_rows = [facts(jie_clock + timedelta(seconds=delta)) for delta in (-1, 0, 1)]
    assert boundaries[0]["bazi_day_ganzhi"] != boundaries[1]["bazi_day_ganzhi"]
    assert boundaries[0]["civil_day_ganzhi"] == boundaries[1]["civil_day_ganzhi"]
    assert boundaries[2]["civil_day_ganzhi"] != boundaries[3]["civil_day_ganzhi"]
    assert jie_rows[0]["month_ganzhi_exact"] != jie_rows[1]["month_ganzhi_exact"]
    profiles = []
    for text in ("1994-10-08T05:00:00+07:00", "1990-06-15T09:30:00+07:00"):
        natal = pillars(datetime.fromisoformat(text))
        result = analyze(natal["gans"], natal["zhis"])
        profiles.append({"synthetic_birth_input": text, "pillars": natal["pillars"],
                         **{key: result[key] for key in ("primary_dung_than", "hy_than", "ky_than", "reason_code")}})
    probe = scan_days(date(2024, 1, 1), date(2030, 12, 31))
    for row in probe["activity_exact_term_counts"].values():
        assert sum(row.values()) == probe["day_count"]
        assert row["YI_ONLY"] > 0 and row["JI_ONLY"] > 0
    anchor_facts = facts(datetime(2026, 10, 12, 12, tzinfo=VN))
    assert "嫁娶" in anchor_facts["day_yi"] and "开市" in anchor_facts["day_ji"]
    static_evidence = static_filter_evidence()
    return {"audit_version": "mvp2-auspicious-date-feasibility-v2",
            "created_at": datetime.now(timezone.utc).astimezone(VN).isoformat(),
            "status": "FEASIBILITY_ONLY", "runtime_changed": False, "database_read_or_written": False,
            "scope": "Pinned software capabilities, sampled coverage, integration boundaries and local timings; no traditional-method validation or outcome evidence.",
            "provider": {"name": "lunar-python", "version": installed, "source_files": sources},
            "graph_baseline": graph_freshness(), "available_methods": {name: hasattr(Lunar, name) for name in methods},
            "provider_method_policy": {"day_yi_ji_sect1": "non-exact provider month Ganzhi; civil day Ganzhi",
                                       "non_exact_month_basis": "Jie month changes on the Beijing civil DATE of Jie, not lunar-month number and not exact Jie instant",
                                       "day_yi_ji_sect2": "exact Jie month Ganzhi; still civil day Ganzhi",
                                       "bazi_sect1": "exact Jie year/month; day changes at 23:00 Beijing",
                                       "hour_yi_ji": "exact day Ganzhi and hour Ganzhi",
                                       "getTimes_count": len(anchor.getTimes()),
                                       "getTimes_warning": "Beijing civil-day list, includes early and late Zi; cannot copy directly into a UTC+7 date."},
            "activity_term_proposals": ACTIVITIES, "coverage": probe,
            "boundary_fixtures": boundaries, "jie_boundary_fixtures": jie_rows,
            "synthetic_profiles": profiles, "single_instant_activity_contrast": anchor_facts,
            "user_three_filter_evidence": static_evidence,
            "user_reference_date_provider_facts": facts(datetime(2026, 8, 10, 12, tzinfo=VN)),
            "benchmarks": [benchmark(31), benchmark(93)],
            "checks": {"bazi_day_change_22_vn": True, "civil_day_change_23_vn": True,
                       "exact_jie_month_change": True, "coverage_counts_reconcile": True,
                       "three_activity_terms_have_yi_and_ji_coverage": True},
            "remaining_gaps": ["Vietnamese activity mapping and special-token semantics need review",
                               "Personalized date rules and ranking remain product proposals",
                               "No independent almanac or expert validation",
                               "Full pipeline/API performance not measured"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/research/mvp2_auspicious_date_feasibility.json")
    args = parser.parse_args()
    report = audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "status": report["status"],
                      "days": report["coverage"]["day_count"], "activities": report["coverage"]["activity_exact_term_counts"],
                      "special_tokens": report["coverage"]["special_token_counts"], "checks": report["checks"],
                      "benchmarks": report["benchmarks"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
