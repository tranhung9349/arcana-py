"""Explicit live smoke test with synthetic profiles; the backend owns credentials."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import json
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',default='http://127.0.0.1:8765')
    parser.add_argument('--output',type=Path,default=Path('docs/research/ai_readings_http_smoke.json'))
    parser.add_argument('--fixtures',type=Path,default=Path('docs/research/ai_readings_smoke_requests.json'))
    args=parser.parse_args()
    def call(path,payload=None):
        req=Request(args.base_url+path,data=json.dumps(payload,ensure_ascii=False).encode() if payload is not None else None,
                    headers={'Content-Type':'application/json'},method='POST' if payload is not None else 'GET')
        try:
            with urlopen(req,timeout=140) as response:return json.load(response)
        except HTTPError as error:
            # Only our backend's sanitized error contract is returned here.
            body=json.load(error)
            raise RuntimeError(body.get('error',{}).get('code','HTTP_FAILURE')) from None
    status=call('/api/v1/ai/status')
    if not status['configured']:raise SystemExit('Backend AI is not configured.')
    cases=[]
    if args.fixtures.exists():
        for fixture in json.loads(args.fixtures.read_text()):
            req=fixture['request'];path=fixture['consultation_path']
            cases.append((req['method'],call(path+req['consultation_id']),path,req))
    else:
        bazi=call('/api/v1/bazi/consultations',{'request_id':str(uuid4()),'display_name':'Lá số mẫu · Luận giải AI',
            'birth':{'civil_datetime':'1994-10-08T05:00:00+07:00'},'topic':'STUDY','question':'Tôi nên chú ý điều gì để học và thực hành hiệu quả hơn?'})
        cases.append(('BAZI',bazi,'/api/v1/bazi/consultations/',{'method':'BAZI','consultation_id':bazi['request_id']}))
        maihoa=call('/api/v1/maihoa/consultations',{'request_id':str(uuid4()),'question':'Kế hoạch học thêm kỹ năng của tôi có điều gì cần chuẩn bị kỹ?',
            'topic':'PLANNING','casting':{'mode':'CUSTOM','custom_timestamp':'2026-10-26T09:00:00+07:00'}})
        cases.append(('MAIHOA',maihoa,'/api/v1/maihoa/consultations/',{'method':'MAIHOA','consultation_id':maihoa['request_id']}))
        coin=call('/api/v1/coins/consultations',{'request_id':str(uuid4()),'question':'Bản đề cương học tập tôi đang chuẩn bị cần rà soát điều gì?',
            'source':'MANUAL','casting':{'mode':'CUSTOM','custom_timestamp':'2026-10-26T09:00:00+07:00'},
            'throws_bottom_to_top':[['BACK']*(v-6)+['INSCRIPTION']*(9-v) for v in (7,8,9,8,7,6)]})
        analysis=call('/api/v1/coins/consultations/'+coin['request_id']+'/analysis',{'topic':'DOCUMENT','intent_acknowledged':True})
        cases.append(('LIUYAO',coin,'/api/v1/coins/consultations/',{'method':'LIUYAO','consultation_id':coin['request_id'],
            'analysis_context':analysis['context'],'analysis_rules_sha256':analysis['rules_sha256']}))
        args.fixtures.parent.mkdir(parents=True,exist_ok=True)
        args.fixtures.write_text(json.dumps([{'request':req,'consultation_path':path} for _,_,path,req in cases],ensure_ascii=False,indent=2)+'\n')
    report={'checked_at':datetime.now(timezone.utc).isoformat(),'provider':status,'synthetic_data_only':True,'results':[]}
    for method,saved,path,request in cases:
        start=time.monotonic();result=call('/api/v1/ai/readings',request);elapsed=time.monotonic()-start
        cache_start=time.monotonic();cached=call('/api/v1/ai/readings',request);cache_ms=(time.monotonic()-cache_start)*1000
        assert cached==result
        assert call('/api/v1/ai/readings/lookup',request)==result
        assert call(path+saved['request_id'])==saved
        record={'method':method,'consultation_id':saved['request_id'],'ai_reading_id':result['reading_id'],
                'model_returned':result['model_returned'],'prompt_version':result['prompt_version'],
                'context_sha256':result['context_sha256'],'case_ids':result['case_ids'],
                'validation':result['validation'],'usage':result['usage'],'generation_passes':result['generation_passes'],'generate_seconds':round(elapsed,3),
                'cache_replay_ms':round(cache_ms,3),'cache_identical':True,'original_snapshot_unchanged':True,
                'analysis_sections':len(result['reading']['analysis']),'summary':result['reading']['summary']['text']}
        report['results'].append(record)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({k:record[k] for k in ('method','model_returned','validation','generate_seconds','cache_identical','original_snapshot_unchanged')},ensure_ascii=False),flush=True)
    print(json.dumps({'passed':len(report['results']),'report':str(args.output)}),flush=True)


if __name__=='__main__':
    main()
