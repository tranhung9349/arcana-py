const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const sandbox={window:{}};
vm.runInNewContext(fs.readFileSync('web/display_text.js','utf8'),sandbox);
const display=sandbox.window.DisplayText;

test('prose, classical text, numbers and ordinary punctuation stay readable',()=>{
  for(const value of ['',0,80,'Ngày 13/10 có một khoảng phù hợp: 08:00–10:00.',
    'Thể sinh Dụng: cần dành thêm công sức.','元亨利貞。','Thê tài (Thủy) · hào 2 · 75/100']) {
    assert.equal(display.plain(value),String(value));
  }
});
test('objects, arrays, serialized structures and machine labels cannot become UI text',()=>{
  for(const value of [{text:'secret'},['secret'],null,undefined,NaN,
    '{"strength":"STRONG"}',"{'schema_version': 'v1'}",'Kết quả: {"type":"object"}',
    '[1,2,3]','["Hỏa","Kim"]','Các hành: ["Hỏa","Kim"].','Số: [[1,2]].','type: object\nproperties:\n  title: string','```json\n{}\n```','[object Object]',
    'analysis_profile: BAZI_NATAL_V1','date:focus','facts:distribution','line:L2',
    '$schema: https://example.test','Traceback (most recent call last)',
    '<html>Upstream failed</html>']) {
    assert.equal(display.plain(value,'Ẩn'),'Ẩn',String(value));
  }
});
test('saved policy prose translates state labels without changing source snapshots',()=>{
  const text='Các trường hợp còn lại giữ MIXED.';
  assert.equal(display.plain(text),'Các trường hợp còn lại giữ đan xen.');
  assert.equal(display.plain('Sinh khắc với Thể · USE_GENERATES_BODY'),'Sinh khắc với Thể · Dụng sinh Thể');
  assert.equal(display.plain('Sinh khắc với Thể · SAME'),'Sinh khắc với Thể · tỷ hòa');
  assert.equal(display.plain('Dụng L4 sinh Thế L3; H2 cần đối chiếu.'),'Dụng hào 4 sinh Thế hào 3; phục thần 2 cần đối chiếu.');
  assert.equal(text,'Các trường hợp còn lại giữ MIXED.');
});
test('API validation errors name the form fields without echoing backend paths or messages',()=>{
  const error=display.responseError({error:{code:'VALIDATION_FAILED',message:'secret schema',fields:[
    {field:'body.subjects.0.birth.civil_datetime',message:'Input should be datetime'},
    {field:'body.question',message:'{"type":"string"}'}]}});
  assert.equal(display.errorMessage(error),'Vui lòng kiểm tra lại ngày giờ sinh, câu hỏi.');
  assert.doesNotMatch(error.message,/body|subjects|civil_datetime|schema|Input|type/);
});
test('unrecognized API errors and native exceptions use controlled Vietnamese messages',()=>{
  for(const data of [{error:{message:'{"detail":[{"loc":["body"]}]}'}},
    {detail:[{type:'value_error',loc:['body']}]},{error:{code:'UNKNOWN_CODE',message:'Traceback'}}]) {
    assert.equal(display.errorMessage(display.responseError(data,'Chưa tải được.')),'Chưa tải được.');
  }
  assert.equal(display.errorMessage(new Error('Cannot read properties of undefined'),'Hãy thử lại.'),'Hãy thử lại.');
  assert.equal(display.errorMessage(display.failure('Kết quả không khớp phiên đang mở.')),'Kết quả không khớp phiên đang mở.');
});
test('all UI renderers load the shared prose boundary before their scripts',()=>{
  const html=fs.readFileSync('web/index.html','utf8');
  const scripts=[...html.matchAll(/src="\/static\/([^?]+)\?/g)].map(m=>m[1]);
  assert.equal(scripts[0],'display_text.js');
  for(const name of ['app.js','dates.js','date_reading.js','bazi.js','maihoa.js','coins.js','liuyao.js','coin_intent.js','ai_reading.js']) {
    const source=fs.readFileSync('web/'+name,'utf8');
    assert.ok(source.includes('window.DisplayText.plain(value)'),name);
    assert.doesNotMatch(source,/textContent\s*=\s*(?:error|failure)\.message/);
    assert.doesNotMatch(source,/new Error\([^\n]*\.error\??\./);
  }
});
test('source references never navigate to local APIs, JSON/schema files or executable URLs',()=>{
  sandbox.document={createElement:tag=>({tag})};
  const parent={children:[],appendChild(node){this.children.push(node);}};
  for(const url of ['/api/v2/auspicious-dates/rules','http://127.0.0.1:8765/api/rules',
    'https://example.test/api/rules','https://example.test/reading.schema.json',
    'https://github.com/example/project/blob/main/data.json#L1','https://example.test/rules.yaml',
    'javascript:alert(1)',{url:'https://example.test'}]) {
    const node=display.sourceLink(parent,'Nguồn tham khảo',url);
    assert.equal(node.tag,'span');assert.equal(node.href,undefined);
  }
  const link=display.sourceLink(parent,'Nguyên văn cổ thư','https://zh.wikisource.org/w/index.php?oldid=844360');
  assert.equal(link.tag,'a');assert.equal(link.rel,'noopener noreferrer');
});
