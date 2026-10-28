const {test}=require('node:test');
const assert=require('node:assert/strict');
const {createClient}=require('../web/session_client.js');
const signature='f'.repeat(64);
const reply=data=>new Response(JSON.stringify(data),{headers:{'Content-Type':'application/json','X-Arcana-Signature':signature}});
const options=body=>({method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
function fixture(responder){
 const calls=[];
 const network=async(path,opts)=>{calls.push({path,opts,body:opts.body && JSON.parse(opts.body)});return responder(path,opts,calls.length);};
 const fresh=()=>createClient({network,origin:'https://arcana.example'});
 return {calls,fresh,api:fresh()};
}
test('current results are in RAM only; a fresh page and another browser have no session',async()=>{
 const s=fixture((path,opts)=>reply({...JSON.parse(opts.body),numbers:['01','02','03','04','05','06']}));
 const body={request_id:'draw-one',birth:{civil_datetime:'1994-10-08T05:00:00+07:00'}};
 const first=await (await s.api.fetch('/api/v1/draw',options(body))).json();
 assert.deepEqual(await (await s.api.fetch('/api/v1/draw',options(body))).json(),first);
 assert.equal(s.calls.length,1);
 assert.equal((await s.fresh().fetch('/api/v1/draw/draw-one')).status,404);
 assert.equal((await s.api.fetch('/api/v1/history')).status,404);
 assert.equal(s.calls.length,1);
});
test('a new consultation removes the previous consultation of the same feature',async()=>{
 const s=fixture((path,opts)=>reply(JSON.parse(opts.body)));
 await s.api.fetch('/api/v1/draw',options({request_id:'first'}));
 await s.api.fetch('/api/v1/draw',options({request_id:'second'}));
 assert.equal((await s.api.fetch('/api/v1/draw/first')).status,404);
 assert.equal((await s.api.fetch('/api/v1/draw/second')).status,200);
});
test('parallel retries share one network call and independent response bodies',async()=>{
 const s=fixture(async(path,opts)=>{await new Promise(r=>setImmediate(r));return reply(JSON.parse(opts.body));});
 const opts=options({request_id:'parallel'});
 const rows=await Promise.all([s.api.fetch('/api/v1/draw',opts),s.api.fetch('/api/v1/draw',opts)]);
 assert.deepEqual(await rows[0].json(),await rows[1].json());assert.equal(s.calls.length,1);
});
test('cross-origin destinations and redirects cannot receive private snapshots',async()=>{
 const s=fixture(()=>reply({}));
 await assert.rejects(s.api.fetch('https://evil.example/api/v1/draw',options({request_id:'x'})));
 await assert.rejects(s.api.fetch('//evil.example/api/v1/draw',options({request_id:'x'})));
 assert.equal(s.calls.length,0);
 await s.api.fetch('/api/v1/health');
 assert.equal(s.calls[0].opts.credentials,'omit');assert.equal(s.calls[0].opts.redirect,'error');
 assert.equal(s.calls[0].opts.cache,'no-store');
});
test('unsigned results are rejected rather than reused in future AI requests',async()=>{
 const s=fixture(()=>new Response('{"request_id":"bad"}',{headers:{'Content-Type':'application/json'}}));
 assert.equal((await s.api.fetch('/api/v1/draw',options({request_id:'bad'}))).status,502);
 assert.equal((await s.api.fetch('/api/v1/draw/bad')).status,404);
});
test('AI receives the exact signed consultation and only runs when explicitly generated',async()=>{
 const s=fixture((path,opts)=>path.endsWith('/lookup')?reply(null):path==='/api/v1/ai/readings'?reply({reading_id:'ai',consultation_id:'chart'}):reply({...JSON.parse(opts.body),chart:{civil_datetime:'1994-10-08T05:00:00+07:00'},reading:{topic_name:'Tổng quan'}}));
 await s.api.fetch('/api/v1/bazi/consultations',options({request_id:'chart'}));
 const request={method:'BAZI',consultation_id:'chart'};
 assert.equal(await (await s.api.fetch('/api/v1/ai/readings/lookup',options(request))).json(),null);
 assert.equal(s.calls.filter(r=>r.path==='/api/v1/ai/readings').length,0);
 await s.api.fetch('/api/v1/ai/readings',options(request));
 const call=s.calls.find(r=>r.path==='/api/v1/ai/readings');
 assert.equal(call.body.consultation.kind,'BAZI');assert.equal(call.body.consultation.signature,signature);
 assert.equal(call.body.consultation.data.request_id,'chart');
 await s.api.fetch('/api/v1/ai/readings',options(request));
 assert.equal(s.calls.filter(r=>r.path==='/api/v1/ai/readings').length,1);
 assert.equal((await s.fresh().fetch('/api/v1/ai/readings',options(request))).status,422);
});
test('Bazi topic readings use the signed parent and stay within the open page',async()=>{
 const s=fixture((path,opts)=>{
  const body=JSON.parse(opts.body);
  return reply(path==='/api/v1/bazi/readings'?{reading_id:body.reading.reading_id,consultation_id:body.consultation.data.request_id,reading:{topic_name:'Công việc'}}:{...body,reading:{topic_name:'Tổng quan'}});
 });
 await s.api.fetch('/api/v1/bazi/consultations',options({request_id:'parent'}));
 await s.api.fetch('/api/v1/bazi/consultations/parent/readings',options({reading_id:'reading',topic:'CAREER'}));
 const call=s.calls[1];assert.equal(call.path,'/api/v1/bazi/readings');assert.equal(call.body.consultation.signature,signature);
 const list=await (await s.api.fetch('/api/v1/bazi/consultations/parent/readings')).json();assert.equal(list.readings.length,2);
});
test('the strict transport permits both versioned date rules and v1 catalogs',async()=>{
 const s=fixture(()=>reply({ok:true}));
 for(const path of ['/api/v2/auspicious-dates/rules','/api/v1/coins/analysis-rules','/api/v1/coins/hexagrams','/api/v1/bazi/rules']) {
  assert.equal((await s.api.fetch(path)).status,200);
  assert.equal(s.calls.at(-1).path,path);
 }
 assert.equal((await s.api.fetch('/api/v2/private-admin')).status,404);
 assert.equal(s.calls.length,4);
});
