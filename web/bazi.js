/* Independent natal charts and immutable topic readings. */
(() => {
  const el = id => document.getElementById(id);
  const text = (parent, tag, value='', cls='') => {
    const node = document.createElement(tag); node.textContent = window.DisplayText.plain(value); node.className = cls; parent.appendChild(node); return node;
  };
  const topics = {GENERAL:'Tổng quan',CAREER:'Công việc',WEALTH:'Tài chính',STUDY:'Học tập',RELATIONSHIPS:'Quan hệ'};
  const dateVN = value => new Date(value).toLocaleString('vi-VN', {timeZone:'Asia/Ho_Chi_Minh'});
  const stateNames = {SUPPORTED:'Dữ kiện đã nhận diện',CONDITIONAL:'Nhận định có điều kiện',UNRESOLVED:'Chưa đủ điều kiện kết luận'};
  const sourceNames = {PRIMARY_TEXT:'Nguyên văn',PROVIDER:'Bảng tra',PRODUCT_POLICY:'Quy ước triển khai'};
  let session = null, activeReading = null, pending = null, controller = null, revision = 0;
  let readingListRevision = 0, readingController = null;
  let aiPanel = null, activeReadingId = null;
  const endpoint = '/api/v1/bazi';

  async function json(url, options={}) {
    const response = await window.ArcanaClient.fetch(url, options);
    const data = await response.json();
    if (!response.ok) throw window.DisplayText.responseError(data,'Chưa nhận được kết quả.');
    return data;
  }
  function busy(value) {
    for (const id of ['bazi-form','bazi-reread-form']) if (el(id)) {
      for (const field of el(id).elements) field.disabled = value;
    }
  }
  function showError(message) {el('bazi-error').textContent=window.DisplayText.plain(message);el('bazi-error').hidden=false;}
  function optionSelect(parent, id, value) {
    const select = text(parent,'select','');select.id=id;
    for (const [key,name] of Object.entries(topics)) {const option=text(select,'option',name);option.value=key;}
    select.value=value;return select;
  }
  function evidenceDetails(parent, refs, findingMap, evidenceMap) {
    const details=text(parent,'details','','bazi-reasons');text(details,'summary','Vì sao có nhận định này?');
    const renderedSources=new Set();
    for (const id of refs) {
      const f=findingMap.get(id);if(!f)continue;
      text(details,'p',f.title+' · '+stateNames[f.state],'bazi-finding-state');
      if (refs.length>1) text(details,'p',f.text);
      for (const key of f.evidence_refs) {
        if(renderedSources.has(key))continue;renderedSources.add(key);
        const e=evidenceMap.get(key);if(!e)continue;
        const article=text(details,'article','','bazi-evidence');
        text(article,'small',sourceNames[e.kind]+' · '+e.title);text(article,'p',e.text,e.kind==='PRIMARY_TEXT'?'source-text':'');
        if(e.url)window.DisplayText.sourceLink(article,'Đối chiếu nguồn',e.url);
      }
    }
  }
  function render(autoGenerate=false) {
    aiPanel?.destroy();
    const root=el('bazi-result');root.replaceChildren();el('bazi-empty').hidden=true;root.hidden=false;
    const reading=activeReading, renderedId=session.request_id, findingMap=new Map(session.findings.map(f=>[f.finding_id,f]));
    const evidenceMap=new Map(session.evidence.map(e=>[e.evidence_id,e]));
    text(root,'p','LÁ SỐ BÁT TỰ · '+reading.topic_name.toLocaleUpperCase('vi-VN'),'eyebrow');
    const title=text(root,'h2',session.display_name || reading.title,'bazi-result-heading');title.id='bazi-result-title';title.tabIndex=-1;
    text(root,'p','Sinh lúc '+dateVN(session.chart.civil_datetime)+' · Giờ Việt Nam','bazi-birth-caption');
    if(reading.question) {const q=text(root,'div','','bazi-question-saved');text(q,'small','Câu hỏi của bạn');text(q,'p',reading.question);}
    const tableWrap=text(root,'div','','bazi-chart-wrap');
    const table=text(tableWrap,'table','','bazi-chart');text(table,'caption','Bàn Tứ Trụ');
    const head=text(text(table,'thead',''),'tr','');
    for(const p of session.chart.pillars) {const th=text(head,'th',p.label);th.scope='col';}
    const body=text(table,'tbody','');
    for(const kind of ['stem','branch','hidden']) {
      const row=text(body,'tr','');
      for(const p of session.chart.pillars) {
        const td=text(row,'td','');
        if(kind==='stem') {
          const token=text(td,'span',p.stem.zh,'bazi-glyph');token.dataset.element=p.stem.element;
          text(td,'strong',p.stem.name);text(td,'small',p.stem.polarity+' '+p.stem.element);text(td,'span',p.stem.ten_god_name,'bazi-god');
        } else if(kind==='branch') {
          const token=text(td,'span',p.branch_zh,'bazi-glyph');token.dataset.element=p.branch_element;
          text(td,'strong',p.branch);text(td,'small',p.branch_element);
        } else {
          text(td,'small','Tàng can','bazi-hidden-label');
          for(const h of p.hidden_stems) {const item=text(td,'div','','bazi-hidden-stem');text(item,'strong',h.name);text(item,'span',h.ten_god_name);}
        }
      }
    }
    const distribution=text(root,'details','','bazi-distribution');text(distribution,'summary','Ngũ hành đang hiện diện');
    text(distribution,'p','Can lộ và tàng can được đếm riêng. Đây là số lần hiện diện, không phải tỷ lệ sức mạnh.');
    const list=text(distribution,'ul','');
    for(const e of session.facts.distribution) text(list,'li',e.element+' · '+e.visible_stems+' can lộ · '+e.hidden_occurrences+' vị trí tàng can');
    aiPanel=window.AIReading.mount(text(root,'section',''),{method:'BAZI',consultation_id:renderedId,bazi_reading_id:activeReadingId || renderedId},{autoGenerate:false});
    const technical=text(root,'details','','bazi-technical');text(technical,'summary','Phân tích lá số và căn cứ');
    const summary=text(technical,'div','','bazi-overview');text(summary,'h3',reading.title);text(summary,'p',reading.summary);
    const prose=text(technical,'div','','bazi-prose');
    for(const section of reading.sections) {
      const article=text(prose,'article','','bazi-reading-section');text(article,'h3',section.title);
      for (const paragraph of section.text.split('\n\n')) text(article,'p',paragraph);
      evidenceDetails(article,section.finding_refs,findingMap,evidenceMap);
    }
    const reread=text(root,'form','','bazi-reread');reread.id='bazi-reread-form';reread.autocomplete='off';text(reread,'h3','Đọc thêm trên cùng lá số');
    const label=text(reread,'label','Chủ đề');optionSelect(label,'bazi-reread-topic',reading.topic);
    const qlabel=text(reread,'label','Câu hỏi (tùy chọn)');const question=text(qlabel,'textarea','');question.id='bazi-reread-question';question.rows=2;question.maxLength=2000;question.value=reading.question;
    const submit=text(reread,'button','Luận chủ đề này ↗');submit.type='submit';
    reread.addEventListener('submit',event=>{event.preventDefault();pending={kind:'reading',id:renderedId,
      payload:{reading_id:crypto.randomUUID(),topic:el('bazi-reread-topic').value,question:question.value.trim()}};perform(pending);});
    const old=text(root,'details','','bazi-saved-readings');text(old,'summary','Các bài luận trong phiên này');
    const oldStatus=text(old,'p','Mở để tải các bài luận.','hint');const oldList=text(old,'ul','');
    old.addEventListener('toggle',()=>{if(old.open)loadReadings(oldList,oldStatus,renderedId);});
    const scope=text(root,'details','','bazi-coverage');text(scope,'summary','Phạm vi và phương pháp luận');
    text(scope,'p','Bản đầu đọc mệnh cục sinh. Chủ đề định hướng bài luận; ghi chú dùng trong phiên, chưa được phân tích để trả lời thời điểm hoặc sự kiện cụ thể.');
    for(const c of session.coverage) {text(scope,'h4',c.feature);text(scope,'p',c.detail);}
    text(scope,'p','Quy tắc đã được kiểm thử phần mềm; phần luận chưa được chuyên gia hiệu đính độc lập.','hint');
  }
  async function loadReadings(list,status,id) {
    const generation=++readingListRevision;readingController?.abort();readingController=new AbortController();
    status.textContent='Đang tải bài luận…';
    try {
      const data=await json(endpoint+'/consultations/'+encodeURIComponent(id)+'/readings',{signal:readingController.signal});
      if(generation!==readingListRevision || session?.request_id!==id)return;
      list.replaceChildren();
      for(const row of data.readings) {
        const li=text(list,'li','');const button=text(li,'button',row.reading.topic_name+' · '+dateVN(row.created_at),'bazi-history-button');button.type='button';
        button.addEventListener('click',()=>{
          if(session?.request_id!==id)return;
          controller?.abort();++revision;++readingListRevision;readingController?.abort();
          pending=null;busy(false);el('bazi-retry').hidden=true;el('bazi-error').hidden=true;
          activeReading=row.reading;activeReadingId=row.reading_id;render();window.ResultPDF?.mount(el('bazi-result'),'Luận giải Bát Tự');el('bazi-result-title').focus();el('bazi-progress').textContent='Đang xem bài luận trong phiên.';
        });
      }
      status.textContent='';
    } catch(error) {if(generation===readingListRevision && error.name!=='AbortError') {status.textContent=window.DisplayText.errorMessage(error,'Chưa tải được bài luận. Đóng rồi mở lại để thử lại.');}}
  }
  async function perform(task) {
    controller?.abort();controller=new AbortController();const requestController=controller,generation=++revision;
    ++readingListRevision;readingController?.abort();busy(true);el('bazi-error').hidden=true;el('bazi-retry').hidden=true;
    el('bazi-progress').textContent=task.kind==='saved'?'Đang mở lá số…':task.kind==='reading'?'Đang luận từ lá số trong phiên…':'Đang lập lá số và luận giải…';
    const timer=setTimeout(()=>requestController.abort(),20000);
    try {
      const path=task.kind==='saved'?'/consultations/'+encodeURIComponent(task.id):task.kind==='reading'?'/consultations/'+encodeURIComponent(task.id)+'/readings':'/consultations';
      const options={signal:requestController.signal};
      if(task.kind!=='saved')Object.assign(options,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(task.payload)});
      const data=await json(endpoint+path,options);if(generation!==revision)return;
      if(task.kind==='reading') {
        if(session?.request_id!==data.consultation_id || data.reading_id!==task.payload.reading_id)throw window.DisplayText.failure('Bài luận không khớp lá số đang mở.');
        activeReading=data.reading;
        activeReadingId=data.reading_id;
      } else {
        const expected=task.kind==='saved'?task.id:task.payload.request_id;
        if(data.request_id!==expected)throw window.DisplayText.failure('Kết quả không khớp hồ sơ đang mở.');
        session=data;activeReading=data.reading;activeReadingId=data.request_id;
      }
      pending=null;render(task.kind!=='saved');window.ResultPDF?.mount(el('bazi-result'),'Luận giải Bát Tự');el('bazi-result-title').focus();
      el('bazi-progress').textContent=task.kind==='saved'?'Đang xem lá số trong phiên.':'Đã có kết quả.';
    } catch(error) {
      if(generation!==revision)return;
      showError(error.name==='AbortError'?'Chưa nhận được kết quả. Thử lại cùng yêu cầu để kiểm tra.':window.DisplayText.errorMessage(error,'Chưa tải được kết quả. Bạn có thể thử lại.'));
      el('bazi-progress').textContent='';el('bazi-retry').hidden=!pending;
    } finally {clearTimeout(timer);if(generation===revision)busy(false);}
  }
  el('bazi-form').addEventListener('submit',event=>{
    event.preventDefault();let value=el('bazi-birth').value;if(value.length===16)value+=':00';
    const birth={civil_datetime:value+'+07:00'},uncertainty=el('bazi-uncertainty').value;
    if(uncertainty!=='')birth.clock_uncertainty_seconds=Number(uncertainty)*60;
    pending={kind:'new',payload:{request_id:crypto.randomUUID(),display_name:el('bazi-name').value.trim(),
      birth,topic:el('bazi-topic').value,question:el('bazi-question').value.trim()}};perform(pending);
  });
  el('bazi-form').addEventListener('input',()=>{pending=null;el('bazi-retry').hidden=true;});
  el('bazi-retry').addEventListener('click',()=>{if(pending)perform(pending);});
})();
