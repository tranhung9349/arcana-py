/* A consultation renders the signed chart and its rule-based reading together. */
(() => {
  const el = id => document.getElementById(id);
  const add = (parent, tag, value = '', className = '') => {
    const node = document.createElement(tag);
    node.textContent = window.DisplayText.plain(value);
    node.className = className;
    parent.appendChild(node);
    return node;
  };
  const dateVN = value => new Date(value).toLocaleString('vi-VN', {timeZone:'Asia/Ho_Chi_Minh'});
  const starLabel = star => star.name + (star.transformation ? ' · Hóa ' + star.transformation : '');
  const perimeter = [5, 6, 7, 8, 4, 9, 3, 10, 2, 1, 0, 11];
  let controller;

  function render(data) {
    const root = el('ziwei-result'), chart = data.chart;
    const palaces = new Map(chart.palaces.map(palace => [palace.branch, palace]));
    const body = palaces.get(chart.body_branch), ming = palaces.get(chart.ming_branch);
    root.replaceChildren();
    const title = add(root, 'h2', 'Lá số Tử Vi', 'bazi-result-heading');
    title.id = 'ziwei-result-title';
    title.tabIndex = -1;
    add(root, 'p', dateVN(data.civil_datetime) + ' · Giờ ' + data.hour_branch + ' · ' +
      (data.gender === 'female' ? 'Nữ' : 'Nam'), 'bazi-birth-caption');
    if (data.effective_date !== data.civil_datetime.slice(0, 10)) {
      add(root, 'p', 'Ngày dùng để lập lá số ' + data.effective_date.split('-').reverse().join('/'), 'hint');
    }

    const board = add(root, 'div', '', 'ziwei-board');
    const controls = new Map();
    for (const branch of perimeter) {
      const palace = palaces.get(branch);
      if (branch === 9) {
        const center = add(board, 'div', '', 'ziwei-board-center');
        add(center, 'strong', chart.cycle_name);
        add(center, 'p', 'Mệnh tại ' + ming.branch_name + ' · Thân tại ' + body.name);
        const lunar = chart.lunar_date;
        add(center, 'p', 'Âm lịch ' + [lunar.day, lunar.month, lunar.year].join('/') + (lunar.leap ? ' · tháng nhuận' : ''));
        if (lunar.leap) add(center, 'p', 'An cung theo tháng ' + chart.chart_lunar_month);
      }
      const button = add(board, 'button', '', 'ziwei-palace');
      button.type = 'button';
      button.setAttribute('aria-controls', 'ziwei-palace-detail');
      add(button, 'strong', palace.name + (branch === chart.body_branch ? ' · Thân' : ''));
      add(button, 'span', palace.stem_name + ' ' + palace.branch_name, 'hint');
      const majors = palace.stars.filter(star => star.type === 'major');
      add(button, 'span', majors.map(star => star.name).join(' · ') || 'Vô chính diệu', 'ziwei-palace-stars');
      controls.set(branch, button);
      button.addEventListener('click', () => {
        selectPalace(branch);
        detail.scrollIntoView({block:'nearest'});
      });
    }
    const detail = add(root, 'section', '', 'ziwei-palace-detail');
    detail.id = 'ziwei-palace-detail';
    detail.setAttribute('aria-live', 'polite');
    function selectPalace(branch) {
      const palace = palaces.get(branch);
      for (const [key, control] of controls) control.setAttribute('aria-pressed', String(branch === key));
      detail.replaceChildren();
      add(detail, 'h3', 'Cung ' + palace.name + ' tại ' + palace.branch_name);
      if (palace.age_range) add(detail, 'p', 'Đại Hạn ' + palace.age_range.join('–') + ' tuổi');
      if (palace.borrowed_from_branch !== null) {
        const opposite = palaces.get(palace.borrowed_from_branch);
        const borrowed = opposite.stars.filter(star => star.type === 'major').map(star => star.name);
        if (borrowed.length) add(detail, 'p', 'Vô chính diệu. Tham chiếu ' + borrowed.join(', ') + ' ở cung ' + opposite.name + '.');
      }
      const stars = add(detail, 'ul', '', 'ziwei-star-list');
      for (const star of palace.stars) {
        add(stars, 'li', starLabel(star) + (star.brightness ? ' · ' + star.brightness : ''),
          star.type === 'major' ? 'ziwei-star-major' : '');
      }
    }
    selectPalace(chart.ming_branch);

    const article = add(root, 'article', '', 'natal-reading');
    for (const section of data.reading.sections) {
      const part = add(article, 'section', '', 'natal-reading-part');
      add(part, 'h3', section.title);
      add(part, 'p', section.text);
    }
    if (chart.patterns.length) {
      const part = add(article, 'section', '', 'natal-reading-part');
      add(part, 'h3', 'Cách cục được nhận diện');
      for (const pattern of data.reading.patterns) {
        const row = add(part, 'div', '', 'ziwei-pattern');
        add(row, 'strong', pattern.title);
        add(row, 'p', pattern.text);
      }
      const trace = add(part, 'details', '', 'ziwei-pattern-trace');
      add(trace, 'summary', 'Điều kiện và nguồn gốc của các cách cục');
      const labels = new Map(data.reading.patterns.map(pattern => [pattern.code, pattern.title]));
      for (const pattern of chart.patterns) {
        const row = add(trace, 'div', '', 'ziwei-pattern');
        add(row, 'strong', labels.get(pattern.code) || pattern.code);
        for (const [label, terms] of [['Điều kiện', pattern.required], ['Yếu tố hỗ trợ', pattern.bonus],
          ['Điều kiện phá cách', pattern.breaking], ['Nguồn', pattern.source ? [pattern.source] : []]]) {
          if (terms.length) {
            const line = add(row, 'p', label + ' · ');
            add(line, 'span', terms.join(' · ')).lang = 'zh-CN';
          }
        }
      }
    }
    window.DisplayText.sourceLink(article, 'Nguồn thuật toán Tử Vi', data.engine.source);
    el('ziwei-empty').hidden = true;
    root.hidden = false;
    window.ResultPDF?.mount(root, 'Lá số Tử Vi');
    title.focus();
  }

  el('ziwei-form').addEventListener('submit', async event => {
    event.preventDefault();
    controller?.abort();
    const request = new AbortController();
    controller = request;
    const birth = el('ziwei-birth').value;
    const civil = birth.length === 16 ? birth + ':00' : birth;
    const payload = {request_id:crypto.randomUUID(), civil_datetime:civil + '+07:00', gender:el('ziwei-gender').value};
    const fields = el('ziwei-form').elements, status = el('ziwei-progress'), error = el('ziwei-error');
    for (const field of fields) field.disabled = true;
    status.textContent = 'Đang lập lá số và luận giải…';
    error.hidden = true;
    const timeout = setTimeout(() => request.abort(), 20000);
    try {
      const response = await window.ArcanaClient.fetch('/api/v1/ziwei/consultations', {
        method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload), signal:request.signal,
      });
      const data = await response.json();
      if (controller !== request) return;
      if (!response.ok) throw window.DisplayText.responseError(data, 'Chưa nhận được lá số.');
      if (data.request_id !== payload.request_id) throw window.DisplayText.failure('Kết quả không khớp lượt lập lá số.');
      render(data);
      status.textContent = 'Đã có lá số và bài luận.';
    } catch (failure) {
      if (controller !== request) return;
      error.textContent = failure.name === 'AbortError' ? 'Chưa nhận được kết quả. Bạn có thể thử lại.' :
        window.DisplayText.errorMessage(failure, 'Chưa lập được lá số Tử Vi. Bạn có thể thử lại.');
      error.hidden = false;
      status.textContent = '';
    } finally {
      clearTimeout(timeout);
      if (controller === request) {
        for (const field of fields) field.disabled = false;
      }
    }
  });
})();
