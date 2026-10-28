"""Offline structural and published-new-moon checks for the prototype.

NASA phase tables by Fred Espenak, GSFC Planetary Systems Laboratory:
https://eclipse.gsfc.nasa.gov/phase/phases1901.html
https://eclipse.gsfc.nasa.gov/phase/phases2001.html
Source tables grant reproduction with acknowledgement. These are UT tables
with minute output, not second-accurate UTC ground truth or Vietnamese month names.
"""

import argparse
from dataclasses import asdict
from datetime import date, datetime, timedelta
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re

from .vietnamese import (
    ALGORITHM_ID, LOOKUP_END, LOOKUP_START, VietnameseCalendar,
    _EPOCH, _SYNODIC_MONTH, _jdn, _new_moon_day, _new_moon_jd,
)


class _PreText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inside = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == "pre":
            self.inside = True

    def handle_endtag(self, tag):
        if tag == "pre":
            self.inside = False
            self.parts.append("\n")

    def handle_data(self, value):
        if self.inside:
            self.parts.append(value)


def read_moons(path: Path) -> list[datetime]:
    parser = _PreText()
    parser.feed(path.read_text())
    months = {name: i for i, name in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}
    result = []
    current_year = None
    for line in "".join(parser.parts).splitlines():
        year = re.match(r"\s*(\d{4})\b", line[:7])
        if year:
            current_year = int(year[1])
        # Only the fixed-width New Moon column; never parse the other phases.
        moon = re.search(r"([A-Z][a-z]{2})\s+(\d{1,2})\s+(\d{2}):(\d{2})", line[7:25])
        if moon:
            if current_year is None:
                raise ValueError("New-moon row appears before its year header.")
            result.append(datetime(current_year, months[moon[1]], int(moon[2]), int(moon[3]), int(moon[4])))
    if len(result) < 1200 or result != sorted(set(result)):
        raise ValueError("Unexpected century-table structure, duplicate or unsorted rows.")
    counts = {}
    for instant in result:
        counts[instant.year] = counts.get(instant.year, 0) + 1
    if len(counts) != 100 or any(count not in (12, 13) for count in counts.values()):
        raise ValueError("Expected 100 years with 12 or 13 new moons each.")
    return result


def structural_check(calendar: VietnameseCalendar) -> dict:
    errors = []
    current = LOOKUP_START
    previous = None
    month_starts = 0
    checked = 0
    while current <= LOOKUP_END:
        lunar = calendar.to_lunar(current)
        if calendar.to_solar(lunar) != current:
            errors.append({"date": current.isoformat(), "rule": "round_trip"})
        if lunar.day == 1:
            month_starts += 1
        if previous is not None:
            same_month = (lunar.year, lunar.month, lunar.is_leap_month) == (previous.year, previous.month, previous.is_leap_month)
            if same_month:
                valid = lunar.day == previous.day + 1
            else:
                repeats_as_leap = (not previous.is_leap_month and lunar.is_leap_month and lunar.month == previous.month and lunar.year == previous.year)
                advances = (not lunar.is_leap_month and lunar.month == previous.month % 12 + 1 and lunar.year == previous.year + int(previous.month == 12))
                valid = lunar.day == 1 and previous.day in (29, 30) and (repeats_as_leap or advances)
            if not valid:
                errors.append({"date": current.isoformat(), "rule": "lunar_continuity"})
        previous = lunar
        checked += 1
        current += timedelta(days=1)
    return {"days_checked": checked, "month_starts": month_starts, "errors": errors, "meaning": "Internal invariants only; not independent verification of every date's month/year label."}


def audit(reference_paths: list[Path]) -> dict:
    calendar = VietnameseCalendar()
    report = {"algorithm_id": ALGORITHM_ID, "lookup_range": [LOOKUP_START.isoformat(), LOOKUP_END.isoformat()], "structural": structural_check(calendar)}
    references = []
    for path in reference_paths:
        references.extend(read_moons(path))
    if references != sorted(set(references)):
        raise ValueError("Reference files overlap or are out of order.")
    errors, midnight_reviews, utc8_differences = [], [], []
    max_time_difference_minutes = 0
    checked = 0
    matches = 0
    for reference_ut in references:
        local = reference_ut + timedelta(hours=7)
        if not LOOKUP_START <= local.date() <= LOOKUP_END:
            continue
        checked += 1
        k = round((_jdn(local.date()) - _EPOCH) / _SYNODIC_MONTH)
        predicted_date = date.fromordinal(_new_moon_day(k, 7) - 1721425)
        predicted_ut = datetime(2000, 1, 1) + timedelta(days=_new_moon_jd(k) - 2451544.5)
        difference_minutes = abs((predicted_ut - reference_ut).total_seconds()) / 60
        max_time_difference_minutes = max(max_time_difference_minutes, difference_minutes)
        lunar = calendar.to_lunar(local.date())
        row = {"reference_UT": reference_ut.isoformat(), "reference_UTC7_date": local.date().isoformat(), "adapter_start_date": predicted_date.isoformat(), "lunar_on_reference_date": asdict(lunar), "approximation_difference_minutes": round(difference_minutes, 4)}
        if local.date() != predicted_date or lunar.day != 1:
            errors.append(row)
        else:
            matches += 1
        seconds = local.hour * 3600 + local.minute * 60
        # A review priority, never an automatic runtime time shift or error bound.
        if min(seconds, 86400 - seconds) <= 300:
            midnight_reviews.append(row)
        other_date = (reference_ut + timedelta(hours=8)).date()
        if local.date() != other_date:
            utc8_differences.append({"reference_UT": reference_ut.isoformat(), "UTC7_date": local.date().isoformat(), "UTC8_date": other_date.isoformat()})
    report["published_new_moons"] = {
        "reference_author": "Fred Espenak, GSFC Planetary Systems Laboratory",
        "source_urls": ["https://eclipse.gsfc.nasa.gov/phase/phases1901.html", "https://eclipse.gsfc.nasa.gov/phase/phases2001.html"],
        "downloaded_html_sha256": [hashlib.sha256(path.read_bytes()).hexdigest() for path in reference_paths],
        "reference_time_scale": "UT, not implicitly second-accurate UTC",
        "reference_output_resolution": "minute",
        "reference_absolute_error_bound_seconds": None,
        "events_checked": checked,
        "matching_start_dates": matches,
        "mismatches": errors,
        "max_observed_approximation_difference_minutes": round(max_time_difference_minutes, 4),
        "near_midnight_manual_review": midnight_reviews,
        "UTC7_UTC8_differing_dates": utc8_differences,
        "meaning": "External published event comparison, not verification of all lunar month/year/leap labels. Both formula families use Meeus; not independent physical measurements.",
    }
    report["production_ready"] = False
    report["remaining_validation"] = ["Independent VN lunar month/year/leap-month labels across the full lookup range", "Precise solar-term provider and Lap Xuan boundaries", "Quantified astronomy/time-scale uncertainty, especially near midnight"]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nasa-1901", type=Path, required=True)
    parser.add_argument("--nasa-2001", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit([args.nasa_1901, args.nasa_2001])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"days_checked": report["structural"]["days_checked"], "structural_errors": len(report["structural"]["errors"]), "new_moons_checked": report["published_new_moons"]["events_checked"], "new_moon_mismatches": len(report["published_new_moons"]["mismatches"]), "production_ready": False}))
    if report["structural"]["errors"] or report["published_new_moons"]["mismatches"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
