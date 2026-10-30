const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {createClient}=require('../web/session_client.js');

class Node {
  constructor(tag){this.tag=tag;this.children=[];this.attributes={};this.handlers={};this.isConnected=true;this.hidden=false;this.disabled=false;this.value='';}
  appendChild(n){this.children.push(n);return n;}
  replaceChildren(){this.children=[];this.value='';}
  setAttribute(k,v){this.attributes[k]=v;}
  addEventListener(k,v){this.handlers[k]=v;}
  set textContent(v){this.value=String(v);this.children=[];}
  get textContent(){return this.value+this.children.map(n=>n.textContent).join(' ');}
  find(tag){return this.children.flatMap(n=>[...(n.tag===tag?[n]:[]),...n.find(tag)]);}
}
const tick=()=>new Promise(resolve=>setImmediate(resolve));
const request={method:'BAZI',consultation_id:'00000000-0000-4000-8000-000000000001'};
const result={consultation_id:request.consultation_id,method:'BAZI',model_returned:'test-model',created_at:'2026-10-26T00:00:00Z',
  context:{facts:[{id:'f1',text:'Căn cứ mẫu'}],evidence:[{id:'e1',title:'Nguồn mẫu',text:'Văn bản mẫu',url:null,kind:'PRODUCT_POLICY'}]},
  reading:{summary:{text:'Lời luận đã lưu',fact_refs:['f1'],evidence_refs:['e1']},analysis:[{text:'Một nhận định cụ thể',fact_refs:['f1'],evidence_refs:['e1']}],
    practical_options:[{text:'Một việc có thể kiểm tra'}],limits:['Phần chưa xác định']}};

function setup(responder,{realClient=false}={}){
  const calls=[];
  const sandbox={window:{},document:{createElement:t=>new Node(t)},AbortController,DOMException,Date,setTimeout,clearTimeout,
    fetch:async(url,options)=>{calls.push({url,body:JSON.parse(options.body)});return responder(url,options,calls.length);}};
  sandbox.window.ArcanaClient=realClient?createClient({network:sandbox.fetch,origin:'http://127.0.0.1:8766'}):{
    async streamReading(request,{generate,onProgress}) {
      const response=await sandbox.fetch('/api/v1/ai/readings/'+(generate?'start':'stream'),{body:JSON.stringify(request)});
      const data=await response.json();
      if(!response.ok)throw Object.assign(Error('Reading failed'),{code:data?.error?.code});
      return data;
    }};
  vm.runInNewContext(fs.readFileSync('web/display_text.js','utf8'),sandbox);
  vm.runInNewContext(fs.readFileSync('web/ai_reading.js','utf8'),sandbox);
  return {api:sandbox.window.AIReading,client:sandbox.window.ArcanaClient,calls,root:new Node('section')};
}
const ok=data=>({ok:true,json:async()=>data});

function lifeResult(){
  const data=structuredClone(result),binding='a'.repeat(64);
  const block=text=>({text,pattern_refs:['P01'],manifestation_refs:['P01-M01'],condition_refs:['P01-C01'],limit_refs:['P01-L01']});
  data.pipeline={version:'bazi-two-stage-2026-10-28-v1',analysis_sha256:binding};
  data.reading={schema_version:'bazi-life-reading-v1',context_id:request.consultation_id,analysis_sha256:binding,
    overview:block('Bạn có thể muốn hiểu việc mới trước khi bắt đầu.\n\nHãy đối chiếu điều này với trải nghiệm của mình.'),
    tendencies:[{...block('Khi có thời gian chuẩn bị, việc chia nhỏ từng bước giúp bạn bắt đầu. Nếu việc đổi quá nhanh, bạn có thể mất nhịp.'),pattern_id:'P01',title:'Hiểu rõ rồi mới làm'}],
    in_life:[{...block('Ở công việc mới, bạn có thể cần một ví dụ rõ ràng để tự thử.'),title:'Bắt đầu việc mới',domains:['WORK']}],
    contradictions:[block('Có lúc bạn muốn chuẩn bị kỹ nhưng cũng muốn tự thử; thời gian được giao sẽ ảnh hưởng cách bạn chọn.')],
    takeaway:block('Bạn có thể thử một bước nhỏ rồi xem kết quả trước khi quyết định tiếp.'),
    limits:[{text:'Chưa đủ căn cứ để nói lúc nào một việc sẽ xảy ra.',source_refs:['G01']}],
    disclaimer:'Đây là cách diễn giải theo hệ thống truyền thống, không phải đánh giá tính cách hay dự đoán khoa học.'};
  return data;
}

