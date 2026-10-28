const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const {randomUUID}=require('node:crypto');
class Node {
  constructor(tag){this.tag=tag;this.children=[];this.attributes={};this.handlers={};this.isConnected=true;}
  appendChild(n){this.children.push(n);return n;}
  replaceChildren(){this.children=[];this.value='';}
  setAttribute(k,v){this.attributes[k]=v;}
  addEventListener(k,v){this.handlers[k]=v;}
  set textContent(v){this.value=String(v);this.children=[];}
  get textContent(){return (this.value||'')+this.children.map(n=>n.textContent).join(' ');}
  find(tag){return this.children.flatMap(n=>[...(n.tag===tag?[n]:[]),...n.find(tag)]);}
}
const tick=()=>new Promise(r=>setImmediate(r));
const query={activity:'BUSINESS_OPENING',date_range:{start:'2026-10-13',end:'2026-10-13'}};
const result=request=>({request_id:request.request_id,result:{activity:request.search.activity,evaluation_mode:'DAY_AND_HOUR',days:[{date:request.search.date_range.start}]},
  explanation:{summary:'Lý do chọn ngày theo việc',reasons:['Lịch ngày hỗ trợ','Đối chiếu hồ sơ'],cautions:['Chỉ dùng khung được khuyến nghị']}});
function setup(responder){
  const calls=[],mounts=[];
  const sandbox={window:{AIReading:{mount:(node,req,opts)=>{const record={node,req,opts,destroyed:false};mounts.push(record);return {destroy(){record.destroyed=true;}};}}},
    document:{createElement:tag=>new Node(tag)},crypto:{randomUUID},AbortController,
    fetch:async(url,opts)=>{const body=JSON.parse(opts.body);calls.push({url,body});return responder(body,calls.length);}};
  sandbox.window.ArcanaClient={fetch:(...args)=>sandbox.fetch(...args)};
  vm.runInNewContext(fs.readFileSync('web/display_text.js','utf8'),sandbox);
  vm.runInNewContext(fs.readFileSync('web/date_reading.js','utf8'),sandbox);
  return {api:sandbox.window.DateReading,root:new Node('section'),calls,mounts};
}
const ok=body=>({ok:true,json:async()=>body});
test('date reasons are visible before AI, with no automatic paid generation',async()=>{
  const s=setup(async req=>ok(result(req)));let loaded;
  s.api.mount(s.root,query,{onLoad:d=>{loaded=d;}});await tick();
  assert.match(s.root.textContent,/Lý do chọn ngày theo việc/);
  assert.match(s.root.textContent,/Đối chiếu hồ sơ/);
  assert.equal(s.calls.length,1);assert.match(s.calls[0].url,/auspicious-dates\/consultations$/);
  assert.equal(s.mounts[0].req.method,'DATE');assert.equal(s.mounts[0].req.consultation_id,loaded.request_id);
  assert.equal(s.mounts[0].opts.autoGenerate,undefined);
});
test('same day and same filters reuse the saved consultation, another activity does not',async()=>{
  const s=setup(async req=>ok(result(req)));
  const first=s.api.mount(s.root,query);await tick();first.destroy();
  s.api.mount(s.root,JSON.parse(JSON.stringify(query)));await tick();
  s.api.mount(new Node('section'),{...query,activity:'LAND_BREAKING'});await tick();
  assert.equal(s.calls[0].body.request_id,s.calls[1].body.request_id);
  assert.notEqual(s.calls[0].body.request_id,s.calls[2].body.request_id);
  assert.equal(s.mounts[0].destroyed,true);
});
test('closed date popups discard pending results',async()=>{
  let resolve;const s=setup(()=>new Promise(r=>{resolve=r;}));
  const handle=s.api.mount(s.root,query);handle.destroy();resolve(ok(result(s.calls[0].body)));await tick();
  assert.equal(s.mounts.length,0);assert.doesNotMatch(s.root.textContent,/Lý do chọn ngày theo việc/);
});
test('day-only scopes are explicit and mismatched results never mount AI',async()=>{
  const s=setup(async req=>{const data=result(req);data.result.evaluation_mode='DAY_ONLY';return ok(data);});
  s.api.mount(s.root,query);await tick();assert.match(s.root.textContent,/chưa chọn giờ đẹp/);
  const bad=setup(async req=>{const data=result(req);data.result.days[0].date='2026-10-14';return ok(data);});
  bad.api.mount(bad.root,query);await tick();
  assert.match(bad.root.textContent,/không khớp/);assert.equal(bad.mounts.length,0);
});
test('retry preserves the request ID and error text stays plain',async()=>{
  const s=setup(async(req,n)=>n===1?{ok:false,json:async()=>({error:{message:'<b>Không tải được</b>'}})}:ok(result(req)));
  s.api.mount(s.root,query);await tick();assert.match(s.root.textContent,/Chưa tải được căn cứ/);assert.doesNotMatch(s.root.textContent,/<b>/);assert.equal(s.root.find('b').length,0);
  s.root.find('button')[0].handlers.click();await tick();
  assert.equal(s.calls[0].body.request_id,s.calls[1].body.request_id);assert.equal(s.mounts.length,1);
});
