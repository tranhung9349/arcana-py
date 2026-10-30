/* A selected date is saved once; reading it never changes search scores. */
(() => {
  let lastKey=null,lastId=null;
  const add=(parent,tag,value='',cls='')=>{const n=document.createElement(tag);n.textContent=window.DisplayText.plain(value);n.className=cls;parent.appendChild(n);return n;};
  function mount(parent, search, {onLoad=()=>{}}={}) {
    let disposed=false, version=0, controller=null, ai=null;
    const key=JSON.stringify(search);
    if(lastKey!==key){lastKey=key;lastId=crypto.randomUUID();}
    const request={request_id:lastId,search};
    parent.replaceChildren();parent.className='date-reading';
    add(parent,'h3','Vì sao ngày này được xếp như vậy?');
    const status=add(parent,'p','Đang đọc căn cứ chọn ngày…','hint');status.setAttribute('role','status');
    const output=add(parent,'div');
    const retry=add(parent,'button','Thử tải lại lời luận','secondary');retry.type='button';retry.hidden=true;
    const active=v=>!disposed && v===version && parent.isConnected;
    async function load() {
      const v=++version;controller?.abort();ai?.destroy();ai=null;controller=new AbortController();retry.hidden=true;status.textContent='Đang đọc căn cứ chọn ngày…';
      try {
        const response=await window.ArcanaClient.fetch('/api/v2/auspicious-dates/consultations',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(request),signal:controller.signal});
        const data=await response.json();
        if(!response.ok)throw window.DisplayText.responseError(data,'Chưa tải được căn cứ của ngày này.');
        if(!active(v))return;
        if(data.request_id!==request.request_id || data.result.activity!==search.activity || data.result.days.length!==1 || data.result.days[0].date!==search.date_range.start)throw window.DisplayText.failure('Lời luận không khớp ngày và việc đang mở.');
        output.replaceChildren();status.textContent='';
        const reading=data.explanation;
        add(output,'p',reading.summary,'date-reading-lead');
        const list=add(output,'ul');for(const reason of reading.reasons.slice(0,4))add(list,'li',reason);
        const details=add(output,'details');add(details,'summary','Đối chiếu điểm và phạm vi áp dụng');
        for(const reason of reading.reasons.slice(4))add(details,'p',reason);
        for(const caution of reading.cautions)add(details,'p',caution);
        if(data.result.evaluation_mode==='DAY_ONLY')add(output,'p','Đã xét ngày; chưa chọn giờ đẹp cho việc này.','hint');
        const panel=add(output,'section');
        ai=window.AIReading.mount(panel,{method:'DATE',consultation_id:data.request_id},{title:'Ngày này có phù hợp với việc của bạn?',emptyText:'Đọc kết luận ngắn và việc cần chuẩn bị cho ngày đã chọn.'});
        window.ResultPDF?.mount(parent,'Tra ngày '+search.date_range.start+' · '+data.result.activity_name);
        onLoad(data);
      } catch(error) {
        if(!active(v) || error.name==='AbortError')return;
        status.textContent=window.DisplayText.errorMessage(error,'Chưa tải được căn cứ của ngày này. Bạn có thể thử lại.');retry.hidden=false;
      }
    }
    retry.addEventListener('click',load);load();
    return {destroy(){disposed=true;version++;controller?.abort();ai?.destroy();}};
  }
  window.DateReading={mount};
})();
