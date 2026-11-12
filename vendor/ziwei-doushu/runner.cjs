'use strict';

const fs = require('node:fs');
require('tsx/cjs');
const {generateChart, resolveEffectiveLunarDate} = require('./lib/ziwei/algorithm.ts');
const {detectPatterns} = require('./lib/ziwei/patterns.ts');
const {STEMS, BRANCHES} = require('./lib/ziwei/constants.ts');
const chinese = require('iztro/lib/i18n/locales/zh-CN').default;
const vietnamese = require('iztro/lib/i18n/locales/vi-VN').default;

const terms = new Map(Object.entries(chinese).map(([key, label]) => [label, vietnamese[key]]));
const localTerms = {
  命宫:'Mệnh', 兄弟:'Huynh Đệ', 夫妻:'Phu Thê', 子女:'Tử Nữ', 财帛:'Tài Bạch',
  疾厄:'Tật Ách', 迁移:'Thiên Di', 仆役:'Nô Bộc', 交友:'Nô Bộc', 官禄:'Quan Lộc',
  田宅:'Điền Trạch', 福德:'Phúc Đức', 父母:'Phụ Mẫu',
  副截:'Phó Triệt', 副旬:'Phó Tuần', 截空:'Triệt Không', 旬空:'Tuần Không', 年解:'Niên Giải',
};
const translate = label => localTerms[label] ?? terms.get(label) ?? label;
const brightness = {庙:'Miếu', 旺:'Vượng', 得:'Đắc', 利:'Lợi', 平:'Bình', 不:'Bất', 陷:'Hãm'};
const cuc = {2:'Thủy Nhị Cục', 3:'Mộc Tam Cục', 4:'Kim Tứ Cục', 5:'Thổ Ngũ Cục', 6:'Hỏa Lục Cục'};

function analyze(birth) {
  const chart = generateChart(birth);
  const lunar = resolveEffectiveLunarDate(birth.year, birth.month, birth.day, 'origin-month');
  return {
    lunar_date: {
      year: lunar.lunarYear, month: lunar.lunarMonth, day: lunar.lunarDay, leap: lunar.isLeapMonth,
    },
    chart_lunar_month: chart.lunarInfo.lunarMonth,
    cycle_name: cuc[chart.wuxingJu],
    ming_branch: chart.mingGongBranch,
    body_branch: chart.shenGongBranch,
    palaces: chart.palaces.map(palace => ({
      code: palace.name,
      name: translate(palace.name),
      branch: palace.branch,
      branch_name: translate(BRANCHES[palace.branch]),
      stem_name: translate(STEMS[palace.stem]),
      opposite_branch: palace.oppositeBranch,
      borrowed_from_branch: palace.borrowedFromBranch ?? null,
      age_range: palace.daXianAge ?? null,
      stars: palace.stars.map(star => ({
        code: star.name, name: translate(star.name), type: star.type,
        brightness: brightness[star.brightness] ?? null,
        transformation: star.siHua ? translate(star.siHua) : null,
      })),
    })),
    patterns: detectPatterns(chart).map(pattern => ({
      code: pattern.name,
      level: pattern.level,
      required: pattern.conditions?.required ?? [],
      bonus: pattern.conditions?.bonus ?? [],
      breaking: pattern.conditions?.breaking ?? [],
      source: pattern.source ?? null,
    })),
  };
}

try {
  const birth = JSON.parse(fs.readFileSync(0, 'utf8'));
  process.stdout.write(JSON.stringify(analyze(birth)));
} catch (error) {
  process.stderr.write(String(error.message).slice(0, 250));
  process.exitCode = 1;
}
