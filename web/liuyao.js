/* A saved casting can be interpreted again without ever posting new coins. */
(() => {
  const node = (parent, tag, value = '', cls = '') => {
    const item = document.createElement(tag); item.textContent = window.DisplayText.plain(value); item.className = cls; parent.appendChild(item); return item;
  };
  const activity = {MOVING:'Minh động', DARK_ACTIVE:'Ám động sơ bộ', STATIC:'Tĩnh', DAY_CLASH_WEAK:'Nhật xung · hào chưa vượng'};
  const stateLabels = {SUPPORTED:'Được sinh phù', MIXED:'Nhật–Nguyệt đan xen', WEAK:'Chưa được sinh phù'};
  const flags = {VOID:'Không', MONTH_CLASH:'Nguyệt Phá', DAY_CLASH:'Nhật xung', MONTH_COMBINE:'Nguyệt hợp', DAY_COMBINE:'Nhật hợp', MONTH_VALUE:'Trực Nguyệt', DAY_VALUE:'Trực Nhật'};
  const transforms = {RETURN_GENERATES:'Hồi đầu sinh', RETURN_CONTROLS:'Hồi đầu khắc', RETURN_SAME:'Hóa đồng hành', RETURN_DRAINS:'Hóa tiết khí', RETURN_CONSUMES:'Hóa hao khí', ADVANCE:'Hóa tiến', RETREAT:'Hóa thoái', REPEAT:'Phục ngâm', RETURN_CLASH:'Phản ngâm', RETURN_COMBINE:'Hóa hợp', CHANGED_VOID:'Hóa Không', CHANGED_MONTH_CLASH:'Hóa Phá'};
  let generation = 0, controller = null, rulesPromise = null, reportGate = null, aiPanel=null;
  function reset() {generation++; controller?.abort(); controller = null; reportGate?.destroy(); reportGate = null;aiPanel?.destroy();aiPanel=null;}
  async function json(url, options = {}) {
    const response = await window.ArcanaClient.fetch(url, options); const data = await response.json();
    if (!response.ok) throw window.DisplayText.responseError(data,'Chưa tải được lời luận.');
    return data;
  }
  function link(parent, source, label) {
    window.DisplayText.sourceLink(parent,label || source.title,source.url);
  }
  function option(select, value, label) {const item = node(select, 'option', label); item.value = value;}
  function field(parent, label, aria) {
    const wrap = node(parent, 'label', label); const select = node(wrap, 'select'); select.setAttribute('aria-label', aria || label); return select;
  }
  function drawReport(parent, data,autoGenerate=false) {
    aiPanel?.destroy();
    parent.replaceChildren(); parent.dataset.tendency = data.tendency;
    aiPanel=window.AIReading.mount(node(parent,'section'),{method:'LIUYAO',consultation_id:data.session_id,
      analysis_context:data.context,analysis_rules_sha256:data.rules_sha256},{autoGenerate:false});
    const technical=node(parent,'details','','ly-technical');node(technical,'summary','Phân tích Lục Hào và căn cứ');parent=technical;
    node(parent, 'p', 'LỜI LUẬN THEO VIỆC HỎI · ' + data.topic_label.toLocaleUpperCase('vi'), 'eyebrow');
    node(parent, 'h3', data.headline, 'ly-headline');
    node(parent, 'p', 'Phân tích bằng quy tắc Lục Hào · ' + (data.selection.status === 'PROVISIONAL' ? 'Dụng thần tạm ưu tiên, có thể chọn lại' : data.selection.status === 'AMBIGUOUS' ? 'Đang đối chiếu nhiều Dụng thần' : 'Đã xác định hào trọng tâm'), 'hint');
    if (data.intent) {
      const intent = node(parent, 'details', '', 'ly-intent-evidence'); node(intent, 'summary', 'Chủ đề và ý nhận diện từ câu hỏi');
      node(intent, 'p', data.intent.needs_review && data.context.intent_acknowledged ? 'Bạn đã xác nhận giữ chủ đề ' + data.topic_label + ' để luận.' : data.intent.message);
      for (const candidate of data.intent.candidates) node(intent, 'p', candidate.label + ': ' + candidate.intent_labels.join(' · ') + '. Tín hiệu: ' + candidate.terms.join(', ') + '.');
    }
    for (const paragraph of data.narrative) node(parent, 'p', paragraph);
    if (data.roles.length) {
      const roles = node(parent, 'div', '', 'ly-roles');
      for (const role of data.roles) {
        const card = node(roles, 'div'); node(card, 'small', role.role === 'Dụng thần' ? 'Dụng · cùng hành' : role.role); node(card, 'strong', role.element);
        const names = role.line_keys.map(key => 'hào ' + key.slice(1)).join(', ');
        node(card, 'span', names || 'Không hiện ở quẻ chủ');
      }
    }
    const factors = node(parent, 'div', '', 'ly-factor-grid');
    for (const [effect, title] of [['SUPPORT','Điểm nâng đỡ'], ['OBSTACLE','Điểm cản trở']]) {
      const column = node(factors, 'section', '', 'ly-factor ' + effect.toLowerCase()); node(column, 'h4', title);
      const rows = data.findings.filter(row => row.effect === effect);
      if (!rows.length) node(column, 'p', 'Chưa có yếu tố trực tiếp được xác lập trong phạm vi đang xét.', 'hint');
      else {const list = node(column, 'ul'); for (const row of rows) {const li = node(list, 'li'); node(li, 'strong', row.title); node(li, 'p', row.explanation);}}
    }
    const conditions = data.findings.filter(row => row.effect === 'CONDITION');
    if (conditions.length) {
      const details = node(parent, 'details', '', 'ly-conditions'); node(details, 'summary', 'Điều kiện có thể thay đổi kết luận · ' + conditions.length);
      for (const row of conditions) {node(details, 'h4', row.title); node(details, 'p', row.explanation);}
    }
    const lines = node(parent, 'details', '', 'ly-lines'); node(lines, 'summary', 'Xét từng hào · Nhật–Nguyệt và động biến');
    node(lines, 'p', 'Vượng, Tướng, Hưu, Tù, Tử là thuật ngữ khí mùa của ngũ hành; “Tử” ở đây không phải dự báo sinh tử. Khí mùa chưa phải toàn bộ sức hào.', 'hint');
    for (const row of [...data.lines].reverse()) {
      const article = node(lines, 'article', '', 'ly-line-card');
      node(article, 'h4', `${row.visibility === 'HIDDEN' ? 'Phục thần dưới hào' : 'Hào'} ${row.position} · ${row.relative} ${row.branch} ${row.element}`);
      node(article, 'p', `${activity[row.activity]} · Khí mùa: ${row.seasonal_state} · ${stateLabels[row.calendar_state]}`, 'ly-line-state');
      node(article, 'p', row.calendar_summary);
      const tags = [...row.flags.map(flag => flags[flag]), ...row.transformation.map(t => transforms[t])];
      if (tags.length) node(article, 'p', tags.join(' · '), 'hint');
      for (const caveat of row.caveats) node(article, 'p', caveat, 'hint');
    }
    if (data.timing_conditions.length) {
      const details = node(parent, 'details'); node(details, 'summary', 'Điều kiện ứng kỳ cần đối chiếu');
      node(details, 'p', 'Các chi dưới đây là điều kiện tham chiếu, chưa phải ngày dự báo.', 'hint');
      for (const item of data.timing_conditions) {node(details, 'h4', (item.line_key.startsWith('H') ? 'Phục thần' : 'Hào') + ' ' + item.line_key.slice(1) + ' · ' + item.branches.join(', ')); node(details, 'p', item.explanation);}
    }
    const actions = node(parent, 'div', '', 'ly-actions'); node(actions, 'h4', 'Mang lời luận về việc thực tế');
    const list = node(actions, 'ul'); for (const question of data.practical_questions) node(list, 'li', question);
    const evidence = node(parent, 'details'); node(evidence, 'summary', 'Căn cứ của từng nhận định · ' + data.findings.length);
    for (const row of data.findings) {
      const article = node(evidence, 'article', '', 'ly-evidence'); node(article, 'h4', row.title); node(article, 'p', row.explanation);
      const lines=row.evidence.filter(value=>/^[LH][1-6]$/.test(value)).map(value=>value[0]==='L'?'hào '+value[1]:'phục thần '+value[1]);
      if(lines.length)node(article, 'small', lines.join(' · '), 'hint');
      for (const id of row.source_ids) {const source = data.sources.find(item => item.id === id); if (source) {link(article, source); node(article, 'br');}}
    }
    const scope = node(parent, 'details'); node(scope, 'summary', 'Phương pháp, nguồn và phạm vi lời luận');
    for (const line of data.limitations) node(scope, 'p', line, 'hint');
    for (const source of data.sources) {link(scope, source); node(scope, 'br');}
  }
  function mount(parent, session, initialContext = null, {autoGenerate=false}={}) {
    reset(); let current = generation, report = null, pendingContext = null, gate = null, preparing = false;
    parent.className = 'ly-panel'; parent.setAttribute('aria-label', 'Luận Lục Hào theo câu hỏi');
    const output = node(parent, 'div', '', 'ly-report');
    const controls = node(parent, 'details', '', 'ly-controls'); node(controls, 'summary', 'Đổi chủ đề hoặc chọn Dụng thần · giữ nguyên quẻ');
    parent.insertBefore(controls, output);
    const form = node(controls, 'form');
    const topic = field(form, 'Chủ đề luận', 'Chủ đề luận lại');
    const intentPreview = node(form, 'div');
    const relative = field(form, 'Chỉ định Lục thân (nếu cần)', 'Chỉ định Lục thân');
    option(relative, '', 'Theo chủ đề'); for (const name of ['Phụ mẫu','Huynh đệ','Tử tôn','Thê tài','Quan quỷ']) option(relative, name, name);
    const focus = field(form, 'Hào Dụng thần', 'Hào Dụng thần'); option(focus, '', 'Theo quy tắc, giữ các ứng viên');
    const submit = node(form, 'button', 'Luận lại trên quẻ này ↗'); submit.type = 'submit';
    const status = node(parent, 'p', 'Đang phân tích Dụng thần và các quan hệ trong quẻ…', 'hint'); status.setAttribute('role', 'status');
    const error = node(parent, 'p'); error.hidden = true; error.setAttribute('role', 'alert');
    const retry = node(parent, 'button', 'Thử tải lời luận'); retry.type = 'button'; retry.className = 'secondary'; retry.hidden = true;
    const base = '/api/v1/coins/consultations/' + encodeURIComponent(session.request_id) + '/analysis';
    const active = version => current === generation && version === current && parent.isConnected;
    function setBusy(value) {for (const field of form.elements) field.disabled = value;}
    function sync(data) {
      report = data; topic.value = data.context.topic; relative.value = data.context.use_relative || '';
      focus.replaceChildren(); option(focus, '', 'Theo quy tắc, giữ các ứng viên');
      for (const key of data.selection.candidate_keys) {
        const row = data.lines.find(line => line.key === key);
        option(focus, row.position, `${row.visibility === 'HIDDEN' ? 'Phục thần dưới hào' : 'Hào'} ${row.position} · ${row.relative} ${row.branch}`);
      }
      focus.value = data.context.focus_line || '';
      gate?.restore(data.context);
    }
    async function run(context, loadSaved = false) {
      controller?.abort(); controller = new AbortController(); const requestController = controller;
      const version = ++generation; current = version; pendingContext = context;
      const timer = setTimeout(() => requestController.abort(), 20000);
      setBusy(true); error.hidden = true; retry.hidden = true; status.textContent = 'Đang phân tích trên đúng quẻ đã lưu…';
      try {
        let data = loadSaved ? await json(base, {signal:requestController.signal}) : null;
        if (!data) {
          const requested = context || await gate.ensure();
          if (!active(version)) return;
          data = await json(base, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(requested), signal:requestController.signal});
        }
        if (!active(version)) return;
        if (data.session_id !== session.request_id) throw window.DisplayText.failure('Lời luận không khớp phiên đang mở.');
        sync(data); drawReport(output, data,autoGenerate || !loadSaved);autoGenerate=false; status.textContent = '';
        if (data.selection.status === 'AMBIGUOUS') controls.open = true;
      } catch (failure) {
        if (!active(version)) return;
        error.textContent = failure.name === 'AbortError' ? 'Chưa nhận được lời luận. Có thể thử lại trên cùng quẻ.' : window.DisplayText.errorMessage(failure,'Chưa tải được lời luận. Bạn có thể thử lại trên cùng quẻ.');
        error.hidden = false; retry.hidden = false; status.textContent = 'Quẻ đã được lưu; phần luận chưa tải thành công.';
        controls.open = true;
      } finally {clearTimeout(timer); if (active(version)) setBusy(false);}
    }
    function clearFocus() {focus.replaceChildren(); option(focus, '', 'Luận theo nhóm mới để xem các ứng viên');}
    topic.addEventListener('change', () => {relative.value = ''; clearFocus();});
    relative.addEventListener('change', clearFocus);
    form.addEventListener('submit', async event => {
      event.preventDefault(); if (preparing) return; preparing = true; const before = current;
      try {
        const context = await gate.ensure();
        if (before === current && before === generation && parent.isConnected) await run({...context, use_relative:relative.value || null, focus_line:focus.value ? Number(focus.value) : null});
      } catch (failure) {if (parent.isConnected) {error.textContent = window.DisplayText.errorMessage(failure,'Chưa đối chiếu được câu hỏi. Bạn có thể thử lại.'); error.hidden = false; controls.open = true;}}
      finally {preparing = false;}
    });
    retry.addEventListener('click', () => {if (!rulesPromise) initialize(); else run(pendingContext, !pendingContext);});
    async function initialize() {
      setBusy(true);
      try {
        rulesPromise ||= json('/api/v1/coins/analysis-rules').catch(failure => {rulesPromise = null; throw failure;});
        const rules = await rulesPromise; if (current !== generation || !parent.isConnected) return;
        topic.replaceChildren(); for (const [key, value] of Object.entries(rules.topics)) option(topic, key, value.label);
        topic.value = initialContext?.topic || 'GENERAL';
        gate = window.CoinIntent.attach({container:intentPreview, topic, question:() => session.question}); reportGate = gate;
        if (initialContext) gate.restore(initialContext);
        await run(initialContext, !initialContext);
      } catch (failure) {if (current === generation && parent.isConnected) {error.textContent = window.DisplayText.errorMessage(failure,'Chưa tải được quy tắc luận. Bạn có thể thử lại.'); error.hidden = false; retry.hidden = false; status.textContent = 'Chưa tải được quy tắc luận.';}}
    }
    initialize();
  }
  window.LiuYaoPanel = {mount, reset};
})();
