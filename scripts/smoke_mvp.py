"""Live localhost API smoke test. Uses public example data, no user profile."""
import json
from pathlib import Path
import sys
import time
from uuid import uuid4
import httpx
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from randomyst.models import DrawRequest, DrawResponse
payload=json.loads((ROOT/'examples/draw_request.json').read_text())
payload['request_id']=str(uuid4())
with httpx.Client(base_url='http://127.0.0.1:8765',timeout=30) as client:
    health=client.get('/api/v1/health');health.raise_for_status()
    assert health.json()['pool']==[0,99]
    start=time.perf_counter(); first=client.post('/api/v1/draw',json=payload);first.raise_for_status();elapsed=(time.perf_counter()-start)*1000
    second=client.post('/api/v1/draw',json=payload);second.raise_for_status()
    result=first.json()
    DrawRequest.model_validate(payload)
    DrawResponse.model_validate(result)
    assert result['rules_version']=='mvp1-logic-2026-10-26-v6'
    assert result['threshold']==(85 if result['trace']['maihoa']['state']=='DAI_HUNG' else 80)
    assert result['trace']['casting_calendar']['maihoa_inputs']=={'Y':7,'M':9,'D':2,'H':7}
    assert result==second.json(), 'Idempotency mismatch'
    numbers=list(map(int,result['numbers']))
    assert len(numbers)==len(set(numbers))==6 and all(0<=n<=99 for n in numbers)
    assert result['attempts']<=5
    assert result['trace']['maihoa']['display_hexagrams']['affects_generation'] is False
    cached_v3_preserved=None
    old_payload=json.loads((ROOT/'docs/archive/draw_request_v3.json').read_text())
    history=client.get('/api/v1/history?limit=100');history.raise_for_status()
    if any(row['request_id']==old_payload['request_id'] and row['rules_version'].endswith('-v3') for row in history.json()['draws']):
        old=client.post('/api/v1/draw',json=old_payload);old.raise_for_status()
        cached_v3_preserved=old.json()==json.loads((ROOT/'docs/archive/draw_response_v3.json').read_text())
        assert cached_v3_preserved, 'Historical v3 result changed'
    (ROOT/'examples/draw_request.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'examples/draw_response.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    report={'health':health.json(),'numbers':result['numbers'],'status':result['status'],'score':result['score'],'threshold':result['threshold'],
            'attempts':result['attempts'],'same_request_same_output':True,'formal_response_valid':True,
            'cached_v3_result_preserved':cached_v3_preserved,'http_elapsed_ms':round(elapsed,2),
            'measurement_scope':'One localhost request, not a latency benchmark'}
    (ROOT/'docs/research/number_draw_v6_http_smoke.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))
