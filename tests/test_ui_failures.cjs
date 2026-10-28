/* Exercise each real screen controller with backend and transport failures. */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const {randomUUID}=require('node:crypto');
class Node {
  constructor(tag='div'){this.tag=tag;this.children=[];this.handlers={};this.attributes={};this.dataset={};this.value='';this.isConnected=true;this.elements=[];this.classList={add(){},remove(){}};}
  appendChild(n){this.children.push(n);return n;}
  insertBefore(n){this.children.unshift(n);return n;}
  replaceChildren(){this.children=[];this._text='';}
  set textContent(v){this._text=String(v);this.children=[];}
  get textContent(){return (this._text||'')+this.children.map(n=>n.textContent).join(' ');}
  setAttribute(k,v){this.attributes[k]=v;}
  addEventListener(k,fn){(this.handlers[k] ||= []).push(fn);}
  removeEventListener(){}
  async fire(k){for(const fn of this.handlers[k]||[])await fn({preventDefault(){},key:'',target:this});}
  click(){return this.fire('click');}
  querySelectorAll(){return [];}
  focus(){}
  scrollIntoView(){}
}
const tick=()=>new Promise(r=>setImmediate(r));
const ok=data=>({ok:true,json:async()=>data});
const attacks=[
  {ok:false,json:async()=>({error:{message:'{"schema_version":"backend-v1","trace":"private"}',fields:[{field:'body.birth.civil_datetime',message:'ValidationError'}]}})},
  {ok:false,json:async()=>({error:{code:'VALIDATION_FAILED',message:'private',fields:[{field:'body.birth.civil_datetime',message:'Input should be datetime'}]}})},
  {ok:false,json:async()=>{throw new SyntaxError('Unexpected token <html> in JSON');}},
  {ok:true,json:async()=>({schema_version:'backend-diagnostic',properties:{trace:'private'}})},
];
function setup(script,attack){
  const nodes=new Map();
  const el=id=>{if(!nodes.has(id)){const n=new Node();n.id=id;nodes.set(id,n);}return nodes.get(id);};
  for(const id of ['birth-date','bazi-birth','date-birth-1'])el(id).value='1994-10-08T05:00:00';
  for(const id of ['custom-date','maihoa-custom-time','coins-custom-time'])el(id).value='2026-10-13T08:00:00';
  el('date-start').value='2026-10-13';el('date-end').value='2026-10-13';
  el('date-hour-start').value='06:00';el('date-hour-end').value='22:00';
  el('coins-question').value='Công việc sắp tới nên chú ý gì?';el('coins-topic').value='CAREER';
  el('maihoa-question').value='Công việc sắp tới nên chú ý gì?';el('maihoa-topic').value='GENERAL';
  const calls=[];
  const sandbox={window:{CoinIntent:{attach:()=>({ensure:async()=>({topic:'CAREER'}),restore(){},destroy(){}})}},
    document:{getElementById:el,createElement:t=>new Node(t),querySelectorAll:()=>[],body:new Node('body')},
    AbortController,AbortSignal,DOMException,Date,setTimeout,clearTimeout,crypto:{randomUUID},
    fetch:async(url,opts)=>{
      calls.push(url);
      if(url==='/api/v1/history')return ok({draws:[]});
      if(url==='/api/v2/auspicious-dates/rules')return ok({groups:[{group_id:'BUSINESS_ASSETS',name:'Kinh doanh'}],
        activities:[{activity:'BUSINESS_OPENING',enabled:true,group_id:'BUSINESS_ASSETS',name:'Khai trương',subject_count:1,subject_roles:['Gia chủ'],hour_evaluation_mode:'DAY_AND_HOUR',event_anchor:'Bắt đầu đón khách',scope_note:'Xét thời điểm bắt đầu.'}]});
      return attack;
    }};
  sandbox.window.ArcanaClient={fetch:(...args)=>sandbox.fetch(...args)};
  vm.runInNewContext(fs.readFileSync('web/display_text.js','utf8'),sandbox);
  vm.runInNewContext(fs.readFileSync('web/'+script,'utf8'),sandbox);
  return {el,calls,sandbox};
}
for(const [script,form,error] of [['app.js','draw-form','error'],['dates.js','date-form','date-error'],
  ['maihoa.js','maihoa-form','maihoa-error'],['bazi.js','bazi-form','bazi-error'],['coins.js','coins-form','coins-error']]) {
  test(script+' hides backend schema, raw validation fields, parser errors and malformed success responses',async()=>{
    for(const attack of attacks) {
      const s=setup(script,attack);await tick();
      if(script==='dates.js'){s.el('date-activity').value='BUSINESS_OPENING';}
      await s.el(form).fire('submit');await tick();
      assert.equal(s.el(error).hidden,false,script);
      assert.match(s.el(error).textContent,/Chưa|Vui lòng|Không thể|không khớp/);
      assert.doesNotMatch(s.el(error).textContent,/schema_version|properties|backend-|private|body\.|civil_datetime|ValidationError|SyntaxError|Unexpected|[{}<>]/);
    }
  });
}
test('Lục Hào rule loading and question-intent previews also hide backend diagnostics',async()=>{
  for(const attack of attacks.slice(0,3)) {
    const ly=setup('liuyao.js',attack),root=new Node('section');
    ly.sandbox.window.LiuYaoPanel.mount(root,{request_id:randomUUID(),question:'Hỏi công việc'});await tick();
    assert.match(root.textContent,/Chưa|Vui lòng/);
    assert.doesNotMatch(root.textContent,/schema_version|private|body\.|civil_datetime|ValidationError|Unexpected|[{}<>]/);
    ly.sandbox.window.LiuYaoPanel.reset();
    const intent=setup('coin_intent.js',attack),preview=new Node('section'),topic=new Node('select');topic.value='CAREER';
    const gate=intent.sandbox.window.CoinIntent.attach({container:preview,topic,question:()=> 'Tôi nên làm gì cho công việc?'});
    await tick();
    assert.match(preview.textContent,/Chưa nhận diện được/);
    assert.doesNotMatch(preview.textContent,/schema_version|private|body\.|civil_datetime|ValidationError|Unexpected|[{}<>]/);
    gate.destroy();
  }
});
