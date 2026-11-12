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
  if(!legacy)saved.reading={...saved.reading,topic:'STUDY',topic_name:'Học tập',narrative_version:'bazi-tinix-narrative-v1',title:'Bát Tự · Học tập',
    summary:'Chưa xác định cách học phù hợp nhất từ lá số này.',sections:[
      {title:'Bạn có thể làm gì?',text:'Bạn có thể tự giải một bài khi đóng tài liệu rồi kiểm tra lỗi.',finding_refs:['strength']},
      {title:'Cần nhớ',text:'Gợi ý để tự thử, không phải dự báo từ ngày sinh.',finding_refs:['strength']},
      ...saved.reading.sections]};
  el('bazi-birth').value='1994-10-08T05:00:00';el('bazi-topic').value='STUDY';
  const sandbox={window:{AIReading:{mount:(parent,request,options)=>{mounts.push({parent,request,options});return {destroy(){}};}}},
    document:{getElementById:el,createElement:tag=>new Node(tag)},Date,AbortController,setTimeout,clearTimeout,crypto:{randomUUID}};
  sandbox.window.ArcanaClient={fetch:async(url,options)=>{
    if(!options?.body) {
      const consultations=requests.some(row=>row.url.endsWith('/consultations')) ?
        [{request_id:requests[0].body.request_id,civil_datetime:saved.chart.civil_datetime,topic_name:saved.reading.topic_name}] : [];
      if(url.endsWith('/history'))return {ok:true,json:async()=>({consultations})};
      return {ok:true,json:async()=>({...saved,request_id:requests[0].body.request_id})};
    }
    const body=JSON.parse(options.body);requests.push({url,body});
    if(url.endsWith('/readings'))return {ok:true,json:async()=>({
      consultation_id:requests[0].body.request_id,reading_id:body.reading_id,
      reading:{...saved.reading,topic:body.topic,topic_name:'Công việc',summary:'Lời luận công việc của cùng lá số.'},
    })};
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
test('Bazi starts the overview and immediately makes the signed topic reading available',async()=>{
  const s=setup(),before=JSON.stringify(s.saved);
  s.el('bazi-form').handlers.submit({preventDefault(){}});await tick();await tick();
  const root=s.el('bazi-result'),visible=visibleText(root);
  assert.match(visible,/Chưa xác định cách học phù hợp nhất.*tự giải một bài khi đóng tài liệu/);
  const reference=root.children.find(n=>n.className==='bazi-reference-tools'),chart=reference.find('details')[0];
  assert.equal(chart.tag,'details');assert.equal(Boolean(chart.open),false);
  assert.equal(chart.find('table').length,1);assert.equal(chart.find('dt').length,0);
  const dialog=root.find('dialog')[0];assert.equal(dialog.find('dt').length,8);
  assert.match(dialog.textContent,/Nhật chủ.*Ký hiệu của ngày sinh/);
  assert.equal(s.mounts.length,1);
  assert.equal(s.mounts[0].request.bazi_scope,'OVERVIEW');
  assert.equal(s.mounts[0].request.consultation_id,s.requests[0].body.request_id);
  assert.equal(s.mounts[0].options.autoGenerate,true);
  assert.ok(root.children.indexOf(s.mounts[0].parent)<root.children.indexOf(reference));
  assert.equal(JSON.stringify(s.saved),before);
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
test('opening the same historical Bazi result keeps the existing overview',async()=>{
  const s=setup(true);
  s.el('bazi-form').handlers.submit({preventDefault(){}});await tick();await tick();
  await s.el('bazi-history-list').find('button')[0].handlers.click();
  const root=s.el('bazi-result');
  assert.equal(root.find('details').length,3);
  assert.doesNotMatch(root.textContent,/Đọc giải thích và căn cứ của từng phần|Vì sao có nhận định này/);
  assert.equal(s.mounts.length,1);
  assert.match(root.textContent,/Nhật chủ Đinh/);
  assert.equal(s.requests.length,1);
});

test('changing only the topic reads the same chart and preserves the overview',async()=>{
  const s=setup();
  s.el('bazi-form').handlers.submit({preventDefault(){}});await tick();await tick();
  s.el('bazi-topic').value='CAREER';
  s.el('bazi-form').handlers.submit({preventDefault(){}});await tick();await tick();
  assert.equal(s.requests.length,2);
  assert.equal(s.requests[1].url,'/api/v1/bazi/consultations/'+s.requests[0].body.request_id+'/readings');
  assert.equal(s.requests[1].body.topic,'CAREER');
  assert.match(s.el('bazi-result').textContent,/Lời luận công việc của cùng lá số/);
  assert.equal(s.mounts.length,1);
  assert.ok(s.el('bazi-result').children.includes(s.mounts[0].parent));
});