test('two-stage Bazi renders the complete reader article as paragraphs without technical intermediate or IDs',async()=>{
  const data=lifeResult(),before=JSON.stringify(data);let loaded;
  // An unexpected technical object must never be displayed as reader content.
  data.bazi_analysis={secret:'Phân tích kỹ thuật không hiển thị'};
  const s=setup(async()=>ok(data));s.api.mount(s.root,request,{onLoad:value=>{loaded=value;}});await tick();
  const content=s.root.find('div').find(n=>n.className==='ai-reading-content');
  assert.deepEqual(content.children.slice(0,5).map(n=>n.tag),['section','section','section','section','section']);
  for(const heading of ['Bức tranh chung','Những khuynh hướng nổi bật','Trong công việc và cuộc sống','Những điểm tưởng như trái nhau','Điều đáng lưu ý nhất'])assert.ok(content.textContent.includes(heading));
  assert.equal(content.children[0].find('p').length,2);
  for(const block of [data.reading.overview,...data.reading.tendencies,...data.reading.in_life,...data.reading.contradictions,data.reading.takeaway]) {
    for(const paragraph of block.text.split('\n\n'))assert.ok(content.textContent.includes(paragraph));
  }
  assert.match(content.textContent,/Đây là cách diễn giải/);
  assert.doesNotMatch(content.textContent,/Phạm vi của bài luận|Chưa đủ căn cứ|Thông tin bài luận/);
  assert.doesNotMatch(content.textContent,/P01|G01|Phân tích kỹ thuật|analysis_sha256|schema_version|[{}]/);
  assert.equal(loaded,data);delete data.bazi_analysis;assert.equal(JSON.stringify(data),before);
});
test('whole-life Bazi opens with the full portrait, three life domains and saved life periods',async()=>{
  const data=lifeResult();data.reading.tendencies=[];data.reading.in_life=[];data.reading.contradictions=[];
  data.reading.overview.text='Đường phát triển sự nghiệp, việc tích lũy và các mối gắn bó được xem cùng những chặng vận đã tính.';
  data.reading.whole_life={areas:[
    {source_id:'L01',area:'CAREER',text:'Đường xây dựng sự nghiệp cần được xét từ nguồn lực và trách nhiệm.'},
    {source_id:'L02',area:'FINANCES',text:'Nguồn thu và việc tích lũy có những điều kiện riêng.'},
    {source_id:'L03',area:'RELATIONSHIPS',text:'Các mối gắn bó trong gia đình được xem riêng với hợp tác công việc.'}],
    periods:[{id:'V01',cycle_indices:[0,1],start_year:2000,end_year:2019,start_age:6,end_age:25,text:'Chặng tạo nền được đối chiếu với các vận đã tính.'}],
    timing_status:'AVAILABLE',timing_note:'Các mốc là phạm vi vận đã tính.'};
  const s=setup(async()=>ok(data));s.api.mount(s.root,request);await tick();
  assert.deepEqual(s.root.find('h4').map(n=>n.textContent),['Bức tranh toàn cảnh','Sự nghiệp và đường phát triển','Tài chính và tích lũy',
    'Tình cảm, quan hệ và gia đình','Các chặng đường theo Đại vận','Điểm tựa và điều cần cân bằng']);
  assert.match(s.root.textContent,/2000–2019 · 6–25 tuổi.*Chặng tạo nền/);
  assert.doesNotMatch(s.root.textContent,/Những khuynh hướng nổi bật|L01|V01|cycle_indices|source_id/);
  data.reading.whole_life.areas[0].text='L01: {"private":"analysis"}';
  const bad=setup(async()=>ok(data));bad.api.mount(bad.root,request);await tick();
  assert.match(bad.root.textContent,/Bài luận chưa thể hiển thị/);assert.doesNotMatch(bad.root.textContent,/Bức tranh toàn cảnh/);
});

