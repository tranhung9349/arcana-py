/* Independent natal charts and immutable topic readings. */
(() => {
  const el = id => document.getElementById(id);
  const text = (parent, tag, value='', cls='') => {
    const node = document.createElement(tag); node.textContent = window.DisplayText.plain(value); node.className = cls; parent.appendChild(node); return node;
  };
  const dateVN = value => new Date(value).toLocaleString('vi-VN', {timeZone:'Asia/Ho_Chi_Minh'});
  let session = null, activeReading = null, pending = null, controller = null, revision = 0;
  let aiPanel = null, glossaryDialog = null;
  const endpoint = '/api/v1/bazi';

  async function json(url, options={}) {
    const response = await window.ArcanaClient.fetch(url, options);
    const data = await response.json();
    if (!response.ok) throw window.DisplayText.responseError(data,'Chưa nhận được kết quả.');
    return data;
  }
  function busy(value) {
    for (const field of el('bazi-form').elements) field.disabled = value;
  }
  function showError(message) {el('bazi-error').textContent=window.DisplayText.plain(message);el('bazi-error').hidden=false;}
  function render({historical=false}={}) {
    aiPanel?.destroy();
    if(glossaryDialog?.open)glossaryDialog.close();
    const root=el('bazi-result');root.replaceChildren();el('bazi-empty').hidden=true;root.hidden=false;
    const reading=activeReading, renderedId=session.request_id;
    text(root,'p','LÁ SỐ BÁT TỰ · '+reading.topic_name.toLocaleUpperCase('vi-VN'),'eyebrow');
    const title=text(root,'h2',session.display_name || reading.title,'bazi-result-heading');title.id='bazi-result-title';title.tabIndex=-1;
    text(root,'p','Sinh lúc '+dateVN(session.chart.civil_datetime)+' · Giờ Việt Nam','bazi-birth-caption');
    if(session.engine)text(root,'p',(session.engine.gender==='female'?'Nữ':'Nam')+' · Năm xem '+session.engine.target_year,'bazi-birth-caption');
    if(session.engine && window.BaziFeatures)window.BaziFeatures.renderIdentity(root,session);
    if(reading.question) {const q=text(root,'div','','bazi-question-saved');text(q,'small','Câu hỏi của bạn');text(q,'p',reading.question);}
    aiPanel=window.AIReading.mount(text(root,'section',''),{method:'BAZI',consultation_id:renderedId,bazi_reading_id:renderedId},
      {autoGenerate:!historical,title:'Luận giải của bạn',
       onLoad:()=>{if(session.request_id===renderedId)el('bazi-progress').textContent='Đã có bài luận.';}});
    const reference=text(root,'div','','bazi-reference-tools');
    const chartDetails=text(reference,'details','','bazi-chart-details');text(chartDetails,'summary','Xem lá số');
    const help=text(reference,'button','Thuật ngữ','bazi-glossary-trigger');help.type='button';
    help.setAttribute('aria-haspopup','dialog');help.setAttribute('aria-controls','bazi-glossary-dialog');help.setAttribute('aria-expanded','false');
    const dialog=text(root,'dialog','','bazi-glossary-dialog');dialog.id='bazi-glossary-dialog';glossaryDialog=dialog;
    dialog.setAttribute('aria-labelledby','bazi-glossary-title');dialog.setAttribute('aria-describedby','bazi-glossary-intro');
    const dialogBody=text(dialog,'div','','bazi-glossary-body'),dialogHeader=text(dialogBody,'div','','bazi-glossary-header');
    const glossaryTitle=text(dialogHeader,'h3','Hiểu các ký hiệu trong lá số');glossaryTitle.id='bazi-glossary-title';
    const close=text(dialogHeader,'button','Đóng','bazi-glossary-close');close.type='button';close.autofocus=true;
    const intro=text(dialogBody,'p','Tra nhanh khi cần đối chiếu bảng lá số. Bạn không cần nhớ các tên này để đọc bài luận.');intro.id='bazi-glossary-intro';
    const glossary=text(dialogBody,'dl','','bazi-glossary');
    for(const [term,meaning] of [
      ['Tứ Trụ','Bốn cột ghi năm, tháng, ngày và giờ sinh.'],
      ['Nhật chủ','Ký hiệu của ngày sinh, dùng làm điểm so sánh với các phần khác trong lá số; hành này được tính từ can ngày.'],
      ['Mệnh năm sinh (nạp âm)','Tên hành gắn với cặp Can Chi năm sinh, chẳng hạn Giáp Tuất là Sơn Đầu Hỏa. Được xác định riêng với Nhật chủ.'],
      ['Tàng can','Các ký hiệu nằm trong phần nhánh của mỗi cột; không phải tính cách bị che giấu.'],
      ['Thập Thần','Tên mười kiểu quan hệ giữa các ký hiệu; không phải mười vị thần.'],
      ['Vượng / nhược','Mức được hỗ trợ của một yếu tố trong phép đọc; không phải mạnh yếu về thể chất hay năng lực.'],
      ['Dụng thần / phù ức','Yếu tố tạm được ưu tiên để cân đối các quan hệ trong lá số.'],
      ['Điều hậu','Phần xét thêm nóng lạnh theo mùa sinh trong cách đọc truyền thống.']
    ]){text(glossary,'dt',term);text(glossary,'dd',meaning);}
    help.addEventListener('click',()=>{dialog.showModal();help.setAttribute('aria-expanded','true');});
    close.addEventListener('click',()=>dialog.close());
    dialog.addEventListener('click',event=>{if(event.target===dialog)dialog.close();});
    dialog.addEventListener('close',()=>{help.setAttribute('aria-expanded','false');help.focus();});
    const tableWrap=text(chartDetails,'div','','bazi-chart-wrap');
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
    const distribution=text(chartDetails,'details','','bazi-distribution');text(distribution,'summary','Năm yếu tố trong lá số');
    text(distribution,'p','Can lộ và tàng can được đếm riêng. Đây là số lần hiện diện, không phải tỷ lệ sức mạnh.');
    const list=text(distribution,'ul','');
    for(const e of session.facts.distribution) text(list,'li',e.element+' · '+e.visible_stems+' can lộ · '+e.hidden_occurrences+' vị trí tàng can');
    if(session.engine && window.BaziFeatures)window.BaziFeatures.mount(text(root,'section'),session);
  }
  async function history() {
    try {
      const data=await json(endpoint+'/history'),list=el('bazi-history-list');list.replaceChildren();
      if(!data.consultations.length)text(list,'p','Chưa có lá số trong phiên này.');
      for(const row of data.consultations) {
        const button=text(list,'button',dateVN(row.civil_datetime)+' · '+row.topic_name+
          (row.target_year?' · '+(row.gender==='female'?'Nữ':'Nam')+' · '+row.target_year:''),'bazi-history-item');button.type='button';
        button.addEventListener('click',async()=>{
          controller?.abort();revision++;pending=null;busy(false);el('bazi-retry').hidden=true;
          el('bazi-progress').textContent='Đang mở lại lá số…';
          const generation=revision;
          try {
            const saved=await json(endpoint+'/consultations/'+encodeURIComponent(row.request_id));
            if(generation!==revision)return;
            session=saved;activeReading=saved.reading;
            el('bazi-birth').value=saved.chart.civil_datetime.slice(0,19);
            el('bazi-gender').value=saved.engine?.gender || 'male';
            if(saved.engine)el('bazi-year').value=saved.engine.target_year;
            el('bazi-topic').value=saved.reading.topic;el('bazi-question').value=saved.reading.question;
            el('bazi-uncertainty').value='';el('bazi-error').hidden=true;
            render({historical:true});
            window.ResultPDF?.mount(el('bazi-result'),'Luận giải Bát Tự');el('bazi-result-title').focus();
            el('bazi-progress').textContent='';
          } catch(error){if(generation===revision){showError(window.DisplayText.errorMessage(error,'Không mở được lá số.'));el('bazi-progress').textContent='';}}
        });
      }
    } catch {el('bazi-history-list').textContent='Chưa tải được lịch sử trong phiên.';}
  }
  async function perform(task) {
    controller?.abort();controller=new AbortController();const requestController=controller,generation=++revision;
    busy(true);el('bazi-error').hidden=true;el('bazi-retry').hidden=true;
    el('bazi-progress').textContent='Đang lập lá số và luận giải…';
    const timer=setTimeout(()=>requestController.abort(),20000);
    try {
      const data=await json(endpoint+'/consultations',{signal:requestController.signal,method:'POST',
        headers:{'Content-Type':'application/json'},body:JSON.stringify(task.payload)});
      if(generation!==revision)return;
      if(data.request_id!==task.payload.request_id)throw window.DisplayText.failure('Kết quả không khớp hồ sơ đang mở.');
      session=data;activeReading=data.reading;
      pending=null;render();window.ResultPDF?.mount(el('bazi-result'),'Luận giải Bát Tự');el('bazi-result-title').focus();
      history();
      el('bazi-progress').textContent='';
    } catch(error) {
      if(generation!==revision)return;
      showError(error.name==='AbortError'?'Chưa nhận được kết quả. Thử lại cùng yêu cầu để kiểm tra.':window.DisplayText.errorMessage(error,'Chưa tải được kết quả. Bạn có thể thử lại.'));
      el('bazi-progress').textContent='';el('bazi-retry').hidden=!pending;
    } finally {clearTimeout(timer);if(generation===revision)busy(false);}
  }
  el('bazi-form').addEventListener('submit',event=>{
    event.preventDefault();let value=el('bazi-birth').value;if(value.length===16)value+=':00';
    const birth={civil_datetime:value+'+07:00',gender:el('bazi-gender').value || 'male'},uncertainty=el('bazi-uncertainty').value;
    if(uncertainty!=='')birth.clock_uncertainty_seconds=Number(uncertainty)*60;
    pending={payload:{request_id:crypto.randomUUID(),
      birth,target_year:Number(el('bazi-year').value) || null,topic:el('bazi-topic').value,question:el('bazi-question').value.trim()}};perform(pending);
  });
  el('bazi-form').addEventListener('input',()=>{pending=null;el('bazi-retry').hidden=true;});
  el('bazi-retry').addEventListener('click',()=>{if(pending)perform(pending);});
})();
