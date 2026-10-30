/* A shared AI panel. All model calls and credentials stay in the backend. */
(() => {
  const add = (parent, tag, value='', cls='') => {
    const node=document.createElement(tag);node.textContent=window.DisplayText.plain(value);node.className=cls;parent.appendChild(node);return node;
  };
  function mount(parent, request, {autoGenerate=false,title='Kết quả này có ý nghĩa gì với bạn?',emptyText='Đọc ý chính và gợi ý cụ thể từ lá số hoặc quẻ đang mở.',onLoad=()=>{}}={}) {
    let generation=0, controller=null, disposed=false;
    parent.className='ai-reading-panel';parent.setAttribute('aria-label','Lời luận AI của phiên đang mở');
    add(parent,'p','LỜI LUẬN','eyebrow');add(parent,'h3',title);
    const status=add(parent,'p','Đang mở bài luận…','ai-reading-status');status.setAttribute('role','status');
    const skeleton=add(parent,'div','','ai-reading-skeleton');skeleton.setAttribute('aria-hidden','true');skeleton.hidden=true;
    for(let paragraph=0;paragraph<2;paragraph++) {
      const lines=add(skeleton,'div','','ai-skeleton-paragraph');
      for(let line=0;line<4;line++)add(lines,'span','','ai-skeleton-line');
    }
    const output=add(parent,'div','','ai-reading-content');
    function setStatus(message,loading=false) {
      status.textContent=window.DisplayText.plain(message);
      status.className='ai-reading-status'+(loading?' is-loading':'');
      skeleton.hidden=!loading;
      output.setAttribute('aria-busy',String(loading));
    }
    const error=add(parent,'p','','ai-reading-error');error.setAttribute('role','alert');error.hidden=true;
    const button=add(parent,'button',request.method==='BAZI'?'Phân tích và viết bài luận':'Đọc lời giải dễ hiểu','ai-reading-button');button.type='button';button.hidden=true;
    const active=version=>!disposed && version===generation && parent.isConnected;
    const stages={QUEUED:'Đang chuẩn bị bài luận…',ANALYZING:'Đang phân tích lá số…',WRITING:'Đang viết bài luận cho bạn…',
      CHECKING:'Đang kiểm tra bài luận…',RECONNECTING:'Đang nối lại kết nối với bài luận…'};
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
      const life=data.reading.schema_version==='bazi-life-reading-v1';
      const portrait=life && data.reading.whole_life;
      if(life && (request.method!=='BAZI' || data.reading.context_id!==request.consultation_id || !data.pipeline
        || data.reading.analysis_sha256!==data.pipeline.analysis_sha256))throw window.DisplayText.failure('Bài luận không khớp phần phân tích đã kiểm tra.');
      const blocks=life?[data.reading.overview,...data.reading.tendencies,...data.reading.in_life,...data.reading.contradictions,data.reading.takeaway]:[];
      const texts=life?[...blocks.map(c=>c.text),...data.reading.tendencies.map(c=>c.title),...data.reading.in_life.map(c=>c.title),...data.reading.limits.map(c=>c.text),data.reading.disclaimer]
        :[data.reading.summary.text,...data.reading.analysis.map(c=>c.text),...data.reading.practical_options.map(c=>c.text),...data.reading.limits];
      if(portrait)texts.push(...portrait.areas.map(c=>c.text),...portrait.periods.map(c=>c.text),portrait.timing_note);
      if(!texts.every(t=>typeof t==='string' && window.DisplayText.readable(t)))throw window.DisplayText.failure('Bài luận chưa thể hiển thị. Bạn có thể thử lại phần luận.');
      if(life && texts.some(t=>/\b(?:P0[1-5](?:-[MCL]0[1-5])?|[LV]0[1-3]|O01)\b/.test(t)))throw window.DisplayText.failure('Bài luận chưa thể hiển thị. Bạn có thể thử lại phần luận.');
      output.replaceChildren();
      if(life) {
        const prose=(parent,value,cls='')=>{for(const paragraph of value.split(/\n\s*\n/).filter(p=>p.trim()))add(parent,'p',paragraph,cls);};
        const section=(heading)=>{const part=add(output,'section','','bazi-life-section');add(part,'h4',heading);return part;};
        prose(section(portrait?'Bức tranh toàn cảnh':'Bức tranh chung'),data.reading.overview.text,'ai-reading-lead');
        if(portrait) {
          const titles={CAREER:'Sự nghiệp và đường phát triển',FINANCES:'Tài chính và tích lũy',RELATIONSHIPS:'Tình cảm, quan hệ và gia đình'};
          for(const area of portrait.areas)prose(section(titles[area.area]),area.text);
          const part=section('Các chặng đường theo Đại vận');
          if(portrait.periods.length)for(const period of portrait.periods) {
            add(part,'h5',period.start_year+'–'+period.end_year+' · '+period.start_age+'–'+period.end_age+' tuổi');
            prose(part,period.text);
          } else prose(part,portrait.timing_note);
        }
        if(data.reading.tendencies.length){
          const part=section('Những khuynh hướng nổi bật');
          for(const tendency of data.reading.tendencies){const article=add(part,'article','','bazi-life-tendency');add(article,'h5',tendency.title);prose(article,tendency.text);}
        }
        if(data.reading.in_life.length){
          const part=section('Trong công việc và cuộc sống');
          for(const item of data.reading.in_life){add(part,'h5',item.title);prose(part,item.text);}
        }
        if(data.reading.contradictions.length){const part=section('Những điểm tưởng như trái nhau');for(const item of data.reading.contradictions)prose(part,item.text);}
        prose(section(portrait?'Điểm tựa và điều cần cân bằng':'Điều đáng lưu ý nhất'),data.reading.takeaway.text);
        add(output,'p',data.reading.disclaimer,'bazi-life-disclaimer');
      } else {
      const takeaway=add(output,'section','','ai-reading-takeaway');add(takeaway,'h4',request.method==='LIUYAO'?'Trả lời câu hỏi của bạn':'Ý chính');
      add(takeaway,'p',data.reading.summary.text,'ai-reading-lead');
      if(request.method==='LIUYAO') {
        const reasons=add(output,'section','','ai-reading-reasons');add(reasons,'h4','Quẻ cho thấy điều gì?');
        for(const claim of data.reading.analysis)add(reasons,'p',claim.text);
      }
      const practical=add(output,'section','','ai-practical');add(practical,'h4','Bạn có thể làm gì?');
      const list=add(practical,'ul','');for(const option of data.reading.practical_options)add(list,'li',option.text);
      const limits=add(output,'section','','ai-reading-limits');add(limits,'h4','Cần lưu ý');
      const cautions=add(limits,'ul');for(const limit of data.reading.limits)add(cautions,'li',limit);
      if(request.method!=='LIUYAO') {
        const explanation=add(output,'details','','ai-reading-explanation');add(explanation,'summary','Vì sao có kết luận này?');
        references(explanation,data.reading.summary,data);
        for(const claim of data.reading.analysis) {const article=add(explanation,'article','','ai-reading-point');add(article,'p',claim.text);references(article,claim,data);}
      }
      }
      setStatus('');button.hidden=true;error.hidden=true;
      onLoad(data);
    }
    async function load(generate=false) {
      controller?.abort();controller=new AbortController();const signal=controller.signal,version=++generation;
      const requestController=controller,timer=setTimeout(()=>requestController.abort(),request.method==='BAZI'?1500000:780000);
      button.disabled=true;error.hidden=true;setStatus(generate?(request.method==='BAZI'?'Đang viết bài luận cho bạn…':'Đang viết lời luận theo câu hỏi của bạn…'):'Đang mở bài luận…',true);
      try {
        const data=await window.ArcanaClient.streamReading(request,{generate,signal,
          onProgress:stage=>{if(active(version) && stages[stage])setStatus(stages[stage],true);}});
        if(!active(version))return;
        if(data)render(data);
        else if(autoGenerate) {autoGenerate=false;clearTimeout(timer);load(true);}
        else {setStatus(emptyText);button.hidden=false;}
      } catch(failure) {
        if(!active(version))return;
        output.replaceChildren();
        error.setAttribute('data-error-code',failure.code || 'AI_DISPLAY_FAILED');
        const publicError=failure.code?window.DisplayText.responseError({error:{code:failure.code}},'Chưa tải được bài luận. Bạn có thể thử lại.'):failure;
        error.textContent=failure.name==='AbortError'?'Chưa nhận được bài luận. Bấm thử lại để nối với bài luận của phiên.':window.DisplayText.errorMessage(publicError,'Chưa tải được bài luận. Bạn có thể thử lại.');
        error.hidden=false;button.textContent=request.method==='BAZI'?'Thử lại bài luận':'Thử lại phần luận AI';button.hidden=false;setStatus('');
      } finally {clearTimeout(timer);if(active(version))button.disabled=false;}
    }
    button.addEventListener('click',()=>load(true));load();
    return {destroy(){disposed=true;generation++;controller?.abort();setStatus('');},reload(){load(false);}};
  }
  window.AIReading={mount};
})();
