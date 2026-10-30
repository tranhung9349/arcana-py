const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const {randomUUID}=require('node:crypto');
const tick=()=>new Promise(r=>setImmediate(r));

function setup(legacy=false){
  const ids=new Map(),mounts=[],requests=[];
  class Node {
    constructor(tag='div'){this.tag=tag;this.children=[];this.attributes={};this.handlers={};this.dataset={};this.value='';this.elements=[];this.isConnected=true;}
    set id(value){this._id=value;ids.set(value,this);} get id(){return this._id;}
    appendChild(n){this.children.push(n);return n;}
    replaceChildren(){this.children=[];this.value='';}
    set textContent(v){this._text=String(v);this.children=[];}
    get textContent(){return (this._text||'')+this.children.map(n=>n.textContent).join(' ');}
    setAttribute(k,v){this.attributes[k]=v;}
    addEventListener(k,fn){this.handlers[k]=fn;}
    focus(){this.focused=true;}
    showModal(){this.open=true;}
    close(){this.open=false;this.handlers.close?.();}
    find(tag){return this.children.flatMap(n=>[...(n.tag===tag?[n]:[]),...n.find(tag)]);}
  }
  const el=id=>{if(!ids.has(id)){const n=new Node();n.id=id;}return ids.get(id);};
  const saved=JSON.parse(fs.readFileSync('examples/bazi_consultation_response.json','utf8'));
  if(!legacy)saved.reading={...saved.reading,narrative_version:'bazi-narrative-2026-10-28-v2',title:'Bát Tự · Học tập',
    summary:'Chưa xác định cách học phù hợp nhất từ lá số này.',sections:[
      {title:'Bạn có thể làm gì?',text:'Bạn có thể tự giải một bài khi đóng tài liệu rồi kiểm tra lỗi.',finding_refs:['strength']},
      {title:'Cần nhớ',text:'Gợi ý để tự thử, không phải dự báo từ ngày sinh.',finding_refs:['strength']},
      ...saved.reading.sections]};
  el('bazi-birth').value='1994-10-08T05:00:00';el('bazi-topic').value='STUDY';
  const sandbox={window:{AIReading:{mount:(parent,request,options)=>{mounts.push({parent,request,options});return {destroy(){}};}}},
    document:{getElementById:el,createElement:tag=>new Node(tag)},Date,AbortController,setTimeout,clearTimeout,crypto:{randomUUID}};
  sandbox.window.ArcanaClient={fetch:async(url,options)=>{
    const body=JSON.parse(options.body);requests.push({url,body});
    return {ok:true,json:async()=>({...saved,request_id:body.request_id})};
  }};
  vm.runInNewContext(fs.readFileSync('web/display_text.js','utf8'),sandbox);
  vm.runInNewContext(fs.readFileSync('web/bazi.js','utf8'),sandbox);
  return {el,saved,mounts,requests};
}
function visibleText(node){
  if(node.hidden || (['details','dialog'].includes(node.tag) && !node.open))return '';
  return (node._text||'')+' '+node.children.map(visibleText).join(' ');
}
test('Bazi opens the final article automatically without showing the native boilerplate',async()=>{
  const s=setup(),before=JSON.stringify(s.saved);
  s.el('bazi-form').handlers.submit({preventDefault(){}});await tick();await tick();
  const root=s.el('bazi-result'),visible=visibleText(root);
  assert.doesNotMatch(root.textContent,/Bạn nên hiểu kết quả này thế nào|Bạn có thể làm gì|Chưa xác định cách học phù hợp nhất|tự giải một bài khi đóng tài liệu|Gợi ý để tự thử/);
  assert.doesNotMatch(visible,/Nhật chủ|Tàng can|Thập Thần|phù ức|nguyệt lệnh/);
  const reference=root.children.find(n=>n.className==='bazi-reference-tools'),chart=reference.find('details')[0];
  assert.equal(chart.tag,'details');assert.equal(Boolean(chart.open),false);
  assert.equal(chart.find('table').length,1);assert.equal(chart.find('dt').length,0);
  const dialog=root.find('dialog')[0];assert.equal(dialog.find('dt').length,8);
  assert.match(dialog.textContent,/Nhật chủ.*Ký hiệu của ngày sinh/);
  const article=s.mounts[0].parent;
  assert.ok(root.children.indexOf(article)<root.children.indexOf(reference));
  assert.equal(s.mounts.length,1);assert.equal(s.mounts[0].options.autoGenerate,true);
  assert.equal(s.mounts[0].request.consultation_id,s.requests[0].body.request_id);
  assert.equal(JSON.stringify(s.saved),before);
  s.mounts[0].options.onLoad();
  assert.equal(s.el('bazi-progress').textContent,'Đã có bài luận.');
});
test('Bazi removes the name and extra reading controls; glossary opens separately and restores focus',async()=>{
  const s=setup();s.el('bazi-form').handlers.submit({preventDefault(){}});await tick();await tick();
  const root=s.el('bazi-result'),help=root.find('button').find(n=>n.className==='bazi-glossary-trigger'),dialog=root.find('dialog')[0];
  assert.equal(Object.hasOwn(s.requests[0].body,'display_name'),false);
  assert.doesNotMatch(fs.readFileSync('web/index.html','utf8'),/id="bazi-name"/);
  assert.doesNotMatch(root.textContent,/Đọc thêm trên cùng lá số|Các bài luận trong phiên|Phạm vi và phương pháp luận|Đọc giải thích và căn cứ của từng phần|Vì sao có nhận định này/);
  assert.equal(root.find('form').length,0);assert.equal(dialog.attributes['aria-labelledby'],'bazi-glossary-title');
  help.handlers.click();assert.equal(dialog.open,true);assert.equal(help.attributes['aria-expanded'],'true');
  dialog.find('button')[0].handlers.click();assert.equal(dialog.open,false);assert.equal(help.focused,true);
  assert.equal(help.attributes['aria-expanded'],'false');assert.equal(s.requests.length,1);
});
test('historical Bazi results also omit the technical explanation',async()=>{
  const s=setup(true);
  s.el('bazi-form').handlers.submit({preventDefault(){}});await tick();await tick();
  const root=s.el('bazi-result');
  assert.equal(root.find('details').length,2);
  assert.doesNotMatch(root.textContent,/Đọc giải thích và căn cứ của từng phần|Vì sao có nhận định này/);
  assert.equal(s.mounts.length,1);
});
