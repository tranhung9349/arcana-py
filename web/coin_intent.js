/* Local phrase recognition assists the selected topic; it never changes it silently. */
(() => {
  const node = (parent, tag, value = '', cls = '') => {const item = document.createElement(tag); item.textContent = window.DisplayText.plain(value); item.className = cls; parent.appendChild(item); return item;};
  function attach({container, topic, question, questionInput = null, onResolved = () => {}}) {
    let generation = 0, controller = null, timer = null, disposed = false, data = null, dataKey = null, inFlight = null, flightKey = null, acknowledged = null, failure = null;
    container.className = 'coin-intent'; container.tabIndex = -1;
    container.setAttribute('aria-label', 'Nhận diện ý từ câu hỏi');
    const key = () => JSON.stringify([question().trim(), topic.value]);
    const topicLabel = () => topic.selectedOptions[0]?.textContent || 'đang chọn';
    function render() {
      container.replaceChildren(); container.hidden = true; delete container.dataset.review;
      if (!failure && (!data || dataKey !== key())) return;
      const confirmed = acknowledged === dataKey;
      if (!failure && (!data.needs_review || confirmed)) {onResolved(); return;}
      container.hidden = false;
      const status = node(container, 'p', '', 'coin-intent-status'); status.setAttribute('role', 'status');
      if (failure) {status.textContent = 'Chưa nhận diện được câu hỏi. ' + failure; return;}
      container.dataset.review = 'needed';
      status.textContent = data.status === 'MULTIPLE' ? 'Câu hỏi có nhiều chủ đề. Chọn phạm vi muốn luận.' : 'Câu hỏi có vẻ thuộc chủ đề khác. Bạn muốn luận theo chủ đề nào?';
      for (const candidate of data.candidates) {
        if (candidate.topic !== topic.value) {
          const choose = node(container, 'button', 'Chọn ' + candidate.label, 'secondary'); choose.type = 'button';
          choose.addEventListener('click', () => {
            topic.value = candidate.topic; topic.dispatchEvent(new Event('change', {bubbles:true}));
            acknowledged = key(); refresh();
          });
        }
      }
      const keep = node(container, 'button', 'Giữ chủ đề ' + topicLabel(), 'secondary'); keep.type = 'button';
      keep.addEventListener('click', () => {acknowledged = key(); render();});
    }
    function invalidate() {
      generation++; controller?.abort(); clearTimeout(timer); inFlight = null; flightKey = null;
      data = null; dataKey = null; acknowledged = null; failure = null; render();
      timer = setTimeout(() => refresh(), 300);
    }
    async function refresh() {
      clearTimeout(timer);
      if (disposed || !container.isConnected) return null;
      const expected = key();
      if (data && dataKey === expected) {render(); return data;}
      if (inFlight && flightKey === expected) return inFlight;
      if (question().trim().length < 5 || !topic.value) {render(); return null;}
      controller?.abort(); controller = new AbortController(); const request = controller;
      const version = ++generation; flightKey = expected; failure = null; render();
      const timeout = setTimeout(() => request.abort(), 15000);
      inFlight = (async () => {
        try {
          const response = await window.ArcanaClient.fetch('/api/v1/coins/question-intent', {method:'POST', headers:{'Content-Type':'application/json'},
            body:JSON.stringify({question:question().trim(), topic:topic.value}), signal:request.signal});
          const result = await response.json();
          if (!response.ok) throw window.DisplayText.responseError(result,'Chưa nhận diện được câu hỏi. Hãy thử lại.');
          if (disposed || version !== generation || expected !== key() || !container.isConnected) return null;
          data = result; dataKey = expected; render(); return result;
        } catch (error) {
          if (!disposed && version === generation && expected === key()) {failure = error.name === 'AbortError' ? 'Chưa nhận được kết quả, hãy thử lại.' : window.DisplayText.errorMessage(error,'Hãy thử lại sau một lát.'); render();}
          return null;
        } finally {clearTimeout(timeout); if (version === generation) {inFlight = null; flightKey = null;}}
      })();
      return inFlight;
    }
    async function ensure() {
      const expected = key(); const result = await refresh();
      if (disposed || expected !== key()) throw window.DisplayText.failure('Câu hỏi hoặc chủ đề vừa thay đổi. Hãy kiểm tra lại trước khi luận.');
      if (!result) throw window.DisplayText.failure('Chưa đối chiếu được câu hỏi với chủ đề. Hãy thử lại.');
      if (result.needs_review && acknowledged !== expected) {
        container.focus({preventScroll:true}); container.scrollIntoView({behavior:'smooth', block:'center'});
        throw window.DisplayText.failure('Câu hỏi có nhiều ý hoặc khác chủ đề. Chọn gợi ý hoặc bấm giữ chủ đề trước khi tiếp tục.');
      }
      return {topic:topic.value, intent_mode:'COMBINED', intent_acknowledged:acknowledged === expected};
    }
    topic.addEventListener('change', invalidate); questionInput?.addEventListener('input', invalidate);
    render(); refresh();
    return {ensure, refresh, restore(context) {acknowledged = context.intent_acknowledged ? key() : null; data = null; dataKey = null; refresh();},
      destroy() {disposed = true; generation++; controller?.abort(); clearTimeout(timer); topic.removeEventListener('change', invalidate); questionInput?.removeEventListener('input', invalidate);}};
  }
  window.CoinIntent = {attach};
})();
