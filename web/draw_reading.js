/* Explain the saved draw; never use the currently edited form or draw again. */
const DrawReading = (() => {
  const elements = ['Mộc', 'Hỏa', 'Thổ', 'Kim', 'Thủy'];
  const generates = {Mộc:'Hỏa', Hỏa:'Thổ', Thổ:'Kim', Kim:'Thủy', Thủy:'Mộc'};
  const controls = {Mộc:'Thổ', Hỏa:'Kim', Thổ:'Thủy', Kim:'Mộc', Thủy:'Hỏa'};
  const caption = 'Sáu con số. Một dấu ấn riêng — được chắt lọc từ hồ sơ sinh và thời điểm bạn chọn.';
  const stateTexts = {
    DAI_CAT:'Dụng sinh Thể, quẻ có thế sinh trợ.',
    BINH_HOA:'Thể và Dụng cùng hành, quẻ có thế tỷ hòa.',
    THU_CAT:'Thể khắc Dụng, quẻ có thế chủ động chế ngự.',
    KHAC_XUAT:'Thể khắc Dụng, quẻ có thế chủ động chế ngự.',
    TIEU_HAO:'Thể sinh Dụng, quẻ có thế sinh xuất.',
    DAI_HUNG:'Dụng khắc Thể, quẻ có thế tương khắc.'
  };
  function relation(element, target) {
    if (element === target) return 'Cùng hành ' + target;
    if (generates[element] === target) return 'Sinh ' + target;
    if (generates[target] === element) return 'Được ' + target + ' sinh';
    if (controls[element] === target) return 'Khắc ' + target;
    if (controls[target] === element) return 'Bị ' + target + ' khắc';
    return '';
  }
  function describe(result) {
    const t = result.trace, b = t?.bazi, m = t?.maihoa;
    if (!b || !m || !Array.isArray(result.numbers)) return null;
    const primary = b.primary_used, the = m.the.element;
    const groups = elements.map(element => ({
      element,
      numbers:result.numbers.filter(n => elements[((Number(n) % 10 + 9) % 10) >> 1] === element),
      birthRelation:relation(element, primary),
      castingRelation:relation(element, the)
    })).filter(group => group.numbers.length);
    const even = result.numbers.filter(n => Number(n) % 2 === 0).length;
    const selected = t.attempt_history?.find(row => row.attempt === result.selected_attempt
      && row.numbers.join(',') === result.numbers.join(','));
    const score = selected && Number.isFinite(selected.yin_yang_score) && Number.isFinite(selected.element_score)
      ? {balance:selected.yin_yang_score, elements:selected.element_score,
         balancePoints:0.4 * selected.yin_yang_score, elementPoints:0.6 * selected.element_score}
      : null;
    const chosen = (t.weights || []).filter(row => result.numbers.includes(row.number));
    const bonuses = [
      ['thien_thoi','Thiên thời'], ['hao_dong','Cùng nhịp hào động'],
      ['than_sat','Thần sát'], ['dan_gian','Ý nghĩa dân gian']
    ].map(([key, label]) => ({label, numbers:chosen.filter(row => row.deltas?.[key] > 0).map(row => row.number)}))
      .filter(row => row.numbers.length);
    const natalDay = b.natal?.pillars?.[2];
    const natal = natalDay ? 'Nhật chủ ' + natalDay.stem + ' · ' + b.strength + '. ' : '';
    const birthText = natal + (b.overridden
      ? `Bạn chọn hành ${primary} thay cho hành ${b.primary_dung_than} từ lá số. Bộ số được chấm theo lựa chọn này.`
      : `Hành ${primary} được lấy làm trục ưu tiên từ hồ sơ sinh của bạn.`);
    let castingText = `${stateTexts[m.state] || ''} Hành ${the} của Thể được xét cùng hành ${primary} từ hồ sơ sinh.`;
    if (t.remediation?.enabled && t.remediation.target) {
      castingText += ` Phiên này ưu tiên ${t.remediation.target}, với ${t.remediation.quota_min}–${t.remediation.quota_max} số thuộc hành này để cân bằng thế quẻ.`;
    }
    return {primary, the, groups, even, odd:result.numbers.length-even, score, bonuses, birthText, castingText,
      castingTitle:`Thể ${m.the.name} · Dụng ${m.dung.name}`,
      selectedAttempt:result.selected_attempt, attempts:result.attempts};
  }
  return {caption, describe, relation};
})();
if (typeof module !== 'undefined' && module.exports) module.exports = DrawReading;