test('Bazi reader rejects mismatched analysis bindings or methods before displaying any prose',async()=>{
  for(const poison of [data=>{data.pipeline.analysis_sha256='b'.repeat(64);},data=>{data.reading.context_id='different';},data=>{delete data.pipeline;},data=>{data.method='MAIHOA';}]) {
    const data=lifeResult();poison(data);let loaded=false;
    const s=setup(async()=>ok(data));s.api.mount(s.root,{...request,method:data.method},{onLoad:()=>{loaded=true;}});await tick();
    assert.doesNotMatch(s.root.textContent,/Hiểu rõ rồi mới làm|Bức tranh chung/);
    assert.match(s.root.textContent,/không khớp/);assert.equal(loaded,false);
  }
});

test('Bazi reader rejects machine notation in all article fields before partial rendering',async()=>{
  for(const poison of [data=>{data.reading.overview.text='{"type":"object"}';},data=>{data.reading.tendencies[0].title='P01-M01';},
    data=>{data.reading.in_life[0].text='backend_schema: v1';},data=>{data.reading.contradictions[0].text='P01';},
    data=>{data.reading.takeaway.text='<script>invalid</script>';},data=>{data.reading.limits[0].text='P01-L01';}]) {
    const data=lifeResult();poison(data);let loaded=false;
    const s=setup(async()=>ok(data));s.api.mount(s.root,request,{onLoad:()=>{loaded=true;}});await tick();
    assert.doesNotMatch(s.root.textContent,/Hiểu rõ rồi mới làm|Bức tranh chung|backend_schema|P01|[{}]/);
    assert.match(s.root.textContent,/Bài luận chưa thể hiển thị/);assert.equal(loaded,false);
    assert.equal(s.root.find('button')[0].hidden,false);
  }
});

