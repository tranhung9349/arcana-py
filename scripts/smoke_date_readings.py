"""Live development smoke for date AI. Uses synthetic profiles; replays cached IDs."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:8765')
    parser.add_argument('--existing-id', help='Reuse a synthetic consultation already tested in the UI.')
    parser.add_argument('--fixtures', type=Path, default=Path('docs/research/date_readings_smoke_requests.json'))
    parser.add_argument('--output', type=Path, default=Path('docs/research/date_readings_http_smoke.json'))
    args = parser.parse_args()
    def call(path, payload=None):
        req = Request(args.base_url + path, data=json.dumps(payload).encode() if payload is not None else None,
                      headers={'Content-Type': 'application/json'}, method='POST' if payload is not None else 'GET')
        try:
            with urlopen(req, timeout=140) as response:
                return json.load(response)
        except HTTPError as exc:
            raise RuntimeError(json.load(exc).get('error', {}).get('code', 'HTTP_FAILURE')) from None
    if args.fixtures.exists():
        ids = json.loads(args.fixtures.read_text())
    else:
        ids = [args.existing_id] if args.existing_id else []
        variants = [('BETROTHAL_NACAI', '2026-10-02', 2)]
        if not ids: variants.insert(0, ('BUSINESS_OPENING', '2026-10-13', 1))
        for activity, date, count in variants:
            births = ['1994-10-08T05:00:00+07:00', '1990-06-15T09:30:00+07:00']
            payload = {'request_id': str(uuid4()), 'search': {'activity': activity,
                'subjects': [{'subject_id': f'synthetic_{i}', 'birth': {'civil_datetime': births[i]}} for i in range(count)],
                'date_range': {'start': date, 'end': date}, 'include_details': True}}
            ids.append(call('/api/v2/auspicious-dates/consultations', payload)['request_id'])
        args.fixtures.write_text(json.dumps(ids, indent=2) + '\n')
    before = call('/api/v1/history')
    report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'synthetic_data_only': True,
              'kind': 'DEVELOPMENT_SMOKE_NOT_EXPERT_OR_PREDICTIVE_VALIDATION', 'results': []}
    for key in ids:
        path = '/api/v2/auspicious-dates/consultations/' + key
        saved = call(path)
        request = {'method': 'DATE', 'consultation_id': key}
        cached_before = call('/api/v1/ai/readings/lookup', request)
        start = time.monotonic()
        result = call('/api/v1/ai/readings', request)
        assert result == call('/api/v1/ai/readings', request) == call('/api/v1/ai/readings/lookup', request)
        assert saved == call(path)
        serialized = json.dumps(result['context'])
        assert all(word not in serialized for word in ('1994-10-08', '1990-06-15', 'civil_datetime', 'synthetic_0'))
        record = {'consultation_id': key, 'activity': saved['result']['activity'], 'evaluation_mode': saved['result']['evaluation_mode'],
                  'day_grade': saved['result']['days'][0]['grade'], 'model_returned': result['model_returned'],
                  'prompt_version': result['prompt_version'], 'case_ids': result['case_ids'],
                  'validation': result['validation'], 'usage': result['usage'], 'generation_passes': result['generation_passes'],
                  'cached_before_test': cached_before is not None, 'test_seconds': round(time.monotonic() - start, 3),
                  'cache_identical': True, 'original_snapshot_unchanged': True, 'no_birth_timestamp_in_ai_context': True,
                  'reading': result['reading']}
        report['results'].append(record)
        report['draw_history_unchanged'] = call('/api/v1/history') == before
        assert report['draw_history_unchanged']
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({k: record[k] for k in ('activity','evaluation_mode','day_grade','validation','cached_before_test','test_seconds')}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
