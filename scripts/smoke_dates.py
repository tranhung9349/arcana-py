"""Fresh-process localhost HTTP checks, using synthetic birth profiles only.

Starts and stops its own server and temporary database. Does not call draw.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
import tempfile
import time

import httpx
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from randomyst.date_models import DateSearchRequest, DateSearchResponse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT/'docs/research/mvp2_runtime_validation.json')
    parser.add_argument('--cold-marriage-first', action='store_true', help='Measure 93 days as the first search on a fresh server.')
    args = parser.parse_args()
    with socket.socket() as reservation:
        reservation.bind(('127.0.0.1', 0))
        port = reservation.getsockname()[1]
    request_validator = Draft202012Validator(json.loads((ROOT/'schemas/date_search_request.schema.json').read_text()))
    response_validator = Draft202012Validator(json.loads((ROOT/'schemas/date_search_response.schema.json').read_text()))
    single = json.loads((ROOT/'examples/date_search_request.json').read_text())
    couple = json.loads((ROOT/'examples/marriage_date_search_request.json').read_text())
    for payload in (single, couple):
        request_validator.validate(payload)
        DateSearchRequest.model_validate(payload)
    measurements = []
    with tempfile.TemporaryDirectory(prefix='randomyst-dates-') as tmp:
        env = {**os.environ, 'RANDOMYST_DATABASE':str(Path(tmp)/'draws.sqlite3')}
        with (Path(tmp)/'server.log').open('w+') as log:
            started = time.perf_counter()
            server = subprocess.Popen([sys.executable,'-m','uvicorn','randomyst.api:app','--host','127.0.0.1','--port',str(port)], cwd=ROOT, env=env, stdout=log, stderr=log)
            try:
                with httpx.Client(base_url=f'http://127.0.0.1:{port}',timeout=30,trust_env=False) as client:
                    for _ in range(100):
                        try:
                            health = client.get('/api/v1/health')
                            health.raise_for_status()
                            break
                        except httpx.HTTPError:
                            if server.poll() is not None:
                                log.seek(0)
                                raise RuntimeError(log.read())
                            time.sleep(0.1)
                    else:
                        raise RuntimeError('Preview server did not become ready.')
                    startup = time.perf_counter()-started
                    history = client.get('/api/v1/history').json()
                    previous = {}
                    full = deepcopy(couple)
                    full['include_details'] = True
                    cases = [('31_days_1_subject_cold_search',single,2),('31_days_1_subject_warm',single,2),
                             ('93_days_2_subjects_first',couple,5),('93_days_2_subjects_warm',couple,5),
                             ('93_days_2_subjects_full_details',full,5)]
                    if args.cold_marriage_first:
                        cases = [('93_days_2_subjects_cold_search',couple,5),('93_days_2_subjects_warm',couple,5)]
                    for name,payload,sla in cases:
                        begin = time.perf_counter()
                        response = client.post('/api/v2/auspicious-dates/search',json=payload)
                        elapsed = time.perf_counter()-begin
                        response.raise_for_status()
                        data = response.json()
                        DateSearchResponse.model_validate(data)
                        response_validator.validate(data)
                        assert data['natal_analysis_count']==len(payload['subjects'])
                        assert data['personal_comparisons']==data['evaluated_windows']*len(payload['subjects'])
                        assert data['disabled_rules']==['TAM_NUONG']
                        assert all(d['assessment_state']=='COMPLETE' for d in data['days'])
                        assert elapsed < sla, f'{name}: {elapsed:.3f}s exceeds {sla}s'
                        key = json.dumps(payload,sort_keys=True)
                        if key in previous:
                            assert previous[key]==data, 'Repeated request changed output'
                        previous[key] = data
                        measurements.append({'case':name,'http_seconds':round(elapsed,4),'target_seconds':sla,
                                             'response_bytes':len(response.content),'days':len(data['days']),
                                             'natal_analysis_count':data['natal_analysis_count'],
                                             'evaluated_windows':data['evaluated_windows'],'personal_comparisons':data['personal_comparisons'],
                                             'grade_counts':{g:sum(d['grade']==g for d in data['days']) for g in ('GOOD','NORMAL','BAD')}})
                    detail = deepcopy(single)
                    detail['date_range']={'start':'2026-10-13','end':'2026-10-13'}
                    detail['include_details']=True
                    result = client.post('/api/v2/auspicious-dates/search',json=detail).json()
                    DateSearchResponse.model_validate(result)
                    (ROOT/'examples/date_search_response.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
                    invalid = deepcopy(single)
                    invalid['date_range']['end']='2027-01-13'
                    assert client.post('/api/v2/auspicious-dates/search',json=invalid).status_code==422
                    assert client.get('/api/v1/history').json()==history
                    rules = client.get('/api/v2/auspicious-dates/rules').json()
                    assert rules['disabled_rules']==['TAM_NUONG']
            finally:
                server.terminate()
                server.wait(timeout=10)
    manifest = json.loads((ROOT/'data/date_calendar/manifest.json').read_text())
    report = {'checked_at_utc':datetime.now(timezone.utc).isoformat(),'python':platform.python_version(),
              'platform':platform.system()+' '+platform.machine(),'rules_version':rules['rules_version'],
              'corpus_sha256':manifest['sha256'],'rules_sha256':hashlib.sha256((ROOT/'config/mvp2_date_rules.json').read_bytes()).hexdigest(),
              'fresh_server_ready_seconds':round(startup,4),'http_measurements':measurements,
              'checks':{'request_and_response_schemas':True,'repeat_is_deterministic':True,'invalid_range_422':True,
                        'draw_history_unchanged':True,'tam_nuong_disabled_no_partial':True,'latency_targets_passed':True},
              'scope':'One fresh local server; first search and one repeated request per size, not load testing or P95. Elapsed HTTP includes serialization and local transfer; schema checks run afterward. Natal call counts are instrumented separately in unit tests. Synthetic profiles; software integration does not validate traditional date-selection outcomes.'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
