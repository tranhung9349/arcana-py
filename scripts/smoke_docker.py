"""Smoke a disposable stateless deployment; never sends an AI generation request.

Usage: python3 scripts/smoke_docker.py http://127.0.0.1:18765
"""
import argparse
import json
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from uuid import uuid4


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('base_url')
    base=parser.parse_args().base_url.rstrip('/')
    if urlsplit(base).hostname not in {'localhost','127.0.0.1','::1'}:
        parser.error('Use a localhost deployment or SSH tunnel for this smoke test.')

    def call(path,payload=None,kind=None):
        data=json.dumps(payload).encode() if payload is not None else None
        with urlopen(Request(base+path,data=data,headers={'Content-Type':'application/json'}),timeout=90) as response:
            assert response.status==200,path
            result=json.load(response)
            if kind:
                signature=response.headers.get('X-Arcana-Signature','')
                assert len(signature)==64,path
                return {'kind':kind,'data':result,'signature':signature}
            return result

    assert call('/api/v1/health')['storage']=='VOLATILE_ONLY'
    for path in ['/','/static/style.css','/static/session_client.js','/static/export_pdf.js','/static/fonts/fonts.css']:
        with urlopen(base+path,timeout=10) as response:
            assert response.status==200 and response.read(100),path
    print('OK: health, HTML, compiled CSS, volatile client, PDF export and local fonts')
    birth={'civil_datetime':'1994-10-08T05:00:00+07:00'}
    casting={'mode':'CUSTOM','custom_timestamp':'2026-10-26T09:00:00+07:00'}
    draw=call('/api/v1/draw',{'request_id':str(uuid4()),'birth':birth,'casting':casting},'DRAW')
    assert len(set(draw['data']['numbers']))==6
    assert call('/api/v1/interpretation',{'consultation':draw})
    print('OK: signed number draw and stateless interpretation')
    bazi=call('/api/v1/bazi/consultations',{'request_id':str(uuid4()),'birth':birth,'topic':'GENERAL','question':''},'BAZI')
    call('/api/v1/bazi/readings',{'consultation':bazi,'reading':{'reading_id':str(uuid4()),'topic':'CAREER','question':''}},'BAZI_READING')
    print('OK: signed Bazi chart and topic reading')
    call('/api/v1/maihoa/consultations',{'request_id':str(uuid4()),'casting':casting,'topic':'GENERAL','question':'Tôi nên cân nhắc điều gì?'},'MAIHOA')
    print('OK: signed Mai Hoa consultation')
    coin=call('/api/v1/coins/consultations',{'request_id':str(uuid4()),'casting':casting,'question':'Hợp tác công việc cần lưu ý điều gì?','source':'RANDOM'},'COINS')
    call('/api/v1/coins/analysis',{'consultation':coin,'context':{'topic':'GENERAL'}},'LIUYAO')
    print('OK: signed coin consultation and Liu Yao analysis')
    search={'activity':'BUSINESS_OPENING','subjects':[{'subject_id':'person_1','birth':birth}],
            'date_range':{'start':'2026-10-29','end':'2026-10-29'},'include_details':False}
    assert call('/api/v2/auspicious-dates/search',search)
    call('/api/v2/auspicious-dates/consultations',{'request_id':str(uuid4()),'search':search},'DATE')
    print('OK: date search and signed selected-day consultation')
    for path in ['/api/v1/history','/api/v1/bazi/history','/api/v1/coins/history','/openapi.json']:
        try:
            urlopen(base+path,timeout=5)
        except HTTPError as error:
            assert error.code==404,path
        else:
            raise AssertionError('Unexpected server history endpoint: '+path)
    status=call('/api/v1/ai/status')
    print('OK: no server history or public API schema; AI configured: '+str(status['configured']))
    print('Stateless Docker smoke completed; no AI generation requested.')


if __name__=='__main__':
    main()
