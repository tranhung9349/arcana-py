const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {describe} = require('../web/draw_reading.js');
const root = path.join(__dirname, '..');
const load = name => JSON.parse(fs.readFileSync(path.join(root, name), 'utf8'));
function fixture() {
  const result = load('examples/draw_response.json');
  result.numbers = ['00','11','22','33','44','99'];
  result.score = 94;
  result.attempts = 3;
  result.selected_attempt = 2;
  result.trace.attempt_history = [
    {attempt:2,numbers:[...result.numbers],yin_yang_score:100,element_score:90},
    {attempt:3,numbers:['01','02','03','04','05','06'],yin_yang_score:70,element_score:10}
  ];
  return result;
}
test('explains endpoints, repeated tails and the selected attempt rather than the last attempt', () => {
  const result = fixture(), before = JSON.stringify(result), reading = describe(result);
  assert.deepEqual(reading.groups.map(g=>[g.element,g.numbers]), [
    ['Mộc',['11','22']],['Hỏa',['33','44']],['Thủy',['00','99']]
  ]);
  assert.equal(reading.even,3);assert.equal(reading.odd,3);
  assert.equal(reading.score.balancePoints,40);assert.equal(reading.score.elementPoints,54);
  assert.equal(reading.score.balancePoints+reading.score.elementPoints,result.score);
  assert.equal(reading.selectedAttempt,2);assert.equal(reading.attempts,3);
  assert.equal(JSON.stringify(result),before);
});
test('number groups agree with all 100 element labels saved by the engine', () => {
  const result=load('examples/draw_response.json');
  result.numbers=result.trace.weights.map(row=>row.number);
  const reading=describe(result);
  for(const row of result.trace.weights){
    assert.ok(reading.groups.find(group=>group.element===row.element).numbers.includes(row.number));
  }
});
test('keeps both profile and casting relations, including an explicit override', () => {
  const result=fixture();
  result.trace.bazi.primary_used='Kim';result.trace.bazi.primary_dung_than='Hỏa';result.trace.bazi.overridden=true;
  result.trace.maihoa.the.element='Hỏa';
  const reading=describe(result), wood=reading.groups.find(group=>group.element==='Mộc');
  assert.equal(wood.birthRelation,'Bị Kim khắc');assert.equal(wood.castingRelation,'Sinh Hỏa');
  assert.match(reading.birthText,/Bạn chọn hành Kim thay cho hành Hỏa/);
});
test('only describes bonuses for selected numbers and does not invent missing score components', () => {
  const result=fixture();
  result.trace.weights=[{number:'00',deltas:{thien_thoi:.15}},{number:'01',deltas:{dan_gian:.05}}];
  result.trace.attempt_history=[];
  const reading=describe(result);
  assert.deepEqual(reading.bonuses,[{label:'Thiên thời',numbers:['00']}]);
  assert.equal(reading.score,null);
});
test('can explain an archived 00–45 draw without changing its saved threshold', () => {
  const result=load('docs/archive/draw_response_v3.json'), before=JSON.stringify(result);
  const reading=describe(result);
  assert.equal(reading.groups.reduce((sum,group)=>sum+group.numbers.length,0),6);
  assert.equal(reading.even+reading.odd,6);
  assert.equal(JSON.stringify(result),before);
});
