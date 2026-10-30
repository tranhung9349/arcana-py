/* One JSON request on stdin, one JSON result on stdout. No HTTP, DB or LLM. */
'use strict';
const fs = require('node:fs');
const Calculator = require('./src/bazi/calculator');
const {formatOutput} = require('./src/bazi/output');
const {analyzeLiuNian} = require('./src/bazi/thoi_gian_luan');
const {createSeededRandom} = require('./src/utils/random');

function analyze(input) {
  const originalRandom = Math.random;
  Math.random = createSeededRandom(JSON.stringify(input)).next;
  try {
  const calc = new Calculator(input.birth);
  const ctx = calc.calculate();
  ctx.referenceYear = input.target_year;
  const actual = ctx.gans.map((g,i)=>g+ctx.zhis[i]);
  if (JSON.stringify(actual)!==JSON.stringify(input.pillars)) throw Error('PILLAR_MISMATCH');
  const result = formatOutput(ctx, {referenceTime:input.reference_time});
  // Source metadata timestamps are not part of a reproducible calculation.
  delete result.metadata;
  return {
    pillars:actual,
    chart:result.chi_tiet_tru,
    basic:result.thong_tin_co_ban,
    scores:result.diem_so,
    analysis:result.phan_tich,
    interpretation:result.luan_giai,
    classics:result.van_ban_co_dien,
    luck_cycles:result.dai_van,
    annual:analyzeLiuNian(ctx, input.target_year)
  };
  } finally { Math.random = originalRandom; }
}

if (require.main===module) {
  try {
    const input=JSON.parse(fs.readFileSync(0,'utf8'));
    process.stdout.write(JSON.stringify(analyze(input)));
  } catch (error) {
    process.stderr.write(String(error.message).slice(0,250));
    process.exitCode=1;
  }
}
module.exports={analyze};
