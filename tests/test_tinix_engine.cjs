const {test}=require('node:test');
const assert=require('node:assert/strict');
const {analyzeQuanHeCanChi}=require('../vendor/tinix-bazi/src/bazi/phan_tich/quan_he');
const ganzhi=require('../vendor/tinix-bazi/src/bazi/ganzhi');

test('identical stems and branches cannot supply two distinct members of a pair',()=>{
  const result=analyzeQuanHeCanChi({gans:['癸','癸','癸','癸'],zhis:['卯','卯','卯','卯']});
  assert.equal(result.thien_can.length,0);
  assert.equal(result.dia_chi.length,0);
});
test('six combinations and clashes are recognized in either order for all 144 branch pairs',()=>{
  const he=new Set(['0,1','2,11','3,10','4,9','5,8','6,7']);
  for(let a=0;a<12;a++)for(let b=0;b<12;b++){
    const result=analyzeQuanHeCanChi({gans:['甲','甲','甲','甲'],zhis:[ganzhi.ZHIS[a],ganzhi.ZHIS[b],ganzhi.ZHIS[a],ganzhi.ZHIS[b]]});
    assert.equal(result.dia_chi.some(r=>r.loai==='Lục Hợp'),he.has([a,b].sort((x,y)=>x-y).join(',')),`he ${a},${b}`);
    assert.equal(result.dia_chi.some(r=>r.loai==='Lục Xung'),Math.abs(a-b)===6,`chong ${a},${b}`);
  }
});
test('Chinese stems find Vietnamese hidden roots',()=>{
  const result=analyzeQuanHeCanChi({gans:['甲','癸','丁','癸'],zhis:['戌','酉','卯','卯']});
  assert.equal(result.can_khi[2].co_can,true);
  assert.equal(result.can_khi[2].roots[0].chi,'Tuất');
});
