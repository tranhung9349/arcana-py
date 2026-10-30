const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const {randomUUID}=require('node:crypto');
const tick=()=>new Promise(resolve=>setImmediate(resolve));
const ok=data=>({ok:true,json:async()=>data});
const names=Array.from({length:64},(_,i)=>({hexagram_id:i+1,name_vi:i===0?'Thuần Càn':'Quẻ '+(i+1),name_zh:String(i+1),symbol:'䷀'}));
function reading(id){
  const value=JSON.parse(fs.readFileSync('examples/coin_consultation_response.json','utf8')).original;
  value.chart.hexagram_id=id;value.chart.name_vi=id===1?'Thuần Càn':'Quẻ '+id;return value;
}
function setup(responder,{realLiuyao=false}={}){
  const ids=new Map(),calls=[],resets=[];
  class Node {
    constructor(tag='div'){this.tag=tag;this.children=[];this.handlers={};this.attributes={};this.dataset={};this.elements=[];this.value='';this.isConnected=true;this.classList={add(){}};}
    set id(value){this._id=value;ids.set(value,this);} get id(){return this._id;}
    appendChild(node){this.children.push(node);return node;}
    replaceChildren(...nodes){this.children=nodes;this._text='';}
    set textContent(value){this._text=String(value);this.children=[];}
    get textContent(){return (this._text||'')+this.children.map(n=>n.textContent).join(' ');}
    setAttribute(key,value){this.attributes[key]=value;}
    getAttribute(key){return this.attributes[key]??null;}
    addEventListener(key,fn){(this.handlers[key]||=[]).push(fn);}
    async fire(key){for(const fn of this.handlers[key]||[])await fn({preventDefault(){}});}
    click(){return this.fire('click');}
    querySelectorAll(){return [];}
    focus(){this.focused=true;}
    scrollIntoView(){}
  }
  const el=id=>{if(!ids.has(id)){const n=new Node();n.id=id;}return ids.get(id);};
  const sandbox={window:{CoinIntent:{attach:()=>({ensure:async()=>({topic:'CAREER'}),restore(){},destroy(){}})},LiuYaoPanel:{reset:()=>resets.push(true),mount(){}}},
    document:{getElementById:el,createElement:tag=>new Node(tag),createTextNode:value=>{const n=new Node('text');n.textContent=value;return n;}},
    AbortController,AbortSignal,Date,crypto:{randomUUID},setTimeout,clearTimeout};
  sandbox.window.ArcanaClient={fetch:async(url,options={})=>{
    calls.push({url,options});
    if(url==='/api/v2/auspicious-dates/rules')return ok({groups:[{group_id:'BUSINESS_ASSETS',name:'Kinh doanh'}],activities:[]});
    return responder?responder(url,options):ok(url.endsWith('/hexagrams')?{hexagrams:names}:reading(Number(url.split('/').at(-1))));
  }};
  if(realLiuyao){
    sandbox.window.AIReading={mount(parent){parent.textContent='Bài AI chưa sẵn sàng. Thử lại phần luận.';return {destroy(){}};}};
    vm.runInNewContext(fs.readFileSync('web/liuyao.js','utf8'),sandbox);
  }
  for(const file of ['display_text.js','dates.js','coins.js','arcana_ui.js'])vm.runInNewContext(fs.readFileSync('web/'+file,'utf8'),sandbox);
  return {el,calls,resets};
}
test('the library is an independent Kinh Dich submenu and the selected submenu survives leaving Kinh Dich',async()=>{
  const s=setup();await tick();
  await s.el('show-iching').click();await tick();
  assert.equal(s.el('coins-workspace').hidden,false);assert.equal(s.el('library-workspace').hidden,true);
  assert.equal(s.calls.filter(c=>c.url.includes('/hexagrams')).length,0);
  await s.el('show-library').click();await tick();
  assert.equal(s.el('library-workspace').hidden,false);assert.equal(s.el('coins-workspace').hidden,true);
  assert.equal(s.el('show-library').getAttribute('aria-pressed'),'true');
  assert.equal(s.el('show-iching').getAttribute('aria-pressed'),'true');
  assert.match(s.el('workspace-title').textContent,/Khám phá 64 quẻ/);
  await s.el('show-bazi').click();await s.el('show-iching').click();await tick();
  assert.equal(s.el('library-workspace').hidden,false);assert.equal(s.el('iching-methods').hidden,false);
  assert.match(s.el('workspace-title').textContent,/Khám phá 64 quẻ/);
  assert.equal(s.calls.filter(c=>c.url.endsWith('/hexagrams')).length,1);
});
test('when AI is unavailable, technical analysis and advanced controls stay inside one closed reference area',async()=>{
  const coin=JSON.parse(fs.readFileSync('examples/coin_consultation_response.json','utf8'));
  const analysis=JSON.parse(fs.readFileSync('examples/liuyao_analysis_response.json','utf8'));
  const before=JSON.stringify(coin);
  const s=setup((url,options)=>{
    if(url==='/api/v1/coins/consultations'){
      const request=JSON.parse(options.body);coin.request_id=request.request_id;coin.question=request.question;analysis.session_id=request.request_id;return ok(coin);
    }
    if(url.endsWith('/analysis-rules'))return ok({topics:{CAREER:{label:'Công việc'}}});
    if(url.endsWith('/analysis'))return ok(analysis);
    return ok({});
  },{realLiuyao:true});
  s.el('coins-source').value='RANDOM';s.el('coins-time-mode').value='CURRENT';s.el('coins-question').value='Công việc hiện tại sẽ ra sao?';
  await s.el('coins-form').fire('submit');await tick();await tick();
  const root=s.el('coins-result'),references=root.children.filter(n=>n.tag==='details');
  assert.equal(references.length,1);
  assert.equal(references[0].children[0].textContent,'Chi tiết quẻ và nguồn tham khảo');
  assert.ok(!references[0].open);
  function all(n){return [n,...n.children.flatMap(all)];}
  const nodes=all(references[0]);
  assert.ok(nodes.some(n=>n.className==='ly-technical'));
  assert.ok(nodes.some(n=>n.className==='ly-controls'));
  assert.ok(nodes.some(n=>n.className==='coins-table'));
  const main=root.children.find(n=>n.className==='ly-panel');
  const casting=root.children.find(n=>n.className==='coins-cast-result');
  const charts=root.children.find(n=>n.className==='coins-hexagrams');
  assert.ok(root.children.indexOf(casting)<root.children.indexOf(charts));
  assert.ok(root.children.indexOf(charts)<root.children.indexOf(main));
  assert.equal(all(casting).filter(n=>n.className==='coins-throw-card').length,6);
  assert.equal(all(casting).filter(n=>n.attributes['aria-label']?.match(/điểm$/)).length,18);
  assert.match(main.textContent,/Bài AI chưa sẵn sàng/);
  assert.doesNotMatch(main.textContent,/Dụng thần|Quan quỷ|Nhật–Nguyệt|Nạp Giáp/);
  assert.equal(coin.original.chart.hexagram_id,JSON.parse(before).original.chart.hexagram_id);
  assert.equal(JSON.stringify(coin.casting),JSON.stringify(JSON.parse(before).casting));
});
test('casting always uses automatic coins and current time, and retry preserves the original request',async()=>{
  const requests=[];
  const s=setup((url,options)=>{
    if(url==='/api/v1/coins/consultations'){
      requests.push(JSON.parse(options.body));
      if(requests.length===1)throw new Error('connection interrupted');
      const result=JSON.parse(fs.readFileSync('examples/coin_consultation_response.json','utf8'));
      result.request_id=requests[1].request_id;return ok(result);
    }
    return ok({});
  });
  s.el('coins-topic').value='CAREER';s.el('coins-question').value='Công việc cần lưu ý điều gì?';
  // A stale client-side value must not switch back to manual/custom casting.
  s.el('coins-source').value='MANUAL';s.el('coins-time-mode').value='CUSTOM';
  await s.el('coins-form').fire('submit');await tick();
  assert.equal(requests[0].source,'RANDOM');assert.equal(requests[0].casting.mode,'CURRENT');
  assert.ok(Number.isFinite(Date.parse(requests[0].casting.clicked_at)));
  assert.match(requests[0].casting.clicked_at,/\+07:00$/);
  assert.ok(Math.abs(Date.parse(requests[0].casting.clicked_at)-Date.now())<2000);
  assert.equal(requests[0].throws_bottom_to_top,undefined);
  assert.equal(requests[0].casting.custom_timestamp,undefined);
  await s.el('coins-retry').click();await tick();
  assert.deepEqual(requests[1],requests[0]);
  assert.equal(s.el('coins-submit').textContent,'Gieo và lập quẻ');
  const html=fs.readFileSync('web/index.html','utf8');
  for(const id of ['coins-source','coins-time-mode','coins-custom-time','coins-manual'])assert.ok(!html.includes('id="'+id+'"'));
});
test('opening a reference uses its own result, preserves the casting and returns to the filtered list',async()=>{
  const s=setup();await s.el('show-library').click();await tick();
  s.el('coins-result').textContent='Lời luận của phiên đã gieo';
  s.el('coins-search').value='thuan can';await s.el('coins-search').fire('input');
  assert.equal(s.el('coins-catalog').children.length,1);
  await s.el('coins-catalog').children[0].click();await tick();
  assert.match(s.el('library-result').textContent,/Thuần Càn/);
  assert.equal(s.el('library-result').hidden,false);
  assert.equal(s.el('coins-result').textContent,'Lời luận của phiên đã gieo');
  assert.equal(s.resets.length,0);
  assert.equal(s.el('library-result-title').focused,true);
  await s.el('library-back').click();
  assert.equal(s.el('library-detail').hidden,true);assert.equal(s.el('library-catalog-panel').hidden,false);
  assert.equal(s.el('coins-search').value,'thuan can');assert.equal(s.el('coins-search').focused,true);
  assert.equal(s.el('coins-catalog').children.length,1);
  assert.ok(s.calls.every(c=>!c.options.method || c.options.method==='GET'));
});
test('back cancels pending reference output without touching an existing casting',async()=>{
  let resolve;
  const s=setup(url=>url.endsWith('/hexagrams')?ok({hexagrams:names}):new Promise(r=>{resolve=r;}));
  await s.el('show-library').click();await tick();
  s.el('coins-result').textContent='Phiên gieo còn nguyên';
  const pending=s.el('coins-catalog').children[0].click();await tick();
  await s.el('library-back').click();resolve(ok(reading(1)));await pending;await tick();
  assert.equal(s.el('library-detail').hidden,true);assert.equal(s.el('library-result').hidden,true);
  assert.equal(s.el('coins-result').textContent,'Phiên gieo còn nguyên');assert.equal(s.resets.length,0);
});
test('reference lookup does not cancel a casting request or receive its result',async()=>{
  let resolve,request;
  const s=setup((url,options)=>{
    if(options.method==='POST'){request=JSON.parse(options.body);return new Promise(r=>{resolve=r;});}
    return ok(url.endsWith('/hexagrams')?{hexagrams:names}:reading(1));
  });
  s.el('coins-source').value='RANDOM';s.el('coins-time-mode').value='CURRENT';s.el('coins-question').value='Một câu hỏi của phiên gieo';
  const posting=s.el('coins-form').fire('submit');await tick();
  const cast=s.calls.find(c=>c.options.method==='POST');assert.ok(cast);
  await s.el('show-library').click();await tick();
  await s.el('coins-catalog').children[0].click();await tick();
  assert.equal(cast.options.signal.aborted,false);assert.match(s.el('library-result').textContent,/Thuần Càn/);
  const result=JSON.parse(fs.readFileSync('examples/coin_consultation_response.json','utf8'));
  result.request_id=request.request_id;result.question=request.question;resolve(ok(result));await posting;await tick();
  assert.ok(s.el('coins-result').textContent.includes(request.question));
  assert.match(s.el('library-result').textContent,/Thuần Càn/);
  assert.equal(s.el('library-workspace').hidden,false);
});
test('malformed catalog and reference output can retry without exposing diagnostics',async()=>{
  let catalogs=0,details=0;
  const s=setup(url=>url.endsWith('/hexagrams')?ok(++catalogs===1?{properties:{debug:'private'}}:{hexagrams:names}):
    ok(++details===1?{chart:{hexagram_id:1},properties:{debug:'private'}}:reading(1)));
  await s.el('show-library').click();await tick();
  assert.equal(s.el('coins-catalog-retry').hidden,false);
  await s.el('coins-catalog-retry').click();await tick();assert.equal(s.el('coins-catalog').children.length,64);
  await s.el('coins-catalog').children[0].click();await tick();
  assert.equal(s.el('library-result').hidden,true);assert.equal(s.el('library-retry').hidden,false);
  assert.doesNotMatch(s.el('library-error').textContent,/properties|private|TypeError/);
  await s.el('library-retry').click();await tick();assert.equal(s.el('library-result').hidden,false);
});
