/* Presentation only: navigation and calculation state remain with each module. */
(() => {
  const copy = {
    draw: ['THE NUMBER RITUAL', 'Những con số,', 'một dấu chỉ.', 'Gieo sáu con số từ quẻ Dịch và dấu ấn Bát Tự của bạn.'],
    dates: ['THE ART OF TIMING', 'Chọn thời điểm,', 'mở một khởi đầu.', 'Tìm ngày và khung giờ phù hợp với việc bạn dự định.'],
    maihoa: ['THE BOOK OF CHANGES', 'Một câu hỏi,', 'muôn sự chuyển dời.', 'Đọc thế quẻ Mai Hoa để nhìn rõ điều thuận và điều cần cân nhắc.'],
    coins: ['THE SIX LINES', 'Tĩnh tâm gieo quẻ,', 'lắng nghe chuyển động.', 'Sáu lượt gieo. Một quẻ Dịch. Một góc nhìn cho điều bạn đang hỏi.'],
    bazi: ['THE FOUR PILLARS', 'Từ bốn trụ,', 'hiểu mình sâu hơn.', 'Khám phá mệnh cục và các mối quan hệ trong lá số sinh của bạn.']
  };
  const title = document.getElementById('workspace-title');
  if (!title) return;
  function update(mode) {
    const [kicker, first, second, description] = copy[mode];
    const accent = document.createElement('em');
    accent.textContent = second;
    title.replaceChildren(document.createTextNode(first), document.createElement('br'), accent);
    document.getElementById('workspace-kicker').textContent = kicker;
    document.getElementById('workspace-description').textContent = description;
  }
  for (const mode of Object.keys(copy)) {
    document.getElementById('show-' + mode).addEventListener('click', () => update(mode));
  }
  document.getElementById('show-iching').addEventListener('click', () => {
    update(document.getElementById('show-maihoa').getAttribute('aria-pressed') === 'true' ? 'maihoa' : 'coins');
  });
})();
