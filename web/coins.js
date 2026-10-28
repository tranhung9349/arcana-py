/* Three coins × six throws. Rendering always uses saved server results. */
(() => {
  const el = id => document.getElementById(id);
  const text = (parent, tag, value = '', cls = '') => {
    const node = document.createElement(tag); node.textContent = window.DisplayText.plain(value); node.className = cls; parent.appendChild(node); return node;
  };
  const lineNames = {6:'Lão âm · động ×', 7:'Thiếu dương · tĩnh', 8:'Thiếu âm · tĩnh', 9:'Lão dương · động ○'};
  const localDate = value => new Date(value).toLocaleString('vi-VN', {timeZone:'Asia/Ho_Chi_Minh'});
  const normalize = value => value.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd');
  let catalog = null, catalogLoading = false, pending = null, pendingAnalysisContext = null, controller = null, revision = 0, posting = false, preparing = false;
  const intent = window.CoinIntent.attach({container:el('coins-intent'), topic:el('coins-topic'), question:() => el('coins-question').value, questionInput:el('coins-question'), onResolved:() => {el('coins-error').hidden = true;}});

  for (let i = 1; i <= 6; i++) {
    const row = text(el('coins-manual-rows'), 'div', '', 'coins-manual-row');
    text(row, 'strong', 'Hào ' + i + (i === 1 ? ' · đầu' : i === 6 ? ' · trên' : ''));
    const faces = text(row, 'div', '', 'coins-manual-faces');
    for (let j = 1; j <= 3; j++) {
      const label = text(faces, 'label', 'Đồng ' + j);
      const select = text(label, 'select', ''); select.id = `coins-face-${i}-${j}`;
      select.setAttribute('aria-label', `Hào ${i}, đồng ${j}`);
      for (const [value, name] of [['','Chọn mặt'], ['BACK','背 Lưng · 3'], ['INSCRIPTION','字 Chữ · 2']]) {
        const option = text(select, 'option', name); option.value = value;
      }
      select.addEventListener('change', () => {
        const values = [1,2,3].map(k => el(`coins-face-${i}-${k}`).value);
        note.textContent = values.every(Boolean) ? lineNames[values.reduce((sum, face) => sum + (face === 'BACK' ? 3 : 2), 0)] : 'Chọn đủ ba mặt';
      });
    }
    const note = text(row, 'small', 'Chọn đủ ba mặt', 'hint'); note.setAttribute('aria-live', 'polite');
  }
  el('coins-custom-time').value = new Date(Date.now() + 7*3600000).toISOString().slice(0,19);

  function updateFields() {
    el('coins-question').disabled = !el('coins-topic').value;
    const manual = el('coins-source').value === 'MANUAL'; el('coins-manual').hidden = !manual;
    for (const select of el('coins-manual').querySelectorAll('select')) {select.disabled = !manual; select.required = manual;}
    const custom = el('coins-time-mode').value === 'CUSTOM'; el('coins-custom-field').hidden = !custom;
    el('coins-custom-time').required = custom;
    el('coins-submit').textContent = manual ? 'Lập quẻ từ 6 lượt đã gieo ↗' : 'Gieo 3 đồng × 6 lượt ↗';
  }
  function busy(value) {
    for (const field of el('coins-form').elements) field.disabled = value;
    if (!value) updateFields();
  }
  function sourceLink(parent, source, label) {
    window.DisplayText.sourceLink(parent,label || 'Nguồn kinh văn',source.url);
  }
  function evidence(parent, card) {
    const article = text(parent, 'article', '', 'reading-card'); text(article, 'h3', card.title);
    const columns = text(article, 'div', '', card.translation ? 'reading-columns' : '');
    const original = text(columns, 'div', ''); text(original, 'small', 'NGUYÊN VĂN HÁN', 'reading-label');
    text(original, 'p', card.text, 'source-text'); sourceLink(original, card.source);
    if (card.translation) {
      const vi = text(columns, 'div', '', 'translated-reading'); text(vi, 'small', 'NGHĨA VIỆT · AI CHƯA HIỆU ĐÍNH', 'reading-label');
      text(vi, 'p', card.translation.text);
    }
  }
  function hexagram(parent, reading, label, moving = []) {
    const card = text(parent, 'article', '', 'mh-hexagram'); text(card, 'small', label, 'reading-label');
    const lines = text(card, 'div', '', 'mh-lines'); lines.setAttribute('role', 'img');
    lines.setAttribute('aria-label', reading.chart.name_vi + ', sáu hào từ dưới lên: ' + reading.chart.lines_bottom_to_top.map(v => v ? 'dương' : 'âm').join(', '));
    for (let i = 5; i >= 0; i--) {
      const bit = reading.chart.lines_bottom_to_top[i];
      const line = text(lines, 'div', '', 'mh-line ' + (bit ? 'yang' : 'yin')); text(line, 'span', ''); text(line, 'span', '');
      if (moving.includes(i+1)) {line.classList.add('moving'); text(line, 'b', bit ? '○' : '×');}
    }
    text(card, 'h3', reading.chart.name_vi); text(card, 'small', '#' + reading.chart.hexagram_id + ' · ' + reading.chart.name_zh, 'hint');
    text(card, 'p', 'Thượng ' + reading.chart.upper_trigram + ' · Hạ ' + reading.chart.lower_trigram, 'hint');
  }
  function najia(parent, data) {
    const chart = data.najia; text(parent, 'h3', 'Bàn Lục Hào · Nạp Giáp cơ bản');
    text(parent, 'p', `Cung ${chart.palace} (${chart.palace_element}) · ${chart.stage} · Thế hào ${chart.world_line}, Ứng hào ${chart.response_line}.`);
    const pillars = data.calendar.pillars;
    text(parent, 'p', `Tháng ${pillars[1].stem} ${pillars[1].branch} · Ngày ${pillars[2].stem} ${pillars[2].branch} · Tuần Không: ${chart.void_branches.join(', ')}.`, 'hint');
    const wrap = text(parent, 'div', '', 'coins-table-wrap'); wrap.tabIndex = 0; wrap.setAttribute('role', 'region'); wrap.setAttribute('aria-label', 'Bảng Nạp Giáp, có thể cuộn ngang');
    const table = text(wrap, 'table', '', 'coins-table'); text(table, 'caption', 'Sáu hào trình bày từ trên xuống; lượt gieo đầu ứng với hào 1 dưới cùng.');
    const header = text(text(table, 'thead', ''), 'tr', '');
    for (const label of ['Hào', 'Lục thú', 'Lục thân', 'Nạp Giáp', 'Trạng thái', 'Hào biến']) text(header, 'th', label).scope = 'col';
    const body = text(table, 'tbody', '');
    for (const row of [...chart.lines_bottom_to_top].reverse()) {
      const tr = text(body, 'tr', '', row.moving ? 'coins-moving' : '');
      text(tr, 'th', row.position + (row.is_world ? ' · Thế' : row.is_response ? ' · Ứng' : '')).scope = 'row';
      text(tr, 'td', row.spirit); text(tr, 'td', row.relative); text(tr, 'td', `${row.stem} ${row.branch} · ${row.element}`);
      text(tr, 'td', [row.moving ? 'Động' : 'Tĩnh', row.void ? 'Không' : '', row.month_clash ? 'Phá' : ''].filter(Boolean).join(' · '));
      text(tr, 'td', row.moving ? `${row.changed_stem} ${row.changed_branch} · ${row.changed_relative}` : '—');
    }
  }
  function render(reading, session = null, analysisContext = null,autoGenerate=false) {
    window.LiuYaoPanel.reset();
    const parent = el('coins-result'); parent.replaceChildren(); parent.hidden = false; el('coins-empty').hidden = true;
    text(parent, 'p', session ? 'PHIÊN GIEO BA ĐỒNG' : 'TRA CỨU KINH VĂN · KHÔNG TẠO PHIÊN', 'eyebrow');
    const heading = text(parent, 'h2', session ? session.question : reading.chart.name_vi); heading.id = 'coins-result-title'; heading.tabIndex = -1;
    if (session) text(parent, 'p', localDate(session.calendar.civil_datetime) + ' · giờ Việt Nam · ' + (session.casting.source === 'MANUAL' ? 'Nhập kết quả gieo thật' : 'Gieo trên app'), 'hint');
    const charts = text(parent, 'div', '', 'coins-hexagrams'); hexagram(charts, reading, session ? 'Quẻ chủ' : 'Quẻ đang tra', session?.moving_lines || []);
    if (session?.changed) hexagram(charts, session.changed, 'Quẻ biến');
    if (session) {
      text(parent, 'p', session.moving_lines.length ? `Hào động: ${session.moving_lines.join(', ')}. Lật đồng thời các hào này để được quẻ biến.` : 'Sáu hào đều tĩnh · không có quẻ biến riêng.', 'coins-state');
      const throws = text(parent, 'details', '', 'coins-throw-record'); text(throws, 'summary', 'Xem đúng 6 lượt tiền đã gieo');
      for (const [i, faces] of session.casting.throws_bottom_to_top.entries()) {
        const row = text(throws, 'div', '', 'coins-saved-throw'); text(row, 'strong', 'Hào ' + (i+1));
        for (const face of faces) text(row, 'span', face === 'BACK' ? '背 3' : '字 2', 'coins-face ' + (face === 'BACK' ? 'back' : 'inscription'));
        text(row, 'small', session.casting.totals_bottom_to_top[i] + ' · ' + lineNames[session.casting.totals_bottom_to_top[i]]);
      }
    }
    if (session) window.LiuYaoPanel.mount(text(parent, 'section'), session, analysisContext,{autoGenerate});
    const overview = text(parent, 'div', '', 'coins-overview'); text(overview, 'small', 'KINH VĂN THAM KHẢO · NGHĨA VIỆT CHƯA HIỆU ĐÍNH', 'reading-label'); text(overview, 'p', reading.text.overview.text);
    evidence(parent, reading.text.cards.find(card => card.text_type === 'HEXAGRAM_TEXT'));
    if (session?.moving_lines.length) {
      text(parent, 'h3', 'Hào động · kinh văn để đối chiếu');
      for (const i of session.moving_lines) evidence(parent, reading.reference_lines[i-1]);
    }
    if (session) najia(parent, session);
    if (session?.changed) {
      const changed = text(parent, 'details', ''); text(changed, 'summary', 'Đọc thêm quẻ biến · ' + session.changed.chart.name_vi);
      text(changed, 'p', session.changed.text.overview.text); evidence(changed, session.changed.text.cards.find(card => card.text_type === 'HEXAGRAM_TEXT'));
    }
    const reference = text(parent, 'details', ''); text(reference, 'summary', 'Tra đủ 6 hào từ · từ dưới lên');
    for (const card of reading.reference_lines) evidence(reference, card);
    const comments = text(parent, 'details', ''); text(comments, 'summary', 'Thoán truyện và Tượng truyện · nguyên văn Hán');
    for (const card of reading.text.cards.filter(card => card.text_type !== 'HEXAGRAM_TEXT')) evidence(comments, card);
    for (const gap of reading.text.source_gaps) text(parent, 'p', gap.message, 'source-gap');
    if (session) {
      const guide = text(parent, 'details', ''); text(guide, 'summary', 'Cách đọc, phạm vi và nguồn của phiên');
      for (const note of [...session.reading_guide, ...session.limitations]) text(guide, 'p', note, 'hint');
      text(guide, 'p', session.calendar.policy, 'hint'); text(guide, 'p', session.casting.convention, 'hint');
      for (const source of session.sources) {sourceLink(guide, source, source.title + ' ↗'); text(guide, 'br', '');}
    }
    window.ResultPDF?.mount(parent,session?'Gieo quẻ Lục Hào':'Kinh văn quẻ');
    heading.focus({preventScroll:true});
    heading.scrollIntoView({behavior:'smooth', block:'start'});
  }
  function filterCatalog() {
    if (!catalog) return;
    const query = normalize(el('coins-search').value.trim()); const grid = el('coins-catalog'); grid.replaceChildren();
    const rows = catalog.hexagrams.filter(row => normalize(`${row.hexagram_id} ${row.name_vi} ${row.name_zh}`).includes(query));
    el('coins-catalog-status').textContent = `${rows.length} / 64 quẻ · chọn một quẻ để đọc kinh văn.`;
    for (const row of rows) {
      const button = text(grid, 'button', '', 'coins-catalog-card'); button.type = 'button';
      text(button, 'span', row.symbol, 'coins-symbol'); text(button, 'small', '#' + row.hexagram_id); text(button, 'strong', row.name_vi);
      button.setAttribute('aria-label', `Quẻ ${row.hexagram_id}, ${row.name_vi}`);
      button.addEventListener('click', () => perform('reading', row.hexagram_id));
    }
  }
  async function loadCatalog() {
    if (catalog || catalogLoading) return;
    catalogLoading = true; el('coins-catalog-retry').hidden = true; el('coins-catalog-status').textContent = 'Đang tải 64 quẻ…';
    try {
      const response = await window.ArcanaClient.fetch('/api/v1/coins/hexagrams', {signal:AbortSignal.timeout(15000)});
      if (!response.ok) throw new Error(); catalog = await response.json(); filterCatalog();
    } catch {el('coins-catalog-status').textContent = 'Chưa tải được thư viện.'; el('coins-catalog-retry').hidden = false;}
    finally {catalogLoading = false;}
  }
  async function perform(kind, target) {
    if (posting && (kind === 'new' || kind === 'retry')) return;
    if (kind === 'retry' && !pending) return;
    if (controller) controller.abort(); controller = new AbortController(); const currentController = controller;
    const generation = ++revision; const isPost = kind === 'new' || kind === 'retry';
    const timer = setTimeout(() => currentController.abort(), 20000); posting = isPost;
    el('coins-error').hidden = true; el('coins-retry').hidden = true; busy(true);
    el('coins-progress').textContent = isPost ? 'Đang ghi nhận đủ 6 lượt và lập bàn quẻ…' : 'Đang đọc kinh văn…';
    let payload;
    try {
      if (kind === 'new') {
        const casting = {mode:el('coins-time-mode').value};
        if (casting.mode === 'CURRENT') casting.clicked_at = new Date(Date.now() + 7*3600000).toISOString().slice(0,-1) + '+07:00';
        else {let value = el('coins-custom-time').value; if (value.length === 16) value += ':00'; casting.custom_timestamp = value + '+07:00';}
        pending = {request_id:crypto.randomUUID(), question:el('coins-question').value.trim(), source:el('coins-source').value, casting};
        pendingAnalysisContext = target || {topic:el('coins-topic').value};
        if (pending.source === 'MANUAL') pending.throws_bottom_to_top = Array.from({length:6}, (_,i) => [1,2,3].map(j => el(`coins-face-${i+1}-${j}`).value));
      }
      payload = isPost ? pending : null;
      const path = kind === 'reading' ? 'hexagrams/' + target : kind === 'saved' ? 'consultations/' + encodeURIComponent(target) : 'consultations';
      const options = {signal:currentController.signal};
      if (isPost) Object.assign(options, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
      const response = await window.ArcanaClient.fetch('/api/v1/coins/' + path, options); const data = await response.json();
      if (!response.ok) throw window.DisplayText.responseError(data,'Chưa tải được kết quả.');
      if (generation !== revision) return;
      if (isPost && data.request_id !== payload.request_id || kind === 'saved' && data.request_id !== target) throw window.DisplayText.failure('Kết quả không khớp phiên đang mở.');
      if (kind === 'reading') {render(data); el('coins-progress').textContent = 'Đang tra kinh văn; không tạo phiên gieo.';}
      else {render(data.original, data, isPost ? pendingAnalysisContext : null,isPost); el('coins-progress').textContent = 'Đã có kết quả của phiên này. Bạn có thể xuất PDF để giữ lại.';}
      if (isPost) pending = null;
      
    } catch (error) {
      if (generation !== revision) return;
      el('coins-error').textContent = error.name === 'AbortError' ? 'Chưa nhận được kết quả. Thử lại cùng phiên để kiểm tra.' : window.DisplayText.errorMessage(error,'Chưa tải được kết quả. Bạn có thể thử lại.');
      el('coins-error').hidden = false; el('coins-progress').textContent = 'Chưa nhận được kết quả.';
    } finally {
      clearTimeout(timer);
      if (generation === revision) {posting = false; busy(false); el('coins-retry').hidden = !pending;}
    }
  }
  el('coins-form').addEventListener('submit', async event => {
    event.preventDefault(); if (preparing || posting) return;
    preparing = true; el('coins-submit').disabled = true; const before = revision;
    try {const context = await intent.ensure(); if (before === revision) await perform('new', context);}
    catch (error) {el('coins-error').textContent = window.DisplayText.errorMessage(error,'Chưa đối chiếu được câu hỏi. Bạn có thể thử lại.'); el('coins-error').hidden = false;}
    finally {preparing = false; if (!posting) el('coins-submit').disabled = false;}
  });
  el('coins-retry').addEventListener('click', () => perform('retry'));
  el('coins-source').addEventListener('change', updateFields);
  el('coins-topic').addEventListener('change', updateFields);
  el('coins-time-mode').addEventListener('change', updateFields);
  el('coins-search').addEventListener('input', filterCatalog);
  el('coins-catalog-retry').addEventListener('click', loadCatalog);
  el('show-coins').addEventListener('click', () => {loadCatalog(); });
  updateFields();
})();
