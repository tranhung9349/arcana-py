/* Volatile page state only: no localStorage, sessionStorage, cookies or IndexedDB. */
(function (root) {
  'use strict';
  const canonical = value => JSON.stringify(value, (key, item) => item && typeof item === 'object' && !Array.isArray(item)
    ? Object.fromEntries(Object.keys(item).sort().map(k => [k,item[k]])) : item);
  function createClient({network, origin}) {
    const memory = {records:[]};
    const response = (data, status=200) => new Response(JSON.stringify(data), {status, headers:{'Content-Type':'application/json'}});
    const fail = (code, status=404) => response({error:{code,message:'Hãy tạo lại phiên đang mở.'}}, status);
    const read = () => memory;
    const persist = state => {memory.records=state.records;};
    function put(kind, key, data, signature, request) {
      const state=read();
      state.records=state.records.filter(r=>!(r.kind===kind && r.key===key));
      if(['DRAW','BAZI','MAIHOA','COINS','DATE'].includes(kind)) {
        const old=state.records.filter(r=>r.kind===kind).map(r=>r.key);
        state.records=state.records.filter(r=>r.kind!==kind && !old.includes(r.data.consultation_id || r.data.session_id)
          && !(r.kind==='EXPLANATION' && old.includes(r.key)));
      }
      state.records.push({kind,key,data,signature,request});
      while(state.records.length>40)state.records.shift();
      persist(state);
    }
    const find=(kind,key)=>read().records.find(r=>r.kind===kind && r.key===key);
    const signed=record=>record && {kind:record.kind,data:record.data,signature:record.signature};
    const all=kind=>read().records.filter(r=>r.kind===kind).reverse();
    async function send(path, options, kind, key, request) {
      const result=await network(path,{...options,credentials:'omit',redirect:'error',cache:'no-store'});
      if(!result.ok)return result;
      const data=await result.clone().json();
      const signature=result.headers.get('X-Arcana-Signature');
      if(kind && !['AI','EXPLANATION','SEARCH'].includes(kind) && !/^[0-9a-f]{64}$/.test(signature || ''))return fail('SNAPSHOT_INVALID',502);
      if(kind)put(kind,key,data,signature,request);
      return result;
    }
    function packAI(request) {
      const kind={BAZI:'BAZI',MAIHOA:'MAIHOA',LIUYAO:'COINS',DATE:'DATE'}[request.method];
      const record=find(kind,request.consultation_id);
      if(!record)return null;
      const packed={...request,consultation:signed(record)};
      if(request.bazi_reading_id && request.bazi_reading_id!==request.consultation_id) {
        const reading=find('BAZI_READING',request.bazi_reading_id);
        if(reading)packed.bazi_reading=signed(reading);
      }
      if(request.method==='LIUYAO') {
        const analysis=all('LIUYAO').find(r=>r.data.session_id===request.consultation_id
          && r.data.rules_sha256===request.analysis_rules_sha256 && canonical(r.data.context)===canonical(request.analysis_context));
        if(analysis)packed.analysis=signed(analysis);
      }
      return packed;
    }
    async function fetchLocal(input, options={}) {
      const url=new URL(input,origin);
      if(url.origin!==origin || !url.pathname.startsWith('/api/'))throw Error('Only same-origin API requests are allowed');
      const path=url.pathname, method=(options.method || 'GET').toUpperCase();
      if(options.signal?.aborted)throw new DOMException('Aborted','AbortError');
      const body=options.body ? JSON.parse(options.body) : null;
      const post=(path,payload,kind,key,request)=>send(path,{...options,method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)},kind,key,request);
      const created={
        '/api/v1/draw':'DRAW','/api/v1/bazi/consultations':'BAZI','/api/v1/maihoa/consultations':'MAIHOA',
        '/api/v1/coins/consultations':'COINS','/api/v2/auspicious-dates/consultations':'DATE',
      };
      if(method==='POST' && created[path]) {
        const kind=created[path], key=body.request_id, existing=find(kind,key);
        if(existing)return canonical(existing.request)===canonical(body)?response(existing.data):fail('REQUEST_ID_CONFLICT',409);
        return send(path,options,kind,key,body);
      }
      let match;
      if(method==='GET' && (match=path.match(/^\/api\/v1\/draw\/([^/]+)$/)))return responseOrMissing('DRAW',match[1]);
      if(method==='GET' && (match=path.match(/^\/api\/(?:v1\/(bazi|maihoa|coins)|v2\/(auspicious-dates))\/consultations\/([^/]+)$/))) {
        return responseOrMissing(({bazi:'BAZI',maihoa:'MAIHOA',coins:'COINS','auspicious-dates':'DATE'})[match[1]||match[2]],match[3]);
      }
      if(method==='GET' && (match=path.match(/^\/api\/v1\/interpretation\/([^/]+)$/))) {
        const key=match[1], saved=find('DRAW',key), cached=find('EXPLANATION',key);
        if(cached)return response(cached.data);
        return saved?post('/api/v1/interpretation',{consultation:signed(saved)},'EXPLANATION',key):fail('DRAW_NOT_FOUND');
      }
      if((match=path.match(/^\/api\/v1\/bazi\/consultations\/([^/]+)\/readings$/))) {
        const parent=match[1], saved=find('BAZI',parent);
        if(!saved)return fail('BAZI_NOT_FOUND');
        if(method==='GET')return response({readings:[{reading_id:parent,consultation_id:parent,created_at:saved.data.created_at,reading:saved.data.reading},
          ...all('BAZI_READING').filter(r=>r.data.consultation_id===parent).map(r=>r.data)]});
        if(method==='POST') {
          const cached=find('BAZI_READING',body.reading_id), identity={parent,body};
          if(cached)return canonical(cached.request)===canonical(identity)?response(cached.data):fail('REQUEST_ID_CONFLICT',409);
          return post('/api/v1/bazi/readings',{consultation:signed(saved),reading:body},'BAZI_READING',body.reading_id,identity);
        }
      }
      if((match=path.match(/^\/api\/v1\/coins\/consultations\/([^/]+)\/analysis$/))) {
        const parent=match[1], saved=find('COINS',parent);
        if(!saved)return fail('COIN_NOT_FOUND');
        if(method==='GET')return response(all('LIUYAO').find(r=>r.data.session_id===parent)?.data || null);
        if(method==='POST') {
          // The exact normalized context is returned and signed by the server.
          const cached=all('LIUYAO').find(r=>r.data.session_id===parent && canonical(r.request)===canonical(body));
          if(cached){put('LIUYAO',cached.key,cached.data,cached.signature,cached.request);return response(cached.data);}
          const key=canonical({parent,body});
          return post('/api/v1/coins/analysis',{consultation:signed(saved),context:body},'LIUYAO',key,body);
        }
      }
      if(method==='POST' && (path==='/api/v1/ai/readings' || path==='/api/v1/ai/readings/lookup')) {
        const key=canonical(body), cached=find('AI',key);
        if(cached)return response(cached.data);
        const packed=packAI(body);
        if(!packed)return fail('SNAPSHOT_INVALID',422);
        const result=await post(path,packed);
        if(result.ok) {
          const data=await result.clone().json();
          if(data)put('AI',key,data,null,body);
        }
        return result;
      }
      if(method==='POST' && path==='/api/v2/auspicious-dates/search')return send(path,options);
      // No caller-supplied path is forwarded except known computation/catalog APIs.
      if((method==='GET' && (path==='/api/v2/auspicious-dates/rules' || /^\/api\/v1\/(?:health|ai\/status|bazi\/rules|maihoa\/rules|coins\/(?:analysis-rules|hexagrams(?:\/\d+)?))$/.test(path)))
        || (method==='POST' && path==='/api/v1/coins/question-intent'))return send(path,options);
      return fail('NOT_FOUND');
    }
    function responseOrMissing(kind,key) {const saved=find(kind,key);return saved?response(saved.data):fail(kind==='DRAW'?'DRAW_NOT_FOUND':kind+'_NOT_FOUND');}
    const pending=new Map();
    async function fetchOnce(input,options={}) {
      const key=canonical([input,options.method || 'GET',options.body || null]);
      if(pending.has(key))return (await pending.get(key)).clone();
      const work=fetchLocal(input,options);pending.set(key,work);
      try {return (await work).clone();}
      finally {pending.delete(key);}
    }
    return {fetch:fetchOnce};
  }
  if(typeof module==='object' && module.exports)module.exports={createClient};
  else {
    root.ArcanaClient=createClient({network:root.fetch.bind(root),origin:root.location.origin});
    root.addEventListener('pageshow',event=>{if(event.persisted)root.location.reload();});
  }
})(typeof window==='object'?window:globalThis);
