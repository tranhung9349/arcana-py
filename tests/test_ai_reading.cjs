const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

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
  reading:{summary:{text:'Lời luận đã lưu'},analysis:[{text:'Một nhận định cụ thể',fact_refs:['f1'],evidence_refs:['e1']}],
    practical_options:[{text:'Một việc có thể kiểm tra'}],limits:['Phần chưa xác định']}};

function setup(responder){
  const calls=[];
  const sandbox={window:{},document:{createElement:t=>new Node(t)},AbortController,DOMException,Date,setTimeout,clearTimeout,
    fetch:async(url,options)=>{calls.push({url,body:JSON.parse(options.body)});return responder(url,options,calls.length);}};
  sandbox.window.ArcanaClient={fetch:(...args)=>sandbox.fetch(...args)};
  vm.runInNewContext(fs.readFileSync('web/display_text.js','utf8'),sandbox);
  vm.runInNewContext(fs.readFileSync('web/ai_reading.js','utf8'),sandbox);
  return {api:sandbox.window.AIReading,calls,root:new Node('section')};
}
const ok=data=>({ok:true,json:async()=>data});

test('opening a cached reading only performs lookup and renders plain text',async()=>{
  const s=setup(async()=>ok(result));s.api.mount(s.root,request,{autoGenerate:true});await tick();
  assert.equal(s.calls.length,1);assert.match(s.calls[0].url,/lookup$/);
  assert.match(s.root.textContent,/Lời luận đã lưu/);assert.match(s.root.textContent,/Một việc có thể kiểm tra/);
  assert.ok(s.root.find('details').length>=3);
});
test('new consultations generate once after an empty lookup',async()=>{
  const s=setup(async(_,__,count)=>ok(count===1?null:result));s.api.mount(s.root,request,{autoGenerate:true});await tick();await tick();
  assert.equal(s.calls.length,2);assert.match(s.calls[1].url,/readings$/);
  assert.match(s.root.textContent,/Lời luận đã lưu/);
});
test('unmatched consultation output is rejected and can be retried',async()=>{
  const wrong={...result,consultation_id:'different'};
  const s=setup(async()=>ok(wrong));s.api.mount(s.root,request);await tick();
  assert.doesNotMatch(s.root.textContent,/Lời luận đã lưu/);
  assert.match(s.root.textContent,/không khớp phiên/);
  assert.equal(s.root.find('button')[0].disabled,false);
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
test('all four methods show saved findings instead of serialized model facts, including collapsed details',async()=>{
  for(const method of ['BAZI','MAIHOA','LIUYAO','DATE']) {
    const data=structuredClone(result);data.method=method;
    data.context.facts=[{id:'f1',text:'{"schema_version":"backend-v1","strength":"STRONG"}'}];
    data.context.findings=[{id:'finding:1',text:'Thời khí đang nâng đỡ yếu tố trọng tâm.',fact_refs:['f1']}];
    data.context.evidence[0].text='{"internal_field":"do not show"}';
    const s=setup(async()=>ok(data));s.api.mount(s.root,{...request,method});await tick();
    assert.match(s.root.textContent,/Thời khí đang nâng đỡ/);
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