test('opening a cached reading only performs lookup and renders plain text',async()=>{
  let loaded;
  const s=setup(async()=>ok(result));s.api.mount(s.root,request,{autoGenerate:true,onLoad:data=>{loaded=data;}});await tick();
  assert.equal(s.calls.length,1);assert.match(s.calls[0].url,/stream$/);
  assert.match(s.root.textContent,/Lời luận đã lưu/);assert.match(s.root.textContent,/Một việc có thể kiểm tra/);
  assert.equal(s.root.find('details').length,3);
  assert.doesNotMatch(s.root.textContent,/Thông tin bài luận/);
  assert.equal(loaded,result);
});
test('Liu Yao shows only the reader answer and reasons without evidence or article metadata controls',async()=>{
  const data=structuredClone(result);data.method='LIUYAO';
  data.reading.analysis.push({...data.reading.analysis[0],text:'Chưa xác định được thời gian còn lại.'});
  const before=JSON.stringify(data),s=setup(async()=>ok(data));
  s.api.mount(s.root,{...request,method:'LIUYAO'});await tick();
  const content=s.root.find('div').find(n=>n.className==='ai-reading-content');
  assert.deepEqual(content.find('h4').map(n=>n.textContent),['Trả lời câu hỏi của bạn','Quẻ cho thấy điều gì?','Bạn có thể làm gì?','Cần lưu ý']);
  const reasons=content.children.find(n=>n.className==='ai-reading-reasons');
  assert.equal(reasons.tag,'section');assert.equal(reasons.find('p').length,2);
  assert.equal(content.find('details').length,0);
  assert.doesNotMatch(content.textContent,/Xem căn cứ của lời giải|Thông tin bài luận|Luận bằng AI/);
  assert.equal(content.textContent.split(data.reading.analysis[0].text).length-1,1);
  assert.equal(JSON.stringify(data),before);
});
test('new Bazi consultations show loading then the final article without a second click',async()=>{
  let finish;
  const s=setup(async(_,__,count)=>count===1?ok(null):new Promise(resolve=>{finish=resolve;}));
  s.api.mount(s.root,request,{autoGenerate:true});await tick();await tick();
  assert.equal(s.calls.length,2);assert.match(s.calls[1].url,/start$/);
  assert.match(s.root.textContent,/Đang viết bài luận cho bạn/);
  assert.equal(s.root.find('button')[0].hidden,true);
  finish(ok(lifeResult()));await tick();
  assert.match(s.root.textContent,/Bức tranh chung.*Hiểu rõ rồi mới làm/);
  assert.equal(s.root.find('button')[0].hidden,true);
  assert.equal(s.calls.length,2);
});
test('automatic Bazi generation carries the signed consultation through the real page client',async()=>{
  const s=setup(async(url)=>url.endsWith('/consultations')?
    new Response(JSON.stringify({request_id:request.consultation_id}),{headers:{'Content-Type':'application/json','X-Arcana-Signature':'a'.repeat(64)}}):
    new Response(url.endsWith('/stream')?'event: missing\ndata: {}\n\n':'event: result\ndata: '+JSON.stringify(lifeResult())+'\n\n',
      {headers:{'Content-Type':'text/event-stream'}}),{realClient:true});
  await s.client.fetch('/api/v1/bazi/consultations',{method:'POST',body:JSON.stringify({request_id:request.consultation_id})});
  s.api.mount(s.root,request,{autoGenerate:true});
  for(let i=0;i<12 && !s.root.textContent.includes('Bức tranh chung');i++)await tick();
  assert.equal(s.calls.length,3);
  assert.equal(s.calls[2].body.consultation.signature,'a'.repeat(64));
  assert.match(s.root.textContent,/Bức tranh chung.*Hiểu rõ rồi mới làm/);
});
test('live progress updates stay separate from the validated article and unknown stages never become prose',async()=>{
  let stream;
  const s=setup(async(url)=>url.endsWith('/consultations')?
    new Response(JSON.stringify({request_id:request.consultation_id}),{headers:{'X-Arcana-Signature':'a'.repeat(64)}}):
    url.endsWith('/stream')?new Response('event: missing\ndata: {}\n\n',{headers:{'Content-Type':'text/event-stream'}}):
    new Response(new ReadableStream({start(controller){stream=controller;}}),{headers:{'Content-Type':'text/event-stream'}}),{realClient:true});
  await s.client.fetch('/api/v1/bazi/consultations',{method:'POST',body:JSON.stringify({request_id:request.consultation_id})});
  s.api.mount(s.root,request,{autoGenerate:true});await tick();await tick();
  const emit=(name,data)=>stream.enqueue(new TextEncoder().encode('event: '+name+'\ndata: '+JSON.stringify(data)+'\n\n'));
  emit('progress',{stage:'ANALYZING'});await tick();assert.match(s.root.textContent,/Đang phân tích lá số/);
  emit('progress',{stage:'private-provider-sentinel'});await tick();assert.doesNotMatch(s.root.textContent,/private-provider/);
  emit('progress',{stage:'WRITING'});await tick();assert.match(s.root.textContent,/Đang viết bài luận/);
  assert.doesNotMatch(s.root.textContent,/Bức tranh chung/);
  emit('result',lifeResult());stream.close();await tick();await tick();
  assert.match(s.root.textContent,/Bức tranh chung/);assert.doesNotMatch(s.root.textContent,/Đang viết bài luận/);
});
test('other methods keep the answer, actions and cautions before collapsed analysis without losing text',async()=>{
  for(const method of ['BAZI','MAIHOA','DATE']) {
    const data=structuredClone(result);data.method=method;
    data.reading.analysis.push({text:'Điều kiện quan trọng vẫn được giữ nguyên',fact_refs:['f1'],evidence_refs:['e1']});
    const before=JSON.stringify(data),s=setup(async()=>ok(data));
    s.api.mount(s.root,{...request,method});await tick();
    const content=s.root.find('div').find(n=>n.className==='ai-reading-content');
    assert.deepEqual(content.children.slice(0,4).map(n=>n.tag),['section','section','section','details']);
    assert.match(content.children[0].textContent,/Ý chính.*Lời luận đã lưu/);
    assert.match(content.children[1].textContent,/Bạn có thể làm gì.*Một việc có thể kiểm tra/);
    assert.match(content.children[2].textContent,/Cần lưu ý.*Phần chưa xác định/);
    const explanation=content.children[3];assert.equal(Boolean(explanation.open),false);
    assert.match(explanation.textContent,/Vì sao có kết luận này/);
    for(const claim of data.reading.analysis)assert.ok(explanation.textContent.includes(claim.text));
    assert.equal(JSON.stringify(data),before);
  }
});
test('unmatched consultation output is rejected and can be retried',async()=>{
  const wrong={...result,consultation_id:'different'};
  let loaded=false;
  const s=setup(async()=>ok(wrong));s.api.mount(s.root,request,{onLoad:()=>{loaded=true;}});await tick();
  assert.doesNotMatch(s.root.textContent,/Lời luận đã lưu/);
  assert.match(s.root.textContent,/không khớp phiên/);
  assert.equal(s.root.find('button')[0].disabled,false);
  assert.equal(loaded,false);
});
test('destroyed panels cannot populate the new view with a stale response',async()=>{
  let resolve;
  const s=setup(()=>new Promise(r=>{resolve=r;}));const handle=s.api.mount(s.root,request);
  handle.destroy();resolve(ok(result));await tick();
  assert.doesNotMatch(s.root.textContent,/Lời luận đã lưu/);
});
test('errors preserve the result area and expose a retry without echoing upstream text',async()=>{
  const s=setup(async()=>({ok:false,json:async()=>({error:{message:'<script>upstream</script>'}})}));
  s.api.mount(s.root,request);await tick();
  assert.match(s.root.textContent,/Chưa tải được bài luận/);
  assert.doesNotMatch(s.root.textContent,/upstream|script/);
  assert.equal(s.root.find('script').length,0);
  assert.equal(s.root.find('button')[0].hidden,false);
});
test('a failed reload clears the old article and exposes a private diagnostic code without replacing the chart',async()=>{
  let fail=false;
  const s=setup(async()=>fail?{ok:false,json:async()=>({error:{code:'AI_RESPONSE_UNBOUND'}})}:ok(result));
  const panel=s.api.mount(s.root,request);await tick();
  const content=s.root.find('div').find(n=>n.className==='ai-reading-content');
  assert.match(content.textContent,/Lời luận đã lưu/);
  fail=true;panel.reload();await tick();
  assert.equal(content.textContent,'');
  const error=s.root.find('p').find(n=>n.className==='ai-reading-error');
  assert.equal(error.attributes['data-error-code'],'AI_RESPONSE_UNBOUND');
  assert.match(error.textContent,/kiểm tra nội dung và căn cứ/);
  assert.equal(error.hidden,false);
});
test('all four methods show saved findings instead of serialized model facts, including collapsed details',async()=>{
  for(const method of ['BAZI','MAIHOA','LIUYAO','DATE']) {
    const data=structuredClone(result);data.method=method;
    data.context.facts=[{id:'f1',text:'{"schema_version":"backend-v1","strength":"STRONG"}'}];
    data.context.findings=[{id:'finding:1',text:'Thời khí đang nâng đỡ yếu tố trọng tâm.',fact_refs:['f1']}];
    data.context.evidence[0].text='{"internal_field":"do not show"}';
    const s=setup(async()=>ok(data));s.api.mount(s.root,{...request,method});await tick();
    if(method==='LIUYAO')assert.doesNotMatch(s.root.textContent,/Thời khí đang nâng đỡ/);
    else assert.match(s.root.textContent,/Thời khí đang nâng đỡ/);
    assert.doesNotMatch(s.root.textContent,/Thông tin bài luận/);
    assert.match(s.root.textContent,/Lời luận đã lưu/);
    assert.doesNotMatch(s.root.textContent,/schema_version|backend-v1|STRONG|internal_field|[{}]/);
  }
});
test('machine notation in any model prose field prevents partial rendering and offers retry',async()=>{
  for(const part of ['summary','analysis','practical_options','limits']) {
    const data=structuredClone(result);
    if(part==='summary')data.reading.summary.text='{"type":"object"}';
    else if(part==='limits')data.reading.limits[0]='backend_schema: v1';
    else data.reading[part][0].text='Kết quả: {"required":["name"]}';
    const s=setup(async()=>ok(data));s.api.mount(s.root,request);await tick();
    assert.doesNotMatch(s.root.textContent,/Lời luận đã lưu|required|backend_schema|[{}]/);
    assert.match(s.root.textContent,/Bài luận chưa thể hiển thị/);
    assert.equal(s.root.find('button')[0].hidden,false);
  }
});
test('non-JSON HTTP responses and malformed successful responses never expose parse or schema errors',async()=>{
  for(const response of [{ok:false,json:async()=>{throw new SyntaxError('Unexpected token < in JSON');}},ok({schema_version:'debug-v1'})]) {
    const s=setup(async()=>response);s.api.mount(s.root,request);await tick();
    assert.match(s.root.textContent,/Chưa tải được bài luận|không khớp phiên/);
    assert.doesNotMatch(s.root.textContent,/SyntaxError|Unexpected|schema_version|debug-v1/);
  }
});
