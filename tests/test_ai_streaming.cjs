const {test}=require('node:test');
const assert=require('node:assert/strict');
const {createClient}=require('../web/session_client.js');
const request={method:'BAZI',consultation_id:'chart'};
const reading={method:'BAZI',consultation_id:'chart',reading:{summary:{text:'Sơn Đầu Hỏa · Nhật chủ Canh Kim'}}};
const encoder=new TextEncoder();
const event=(name,data)=>'event: '+name+'\r\ndata: '+JSON.stringify(data)+'\r\n\r\n';
const response=(text,split=7)=>{
  const bytes=encoder.encode(text);
  return new Response(new ReadableStream({start(controller){
    for(let i=0;i<bytes.length;i+=split)controller.enqueue(bytes.slice(i,i+split));controller.close();
  }}),{headers:{'Content-Type':'text/event-stream'}});
};
async function fixture(responder,config={}){
  const calls=[];
  const api=createClient({origin:'https://arcana.example',reconnectDelayMs:0,...config,network:async(path,opts)=>{
    calls.push({path,opts,body:JSON.parse(opts.body)});
    if(path.endsWith('/consultations'))return new Response(JSON.stringify({request_id:'chart'}),{headers:{'X-Arcana-Signature':'f'.repeat(64)}});
    return responder(path,opts,calls.length-1);
  }});
  await api.fetch('/api/v1/bazi/consultations',{method:'POST',body:JSON.stringify({request_id:'chart'})});
  calls.length=0;return {api,calls};
}
test('SSE assembles split UTF-8/CRLF, ignores heartbeat comments and caches the final article in page memory',async()=>{
  const stages=[];
  const s=await fixture(()=>response(': heartbeat\r\n\r\n'+event('progress',{stage:'ANALYZING'})+event('progress',{stage:'WRITING'})+event('result',reading),1));
  assert.deepEqual(await s.api.streamReading(request,{generate:true,onProgress:s=>stages.push(s)}),reading);
  assert.deepEqual(stages,['ANALYZING','WRITING']);assert.equal(s.calls.length,1);
  assert.equal(s.calls[0].path,'/api/v1/ai/readings/start');
  assert.equal(s.calls[0].body.consultation.signature,'f'.repeat(64));
  assert.equal(s.calls[0].opts.credentials,'omit');assert.equal(s.calls[0].opts.redirect,'error');
  assert.equal(s.calls[0].opts.cache,'no-store');
  assert.deepEqual(await s.api.streamReading(request),reading);assert.equal(s.calls.length,1);
  assert.deepEqual(await (await s.api.fetch('/api/v1/ai/readings/lookup',{method:'POST',body:JSON.stringify(request)})).json(),reading);
  assert.equal(s.calls.length,1);
});
test('a dropped response reconnects to the existing worker and never replays the paid start',async()=>{
  const stages=[];
  const s=await fixture((path,opts,count)=>response(count===0?event('progress',{stage:'ANALYZING'}):event('result',reading)));
  assert.deepEqual(await s.api.streamReading(request,{generate:true,onProgress:stage=>stages.push(stage)}),reading);
  assert.deepEqual(s.calls.map(c=>c.path),['/api/v1/ai/readings/start','/api/v1/ai/readings/stream']);
  assert.deepEqual(stages,['ANALYZING','RECONNECTING']);
});
test('lost start acknowledgement cannot automatically create another paid job',async()=>{
  const s=await fixture((path,opts,count)=>{
    if(count===0)throw new TypeError('Network lost with private details');
    return response(event('missing',{}));
  });
  await assert.rejects(s.api.streamReading(request,{generate:true}),{code:'AI_STREAM_INTERRUPTED'});
  assert.deepEqual(s.calls.map(c=>c.path),['/api/v1/ai/readings/start','/api/v1/ai/readings/stream']);
});
test('reopening a running article subscribes without creating a job, and missing articles stay read-only',async()=>{
  const s=await fixture(()=>response(event('progress',{stage:'WRITING'})+event('result',reading)));
  assert.deepEqual(await s.api.streamReading(request),reading);assert.equal(s.calls[0].path,'/api/v1/ai/readings/stream');
  const missing=await fixture(()=>response(event('missing',{})));
  assert.equal(await missing.api.streamReading(request),null);assert.equal(missing.calls.length,1);
});
test('terminal provider/validation errors are not retried and do not replace the signed chart',async()=>{
  const s=await fixture(()=>response(event('error',{error:{code:'AI_RESPONSE_UNBOUND',message:'private provider response'}})));
  await assert.rejects(s.api.streamReading(request,{generate:true}),e=>e.code==='AI_RESPONSE_UNBOUND' && !e.message.includes('private'));
  assert.equal(s.calls.length,1);
  assert.equal((await s.api.fetch('/api/v1/bazi/consultations/chart')).status,200);
});
test('mismatched results, oversized frames and malformed SSE never enter the page cache',async()=>{
  for(const text of [event('result',{...reading,consultation_id:'other'}),'event: result\ndata: not json\n\n',
    'data: '+ 'x'.repeat(2097153)+'\n\n']){
    const s=await fixture(()=>response(text,65536));
    await assert.rejects(s.api.streamReading(request,{generate:true}),{code:'AI_RESPONSE_INVALID'});
    assert.equal(s.calls.length,1);
  }
});
test('idle connection watchdog reconnects to the same worker',async()=>{
  const s=await fixture((path,opts,count)=>count===0?
    new Response(new ReadableStream({start(controller){opts.signal.addEventListener('abort',()=>controller.error(new DOMException('Aborted','AbortError')));}}),
      {headers:{'Content-Type':'text/event-stream'}}):response(event('result',reading)),{streamIdleMs:10});
  assert.deepEqual(await s.api.streamReading(request,{generate:true}),reading);
  assert.deepEqual(s.calls.map(c=>c.path),['/api/v1/ai/readings/start','/api/v1/ai/readings/stream']);
});
test('definitive HTTP configuration errors preserve their code without reconnecting',async()=>{
  const s=await fixture(()=>new Response(JSON.stringify({error:{code:'AI_NOT_CONFIGURED',message:'private'}}),
    {status:503,headers:{'Content-Type':'application/json'}}));
  await assert.rejects(s.api.streamReading(request,{generate:true}),{code:'AI_NOT_CONFIGURED'});
  assert.equal(s.calls.length,1);
});
test('destroying an observer cancels its connection without retrying or sending a cancellation to the worker',async()=>{
  const controller=new AbortController();let started;
  const ready=new Promise(resolve=>{started=resolve;});
  const s=await fixture((path,opts)=>new Response(new ReadableStream({start(stream){
    opts.signal.addEventListener('abort',()=>stream.error(new DOMException('Aborted','AbortError')));started();
  }}),{headers:{'Content-Type':'text/event-stream'}}));
  const work=s.api.streamReading(request,{generate:true,signal:controller.signal});await ready;controller.abort();
  await assert.rejects(work,{name:'AbortError'});assert.equal(s.calls.length,1);
});
test('unsigned or absent profiles cannot start a stream',async()=>{
  let calls=0;
  const api=createClient({origin:'https://arcana.example',network:()=>{calls++;}});
  await assert.rejects(api.streamReading(request,{generate:true}),{code:'SNAPSHOT_INVALID'});assert.equal(calls,0);
});
