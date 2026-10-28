"""Integration-test page: volatile current results plus the production signed-snapshot API.

Raw security/API tests deliberately use Starlette's unmodified TestClient instead.
"""
from copy import deepcopy
import json
import re
from threading import RLock
from urllib.parse import urlsplit, parse_qs
from uuid import UUID

import httpx
from fastapi.testclient import TestClient as RawClient


def canonical(data):
    return json.dumps(data, sort_keys=True, separators=(',', ':'))


class TestClient(RawClient):
    __test__ = False

    def __init__(self, app, *args, storage=None, **kwargs):
        self.storage = storage if storage is not None else []
        self.browser_lock = RLock()
        super().__init__(app, *args, **kwargs)

    def record(self, kind, key):
        return next((r for r in reversed(self.storage) if r['kind'] == kind and r['key'] == key), None)

    def snapshot(self, kind, key):
        row = self.record(kind, key)
        return {k: row[k] for k in ('kind', 'data', 'signature')} if row else None

    def enrich(self, body):
        packed = deepcopy(body)
        kind = {'BAZI':'BAZI','MAIHOA':'MAIHOA','LIUYAO':'COINS','DATE':'DATE'}.get(body.get('method'))
        packed['consultation'] = self.snapshot(kind, body.get('consultation_id'))
        if body.get('bazi_reading_id') and body['bazi_reading_id'] != body['consultation_id']:
            row = self.snapshot('BAZI_READING', body['bazi_reading_id'])
            if row: packed['bazi_reading'] = row
        if body.get('method') == 'LIUYAO':
            row = next((r for r in reversed(self.storage) if r['kind'] == 'LIUYAO'
                and r['data']['session_id'] == body['consultation_id']
                and r['data']['context'] == body.get('analysis_context')
                and r['data']['rules_sha256'] == body.get('analysis_rules_sha256')), None)
            if row: packed['analysis'] = {k: row[k] for k in ('kind','data','signature')}
        return packed

    def request(self, method, url, **kwargs):
        # Local history/idempotency is a browser responsibility, not server state.
        with self.browser_lock:
            return self._browser_request(method, str(url), **kwargs)

    def _browser_request(self, method, url, **kwargs):
        method = method.upper()
        parsed = urlsplit(url); path = parsed.path
        body = kwargs.get('json')
        def result(data, code=200):
            return httpx.Response(code, content=json.dumps(deepcopy(data)).encode(), headers={'Content-Type':'application/json'}, request=httpx.Request(method, 'http://testserver'+url))
        def missing(code='DRAW_NOT_FOUND', status=404):
            return result({'error':{'code':code, 'message':'Không tìm thấy kết quả trong trình duyệt.'}}, status)
        def saved(kind, key):
            try: UUID(key)
            except ValueError: return missing('VALIDATION_FAILED',422)
            row=self.record(kind,key)
            return result(row['data']) if row else missing(kind+'_NOT_FOUND')
        def send(target, payload=None, kind=None, key=None, identity=None):
            options=dict(kwargs)
            if payload is not None: options['json']=payload
            response=super(TestClient,self).request('POST' if payload is not None else method,target,**options)
            if response.is_success and kind and response.json() is not None:
                self.storage[:]=[r for r in self.storage if not (r['kind']==kind and r['key']==key)]
                self.storage.append({'kind':kind,'key':key,'data':response.json(),
                                     'signature':response.headers.get('x-arcana-signature'),'identity':deepcopy(identity)})
            return response
        creations={'/api/v1/draw':'DRAW','/api/v1/bazi/consultations':'BAZI','/api/v1/maihoa/consultations':'MAIHOA',
                   '/api/v1/coins/consultations':'COINS','/api/v2/auspicious-dates/consultations':'DATE'}
        if method=='POST' and path in creations and body:
            kind=creations[path];key=body.get('request_id');row=self.record(kind,key)
            if row:return result(row['data']) if canonical(row['identity'])==canonical(body) else missing('REQUEST_ID_CONFLICT',409)
            return send(url,kind=kind,key=key,identity=body)
        if method=='GET' and path.endswith('/history'):
            kind={'/api/v1/history':'DRAW','/api/v1/bazi/history':'BAZI','/api/v1/maihoa/history':'MAIHOA','/api/v1/coins/history':'COINS'}.get(path)
            limit=int(parse_qs(parsed.query).get('limit',[10])[0])
            if not 1<=limit<=100:return missing('VALIDATION_FAILED',422)
            rows=[r['data'] for r in reversed(self.storage) if r['kind']==kind][:limit]
            return result({'draws' if kind=='DRAW' else 'consultations':rows})
        if method=='GET' and (match:=re.fullmatch(r'/api/v1/draw/([^/]+)',path)):return saved('DRAW',match[1])
        if method=='GET' and (match:=re.fullmatch(r'/api/(?:v1/(bazi|maihoa|coins)|v2/(auspicious-dates))/consultations/([^/]+)',path)):
            return saved({'bazi':'BAZI','maihoa':'MAIHOA','coins':'COINS','auspicious-dates':'DATE'}[match[1] or match[2]],match[3])
        if method=='GET' and (match:=re.fullmatch(r'/api/v1/interpretation/([^/]+)',path)):
            try: UUID(match[1])
            except ValueError: return missing('VALIDATION_FAILED',422)
            snapshot=self.snapshot('DRAW',match[1]);cached=self.record('EXPLANATION',match[1])
            if cached:return result(cached['data'])
            return send('/api/v1/interpretation',{'consultation':snapshot},'EXPLANATION',match[1]) if snapshot else missing()
        if match:=re.fullmatch(r'/api/v1/bazi/consultations/([^/]+)/readings',path):
            snapshot=self.snapshot('BAZI',match[1])
            if not snapshot:return missing('BAZI_NOT_FOUND')
            if method=='GET':return result({"readings":[{'reading_id':match[1],'consultation_id':match[1],
                'created_at':snapshot['data']['created_at'],'reading':snapshot['data']['reading']},
                *[r['data'] for r in reversed(self.storage) if r['kind']=='BAZI_READING' and r['data']['consultation_id']==match[1]]]})
            row=self.record('BAZI_READING',body.get('reading_id'));identity={'parent':match[1],'body':body}
            if row:return result(row['data']) if canonical(row['identity'])==canonical(identity) else missing('REQUEST_ID_CONFLICT',409)
            return send('/api/v1/bazi/readings',{'consultation':snapshot,'reading':body},'BAZI_READING',body.get('reading_id'),identity)
        if match:=re.fullmatch(r'/api/v1/coins/consultations/([^/]+)/analysis',path):
            snapshot=self.snapshot('COINS',match[1])
            if not snapshot:return missing('COIN_NOT_FOUND')
            rows=[r for r in reversed(self.storage) if r['kind']=='LIUYAO' and r['data']['session_id']==match[1]]
            if method=='GET':return result(rows[0]['data'] if rows else None)
            rules=self.app.state.liuyao.rules_sha256
            row=next((r for r in rows if canonical(r['identity'])==canonical(body) and r['data']['rules_sha256']==rules),None)
            if row:
                self.storage.remove(row);self.storage.append(row)
                return result(row['data'])
            return send('/api/v1/coins/analysis',{'consultation':snapshot,'context':body},'LIUYAO',canonical([match[1],body,rules]),body)
        if method=='POST' and path in ('/api/v1/ai/readings','/api/v1/ai/readings/lookup'):
            key=canonical(body);row=self.record('AI',key)
            if row:return result(row['data'])
            return send(url,self.enrich(body),'AI',key,body)
        return super().request(method,url,**kwargs)
