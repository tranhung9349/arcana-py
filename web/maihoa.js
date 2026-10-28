/* Dedicated time-based Mai Hoa sessions; no calls to draw or date-search APIs. */
(() => {
  const el = id => document.getElementById(id);
  const text = (parent, tag, value='', cls='') => {
    const node = document.createElement(tag); node.textContent = window.DisplayText.plain(value); node.className = cls; parent.appendChild(node); return node;
  };
  const phaseNames = {BEGINNING:'Dụng',MIDDLE_BODY:'Thể hỗ',MIDDLE_USE:'Dụng hỗ',ENDING:'Dụng biến'};
  const relationName = (code, role) => ({SAME:'Thể và '+role+' tỷ hòa',USE_GENERATES_BODY:role+' sinh Thể',BODY_CONTROLS_USE:'Thể khắc '+role,BODY_GENERATES_USE:'Thể sinh '+role,USE_CONTROLS_BODY:role+' khắc Thể'})[code];
  const strengthNames = {STRONG:'Vượng',WEAK:'Suy',NOT_SPECIFIED:'Không gán mức vượng/suy'};
  const phaseKeys = {BEGINNING:'dung',MIDDLE_BODY:'mutual_body',MIDDLE_USE:'mutual_use',ENDING:'changed_use'};
  const nowVN = () => new Date(Date.now()+7*3600000).toISOString().slice(0,-1)+'+07:00';
  let pending = null, controller = null, revision = 0;
  let aiPanel=null;
  function updateQuestion() {el('maihoa-question').disabled = !el('maihoa-topic').value;}
  function busy(value) {for (const field of el('maihoa-form').elements) field.disabled = value; if (!value) updateQuestion();}
  function source(parent, evidence) {
    window.DisplayText.sourceLink(parent,'Mai Hoa · quyển '+evidence.volume+' · '+evidence.section,evidence.source.url);
  }
  function render(data,autoGenerate=false) {
    aiPanel?.destroy();
    let container = el('maihoa-result'); container.replaceChildren();
    el('maihoa-empty').hidden = true; container.hidden = false;
    text(container,'p',data.topic_name,'eyebrow');
    const heading = text(container,'h2',data.question);heading.id='maihoa-result-question';heading.tabIndex=-1;
    const localDate = value => new Date(value).toLocaleString('vi-VN',{timeZone:'Asia/Ho_Chi_Minh'});
    text(container,'p','Thời điểm hỏi: '+localDate(data.calendar.civil_datetime)+' · giờ Việt Nam','hint');
    const cards = text(container,'div','','mh-hexagrams');
    for (const [key,label] of [['original','Quẻ chủ'],['mutual','Quẻ hỗ'],['changed','Quẻ biến']]) {
      const card = text(cards,'article','','mh-hexagram');
      text(card,'small',label,'reading-label');
      const lines = text(card,'div','','mh-lines'); lines.setAttribute('role','img');
      lines.setAttribute('aria-label',label+' '+data.texts[key].name_vi+(key==='original'?', hào '+data.chart.moving_line+' động':''));
      for (let i=5;i>=0;i--) {
        const line = text(lines,'div','','mh-line '+(data.chart[key].lines_bottom_to_top[i]?'yang':'yin'));
        text(line,'span',''); text(line,'span','');
        if (key==='original' && i+1===data.chart.moving_line) {line.classList.add('moving');text(line,'b','○');}
      }
      text(card,'h3',data.texts[key].name_vi);text(card,'small','#'+data.chart[key].hexagram_id+' · '+data.chart[key].name_zh,'hint');
    }
    const body = data.chart.the, use = data.chart.dung;
    text(container,'p','Thể '+body.name+' ('+body.element+') · Dụng '+use.name+' ('+use.element+') · Hào '+data.chart.moving_line+' động.');
    aiPanel=window.AIReading.mount(text(container,'section',''),{method:'MAIHOA',consultation_id:data.request_id},{autoGenerate:false});
    const technical=text(container,'details','','mh-technical');text(technical,'summary','Phân tích quẻ và căn cứ');
    container=technical;
    const summary = text(container,'div','','mh-summary '+data.summary.pattern.toLowerCase());
    text(summary,'small','CHỈ BÁO THEO CÁC QUAN HỆ TRONG QUẺ','reading-label');
    text(summary,'h3',data.summary.text);text(summary,'p',data.summary.sequence);
    text(container,'h3','Thời khí và vượng suy');
    text(container,'p','Tháng '+data.season.month_branch+' theo tiết khí · Thể '+body.name+': '+strengthNames[body.strength]+'.');
    for (const warning of data.warnings) text(container,'p',warning.message,'source-gap');
    text(container,'h3','Luận theo từng phần của việc');
    const evidence = Object.fromEntries(data.evidence.map(row => [row.evidence_id,row]));
    for (const finding of data.findings) {
      const article = text(container,'article','','reading-card mh-finding');
      text(article,'h3',finding.title);
      const other = data.chart[phaseKeys[finding.phase]];
      text(article,'p',other.name+' ('+other.element+') · '+strengthNames[other.strength]);
      text(article,'strong',relationName(finding.relation,phaseNames[finding.phase])); text(article,'p',finding.text_vi);
      const details = text(article,'details','');text(details,'summary','Căn cứ nguyên văn');
      for (const id of finding.evidence_refs) {text(details,'p',evidence[id].text,'source-text');source(details,evidence[id]);}
    }
    const originals = text(container,'details','');text(originals,'summary','Đối chiếu quẻ từ, hào từ và lời truyện');
    for (const [key,label] of [['original','Quẻ chủ và hào động'],['mutual','Quẻ hỗ'],['changed','Quẻ biến']]) {
      text(originals,'h3',label+' · '+data.texts[key].name_vi);
      for (const card of data.texts[key].cards) sourceCard(originals,card);
      for (const gap of data.texts[key].source_gaps) text(originals,'p',gap.message,'source-gap');
    }
    const limits = text(container,'details','');text(limits,'summary','Phạm vi của phần luận');
    for (const value of data.limitations) text(limits,'p',value,'hint');
    const rules = text(container,'details','');text(rules,'summary','Quy tắc lập quẻ và phiên bản nguồn');
    text(rules,'p',`Số lập quẻ: năm ${data.chart.variables.Y} · tháng ${data.chart.variables.M} · ngày ${data.chart.variables.D} · giờ ${data.chart.variables.H}.`);
    text(rules,'p','Thời điểm theo lịch Bắc Kinh: '+new Date(data.calendar.beijing_datetime).toLocaleString('vi-VN',{timeZone:'Asia/Shanghai'})+' · Đổi ngày lúc 00:00; tháng nhuận giữ số tháng.','hint');
    for (const item of data.evidence.filter(row=>!row.evidence_id.match(/^(GENERAL|WEALTH|TRADE|PLANNING|MARRIAGE|TRAVEL)_/))) {
      const d = text(rules,'details','');text(d,'summary',item.title);text(d,'p',item.text,'source-text');source(d,item);
    }
    heading.focus({preventScroll:true});heading.scrollIntoView({behavior:'smooth',block:'start'});
  }
  async function perform(kind,id) {
    if (controller) controller.abort();
    const requestController = new AbortController(); controller=requestController;const generation=++revision;
    const timer=setTimeout(()=>requestController.abort(),20000);
    el('maihoa-error').hidden=true;el('maihoa-retry').hidden=true;busy(true);
    el('maihoa-progress').textContent=kind==='saved'?'Đang đọc phiên đã lưu…':'Đang lập và đối chiếu quẻ…';
    try {
      if (kind==='new') {
        const casting={mode:el('maihoa-time-mode').value};
        if (casting.mode==='CURRENT') casting.clicked_at=nowVN();
        else {let value=el('maihoa-custom-time').value;if(value.length===16)value+=':00';casting.custom_timestamp=value+'+07:00';}
        pending={request_id:crypto.randomUUID(),question:el('maihoa-question').value.trim(),topic:el('maihoa-topic').value,casting};
      } else if (kind==='saved') pending=null;
      const url=kind==='saved'?'/api/v1/maihoa/consultations/'+encodeURIComponent(id):'/api/v1/maihoa/consultations';
      const options={signal:requestController.signal};
      if (kind!=='saved') Object.assign(options,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(pending)});
      const response=await window.ArcanaClient.fetch(url,options);const data=await response.json();
      if (!response.ok) throw window.DisplayText.responseError(data,'Chưa tải được phiên luận.');
      if (generation!==revision) return;
      if (data.request_id!==(kind==='saved'?id:pending.request_id)) throw window.DisplayText.failure('Kết quả không khớp phiên đang mở.');
      render(data,kind!=='saved');window.ResultPDF?.mount(el('maihoa-result'),'Luận quẻ Mai Hoa');pending=null;el('maihoa-progress').textContent=kind==='saved'?'Đang xem đúng phiên đã lưu.':'Đã lập quẻ và phần luận của phiên.';
      
    } catch(error) {
      if (generation!==revision) return;
      el('maihoa-error').textContent=error.name==='AbortError'?'Chưa nhận được kết quả. Thử lại cùng phiên để kiểm tra.':window.DisplayText.errorMessage(error,'Chưa tải được phiên luận. Bạn có thể thử lại.');
      el('maihoa-error').hidden=false;el('maihoa-progress').textContent='Chưa nhận được phiên luận.';
      el('maihoa-retry').hidden=!pending;
    } finally {clearTimeout(timer);if(generation===revision)busy(false);}
  }
  el('maihoa-time-mode').addEventListener('change',()=>{
    const custom=el('maihoa-time-mode').value==='CUSTOM';el('maihoa-custom-field').hidden=!custom;el('maihoa-custom-time').required=custom;
  });
  el('maihoa-form').addEventListener('submit',event=>{event.preventDefault();perform('new');});
  el('maihoa-retry').addEventListener('click',()=>{if(pending)perform('retry');});
  el('maihoa-topic').addEventListener('change',updateQuestion);
  updateQuestion();
})();
