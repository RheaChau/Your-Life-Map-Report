#!/usr/bin/env node

// Normalize the user-facing input schema, including lunar dates, then invoke
// the deterministic chart calculator bundled with this skill.
const fs = require('fs');
const path = require('path');
const cp = require('child_process');

function args() {
  const out = {};
  for (const item of process.argv.slice(2)) {
    const match = item.match(/^--([^=]+)=(.*)$/);
    if (match) out[match[1]] = match[2];
  }
  return out;
}

function fail(message) {
  console.error(message.replace(/\d{4}[-/]\d{1,2}[-/]\d{1,2}[^\n]*/g, '[REDACTED_BIRTH_DATA]'));
  process.exit(1);
}

const a = args();
if (!a.input) fail('Usage: node scripts/run_chart.js --input=input.json --output=chart.json');
let input;
try { input = JSON.parse(fs.readFileSync(path.resolve(a.input), 'utf8')); }
catch (err) { fail(`无法读取输入文件：${err.message}`); }

const b = input.birth || {};
const date = String(b.date || '');
const time = String(b.time || '');
const dm = date.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
const tm = time.match(/^(\d{1,2}):(\d{2})$/);
if (!dm || !tm) fail('出生日期必须为 YYYY-MM-DD，时间必须为 HH:MM');
const year = Number(dm[1]);
const month = Number(dm[2]);
const day = Number(dm[3]);
const hour = Number(tm[1]);
const minute = Number(tm[2]);
if (hour > 23 || minute > 59) fail('出生时间超出范围');
const genderMap = { male: 'male', female: 'female', '男': 'male', '女': 'female' };
const gender = genderMap[b.gender];
if (!gender) fail('八字/紫微大运计算需要 birth.gender 为男或女');

let solar = { year, month, day, hour, minute };
if (b.calendar === 'lunar') {
  let Lunar;
  try { ({ Lunar } = require(path.resolve(__dirname, '../calculator/node_modules/lunar-typescript'))); }
  catch (err) { fail('缺少 lunar-typescript 依赖，请先在 calculator/ 执行 npm install'); }
  try {
    // lunar-typescript represents a leap month with a negative month number.
    const lunarMonth = b.leap_month === true || b.is_leap_month === true ? -month : month;
    const converted = Lunar.fromYmdHms(year, lunarMonth, day, hour, minute, 0).getSolar();
    solar = { year: converted.getYear(), month: converted.getMonth(), day: converted.getDay(), hour, minute };
  } catch (err) { fail(`农历日期无法转换：${err.message}`); }
} else if (b.calendar !== 'solar') {
  fail('birth.calendar 只能是 solar 或 lunar');
}

const calculator = path.resolve(__dirname, '../calculator/dist/run-chart.js');
if (!fs.existsSync(calculator)) fail('算法层文件缺失：calculator/dist/run-chart.js');
const child = cp.spawnSync(process.execPath, [calculator,
  `--year=${solar.year}`, `--month=${solar.month}`, `--day=${solar.day}`,
  `--hour=${solar.hour}`, `--minute=${solar.minute}`, `--gender=${gender}`
], { encoding: 'utf8' });
if (child.status !== 0) fail(child.stderr || '排盘计算失败');
if (!child.stdout || !child.stdout.trim().startsWith('{')) fail('算法层没有返回有效 JSON');
if (a.output) fs.writeFileSync(path.resolve(a.output), child.stdout, 'utf8');
else process.stdout.write(child.stdout);
if (child.stderr) process.stderr.write(child.stderr);
