/* Tinix engine views. Source text is rendered as text nodes, never HTML. */
(() => {
  'use strict';
  const add=(parent,tag,value='',cls='')=>{
    const node=document.createElement(tag);node.textContent=window.DisplayText.plain(value);node.className=cls;parent.appendChild(node);return node;
  };
  const clean=value=>String(value).replace(/<br\s*\/?>|<\/p>/gi,'\n').replace(/<[^>]*>/g,'')
    .replace(/&nbsp;/g,' ').replace(/&amp;/g,'&').replace(/&quot;/g,'"').replace(/&#39;/g,"'")
    .replace(/[*#=]{2,}/g,'').trim();
  const labels={
    personality:'Tính cách theo cách luận truyền thống',career:'Công việc',marriage:'Quan hệ',metadata:'Thông tin đối chiếu',
    strengths:'Điểm thuận',weaknesses:'Điểm cần chú ý',intro:'Tổng quan',summary:'Tổng quan',description:'Diễn giải',
    title:'Chủ đề',content:'Nội dung',text:'Diễn giải',analysis:'Phân tích',detail:'Chi tiết',loai:'Loại quan hệ',
    dien_giai:'Diễn giải',luan_giai:'Luận giải',y_nghia:'Ý nghĩa',mo_ta:'Mô tả',can:'Thiên can',chi:'Địa chi',
    ngu_hanh:'Ngũ Hành',cuong_do:'Vượng nhược',dung_than:'Dụng thần',hy_than:'Hỷ thần',ky_than:'Kỵ thần',
    nhan_dinh:'Nhận định',dieu_hau:'Điều hậu',cat_hung:'Tình huống thuận và nghịch',phong_thuy:'Phong thủy',
    thien_can:'Quan hệ Thiên can',dia_chi:'Quan hệ Địa chi',tang_can:'Tàng can',can_khi:'Căn khí',manh_yeu:'Vượng nhược',
    thap_than:'Thập Thần',cach:'Cách cục',van_ban:'Điển tích',nghe_nghiep:'Công việc theo hành',loi_khuyen:'Gợi ý',
    relationships:'Quan hệ với lá số',luck_interaction:'Quan hệ với Đại vận',special_stars:'Thần sát',
    evaluations:'Diễn giải theo lĩnh vực',interpretation:'Luận giải năm',finance:'Tài chính',wealth:'Tài chính',love:'Quan hệ',
    health:'Sức khỏe theo cách luận truyền thống',suc_khoe:'Sức khỏe theo cách luận truyền thống',
    benh_duoc:'Bệnh Dược',dich_thien_tuy:'Trích Thiên Tủy',tu_binh_chan_thuyen:'Tử Bình Chân Thuyên',
    nap_am_chuyen_sau:'Nạp Âm chuyên sâu',hinh_hai_pha:'Hình · Hại · Phá',vong_trang_sinh:'Vòng Trường Sinh',
    dong_tinh_luan:'Động Tĩnh Luận',kim_bat_hoan:'Kim Bất Hoán',cung_thong_bao_giam:'Cung Thông Bảo Giám',
    tam_menh_thong_hoi:'Tam Mệnh Thông Hội',luan_tinh:'Luận tĩnh',luan_dong:'Luận động',shishen:'Thập Thần chuyên sâu',
    nam:'Trụ năm',thang:'Trụ tháng',ngay:'Trụ ngày',gio:'Trụ giờ',muoi_hai_thoi_thanh:'Mười hai thời thần',
    score:'Điểm theo quy tắc engine',life_stage:'Trường Sinh',giai_thich:'Giải thích',
    noi_dung:'Nội dung',ket_luan:'Kết luận',than_sat:'Thần sát',diem:'Điểm',tac_dong:'Tác động'
  };
  function tree(parent,value) {
    if(value===null || value===undefined || typeof value==='boolean')return;
    if(typeof value==='string' || typeof value==='number') {
      const text=clean(value);
      if(text && window.DisplayText.readable(text))for(const line of text.split(/\n\s*\n/).filter(Boolean))add(parent,'p',line);
    } else if(Array.isArray(value))for(const item of value)tree(parent,item);
    else for(const [key,item] of Object.entries(value)){
      const part=add(parent,'div','','bazi-source-block');
      if(labels[key])add(part,'strong',labels[key]);
      tree(part,item);
      if(!part.textContent.trim())part.remove();
    }
  }
  function details(parent,title,render) {
    const node=add(parent,'details','','bazi-engine-detail');add(node,'summary',title);
    let ready=false;node.addEventListener('toggle',()=>{if(node.open && !ready){ready=true;render(add(node,'div','','bazi-source-content'));}});
    return node;
  }
  function table(parent,headers,rows) {
    const wrap=add(parent,'div','','bazi-engine-table-wrap'),node=add(wrap,'table','','bazi-engine-table');
    const tr=add(add(node,'thead'),'tr');for(const h of headers){const th=add(tr,'th',h);th.scope='col';}
    const body=add(node,'tbody');for(const row of rows){const tr=add(body,'tr');for(const cell of row)add(tr,'td',cell ?? '—');}
    return node;
  }
  function radar(parent,scores) {
    const entries=Object.entries(scores),total=entries.reduce((sum,[,n])=>sum+n,0),max=Math.max(...entries.map(([,n])=>n),1);
    const figure=add(parent,'figure','','bazi-radar');
    const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 320 300');
    svg.setAttribute('role','img');svg.setAttribute('aria-label','Biểu đồ Ngũ Hành; số liệu đầy đủ trong bảng bên dưới');figure.appendChild(svg);
    const element=(tag,attrs,value)=>{const n=document.createElementNS(svg.namespaceURI,tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,v);if(value)n.textContent=value;svg.appendChild(n);return n;};
    const point=(i,r)=>[160+Math.cos(-Math.PI/2+i*2*Math.PI/5)*r,150+Math.sin(-Math.PI/2+i*2*Math.PI/5)*r];
    for(const r of [30,60,90])element('polygon',{points:entries.map((_,i)=>point(i,r).join(',')).join(' '),class:'bazi-radar-grid'});
    entries.forEach(([name,n],i)=>{
      const [x,y]=point(i,90);element('line',{x1:160,y1:150,x2:x,y2:y,class:'bazi-radar-grid'});
      const [tx,ty]=point(i,121);element('text',{x:tx,y:ty,'text-anchor':'middle','dominant-baseline':'middle',class:'bazi-radar-label'},name);
    });
    element('polygon',{points:entries.map(([,n],i)=>point(i,n/max*90).join(',')).join(' '),class:'bazi-radar-shape'});
    entries.forEach(([,n],i)=>{const [cx,cy]=point(i,n/max*90);element('circle',{cx,cy,r:4,class:'bazi-radar-point'});});
    add(figure,'figcaption','Điểm quy ước của engine, không phải thước đo năng lực hay xác suất.');
    table(parent,['Yếu tố','Điểm','Tỷ lệ'],entries.map(([name,n])=>[name,n,(100*n/total).toFixed(1)+'%']));
  }
  function renderIdentity(parent,session) {
    const year=session.chart.pillars[0],day=session.chart.pillars[2].stem;
    const block=add(parent,'section','','bazi-element-identity');
    block.setAttribute('aria-label','Mệnh năm sinh và Nhật chủ');
    const list=add(block,'dl');
    for(const [label,value] of [
      ['Mệnh năm sinh · Nạp âm',year.stem.name+' '+year.branch+' · '+session.engine.result.chart[0].nap_am],
      ['Nhật chủ Bát Tự · Can ngày',day.name+' · '+day.polarity+' '+day.element]
    ]){const item=add(list,'div');add(item,'dt',label);add(item,'dd',value);}
    add(block,'p','Mệnh năm sinh lấy từ Can Chi năm. Nhật chủ lấy từ Thiên can ngày sinh, dùng làm điểm đối chiếu khi luận Bát Tự.');
    return block;
  }
  function mount(parent,session) {
    const result=session.engine.result,panels=[],buttons=[];
    parent.className='bazi-engine-workspace';
    add(parent,'p','KHÁM PHÁ LÁ SỐ','eyebrow');
    const navigation=add(parent,'div','','bazi-engine-tabs');navigation.setAttribute('role','tablist');navigation.setAttribute('aria-label','Các phần của lá số');
    const makeTab=(name,render)=>{
      const index=panels.length,button=add(navigation,'button',name),panel=add(parent,'section','','bazi-engine-panel');button.type='button';
      button.id='bazi-engine-tab-'+index;panel.id='bazi-engine-panel-'+index;
      button.setAttribute('role','tab');button.setAttribute('aria-controls',panel.id);
      panel.setAttribute('role','tabpanel');panel.setAttribute('aria-labelledby',button.id);panel.tabIndex=0;
      let ready=false;
      const select=()=>{panels.forEach((p,i)=>{p.hidden=i!==index;buttons[i].setAttribute('aria-selected',String(i===index));buttons[i].tabIndex=i===index?0:-1;});if(!ready){ready=true;render(panel);}};
      button.addEventListener('click',select);buttons.push(button);panels.push(panel);panel.hidden=true;
      button.addEventListener('keydown',event=>{
        let next;if(event.key==='ArrowRight')next=(index+1)%buttons.length;if(event.key==='ArrowLeft')next=(index+buttons.length-1)%buttons.length;
        if(event.key==='Home')next=0;if(event.key==='End')next=buttons.length-1;
        if(next!==undefined){event.preventDefault();buttons[next].click();buttons[next].focus();}
      });
      return select;
    };
    const first=makeTab('Lá số & Ngũ Hành',panel=>{
      add(panel,'h3','Phân bố Ngũ Hành');radar(panel,result.scores.ngu_hanh_vn);
      const assessment=session.assessment;
      add(panel,'p',assessment.strength_name,'bazi-engine-strength');
      table(panel,['Đối chiếu','Yếu tố'],[['Dụng thần',assessment.balance.preferred.join(', ')],['Hỷ thần',assessment.balance.supporting.join(', ')],['Kỵ thần',assessment.balance.restrain.join(', ')]]);
      details(panel,'Nạp Âm · Trường Sinh · Thần sát',body=>table(body,['Trụ','Nạp Âm','Trường Sinh','Thần sát'],result.chart.map((p,i)=>[session.chart.pillars[i].label,p.nap_am,p.truong_sinh,p.than_sat.join(', ')])));
    });
    makeTab('Đại vận & Lưu niên',panel=>{
      add(panel,'h3','Đại vận');add(panel,'p','Chọn một giai đoạn để xem luận giải và từng năm. Các mốc là kết quả của cách tính vận trong engine.');
      for(const cycle of result.luck_cycles)details(panel,cycle.start+'–'+cycle.end+' · '+cycle.can_chi+' · '+cycle.startAge+'–'+cycle.endAge+' tuổi',body=>{
        tree(body,cycle.luan_giai);
        table(body,['Năm','Tuổi','Can Chi','Thập Thần','Điểm'],cycle.luu_nien.map(y=>[y.nam,y.tuoi,y.can_chi || [y.gan,y.zhi].join(' '),y.thap_than,y.diem_so ?? y.score ?? '—']));
        for(const year of cycle.luu_nien)details(body,'Luận năm '+year.nam,part=>tree(part,year));
      });
      add(panel,'h3','Lưu niên '+session.engine.target_year);add(panel,'p',result.annual.ganzhiVN+' · '+result.annual.shishen);
      tree(panel,{relationships:result.annual.relationships,luck_interaction:result.annual.luck_interaction,evaluations:result.annual.evaluations,interpretation:result.annual.interpretation});
    });
    makeTab('Phân tích & điển tích',panel=>{
      add(panel,'h3','Ma trận phân tích');
      add(panel,'p','Nội dung dưới đây do engine tinix-bazi luận theo hệ thống truyền thống. Các nhánh có thể dùng cách chấm khác nhau; phần Ngũ Hành ở trên dùng phép cân bằng Ngũ Hành.');
      details(panel,'Quan hệ Can Chi',body=>{
        const matrix=result.analysis.quan_he_can_chi;
        for(const [title,rows] of [['Thiên can',matrix.thien_can],['Địa chi',matrix.dia_chi]]){
          add(body,'h4',title);table(body,['Quan hệ','Vị trí','Chi tiết'],rows.map(r=>[r.loai,r.tru,r.chi_tiet]));
        }
        details(body,'Lời giải của các quan hệ',part=>tree(part,matrix));
      });
      details(panel,'Cách cục',body=>tree(body,result.analysis.ket_luan));
      details(panel,'Cân bằng Ngũ Hành',body=>tree(body,result.analysis.can_bang_ngu_hanh));
      for(const [key,value] of Object.entries(result.analysis.phan_tich_nang_cao))details(panel,labels[key] || 'Phân tích chuyên sâu',body=>tree(body,value));
      details(panel,'Luận giải tổng hợp',body=>tree(body,result.interpretation));
      details(panel,'Điển tích theo lá số',body=>{
        add(body,'p','Đây là diễn giải đi kèm mã nguồn, chưa xác minh là nguyên văn cổ thư.');tree(body,result.classics);
        window.DisplayText.sourceLink(body,'Xem nguồn engine','https://github.com/vhphuoc1102/tinix-bazi/tree/'+session.engine.commit+'/backendjs/src/bazi');
      });
    });
    first();
  }
  window.BaziFeatures={mount,renderIdentity};
})();
