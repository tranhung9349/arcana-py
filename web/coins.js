/* Three coins × six throws. Rendering always uses saved server results. */
(() => {
  const el = id => document.getElementById(id);
  const text = (parent, tag, value = '', cls = '') => {
    const node = document.createElement(tag); node.textContent = window.DisplayText.plain(value); node.className = cls; parent.appendChild(node); return node;
  };
  const lineNames = {6:'Âm · hào động', 7:'Dương', 8:'Âm', 9:'Dương · hào động'};
  const normalize = value => value.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd');
  let catalog = null, catalogLoading = false, pending = null, pendingAnalysisContext = null, controller = null, revision = 0, posting = false, preparing = false;
  let referenceController=null, referenceRevision=0, referenceId=null;
  const intent = window.CoinIntent.attach({container:el('coins-intent'), topic:el('coins-topic'), question:() => el('coins-question').value, questionInput:el('coins-question'), onResolved:() => {el('coins-error').hidden = true;}});

  function updateFields() {
    el('coins-question').disabled = !el('coins-topic').value;
    el('coins-submit').textContent = 'Gieo và lập quẻ';
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
  function render(reading, session = null, analysisContext = null,autoGenerate=false,parent=el('coins-result')) {
    if(session){window.LiuYaoPanel.reset();el('coins-empty').hidden = true;}
    parent.replaceChildren(); parent.hidden = false;
    text(parent, 'p', session ? 'PHIÊN GIEO BA ĐỒNG' : 'TRA CỨU KINH VĂN · KHÔNG TẠO PHIÊN', 'eyebrow');
    const heading = text(parent, 'h2', session ? session.question : reading.chart.name_vi); heading.id = session?'coins-result-title':'library-result-title'; heading.tabIndex = -1;
    const resultParent = parent;
    if (session) {
      const casting = text(parent, 'section', '', 'coins-cast-result');
      text(casting, 'h3', '6 lượt gieo');
      text(casting, 'p', '背 Lưng = 3 điểm · 字 Chữ = 2 điểm. Lượt đầu là hào dưới cùng.', 'hint');
      const throws = text(casting, 'div', '', 'coins-throws');
      for (const [i, faces] of session.casting.throws_bottom_to_top.entries()) {
        const row = text(throws, 'article', '', 'coins-throw-card'); text(row, 'strong', 'Lượt ' + (i+1));
        const coins = text(row, 'div', '', 'coins-throw-faces');
        for (const face of faces) {
          const coin = text(coins, 'span', face === 'BACK' ? '背' : '字', 'coins-face ' + (face === 'BACK' ? 'back' : 'inscription'));
          coin.setAttribute('aria-label', face === 'BACK' ? 'Lưng, 3 điểm' : 'Chữ, 2 điểm');
        }
        text(row, 'small', session.casting.totals_bottom_to_top[i] + ' điểm · ' + lineNames[session.casting.totals_bottom_to_top[i]]);
      }
    }
    const charts = text(parent, 'div', '', 'coins-hexagrams'); hexagram(charts, reading, session ? 'Quẻ chủ' : 'Quẻ đang tra', session?.moving_lines || []);
    if (session?.changed) hexagram(charts, session.changed, 'Quẻ biến');
    if (session) {
      text(parent, 'p', session.moving_lines.length ? `Hào động: ${session.moving_lines.join(', ')}. Lật đồng thời các hào này để được quẻ biến.` : 'Sáu hào đều tĩnh · không có quẻ biến riêng.', 'coins-state');
    }
    let analysisHost = null, referenceParent = null;
    if (session) {
      analysisHost = text(parent, 'section');
      parent = referenceParent = text(parent, 'details', '', 'coins-reference');
      text(parent, 'summary', 'Chi tiết quẻ và nguồn tham khảo');
    }
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
      window.LiuYaoPanel.mount(analysisHost, session, analysisContext,{autoGenerate,referenceParent});
    }
    window.ResultPDF?.mount(resultParent,session?'Gieo quẻ Lục Hào':'Kinh văn quẻ');
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
      button.addEventListener('click', () => openReference(row.hexagram_id));
    }
  }
  async function loadCatalog() {
    if (catalog || catalogLoading) return;
    catalogLoading = true; el('coins-catalog-retry').hidden = true; el('coins-catalog-status').textContent = 'Đang tải 64 quẻ…';
    try {
      const response = await window.ArcanaClient.fetch('/api/v1/coins/hexagrams', {signal:AbortSignal.timeout(15000)});
      if (!response.ok) throw new Error();
      const data=await response.json();
      if(!Array.isArray(data.hexagrams) || data.hexagrams.length!==64
        || new Set(data.hexagrams.map(row=>row.hexagram_id)).size!==64
        || data.hexagrams.some(row=>!Number.isInteger(row.hexagram_id) || row.hexagram_id<1 || row.hexagram_id>64
          || typeof row.name_vi!=='string' || typeof row.name_zh!=='string'))throw new Error();
      catalog = data; filterCatalog();
    } catch {catalog=null;el('coins-catalog-status').textContent = 'Chưa tải được thư viện.'; el('coins-catalog-retry').hidden = false;}
    finally {catalogLoading = false;}
  }
  async function openReference(id) {
    referenceController?.abort();referenceController=new AbortController();const requestController=referenceController,current=++referenceRevision;
    referenceId=id;el('library-catalog-panel').hidden=true;el('library-detail').hidden=false;el('library-result').hidden=true;
    el('library-error').hidden=true;el('library-retry').hidden=true;el('library-progress').textContent='Đang tải kinh văn quẻ '+id+'…';
    el('library-back').focus();const timer=setTimeout(()=>requestController.abort(),20000);
    try {
      const response=await window.ArcanaClient.fetch('/api/v1/coins/hexagrams/'+id,{signal:requestController.signal});
      const data=await response.json();
      if(current!==referenceRevision)return;
      el('library-result').hidden=true;
      if(!response.ok)throw window.DisplayText.responseError(data,'Chưa tải được quẻ. Bạn có thể thử lại.');
      if(data.chart?.hexagram_id!==id)throw window.DisplayText.failure('Kinh văn không khớp quẻ đã chọn.');
      render(data,null,null,false,el('library-result'));el('library-progress').textContent='';
    } catch(error) {
      if(current!==referenceRevision)return;
      el('library-result').hidden=true;
      el('library-error').textContent=window.DisplayText.errorMessage(error,'Chưa tải được quẻ. Bạn có thể thử lại.');
      el('library-error').hidden=false;el('library-retry').hidden=false;el('library-progress').textContent='';
    } finally {clearTimeout(timer);}
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
        const casting = {mode:'CURRENT',clicked_at:new Date(Date.now()+7*3600000).toISOString().slice(0,-1)+'+07:00'};
        pending = {request_id:crypto.randomUUID(), question:el('coins-question').value.trim(), source:'RANDOM', casting};
        pendingAnalysisContext = target || {topic:el('coins-topic').value};
      }
      payload = isPost ? pending : null;
      const path = kind === 'saved' ? 'consultations/' + encodeURIComponent(target) : 'consultations';
      const options = {signal:currentController.signal};
      if (isPost) Object.assign(options, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
      const response = await window.ArcanaClient.fetch('/api/v1/coins/' + path, options); const data = await response.json();
      if (!response.ok) throw window.DisplayText.responseError(data,'Chưa tải được kết quả.');
      if (generation !== revision) return;
      if (isPost && data.request_id !== payload.request_id || kind === 'saved' && data.request_id !== target) throw window.DisplayText.failure('Kết quả không khớp phiên đang mở.');
      render(data.original, data, isPost ? pendingAnalysisContext : null,isPost); el('coins-progress').textContent = 'Đã có kết quả của phiên này. Bạn có thể xuất PDF để giữ lại.';
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
  el('coins-topic').addEventListener('change', updateFields);
  el('coins-search').addEventListener('input', filterCatalog);
  el('coins-catalog-retry').addEventListener('click', loadCatalog);
  el('show-library').addEventListener('click', loadCatalog);
  el('library-retry').addEventListener('click',()=>{if(referenceId!==null)openReference(referenceId);});
  el('library-back').addEventListener('click',()=>{
    referenceRevision++;referenceController?.abort();el('library-detail').hidden=true;el('library-catalog-panel').hidden=false;el('coins-search').focus();
  });
  updateFields();
})();
