const $=id=>document.getElementById(id);
let pending=null;
let displayedRequestId=null,explanationAbort=null;
const vnNow=()=>new Date(Date.now()+7*3600000).toISOString().slice(0,-1)+'+07:00';
const civil=id=>{let value=$(id).value;if(value.length===16)value+=':00';return value+'+07:00';};
$('casting-mode').addEventListener('change',()=>{$('custom-field').hidden=$('casting-mode').value!=='CUSTOM';$('custom-date').required=$('casting-mode').value==='CUSTOM';});
function setBusy(busy){for(const field of $('draw-form').elements)field.disabled=busy;}
function appendText(parent,tag,value='',className){const item=document.createElement(tag);item.textContent=window.DisplayText.plain(value);if(className)item.className=className;parent.appendChild(item);return item;}
function renderNumberReading(result){
  const root=$('number-reading');root.replaceChildren();
  const reading=DrawReading.describe(result);if(!reading)return;
  const grid=appendText(root,'div','','draw-context-grid');
  for(const [label,title,body] of [
    ['TỪ HỒ SƠ SINH','Ưu tiên hành '+reading.primary,reading.birthText],
    ['TỪ QUẺ GIEO',reading.castingTitle,reading.castingText]
  ]){const card=appendText(grid,'article','','draw-context-card');appendText(card,'small',label);appendText(card,'h3',title);appendText(card,'p',body);}
  appendText(root,'h3','Dấu ấn của 6 con số','draw-reading-heading');
  appendText(root,'p',`${reading.even} số chẵn · ${reading.odd} số lẻ · ${reading.groups.length} hành hiện diện`,'draw-balance');
  const table=appendText(root,'table','','draw-element-table');
  const header=appendText(appendText(table,'thead',''),'tr','');
  for(const title of ['Ngũ hành','Các số trong bộ','Với hồ sơ · với quẻ'])appendText(header,'th',title);
  const body=appendText(table,'tbody','');
  for(const group of reading.groups){
    const row=appendText(body,'tr','');appendText(row,'th',group.element);
    appendText(row,'td',group.numbers.join(' · '),'draw-group-numbers');
    const relation=appendText(row,'td','');appendText(relation,'span',group.birthRelation+' · hồ sơ');appendText(relation,'span',group.castingRelation+' · quẻ');
  }
  if(reading.score){
    appendText(root,'h3','Điểm hài hòa đến từ đâu?','draw-reading-heading');
    const scores=appendText(root,'div','','draw-score-grid');
    for(const [label,raw,points,weight] of [
      ['Âm dương',reading.score.balance,reading.score.balancePoints,40],
      ['Ngũ hành',reading.score.elements,reading.score.elementPoints,60]
    ]){const card=appendText(scores,'div','');appendText(card,'small',label+' · '+weight+'%');appendText(card,'strong',points.toFixed(1)+' điểm');appendText(card,'span','Từ '+raw.toFixed(1)+'/100');}
  }
  if(reading.bonuses.length){
    const detail=appendText(root,'details','','draw-bonuses');appendText(detail,'summary','Yếu tố được ưu tiên khi chọn số');
    const list=appendText(detail,'ul','');
    for(const bonus of reading.bonuses)appendText(list,'li',bonus.label+': '+bonus.numbers.join(' · '));
    appendText(detail,'p','Những yếu tố này tác động vào cách chọn số; điểm hài hòa được tính từ Âm Dương và Ngũ Hành ở trên.');
  }
  appendText(root,'p',`Bộ số được chọn ở lượt ${reading.selectedAttempt} trong ${reading.attempts} lượt gieo của phiên này.`,'draw-selection');
}
function render(result){
  displayedRequestId=result.request_id;
  $('empty-result').hidden=true;$('result').hidden=false;$('numbers').replaceChildren();
  for(const n of result.numbers)appendText($('numbers'),'span',n);
  $('result-status').textContent=result.status==='OPTIMAL'?'Đạt ngưỡng':'Bộ hợp lệ tốt nhất';
  $('score').textContent=result.score.toFixed(1);$('threshold').textContent=window.DisplayText.plain(result.threshold);$('attempts').textContent=window.DisplayText.plain(result.attempts);$('disclaimer').textContent=DrawReading.caption;
  $('warnings').replaceChildren();for(const warning of result.warnings.filter(row=>row.code!=='BOUNDARY_UNCERTAINTY_UNKNOWN'))appendText($('warnings'),'p',(warning.context==='birth'?'Hồ sơ sinh: ':warning.context==='casting'?'Phiên gieo: ':'')+warning.message);
  renderNumberReading(result);
  window.ResultPDF?.mount($('result'),'Gieo số');

}
function sourceLink(parent,item){
  window.DisplayText.sourceLink(parent,'Nguồn: '+item.source.repository,item.source.url);
}
function sourceCard(parent,item){
  const article=appendText(parent,'article','','reading-card');appendText(article,'h3',item.title);
  if(item.language==='zh'){
    const columns=appendText(article,'div','','reading-columns');
    const original=appendText(columns,'div','','original-reading');appendText(original,'small','Nguyên văn Hán · open-iching','reading-label');appendText(original,'p',item.text,'source-text');sourceLink(original,item);
    if(item.translation){const translated=appendText(columns,'div','','translated-reading');appendText(translated,'small','Nghĩa Việt · bản nháp AI','reading-label');appendText(translated,'p',item.translation.text);}
  }else{appendText(article,'p',item.text);sourceLink(article,item);}
}
function renderModuleReading(root,reading){
  root.replaceChildren();
  const summary=appendText(root,'div','','deep-reading-summary');
  appendText(summary,'h3',reading.title);appendText(summary,'p',reading.summary);
  for(const section of reading.sections){
    const article=appendText(root,'article','','deep-reading-section');
    appendText(article,'h4',section.title);appendText(article,'p',section.text);
  }
  if(reading.limitations.length){
    const details=appendText(root,'details','','deep-reading-limits');appendText(details,'summary','Phạm vi của phần luận');
    for(const value of reading.limitations)appendText(details,'p',value);
  }
  const sources=reading.evidence.filter(row=>row.kind!=='SAVED_FACT');
  if(sources.length){
    const details=appendText(root,'details','');appendText(details,'summary','Căn cứ và nguồn đối chiếu');
    for(const item of sources){
      const article=appendText(details,'article','','reading-card');appendText(article,'h4',item.title);appendText(article,'p',item.text);
      if(item.url)window.DisplayText.sourceLink(article,'Đối chiếu nguồn',item.url);
    }
  }
}
function renderExplanation(data){
  if(!data.readings?.maihoa||!data.readings?.bazi)throw new Error('Chưa có phần luận của hai module.');
  renderModuleReading($('iching-reading'),data.readings.maihoa);
  renderModuleReading($('bazi-reading'),data.readings.bazi);
  const originals=appendText($('iching-reading'),'details','');appendText(originals,'summary','Quẻ từ và hào động để đối chiếu');
  for(const card of data.original.cards.filter(row=>row.translation))sourceCard(originals,card);
  $('explanation-content').hidden=false;
  $('explanation-status').textContent='';
}
async function loadExplanation(requestId){
  if(explanationAbort)explanationAbort.abort();
  const controller=new AbortController();explanationAbort=controller;
  const timer=setTimeout(()=>controller.abort(),20000);
  $('explanation-content').hidden=true;$('explanation-retry').hidden=true;
  $('explanation-status').textContent='Đang đọc phần giải thích của phiên…';
  try{
    const response=await window.ArcanaClient.fetch('/api/v1/interpretation/'+encodeURIComponent(requestId),{signal:controller.signal});
    const data=await response.json();
    if(!response.ok)throw window.DisplayText.responseError(data,'Chưa tải được phần giải thích.');
    if(displayedRequestId!==requestId||explanationAbort!==controller)return;
    if(data.context_id!==requestId)throw new Error('Phần giải thích không khớp phiên gieo.');
    renderExplanation(data);
  }catch(error){
    if(displayedRequestId!==requestId||explanationAbort!==controller)return;
    $('explanation-status').textContent='Bộ số đã được lưu. Phần giải thích chưa tải được; có thể thử lại.';
    $('explanation-retry').hidden=false;
  }finally{clearTimeout(timer);}
}
const readingTabs=[...document.querySelectorAll('[data-panel]')];
function selectReadingTab(tab){for(const item of readingTabs){const selected=item===tab;item.setAttribute('aria-selected',String(selected));item.tabIndex=selected?0:-1;$(item.dataset.panel).hidden=!selected;}}
for(const tab of readingTabs){tab.addEventListener('click',()=>selectReadingTab(tab));tab.addEventListener('keydown',event=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(event.key)){event.preventDefault();const index=event.key==='Home'?0:event.key==='End'?readingTabs.length-1:(readingTabs.indexOf(tab)+(event.key==='ArrowRight'?1:-1)+readingTabs.length)%readingTabs.length;selectReadingTab(readingTabs[index]);readingTabs[index].focus();}});}
$('explanation-retry').addEventListener('click',()=>loadExplanation(displayedRequestId));
async function openSavedDraw(requestId){
  $('error').hidden=true;setBusy(true);
  try{const response=await window.ArcanaClient.fetch('/api/v1/draw/'+encodeURIComponent(requestId),{signal:AbortSignal.timeout(20000)});const data=await response.json();if(!response.ok)throw window.DisplayText.responseError(data,'Chưa tải được phiên đã lưu.');render(data);loadExplanation(data.request_id);$('progress').textContent='Đang xem phiên đã lưu; bộ số giữ nguyên.';}
  catch(error){$('error').textContent=window.DisplayText.errorMessage(error,'Chưa mở được phiên đã lưu. Bạn có thể thử lại.');$('error').hidden=false;}
  finally{setBusy(false);}
}

