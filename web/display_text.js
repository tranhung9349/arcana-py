/* The UI accepts prose and numbers, never serialized backend objects. */
(() => {
  const fallback='Nội dung này chưa sẵn sàng. Hãy thử tải lại.';
  const internal=/```|[{}]|\[object\s+\w+\]|\b[A-Za-z0-9]+_[A-Za-z0-9_]+\b|\$(?:schema|defs|ref)\b|\b(?:facts?|evidence|findings?|context|assessment|chart|line|engine|date|reading|pillar|stem|root):[A-Za-z0-9_:-]+|\b(?:Traceback|ValidationError|TypeError|SyntaxError)\b|(?:["']\s*:\s*["'\[{\d])|<\/?[A-Za-z][^>]*>/;
  function readable(value) {
    if(typeof value==='number')return Number.isFinite(value);
    if(typeof value!=='string')return false;
    if(internal.test(value))return false;
    if(/(?:^|\n)\s*(?:type|properties|required|additionalProperties|summary|analysis)\s*:\s*(?:object|array|string|boolean|number|\[|\n|$)/.test(value))return false;
    for(const part of value.matchAll(/\[[^\[\]]*\]/g)) {
      try {if(Array.isArray(JSON.parse(part[0])))return false;}catch {}
    }
    const s=value.trim();
    if(s.startsWith('[') && s.endsWith(']'))return false;
    return true;
  }
  const stateNames={MIXED:'đan xen',STRONG:'thiên vượng',WEAK:'thiên nhược',SUPPORTED:'đã xác định',CONDITIONAL:'có điều kiện',UNRESOLVED:'chưa đủ kết luận',GOOD:'phù hợp',NORMAL:'bình thường',BAD:'nên tránh',
    SAME:'tỷ hòa',USE_GENERATES_BODY:'Dụng sinh Thể',USE_CONTROLS_BODY:'Dụng khắc Thể',BODY_GENERATES_USE:'Thể sinh Dụng',BODY_CONTROLS_USE:'Thể khắc Dụng'};
  const statePattern=new RegExp('\\b('+Object.keys(stateNames).join('|')+')\\b','g');
  function plain(value,alternative=fallback) {
    const translated=typeof value==='string'?value.replace(statePattern,key=>stateNames[key]).replace(/\bL([1-6])\b/g,'hào $1').replace(/\bH([1-6])\b/g,'phục thần $1'):value;
    return readable(translated)?String(translated):alternative;
  }
  class PublicError extends Error {}
  const failure=message=>new PublicError(plain(message));
  const messages={
    SNAPSHOT_INVALID:'Kết quả của phiên không còn hợp lệ. Hãy tạo một phiên mới.',
    RATE_LIMITED:'Bạn thao tác quá nhanh. Hãy đợi một lát rồi thử lại.',
    SERVER_BUSY:'Ứng dụng đang bận. Hãy thử lại sau một lát.',
    BODY_TOO_LARGE:'Dữ liệu của phiên quá lớn. Hãy tạo lại phiên.',
    AI_BUDGET_EXHAUSTED:'Phần luận AI đã đạt giới hạn hôm nay. Bạn có thể quay lại ngày mai.',
    VALIDATION_FAILED:'Vui lòng kiểm tra lại các mục đã nhập.',
    BIRTH_BOUNDARY_UNSTABLE:'Sai số giờ sinh đi qua ranh đổi lá số. Hãy kiểm tra lại giờ sinh.',
    BAZI_ENGINE_FAILED:'Chưa tính được lá số Bát Tự. Hãy kiểm tra ngày giờ sinh và thử lại.',
    INVALID_USE_LINE:'Hãy chọn một hào Dụng thần trong danh sách gợi ý.',
    INTENT_REVIEW_REQUIRED:'Hãy chọn gợi ý hoặc xác nhận giữ chủ đề trước khi luận.',
    REQUEST_ID_CONFLICT:'Yêu cầu này đã gắn với dữ liệu khác. Hãy tạo một phiên mới.',
    COIN_REQUEST_CONFLICT:'Hãy tạo phiên gieo mới cho câu hỏi vừa thay đổi.',
    MAIHOA_REQUEST_CONFLICT:'Hãy lập quẻ mới cho câu hỏi vừa thay đổi.',
    BAZI_NOT_FOUND:'Chưa tìm thấy lá số đã lưu. Hãy mở lại lịch sử.',
    BAZI_READING_NOT_FOUND:'Chưa tìm thấy bài luận của lá số này.',
    COIN_NOT_FOUND:'Chưa tìm thấy phiên gieo đã lưu.',
    MAIHOA_NOT_FOUND:'Chưa tìm thấy phiên luận đã lưu.',
    DRAW_NOT_FOUND:'Chưa tìm thấy bộ số đã lưu.',
    DATE_CONSULTATION_NOT_FOUND:'Hãy mở lại ngày đã chọn để tải căn cứ luận.',
    LIUYAO_ANALYSIS_NOT_FOUND:'Hãy tải phần phân tích Lục Hào trước khi luận thêm.',
    AI_CONTEXT_INVALID:'Hãy mở lại phần phân tích của phiên này rồi thử luận lại.',
    AI_BUSY:'Bài luận đang được viết. Bạn có thể đợi một lát rồi mở lại.',
    AI_STREAM_INTERRUPTED:'Kết nối bị gián đoạn. Bấm thử lại để nối với bài luận của phiên.',
    AI_RATE_LIMITED:'Dịch vụ luận đang bận. Bạn có thể thử lại sau.',
    AI_NOT_CONFIGURED:'Dịch vụ luận AI chưa được cấu hình. Quẻ của bạn vẫn được giữ.',
    AI_AUTH_FAILED:'Phần luận AI tạm chưa kết nối được. Bạn có thể thử lại sau.',
    AI_CONNECTION_FAILED:'Kết nối đến dịch vụ AI bị ngắt. Quẻ vẫn được giữ; bạn có thể thử lại phần luận.',
    AI_FAILED:'Phần luận AI gặp lỗi xử lý. Quẻ vẫn được giữ; bạn có thể thử lại phần luận.',
    AI_RESPONSE_INCOMPLETE:'Bài luận chưa viết xong. Bạn có thể thử lại phần luận.',
    AI_RESPONSE_INVALID:'Dịch vụ AI trả về bài luận chưa đúng định dạng. Bạn có thể thử lại trên cùng quẻ.',
    AI_RESPONSE_UNBOUND:'Bài AI chưa đạt kiểm tra nội dung và căn cứ nên chưa được hiển thị. Bạn có thể thử lại trên cùng quẻ.',
    AI_REQUEST_REPLACED:'Hãy mở lại phiên này để đọc bài luận đã lưu.',
    INPUT_OUT_OF_RANGE:'Ngày đã nhập nằm ngoài phạm vi hỗ trợ. Hãy chọn lại ngày.',
    CIVIL_RANGE_INVALID:'Ngày đã nhập nằm ngoài phạm vi hỗ trợ. Hãy chọn lại ngày.',
    INVALID_INPUT_TIMEZONE:'Hãy nhập lại ngày giờ theo giờ Việt Nam.',
    TIMEZONE_REQUIRED:'Hãy nhập đầy đủ ngày và giờ.',
  };
  function responseError(data, alternative=fallback) {
    const code=typeof data?.error?.code==='string'?data.error.code:'';
    let message=messages[code] || alternative;
    if(code==='VALIDATION_FAILED') {
      const fields=Array.isArray(data.error.fields)?data.error.fields:[];
      const labels=new Set();
      for(const item of fields) {
        const field=typeof item.field==='string'?item.field:'';
        if(/question/.test(field))labels.add('câu hỏi');
        else if(/birth|civil_datetime/.test(field))labels.add('ngày giờ sinh');
        else if(/date_range/.test(field))labels.add('khoảng ngày tra');
        else if(/allowed_hours/.test(field))labels.add('khoảng giờ tra');
        else if(/allowed_weekdays/.test(field))labels.add('ngày trong tuần');
        else if(/casting|timestamp|clicked_at/.test(field))labels.add('thời điểm gieo');
        else if(/topic/.test(field))labels.add('chủ đề');
        else if(/throws/.test(field))labels.add('kết quả đủ sáu lượt gieo');
      }
      if(labels.size)message='Vui lòng kiểm tra lại '+[...labels].join(', ')+'.';
    }
    const error=failure(message);error.code=code;return error;
  }
  const errorMessage=(error,alternative=fallback)=>error instanceof PublicError?error.message:alternative;
  function sourceLink(parent,label,value) {
    // Reference buttons must not open an API response or a machine-readable file.
    const allowed=typeof value==='string' && /^https:\/\//i.test(value)
      && !/https:\/\/(?:localhost|127\.0\.0\.1|\[::1\])(?=[:/]|$)|\/api(?:\/|$)|\.(?:json|ya?ml)(?:[?#]|$)/i.test(value);
    const node=document.createElement(allowed?'a':'span');node.textContent=plain(label);node.className=allowed?'source-link':'source-credit hint';
    if(allowed){node.href=value;node.target='_blank';node.rel='noopener noreferrer';}
    parent.appendChild(node);return node;
  }
  window.DisplayText={plain,readable,failure,responseError,errorMessage,sourceLink};
})();
