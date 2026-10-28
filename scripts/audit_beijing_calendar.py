"""Full-range integration/roundtrip audit, not independent astronomy proof."""
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lunar_python import Lunar
from randomyst.time_engine import resolve_maihoa


def main():
    start, end = date(1950, 1, 1), date(2030, 12, 31)
    day, tested = start, 0
    errors = []
    while day <= end:
        civil = datetime(day.year, day.month, day.day, 10, tzinfo=timezone(timedelta(hours=7)))
        kind = 'birth' if day.year <= 2026 else 'casting'
        result = resolve_maihoa(civil, kind=kind)
        lunar = result['lunar']
        signed_month = -lunar['month'] if lunar['is_leap_month'] else lunar['month']
        back = Lunar.fromYmdHms(lunar['year'], signed_month, lunar['day'], 11, 0, 0).getSolar()
        if back.toYmdHms() != day.isoformat()+' 11:00:00':
            errors.append(day.isoformat())
        values = result['maihoa_inputs']
        if not (1 <= values['Y'] <= 12 and 1 <= values['M'] <= 12 and 1 <= values['D'] <= 30 and values['H'] == 7):
            errors.append(day.isoformat()+': variable range')
        tested += 1
        day += timedelta(days=1)
    report = {'rules_version': 'mvp1-logic-2026-10-11-v4', 'provider': 'lunar-python==1.4.8',
              'civil_range': [start.isoformat(), end.isoformat()], 'days_checked': tested,
              'roundtrip_mismatches': errors, 'scope': 'Same-library roundtrip and integration; not independent astronomy validation',
              'full_range_independent_calendar_verified': False,
              'time_engine_sha256': hashlib.sha256((ROOT/'randomyst/time_engine.py').read_bytes()).hexdigest()}
    (ROOT/'docs/research/beijing_calendar_range_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