async function send(payload){
  $('progress').textContent='Đang tính ngữ cảnh và gieo số…';
  const response=await window.ArcanaClient.fetch('/api/v1/draw',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),signal:AbortSignal.timeout(30000)});
  const data=await response.json();if(!response.ok)throw window.DisplayText.responseError(data,'Chưa gieo được bộ số. Bạn có thể thử lại cùng yêu cầu.');
  render(data);loadExplanation(data.request_id);$('progress').textContent='Đã hoàn tất phiên gieo.';pending=null;$('retry-button').hidden=true;
}
async function perform(makeNew){
  $('error').hidden=true;setBusy(true);
  try{
    if(makeNew){
      const casting={mode:$('casting-mode').value};if(casting.mode==='CURRENT')casting.clicked_at=vnNow();else casting.custom_timestamp=civil('custom-date');
      const birth={civil_datetime:civil('birth-date')};
      if($('override').value)birth.override_dung_than=$('override').value;
      pending={request_id:crypto.randomUUID(),birth,casting};
    }
    await send(pending);
  }catch(error){$('error').textContent=window.DisplayText.errorMessage(error,'Chưa hoàn tất phiên gieo. Bạn có thể thử lại cùng yêu cầu.');$('error').hidden=false;$('progress').textContent='Phiên chưa hoàn tất.';$('retry-button').hidden=!pending;}
  finally{setBusy(false);}
}
$('draw-form').addEventListener('submit',event=>{event.preventDefault();perform(true);});$('retry-button').addEventListener('click',()=>perform(false));
