/* A shared AI panel. All model calls and credentials stay in the backend. */
(() => {
  const add = (parent, tag, value='', cls='') => {
    const node=document.createElement(tag);node.textContent=window.DisplayText.plain(value);node.className=cls;parent.appendChild(node);return node;
  };
  function mount(parent, request, {autoGenerate=false,title='Đọc lá số và quẻ bằng lời dễ hiểu',emptyText='Diễn giải từ đúng lá số hoặc quẻ đang mở.'}={}) {
    let generation=0, controller=null, disposed=false;
    const payload=JSON.stringify(request);
    parent.className='ai-reading-panel';parent.setAttribute('aria-label','Lời luận AI của phiên đang mở');
    add(parent,'p','LỜI LUẬN','eyebrow');add(parent,'h3',title);
    const status=add(parent,'p','Đang kiểm tra bài luận của phiên…','ai-reading-status');status.setAttribute('role','status');
    const output=add(parent,'div','','ai-reading-content');
    const error=add(parent,'p','','ai-reading-error');error.setAttribute('role','alert');error.hidden=true;
    const button=add(parent,'button','Luận giải AI ↗','ai-reading-button');button.type='button';button.hidden=true;
    const active=version=>!disposed && version===generation && parent.isConnected;
    async function json(path, signal) {
      const response=await window.ArcanaClient.fetch('/api/v1/ai/'+path,{method:'POST',headers:{'Content-Type':'application/json'},body:payload,signal});
      const data=await response.json();
      if(!response.ok) throw window.DisplayText.responseError(data,'Chưa tải được bài luận AI. Bạn có thể thử lại.');
      return data;
    }
    function references(parent, claim, data) {
      const details=add(parent,'details','','ai-reading-references');add(details,'summary','Căn cứ của lời luận');
      const sourceMap=new Map(data.context.evidence.map(e=>[e.id,e]));
      // Facts are machine input. Only saved, readable findings belong in this view.
      const findings=(data.context.findings || []).filter(f=>f.fact_refs.some(id=>claim.fact_refs.includes(id)) && window.DisplayText.readable(f.text));
      for(const text of [...new Set(findings.map(f=>f.text))].slice(0,3))add(details,'p',text,'ai-fact-text');
      for(const id of claim.evidence_refs) {
        const source=sourceMap.get(id);if(!source)continue;
        add(details,'strong',source.title);add(details,'p',source.text,source.kind==='PRIMARY_TEXT'?'source-text':'');
        if(source.url)window.DisplayText.sourceLink(details,'Đối chiếu nguồn',source.url);
      }
    }
    function render(data) {
      if(data.consultation_id!==request.consultation_id || data.method!==request.method)throw window.DisplayText.failure('Bài luận không khớp phiên đang mở.');
      const texts=[data.reading.summary.text,...data.reading.analysis.map(c=>c.text),...data.reading.practical_options.map(c=>c.text),...data.reading.limits];
      if(!texts.every(t=>typeof t==='string' && window.DisplayText.readable(t)))throw window.DisplayText.failure('Bài luận chưa thể hiển thị. Bạn có thể thử lại phần luận.');
      output.replaceChildren();
      add(output,'p',data.reading.summary.text,'ai-reading-lead');
      for(const claim of data.reading.analysis) {const article=add(output,'article','','ai-reading-point');add(article,'p',claim.text);references(article,claim,data);}
      const practical=add(output,'section','','ai-practical');add(practical,'h4','Điều bạn có thể thử');
      const list=add(practical,'ul','');for(const option of data.reading.practical_options)add(list,'li',option.text);
      const limits=add(output,'details','','ai-reading-limits');add(limits,'summary','Điều còn để ngỏ');
      for(const limit of data.reading.limits)add(limits,'p',limit);
      const provenance=add(output,'details','','ai-reading-provenance');add(provenance,'summary','Thông tin bài luận');
      add(provenance,'p','Luận bằng AI · '+new Date(data.created_at).toLocaleString('vi-VN',{timeZone:'Asia/Ho_Chi_Minh'}));
      add(provenance,'p','Bài luận dựa trên dữ kiện của phiên đang mở; nội dung chưa được chuyên gia hiệu đính.');
      status.textContent='';button.hidden=true;error.hidden=true;
    }
    async function load(generate=false) {
      controller?.abort();controller=new AbortController();const signal=controller.signal,version=++generation;
      const timer=setTimeout(()=>controller?.abort(),390000);
      button.disabled=true;error.hidden=true;status.textContent=generate?'Đang viết lời luận theo câu hỏi của bạn…':'Đang kiểm tra bài luận của phiên…';
      try {
        let data;
        try {data=await json(generate?'readings':'readings/lookup',signal);}
        catch(failure) {
          if(failure.code!=='AI_BUSY')throw failure;
          // Another tab may already be generating this exact saved reading.
          for(let i=0;i<24 && !data;i++) {
            await new Promise((resolve,reject)=>{
              const timer=setTimeout(done,2500);
              function abort(){clearTimeout(timer);signal.removeEventListener('abort',abort);reject(new DOMException('Aborted','AbortError'));}
              function done(){signal.removeEventListener('abort',abort);resolve();}
              signal.addEventListener('abort',abort,{once:true});if(signal.aborted)abort();
            });
            if(!active(version))return;
            data=await json('readings/lookup',signal);
          }
          if(!data)throw window.DisplayText.failure('Bài luận vẫn đang được viết. Bạn có thể mở lại sau một lát.');
        }
        if(!active(version))return;
        if(data)render(data);
        else if(autoGenerate) {autoGenerate=false;clearTimeout(timer);load(true);}
        else {status.textContent=window.DisplayText.plain(emptyText);button.hidden=false;}
      } catch(failure) {
        if(!active(version))return;
        error.textContent=failure.name==='AbortError'?'Chưa nhận được bài luận. Bấm thử lại để kiểm tra kết quả của phiên.':window.DisplayText.errorMessage(failure,'Chưa tải được bài luận. Bạn có thể thử lại.');
        error.hidden=false;button.textContent='Thử lại phần luận AI';button.hidden=false;status.textContent='';
      } finally {clearTimeout(timer);if(active(version))button.disabled=false;}
    }
    button.addEventListener('click',()=>load(true));load();
    return {destroy(){disposed=true;generation++;controller?.abort();},reload(){load(false);}};
  }
  window.AIReading={mount};
})();
