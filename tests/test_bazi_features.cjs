const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const {analyze}=require('../vendor/tinix-bazi/runner.cjs');
const result=analyze({birth:{year:1994,month:10,day:8,hour:6,isFemale:false,isSolar:true},
  pillars:['甲戌','癸酉','丁卯','癸卯'],target_year:2026,reference_time:'2026-07-01T12:00:00+07:00'});
function setup(){
  class Node{
    constructor(tag){this.tag=tag;this.children=[];this.attributes={};this.handlers={};this.isConnected=true;this.value='';}
    appendChild(node){this.children.push(node);node.parent=this;return node;}
    set textContent(value){this._text=String(value);this.children=[];}
    get textContent(){return (this._text||'')+this.children.map(n=>n.textContent).join(' ');}
    replaceChildren(){this._text='';this.children=[];}
    setAttribute(key,value){this.attributes[key]=String(value);}
    addEventListener(key,handler){this.handlers[key]=handler;}
    remove(){this.parent.children=this.parent.children.filter(n=>n!==this);}
    focus(){this.focused=true;}
    click(){this.handlers.click?.();}
    find(tag){return this.children.flatMap(n=>[...(n.tag===tag?[n]:[]),...n.find(tag)]);}
  }
  const root=new Node('main'),mounts=[],requests=[],readings=[{reading_id:'profile',reading:{topic_name:'Tổng quan',question:''}}];
  const session=JSON.parse(fs.readFileSync('examples/bazi_consultation_response.json','utf8'));
  session.request_id='profile';session.engine={result,commit:'80ff4463d0397c1b11db76f38d880255f55558bc',gender:'male',target_year:2026};
  const sandbox={document:{createElement:tag=>new Node(tag),createElementNS:(namespace,tag)=>{const n=new Node(tag);n.namespaceURI=namespace;return n;}},
    window:{AIReading:{mount:(parent,request,options)=>{const record={parent,request,options,destroyed:false};mounts.push(record);return {destroy(){record.destroyed=true;}};}},
      ArcanaClient:{fetch:async(path,options={})=>{
        const body=options.body?JSON.parse(options.body):null;requests.push({path,body});
        if(body){const saved={...body,consultation_id:'profile',reading:{topic_name:body.topic,question:body.question}};readings.push(saved);return {ok:true,json:async()=>saved};}
        return {ok:true,json:async()=>({readings})};
      }}}};
  vm.runInNewContext(fs.readFileSync('web/display_text.js','utf8'),sandbox);
  vm.runInNewContext(fs.readFileSync('web/bazi_features.js','utf8'),sandbox);
  sandbox.window.BaziFeatures.mount(root,session);
  return {root,mounts,requests,renderIdentity:session=>sandbox.window.BaziFeatures.renderIdentity(root,session)};
}
test('September first 1994 labels year Na Yin and day master independently',()=>{
  const result=analyze({birth:{year:1994,month:9,day:1,hour:8,isFemale:false,isSolar:true},
    pillars:['甲戌','壬申','庚寅','庚辰'],target_year:2026,reference_time:'2026-07-01T12:00:00+07:00'});
  const s=setup();
  const block=s.renderIdentity({engine:{result},chart:{pillars:[{stem:{name:'Giáp'},branch:'Tuất'},
    {},{stem:{name:'Canh',polarity:'Dương',element:'Kim'}}]}});
  const values=block.find('dd').map(n=>n.textContent);
  assert.equal(values[0],'Giáp Tuất · Sơn Đầu Hỏa');
  assert.equal(values[1],'Canh · Dương Kim');
  assert.equal(block.attributes['aria-label'],'Mệnh năm sinh và Nhật chủ');
  assert.match(block.textContent,/Mệnh năm sinh.*Nạp âm.*Sơn Đầu Hỏa.*Nhật chủ Bát Tự.*Can ngày.*Canh.*Kim/);
});
test('engine chart renders an accessible radar with numerical fallback and keyboard tabs',()=>{
  const s=setup(),tabs=s.root.find('button').filter(n=>n.attributes.role==='tab');
  assert.deepEqual(tabs.map(n=>n.textContent),['Lá số & Ngũ Hành','Đại vận & Lưu niên','Phân tích & điển tích']);
  assert.equal(tabs.length,3);assert.equal(s.root.find('svg').length,1);
  assert.equal(s.root.find('svg')[0].attributes.role,'img');assert.equal(s.root.find('table').length,2);
  assert.match(s.root.textContent,/Kim.*18.*30.0%/);
  tabs[0].handlers.keydown({key:'ArrowRight',preventDefault(){}});
  assert.equal(tabs[1].attributes['aria-selected'],'true');assert.equal(tabs[1].focused,true);
  assert.equal(s.mounts.length,0);assert.equal(s.requests.length,0);
});
test('cycles and source matrices expand lazily while source markup stays text',()=>{
  const s=setup(),tabs=s.root.find('button').filter(n=>n.attributes.role==='tab');tabs[1].click();
  const cycle=s.root.find('details').find(n=>n.children[0].textContent.includes('2003–2012'));
  assert.ok(cycle);assert.equal(cycle.find('table').length,0);
  cycle.open=true;cycle.handlers.toggle();assert.equal(cycle.find('table').length,1);
  assert.equal(cycle.find('details').length,10);
  tabs[2].click();const matrix=s.root.find('details').find(n=>n.children[0].textContent==='Quan hệ Can Chi');
  matrix.open=true;matrix.handlers.toggle();assert.equal(matrix.find('table').length,2);
  assert.equal(s.root.find('script').length,0);assert.doesNotMatch(matrix.textContent,/[{}]|<br/);
});
