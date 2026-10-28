"""Read-only audit of activity tokens in the pinned MVP2 corpus; no new rules.

Counts Beijing civil dates/anchors, not personalized Vietnamese GOOD windows.
Excludes the 2031 padding day. Run from any directory with the project venv.
"""
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from randomyst.date_calendar import DateCalendar
from randomyst.date_rules import activity_status

# These are proposed product mappings. Different ritual steps remain separate.
CANDIDATES = [
    ('MARRIAGE', 'Cưới hỏi', 'LIVE', '嫁娶', '嫁娶', 2),
    ('BUSINESS_OPENING', 'Khai trương', 'LIVE', '开市', '开市', 1),
    ('TRAVEL', 'Xuất hành', 'LIVE', '出行', '出行', 1),
    ('HOME_ENTRY', 'Nhập trạch', 'NEXT', '入宅', '入宅', 1),
    ('RELOCATION', 'Chuyển chỗ ở', 'NEXT', '移徙', '移徙', 1),
    ('BED_SETUP', 'An sàng — đặt giường', 'NEXT', '安床', '安床', 1),
    ('RENOVATION', 'Sửa chữa, tu tạo', 'NEXT', '修造', '修造', 1),
    ('TRADE', 'Giao dịch', 'NEXT', '交易', '交易', 1),
    ('BETROTHAL_NACAI', 'Nạp thái — lễ dạm hỏi', 'REVIEW_MAPPING', '纳采', '订婚', 2),
    ('BETROTHAL_COVENANT', 'Đính ước', 'REVIEW_MAPPING', '订盟', '订婚', 2),
    ('CONTRACT_RITE', 'Lập văn khế', 'DAY_ONLY_REVIEW', '立券', '立券', 1),
    ('LAND_BREAKING', 'Động thổ', 'DAY_ONLY_REVIEW', '动土', '动土', 1),
    ('ROOF_BEAM', 'Thượng lương — gác đòn nóc', 'DAY_ONLY_REVIEW', '上梁', '上梁', 1),
    ('DEMOLITION', 'Tháo dỡ', 'RULE_SCOPE_REVIEW', '拆卸', '拆卸', 1),
    ('ANCESTOR_RITE', 'Tế lễ', 'LATER', '祭祀', '祭祀', 1),
    ('PRAYER', 'Cầu phúc', 'LATER', '祈福', '祈福', 1),
    ('START_JOB', 'Nhậm chức', 'LATER', '赴任', '赴任', 1),
    ('MEET_FAMILY', 'Hội họp thân hữu', 'DAY_ONLY_REVIEW', '会亲友', '会亲友', 1),
    ('HAIRCUT', 'Cắt tóc', 'DAY_ONLY_REVIEW', '理发', '理发', 1),
    ('MEDICAL_VISIT', 'Cầu y — đi khám', 'DEFER', '求医', '求医', 1),
    ('TREATMENT', 'Trị bệnh', 'DEFER', '治病', '治病', 1),
    ('BURIAL', 'An táng', 'SEPARATE_DOMAIN', '安葬', '安葬', None),
    ('GRAVE_BREAKING', 'Phá thổ phần mộ', 'SEPARATE_DOMAIN', '破土', '破土', None),
]


def summarize(rows, token):
    counts = Counter()
    conflicts = []
    for key, row in rows:
        counts['yi_mentions'] += token in row['yi']
        counts['ji_mentions'] += token in row['ji']
        state = activity_status(row['yi'], row['ji'], token)
        counts[state] += 1
        if state == 'UNRESOLVED':
            conflicts.append(key)
    return {'records': len(rows), 'yi_mentions': counts['yi_mentions'], 'ji_mentions': counts['ji_mentions'],
            'statuses': {s: counts[s] for s in ('SUPPORTED', 'AVOID', 'NOT_LISTED', 'UNRESOLVED')},
            'conflicts': conflicts}


def audit():
    calendar = DateCalendar()  # Validates corpus and pinned provider hashes.
    days = sorted((key, row) for key, row in calendar.data['days'].items() if '2024-01-01' <= key <= '2030-12-31')
    hours = [(f"{key}T{row['anchor_hour']:02}:00+08:00", row) for key, day in days for row in day['hours']]
    candidates = []
    for activity, name, phase, day_token, hour_token, subjects in CANDIDATES:
        candidates.append({'candidate_id': activity, 'name_vi': name, 'phase': phase, 'runtime_enabled': phase == 'LIVE',
                           'day_token': day_token, 'hour_token': hour_token,
                           'token_mapping_reviewed': phase == 'LIVE', 'proposed_subject_count': subjects,
                           'day': summarize(days, day_token), 'hour': summarize(hours, hour_token),
                           'annual': {str(year): {'day': summarize([r for r in days if r[0].startswith(str(year))], day_token),
                                                 'hour': summarize([r for r in hours if r[0].startswith(str(year))], hour_token)}
                                      for year in range(2024, 2031)}})
    return {'schema_version': 'mvp2-activity-research-v1', 'research_date_utc7': '2026-10-14',
            'provider': 'lunar-python==1.4.8', 'corpus_gzip_sha256': calendar.manifest['sha256'],
            'basis': 'Beijing civil days 2024-01-01..2030-12-31 inclusive; 13 anchors/day including both Zi anchors; 2031 padding excluded.',
            'day_count': len(days), 'hour_anchor_count': len(hours),
            'meaning': 'Token presence and existing activity_status only. Not a GOOD score, traditional validation, demand estimate, or runtime activation.',
            'sources': ['https://github.com/6tail/lunar-python', 'https://6tail.cn/calendar/lunar.yiji.html',
                        'https://6tail.cn/calendar/lunar.timeyiji.html'],
            'candidates': candidates}


if __name__ == '__main__':
    result = audit()
    output = ROOT / 'docs/research/mvp2_activity_token_coverage.json'
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(f"Audited {result['day_count']} days / {result['hour_anchor_count']} anchors / {len(result['candidates'])} candidates → {output}")
