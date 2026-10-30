/* Presentation only: navigation and calculation state remain with each module. */
(() => {
  const copy = {
    draw: ['THE NUMBER RITUAL', 'Những con số,', 'một dấu chỉ.', 'Gieo sáu con số từ quẻ Dịch và dấu ấn Bát Tự của bạn.'],
    dates: ['THE ART OF TIMING', 'Chọn thời điểm,', 'mở một khởi đầu.', 'Tìm ngày và khung giờ phù hợp với việc bạn dự định.'],
    maihoa: ['THE BOOK OF CHANGES', 'Một câu hỏi,', 'muôn sự chuyển dời.', 'Đọc thế quẻ Mai Hoa để nhìn rõ điều thuận và điều cần cân nhắc.'],
    coins: ['THE SIX LINES', 'Tĩnh tâm gieo quẻ,', 'lắng nghe chuyển động.', 'Sáu lượt gieo. Một quẻ Dịch. Một góc nhìn cho điều bạn đang hỏi.'],
    library: ['THE I CHING LIBRARY', 'Khám phá 64 quẻ,', 'đọc từng ý nghĩa.', 'Tra cứu quẻ từ, sáu hào và lời giải nghĩa trong một thư viện riêng.'],
    bazi: ['THE FOUR PILLARS', 'Từ ngày sinh,', 'thêm một góc nhìn.', 'Đọc ý chính và điều cần cân nhắc theo câu hỏi của bạn.']
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
    update(['maihoa','coins','library'].find(mode=>document.getElementById('show-'+mode).getAttribute('aria-pressed') === 'true') || 'coins');
  });
})();
