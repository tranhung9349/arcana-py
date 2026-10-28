/* Date search has independent state and never invokes the draw endpoint. */
(() => {
  const el = id => document.getElementById(id);
  const text = (parent, tag, value='', cls='') => {
    const node = document.createElement(tag); node.textContent = window.DisplayText.plain(value); node.className = cls; parent.appendChild(node); return node;
  };
  const statusNames = {SUPPORTED:'Có mục phù hợp', AVOID:'Nên tránh', NOT_LISTED:'Không đề cập', UNRESOLVED:'Chưa rõ'};
  const gradeNames = {GOOD:'Ngày Đẹp', NORMAL:'Ngày Bình Thường', BAD:'Ngày Xấu'};
  const officers = {'建':'Kiến','除':'Trừ','满':'Mãn','平':'Bình','定':'Định','执':'Chấp','破':'Phá','危':'Nguy','成':'Thành','收':'Thu','开':'Khai','闭':'Bế'};
  const gods = {'青龙':'Thanh Long','明堂':'Minh Đường','天刑':'Thiên Hình','朱雀':'Chu Tước','金匮':'Kim Quỹ','天德':'Thiên Đức','白虎':'Bạch Hổ','玉堂':'Ngọc Đường','天牢':'Thiên Lao','玄武':'Huyền Vũ','司命':'Tư Mệnh','勾陈':'Câu Trần'};
  const branches = {'子':'Tý','丑':'Sửu','寅':'Dần','卯':'Mão','辰':'Thìn','巳':'Tỵ','午':'Ngọ','未':'Mùi','申':'Thân','酉':'Dậu','戌':'Tuất','亥':'Hợi'};
  const exclusions = {'SAT_CHU':'Sát Chủ','THO_TU':'Thọ Tử','NGUYET_PHA':'Nguyệt Phá','NGUYET_PHA_V2':'Nguyệt Phá','ACTIVITY_DAY_JI':'Lịch ngày kỵ việc đã chọn','ACTIVITY_HOUR_JI':'Lịch giờ kỵ việc đã chọn'};
  const subjectLabel = (spec, index) => spec?.subject_roles[index] || 'Đương sự';
  const subjectName = id => {
    const index = query?.subjects.findIndex(s=>s.subject_id === id) ?? -1;
    return index < 0 ? 'Đương sự' : subjectLabel(resultSpec, index);
  };
  const exclusionName = value => value.startsWith('NATAL_CLASH:') ? 'Xung chi năm/ngày sinh của '+subjectName(value.split(':')[1]).toLowerCase() : (exclusions[value] || 'Có điều kiện loại trừ cần đối chiếu');
  const gradeLabel = (grade, activity) => grade === 'GOOD' ? 'Ngày Đẹp cho '+activity.toLowerCase() : (gradeNames[grade] || 'Chưa đủ kết luận');
  let query = null, controller = null, revision = 0, popup = null, detailController = null, resultSpec = null;
  let catalog = new Map(), catalogLoading = false;
  let ichingMethod = 'coins';
  function showWorkspace(mode) {
    const iching = mode === 'maihoa' || mode === 'coins';
    for (const name of ['draw','dates','maihoa','coins','bazi']) {
      el((name === 'dates' ? 'date' : name)+'-workspace').hidden = mode !== name;
      el('show-'+name).setAttribute('aria-pressed', String(mode === name));
    }
    el('show-iching').setAttribute('aria-pressed', String(iching));
    el('iching-methods').hidden = !iching;
    if (iching) ichingMethod = mode;
    if (mode === 'dates' && !query) {el('date-birth-1').value = el('birth-date').value; el('date-override-1').value = el('override').value;}
  }
  for (const mode of ['draw','dates','maihoa','coins','bazi']) el('show-'+mode).addEventListener('click', () => showWorkspace(mode));
  el('show-iching').addEventListener('click', () => el('show-'+ichingMethod).click());
  function updateSubjectLabels() {
    const spec = catalog.get(el('date-activity').value), two = spec?.subject_count === 2;
    el('date-second-person').hidden = !two; el('date-birth-2').required = two;
    for (const name of ['date-birth-2','date-override-2','date-uncertainty-2']) el(name).disabled = !two;
    el('date-subject-label-1').textContent = window.DisplayText.plain(subjectLabel(spec, 0));
    el('date-subject-label-2').textContent = window.DisplayText.plain(subjectLabel(spec, 1));
    const dayOnly = spec?.hour_evaluation_mode === 'DAY_ONLY';
    el('date-hours').hidden = dayOnly;
    for (const name of ['date-hour-start','date-hour-end']) {el(name).required = !dayOnly;el(name).disabled = dayOnly;}
    el('date-event-anchor').textContent = window.DisplayText.plain(spec ? 'Mốc tra: '+spec.event_anchor : '');
    el('date-activity-note').textContent = window.DisplayText.plain(spec?.scope_note || '');
    el('date-hour-capability').textContent = dayOnly ? 'Chỉ xét ngày và hồ sơ; chưa khuyến nghị giờ cho việc này.' : 'Xét ngày và giờ bắt đầu trong khoảng tổ chức đã chọn.';
  }
  function updateActivities(preferred) {
    const available = [...catalog.values()].filter(a=>a.enabled && a.group_id === el('date-group').value);
    el('date-activity').replaceChildren();
    for (const a of available) {const option = text(el('date-activity'),'option',a.name);option.value=a.activity;}
    if (available.some(a=>a.activity === preferred)) el('date-activity').value = preferred;
    el('date-activity').disabled = !available.length;
    updateSubjectLabels();
  }
  async function loadCatalog() {
    if (catalogLoading) return;
    catalogLoading = true; el('date-catalog-retry').hidden = true;
    el('date-catalog-status').textContent = 'Đang tải danh mục việc…';
    try {
      const response = await window.ArcanaClient.fetch('/api/v2/auspicious-dates/rules');
      if (!response.ok) throw window.DisplayText.failure('Chưa tải được danh mục việc.');
      const data = await response.json();
      const enabled = data.activities.filter(a=>a.enabled);
      if (!enabled.length || !data.groups?.length) throw window.DisplayText.failure('Danh mục việc chưa sẵn sàng.');
      catalog = new Map(enabled.map(a=>[a.activity,a]));
      el('date-group').replaceChildren();
      for (const group of data.groups.filter(g=>enabled.some(a=>a.group_id === g.group_id))) {
        const option = text(el('date-group'),'option',group.name);option.value=group.group_id;
      }
      el('date-group').value = 'BUSINESS_ASSETS'; el('date-group').disabled = false;
      updateActivities('BUSINESS_OPENING'); el('date-search-button').disabled = false;
      el('date-catalog-status').textContent = `${data.groups.length} nhóm · ${enabled.length} việc trọng đại`;
    } catch(error) {
      el('date-catalog-status').textContent = window.DisplayText.errorMessage(error,'Chưa tải được danh mục việc.');
      el('date-catalog-retry').hidden = false; el('date-search-button').disabled = true;
    } finally {catalogLoading = false;}
  }
  el('date-group').addEventListener('change',()=>updateActivities());
  el('date-catalog-retry').addEventListener('click',loadCatalog);
  el('date-activity').addEventListener('change', updateSubjectLabels);
  updateSubjectLabels();
  loadCatalog();
  const now = new Date(Date.now()+7*3600000).toISOString().slice(0,10);
  const validNow = now >= '2024-01-01' && now <= '2030-12-31' ? now : '2026-10-12';
  el('date-start').value = validNow;
  const end = new Date(validNow+'T00:00:00Z'); end.setUTCDate(end.getUTCDate()+30);
  el('date-end').value = end.toISOString().slice(0,10) > '2030-12-31' ? '2030-12-31' : end.toISOString().slice(0,10);
  const clock = value => value.slice(17,19) === '00' ? value.slice(11,16) : value.slice(11,19);
  const windowLabel = w => {
    const endClock = w.end_at.slice(0,10) !== w.start_at.slice(0,10) ? '24:00' : clock(w.end_at);
    return `Giờ ${branches[w.hour_branch] || w.hour_branch} - Từ ${clock(w.start_at)} đến ${endClock}`;
  };
  const periodLabel = w => `Từ ${clock(w.start_at)} đến ${w.end_at.slice(0,10) !== w.start_at.slice(0,10) ? '24:00' : clock(w.end_at)}`;
  function subject(i) {
    let birthClock = el('date-birth-'+i).value; if (birthClock.length === 16) birthClock += ':00';
    const birth = {civil_datetime:birthClock+'+07:00'};
    const override = el('date-override-'+i).value, uncertainty = el('date-uncertainty-'+i).value;
    if (override) birth.override_dung_than = override;
    if (uncertainty !== '') birth.clock_uncertainty_seconds = Number(uncertainty);
    return {subject_id:'person_'+i, birth};
  }
  async function fetchDates(payload, signal) {
    const response = await window.ArcanaClient.fetch('/api/v2/auspicious-dates/search', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),signal});
    const data = await response.json();
    if (!response.ok) throw window.DisplayText.responseError(data,'Không thể tra ngày lúc này. Bạn có thể thử lại.');
    return data;
  }
  function render(data) {
    resultSpec = data.activity_spec;
    const dayOnly = data.evaluation_mode === 'DAY_ONLY';
    el('date-empty').hidden = true; el('date-results').hidden = false;
    el('date-result-heading').textContent = window.DisplayText.plain('Ngày cho '+data.activity_name.toLowerCase());
    el('date-coverage').textContent = window.DisplayText.plain(data.coverage_note+' '+resultSpec.scope_note);
    el('date-profile-summary').replaceChildren();
    for (const p of data.subject_summaries) text(el('date-profile-summary'),'p',`${subjectName(p.subject_id)}: Dụng Thần ${p.primary}${p.overridden?' (nhập đè)':''} · Hỷ ${p.hy.join(', ')} · Kỵ ${p.ky.join(', ')}`,'hint');
    for (const warning of data.warnings) text(el('date-profile-summary'),'p',subjectName(warning.subject_id)+': '+warning.message,'hint');
    const good = data.days.filter(d=>d.grade === 'GOOD').length;
    el('date-result-summary').textContent = window.DisplayText.plain(dayOnly ? `${good} ngày có khoảng đạt mức Ngày Đẹp cho ${data.activity_name.toLowerCase()}. Đã xét ngày; chưa khuyến nghị giờ. Bấm vào ngày để xem phạm vi và lý do.` : good ? `${good} ngày có khung đẹp cho ${data.activity_name.toLowerCase()}. Bấm vào ngày để xem giờ đẹp.` : 'Chưa có khung đạt mức Ngày Đẹp trong phạm vi này. Bấm vào ngày để xem lý do.');
    el('date-grid').replaceChildren();
    for (const day of data.days) {
      const button = text(el('date-grid'),'button','', 'date-tile '+(day.grade||'UNKNOWN').toLowerCase()); button.type = 'button';
      text(button,'strong',day.date.slice(8)+'/'+day.date.slice(5,7));
      const label = day.assessment_state === 'FILTERED' ? 'Ngoài lịch đã chọn' : (gradeNames[day.grade] || 'Chưa đủ kết luận');
      text(button,'span',label);
      const count = day.recommended_windows.length;
      const capability = day.assessment_state === 'FILTERED' ? 'Không đánh giá' : dayOnly ? 'Đã xét ngày · Chưa xét giờ' : count ? `${count} khung giờ đẹp` : day.has_unresolved_windows ? 'Có khung chưa rõ' : 'Chưa có giờ đẹp';
      text(button,'small',capability);
      text(button,'span',day.assessment_state === 'FILTERED' ? 'Không áp dụng' : count ? 'Xem giờ đẹp ↗' : 'Xem đánh giá ↗','date-tile-action');
      button.disabled = day.assessment_state === 'FILTERED';
      button.setAttribute('aria-label',[day.date,label,data.activity_name,capability].join(' · '));
      button.setAttribute('aria-haspopup','dialog'); button.setAttribute('aria-controls','date-popup');
      button.addEventListener('click',()=>openDatePopup(day,data));
    }
    window.ResultPDF?.mount(el('date-results'),'Tra ngày · '+data.activity_name);
    el('date-result-heading').focus({preventScroll:true});
    el('date-result-heading').scrollIntoView({behavior:'smooth',block:'start'});
  }
  function resetPopup() {
    popup?.reading?.destroy();
    detailController?.abort(); detailController = null; popup = null;
    document.body.classList.remove('date-popup-open');
  }
  function closePopup() {
    resetPopup();
    if (el('date-popup').open) el('date-popup').close();
  }
  function openDatePopup(day, data) {
    if (!query) return;
    resetPopup(); popup = {day, query, loaded:false, loading:false,reading:null};
    const dayOnly = data.evaluation_mode === 'DAY_ONLY', activityName = data.activity_name;
    el('date-popup-title').textContent = window.DisplayText.plain((dayOnly ? 'Đánh giá ngày ' : 'Khung giờ ngày ')+day.date.split('-').reverse().join('/'));
    const count = day.recommended_windows.length;
    el('date-popup-summary').textContent = window.DisplayText.plain(dayOnly ? `${gradeLabel(day.grade,activityName)}. Đã xét ngày; chưa khuyến nghị giờ.` : `${gradeLabel(day.grade,activityName)} · ${count} khung giờ đẹp cho ${activityName.toLowerCase()}.`);
    if (day.has_unresolved_windows) el('date-popup-summary').textContent += ' Có khoảng chưa đủ dữ liệu kết luận.';
    el('date-popup-time-note').textContent = dayOnly ? 'Các khoảng dưới đây là phạm vi hiệu lực của đánh giá ngày, chưa phải giờ đẹp. Mốc theo UTC+7; đầu khoảng bao gồm, cuối khoảng không bao gồm.' : 'Khoảng giờ Việt Nam UTC+7; tên giờ theo lịch Bắc Kinh UTC+8. Đầu khung bao gồm, cuối khung không bao gồm.';
    el('date-detail-label').textContent = dayOnly ? 'Xem lý do và phạm vi đánh giá ngày' : 'Xem lý do đánh giá từng khung giờ';
    el('date-good-hours').replaceChildren();
    const recommendations = dayOnly ? day.recommended_day_periods : day.recommended_windows;
    for (const w of recommendations) text(el('date-good-hours'),'li',dayOnly ? 'Đánh giá ngày có hiệu lực: '+periodLabel(w) : windowLabel(w));
    el('date-good-hours').setAttribute('aria-label',dayOnly ? 'Khoảng hiệu lực của đánh giá ngày phù hợp' : 'Các khung giờ đẹp');
    el('date-good-hours').hidden = !recommendations.length; el('date-good-hours-empty').hidden = !!recommendations.length;
    el('date-good-hours-empty').textContent = dayOnly ? 'Chưa có khoảng của ngày đạt mức Ngày Đẹp. Mở phần lý do để đối chiếu; giờ chưa được đánh giá.' : day.has_unresolved_windows ? 'Chưa có khung đạt mức Ngày Đẹp; có khung chưa đủ dữ liệu kết luận. Mở phần lý do để đối chiếu.' : 'Chưa có khung đạt mức Ngày Đẹp trong lịch đã chọn. Mở phần lý do để đối chiếu.';
    el('date-detail').open = false; el('date-detail-status').textContent = ''; el('date-detail-body').replaceChildren();
    el('date-detail-retry').hidden = true;
    document.body.classList.add('date-popup-open');
    if (!el('date-popup').open) el('date-popup').showModal();
    el('date-popup-content').scrollTop = 0;
    const state=popup;
    state.reading=window.DateReading.mount(el('date-reading'),{...state.query,date_range:{start:day.date,end:day.date},include_details:true},{onLoad(saved){
      if(state!==popup)return;
      state.data=saved.result;detail(state);
    }});
  }
  async function detail(state) {
    if (!state || state !== popup || state.loaded || state.loading || !state.data) return;
    state.loading = true; detailController = new AbortController();
    el('date-detail-retry').hidden = true;
    el('date-detail-status').textContent = 'Đang lấy chi tiết…'; el('date-detail-body').replaceChildren();
    try {
      const data = state.data;
      if (state !== popup) return;
      state.loaded = true;
      const dayOnly = data.evaluation_mode === 'DAY_ONLY';
      el('date-detail-status').textContent = dayOnly ? 'Đánh giá ngày tại từng khoảng hiệu lực, chưa xét trụ giờ.' : 'Đánh giá tất cả khung giờ trong lịch đã chọn.';
      for (const w of (dayOnly ? data.days[0].day_periods : data.days[0].windows)) {
        const article = text(el('date-detail-body'),'article','', 'date-window '+(w.grade||'UNKNOWN').toLowerCase());
        text(article,'h4',`${dayOnly ? 'Phạm vi · '+periodLabel(w) : windowLabel(w)} · ${gradeLabel(w.grade,data.activity_name)}${w.score === null?'':' · '+w.score+' điểm'}`);
        text(article,'p',`${w.calendar_class === 'HOANG_DAO'?'Hoàng Đạo':'Hắc Đạo'} · ${gods[w.tian_shen]||w.tian_shen} · Trực ${officers[w.day_officer]||w.day_officer} · Ngày lịch ${w.civil_day_ganzhi} / Bát Tự ${w.bazi_day_ganzhi}`,'hint');
        text(article,'p',`Việc theo ngày: ${statusNames[w.day_activity_status]}${dayOnly ? ' · Chưa đánh giá giờ' : ' · Theo giờ: '+statusNames[w.hour_activity_status]}`);
        if (w.hard_exclusions.length) text(article,'p','Loại trừ: '+w.hard_exclusions.map(exclusionName).join(', '));
        for (const warning of (w.rule_warnings || [])) text(article,'p','Lưu ý: '+warning.message,'hint');
        for (const p of w.subject_assessments) text(article,'p',subjectName(p.subject_id)+' · '+({SUPPORTED:'Phù hợp theo hành',TENSION:'Có hành Kỵ',CLASH:'Xung chi năm/ngày sinh',UNSTABLE_BIRTH:'Giờ sinh có thể đổi trụ'}[p.status]||p.status));
        const details = text(article,'details',''); text(details,'summary','Cách tính điểm và đối chiếu lịch');
        for (const p of w.penalties) text(details,'p',`−${p.points}: ${p.message}`);
        text(details,'p','Ngày nên: '+w.facts.day_yi.join(' · ')); text(details,'p','Ngày kỵ: '+w.facts.day_ji.join(' · '));
        if (!dayOnly) {text(details,'p','Giờ nên: '+w.facts.hour_yi.join(' · ')); text(details,'p','Giờ kỵ: '+w.facts.hour_ji.join(' · '));}
      }
      const sourceNames={'6TAIL_CORPUS':'Lịch Can Chi và việc nên kỵ','TINIX_MONTH_TABLES':'Bảng tra theo tháng','PRODUCT_PERSONAL_POLICY':'Quy tắc đối chiếu hồ sơ','PRODUCT_ACTIVITY_POLICY':'Quy tắc theo việc đã chọn'};
      for (const source of data.sources)window.DisplayText.sourceLink(el('date-detail-body'),sourceNames[source.source_id] || 'Nguồn đối chiếu lịch',source.url);
    } catch(error) {
      if(error.name !== 'AbortError' && state === popup) {el('date-detail-status').textContent = window.DisplayText.errorMessage(error,'Chưa tải được chi tiết của ngày này. Bạn có thể thử lại.'); el('date-detail-retry').hidden = false;}
    } finally {state.loading = false;}
  }
  el('date-popup-close').addEventListener('click',closePopup);
  el('date-popup').addEventListener('cancel',event=>{event.preventDefault();closePopup();});
  el('date-popup').addEventListener('close',()=>{if(!el('date-popup').open) resetPopup();});
  el('date-popup').addEventListener('keydown',event=>{
    if(event.key !== 'Tab') return;
    const controls = [...el('date-popup').querySelectorAll('button:not(:disabled), summary, a[href], [tabindex]:not([tabindex="-1"])')].filter(node=>node.getClientRects().length);
    const target = event.shiftKey ? controls.at(-1) : controls[0];
    if(document.activeElement === (event.shiftKey ? controls[0] : controls.at(-1))) {event.preventDefault();target?.focus();}
  });
  let backdropPressed = false;
  const isBackdrop = event => {const rect = el('date-popup').getBoundingClientRect();return event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom;};
  el('date-popup').addEventListener('pointerdown',event=>{backdropPressed = isBackdrop(event);});
  el('date-popup').addEventListener('click',event=>{if(backdropPressed && isBackdrop(event)) closePopup();backdropPressed = false;});
  el('date-detail').addEventListener('toggle',()=>{if(el('date-detail').open) detail(popup);});
  el('date-detail-retry').addEventListener('click',()=>detail(popup));
  el('date-form').addEventListener('submit',async event => {
    event.preventDefault(); const run = ++revision; controller?.abort(); controller = new AbortController();
    el('date-error').hidden = true; el('date-search-button').disabled = true; el('date-progress').textContent = 'Đang đối chiếu ngày và hồ sơ…';
    closePopup(); el('date-results').hidden = true;
    const activity = el('date-activity').value, spec = catalog.get(activity);
    if (!spec) {el('date-search-button').disabled=false;el('date-progress').textContent='Vui lòng tải lại danh mục việc.';return;}
    const payload = {activity,subjects:spec.subject_count === 2?[subject(1),subject(2)]:[subject(1)],
      date_range:{start:el('date-start').value,end:el('date-end').value},
      allowed_weekdays:[...document.querySelectorAll('[name="date-weekday"]:checked')].map(x=>Number(x.value))};
    if (spec.hour_evaluation_mode !== 'DAY_ONLY') payload.allowed_hours={start:el('date-hour-start').value,end:el('date-hour-end').value};
    try {const data = await fetchDates(payload,controller.signal);if(run !== revision)return;query=payload;render(data);el('date-progress').textContent='Đã tra xong.';}
    catch(error){if(error.name !== 'AbortError' && run === revision){el('date-error').textContent=window.DisplayText.errorMessage(error,'Chưa tra được ngày. Bạn có thể thử lại.');el('date-error').hidden=false;el('date-progress').textContent='';}}
    finally {if(run === revision)el('date-search-button').disabled=false;}
  });
})();
