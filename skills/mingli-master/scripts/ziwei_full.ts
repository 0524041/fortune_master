#!/usr/bin/env npx tsx
/** 紫微全量排盤 + 倪師三合思維輸出. 引擎內嵌於 scripts/vendor/ziwei (algorithm+patterns+sihua+constants+types 全量 detectPatterns).
 * 用法: npx tsx scripts/ziwei_full.ts --date 1990-08-18 --hour 卯 --gender male [--liunian 2026] [--at 2026-06-15] [--format text|json]
 * 立場: 倪師三合派. 本命四化固定; 大限流年四化疊加看宮位; 宮干自化/來因宮標飛星參考不主斷.
 * 運限: 給 --at YYYY-MM-DD 出六層 (大限/小限/流年/流月/流日/流時), --at-time HH:MM 指定流時, --horoscope-divide exact 改立春分界.
 */
import { generateChart } from './vendor/ziwei/algorithm.js';
import { generateHoroscope } from './vendor/ziwei/horoscope.js';
import { detectPatterns, getMingGongSummary } from './vendor/ziwei/patterns.js';
import { getSiHuaByStem, getDaXianSiHua, getLiuNianSiHua, detectSelfSihua, findIncomingPalaces } from './vendor/ziwei/sihua.js';
import { STEMS, BRANCHES } from './vendor/ziwei/constants.js';
import { Lunar } from 'lunar-javascript';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

// 真太陽時 (與 time_correct.py 同公式: 經差×4分 + 均時差EoT, 誤差<1分)
const SKILL_DIR = join(dirname(fileURLToPath(import.meta.url)), '..');
const CITIES: Record<string, any[]> = JSON.parse(readFileSync(join(SKILL_DIR, 'data', 'cities.json'), 'utf8'));
const FLAT: Record<string, number> = {};
for (const k of Object.keys(CITIES)) for (const c of CITIES[k]) FLAT[c.name] = c.lon;
Object.assign(FLAT, { 台北市: 121.56, 新北市: 121.46, 台中市: 120.68, 台南市: 120.19, 高雄市: 120.31 });

function equationOfTime(y: number, doy: number): number {
  const D = 6.24004077 + 0.01720197 * (365.25 * (y - 2000) + doy);
  return -7.659 * Math.sin(D) + 9.863 * Math.sin(2 * D + 3.5932);
}

function trueSolarBranch(Y: number, M: number, D: number, time: string, city: string, lonOpt?: string):
  { branch: number; true_solar: string; corr_min: number; lon: number } | null {
  const m = time.match(/^(\d{1,2}):(\d{2})$/);
  if (!m || (!city && lonOpt === undefined)) return null;
  const lon = lonOpt !== undefined ? +lonOpt : FLAT[city];
  if (lon === undefined || Number.isNaN(lon)) {
    console.error(`錯誤: 未知城市:${city}, 可用 --lon 手輸經度 (無預設值以免靜默錯盤)`);
    process.exit(2);
  }
  const doy = Math.floor((Date.UTC(Y, M - 1, D) - Date.UTC(Y, 0, 0)) / 864e5);
  const delta = (lon - 120) * 4 + equationOfTime(Y, doy);
  const mins = (+m[1]) * 60 + (+m[2]) + delta;
  const norm = ((Math.round(mins) % 1440) + 1440) % 1440;
  const hh = String(Math.floor(norm / 60)).padStart(2, '0');
  const mm = String(norm % 60).padStart(2, '0');
  return { branch: Math.floor(((norm + 60) % 1440) / 120), true_solar: `${hh}:${mm}`, corr_min: +delta.toFixed(2), lon };
}

const args: Record<string, string> = {};
for (let i = 2; i < process.argv.length; i++) {
  if (process.argv[i].startsWith('--')) {
    const k = process.argv[i].slice(2);
    const n = process.argv[i + 1];
    args[k] = (n && !n.startsWith('--')) ? n : 'true'; if (n && !n.startsWith('--')) i++;
  }
}
const ZHI = '子丑寅卯辰巳午未申酉戌亥'.split('');
function parseHour(h?: string): number {
  if (!h) return 5;
  if (/^\d{1,2}$/.test(h)) return +h % 12;
  if (ZHI.includes(h)) return ZHI.indexOf(h);
  const m = h.match(/^(\d{1,2}):(\d{2})/);
  if (m) return Math.floor((((+m[1]) + 1) % 24) / 2);
  return 5;
}
if (!args.date) { console.error('need --date YYYY-MM-DD --hour 卯 --gender male|female'); process.exit(1); }
let [Y, M, D] = args.date.split('-').map(Number);
const calendar = args.calendar === 'lunar' ? 'lunar' : 'solar';
if (calendar === 'lunar') {
  try {
    const sol = Lunar.fromYmd(Y, args.leap ? -Math.abs(M) : M, D).getSolar();
    Y = sol.getYear(); M = sol.getMonth(); D = sol.getDay();
  } catch (e: any) {
    console.error(`錯誤: 農曆日期無效 (${args.date}${args.leap ? ' 閏月' : ''}): ${e?.message ?? e}`);
    process.exit(2);
  }
}
const solarDate = `${Y}-${M}-${D}`;
const tsCorr = trueSolarBranch(Y, M, D, args.time || '', args.city || '', args.lon);
const hour = tsCorr ? tsCorr.branch : parseHour(args.hour);
const hourSrc = tsCorr ? `真太陽時${tsCorr.true_solar}(經度${tsCorr.lon},校正${tsCorr.corr_min}分)` : '直給時支';
const warnings: string[] = [];
if (tsCorr) {
  const om = args.time.match(/^(\d{1,2}):(\d{2})$/)!;
  const origMin = +om[1] * 60 + +om[2];
  if (origMin + tsCorr.corr_min < 0 || origMin + tsCorr.corr_min >= 1440) warnings.push('真太陽時跨日');
  const [hh, mm] = tsCorr.true_solar.split(':').map(Number);
  const mins = hh * 60 + mm;
  const bounds = [0, ...Array.from({ length: 12 }, (_, i) => 60 + 120 * i)];
  const nearest = Math.min(...bounds.map(b => Math.min(Math.abs(mins - b), 1440 - Math.abs(mins - b))));
  if (nearest <= 10) warnings.push(`近時辰交界(距${nearest}分)`);
}
const gender = args.gender === 'female' ? 'female' : 'male';
const liunian = args.liunian ? +args.liunian : new Date().getFullYear();
const fmt = args.format || 'text';

const chart = generateChart({ year: Y, month: M, day: D, hour, gender } as any);
const patterns = detectPatterns(chart);
const summary = getMingGongSummary(chart);
// 本命四化 (年干固定)
const yearStem = chart.lunarInfo.yearStem;
const native4 = getSiHuaByStem(yearStem);
// 大限四化 (當前大限宮干) + 流年四化
const dx = getDaXianSiHua(chart as any, (chart as any).currentDaXianIndex ?? 0);
const ln = getLiuNianSiHua(liunian);
// 運限六層 (大限/小限/流年/流月/流日/流時): 只在給 --at 陽曆日期時計算
let horoscope: any = undefined;
if (args.at) {
  if (!/^\d{4}-\d{1,2}-\d{1,2}$/.test(args.at)) {
    console.error(`錯誤: --at 須為陽曆 YYYY-MM-DD, 收到:${args.at}`); process.exit(2);
  }
  const divide = args['horoscope-divide'] === 'exact' ? 'exact' : 'normal';
  horoscope = generateHoroscope(
    { year: Y, month: M, day: D, hour, gender }, args.at, parseHour(args['at-time'] || '12:00'), divide);
}
// 自化/來因宮 (飛星參考, 不主斷)
const selfSihua: Record<string, any> = {};
for (const p of chart.palaces) { const l = detectSelfSihua(p as any); if (l.length) selfSihua[p.name] = l; }
const jiStars: string[] = [];
for (const p of chart.palaces) for (const s of p.stars) if ((s as any).siHua === '忌' && (s as any).type === 'major') jiStars.push(s.name);
const laiyin: Record<string, string[]> = {};
for (const s of [...new Set(jiStars)]) laiyin[s + '化忌來因'] = findIncomingPalaces(chart as any, s, '忌' as any).map(p => p.name);

const lu = (m: any) => m['祿'] ?? m['禄'] ?? '';
const quan = (m: any) => m['權'] ?? m['权'] ?? '';
const out = {
  date: solarDate, hour: ZHI[hour], gender, liunian,
  calendar,
  birth_input: { date: args.date, calendar, leap: !!args.leap },
  time_src: hourSrc,
  warnings,
  true_solar: tsCorr ? `${solarDate} ${tsCorr.true_solar}` : undefined,
  ming: { branch: BRANCHES[chart.mingGongBranch], shen: BRANCHES[chart.shenGongBranch], wuju: chart.wuxingJuName, summary },
  native_sihua: { stem: STEMS[yearStem], ...native4 },
  daxian: chart.daXians, currentDaXianIndex: (chart as any).currentDaXianIndex,
  daxian_sihua: dx, liunian_sihua: { year: liunian, ...ln },
  horoscope: horoscope ?? undefined,
  palaces: chart.palaces.map(p => ({ name: p.name, gz: STEMS[(p as any).stem] + BRANCHES[(p as any).branch], stars: p.stars })),
  patterns: patterns.map(p => ({ name: p.name, level: p.level, desc: p.description, cond: p.conditions, src: p.source })),
  feixing_ref: { selfSihua, laiyin, note: '宮干自化/來因宮為飛星派參考, 倪師三合主斷不用' },
  engine: 'mingli vendor ziwei (algorithm+patterns+sihua+horoscope, snapshot 2026-09-13)',
};

if (fmt === 'json' || fmt === 'both') { if (fmt === 'both') console.log('===== JSON ====='); console.log(JSON.stringify(out, null, 2)); }
if (fmt === 'text' || fmt === 'both') {
  console.log(`【紫微全量】${solarDate} ${ZHI[hour]}時 ${gender === 'female' ? '女' : '男'} 流年${liunian}`);
  if (warnings.length) console.log(`⚠ 低置信: ${warnings.join('; ')}`);
  console.log(`命${BRANCHES[chart.mingGongBranch]} 身${BRANCHES[chart.shenGongBranch]} ${chart.wuxingJuName}｜${summary.nature} ${summary.keywords.join('·')}`);
  console.log(`本命四化(${STEMS[yearStem]}): 祿${lu(native4)} 權${quan(native4)} 科${native4['科']} 忌${native4['忌']}`);
  if (dx) console.log(`大限四化(${dx.stemName}): 祿${lu(dx.transforms)} 權${quan(dx.transforms)} 科${dx.transforms['科']} 忌${dx.transforms['忌']}`);
  console.log(`流年四化(${ln.stemName}): 祿${lu(ln.transforms)} 權${quan(ln.transforms)} 科${ln.transforms['科']} 忌${ln.transforms['忌']}`);
  for (const p of chart.palaces) {
    const ms = p.stars.map(s => `${s.name}${(s as any).siHua ? '化' + (s as any).siHua : ''}`).join(' ');
    console.log(`${p.name}(${(p as any).stem != null ? STEMS[(p as any).stem] : ''}${BRANCHES[(p as any).branch]}): ${ms || '空宮借對'}`);
  }
  console.log('\n【格局】程式全量判定 (required成立/bonus加分/breaking破格)');
  for (const g of patterns) {
    console.log(`- ${g.name} [${g.level}] ${g.description}`);
    console.log(`  成立:${(g.conditions?.required || []).join('；')} ${((g.conditions as any)?.bonus?.length ? '加分:' + (g.conditions as any).bonus.join('、') : '')} ${((g.conditions as any)?.breaking?.length ? '破格:' + (g.conditions as any).breaking.join('、') : '')} (${g.source || ''})`);
  }
  const selfKeys = Object.keys(selfSihua);
  if (selfKeys.length) console.log(`\n【飛星參考】自化: ${selfKeys.map(k => k + ':' + selfSihua[k].map((x: any) => x.starName + '化' + x.siHua).join(',')).join('；')}`);
  if (Object.keys(laiyin).length) console.log(`來因: ${Object.entries(laiyin).map(([k, v]) => k + '<-' + (v as string[]).join(',')).join('；')}`);
  if (horoscope) {
    console.log(`\n【運限】${horoscope.at} (${horoscope.lunar}) 分界:${horoscope.divide === 'exact' ? '立春' : '正月初一'}`);
    const order: Array<[string, string]> = [['daxian', '大限'], ['xiaoxian', '小限'], ['liunian', '流年'], ['liuyue', '流月'], ['liuri', '流日'], ['liushi', '流時']];
    for (const [key, label] of order) {
      const L = horoscope[key];
      const tag = key === 'xiaoxian' ? `${label}(虛歲${L.nominalAge})` : label;
      console.log(`${tag}(${L.ganzhi}) 命落${L.palace}${L.branch}: 祿${L.mutagen['祿']} 權${L.mutagen['權']} 科${L.mutagen['科']} 忌${L.mutagen['忌']}`);
      if (L.stars) console.log(`  流耀: ${Object.entries(L.stars).map(([k, v]) => `${k}:${(v as string[]).join(',')}`).join('；')}`);
    }
    const ds = horoscope.liunian.dec_star;
    if (ds.suiqian12.length) console.log(`  流年將前: ${ds.jiangqian12.join(' ')} | 歲前: ${ds.suiqian12.join(' ')}`);
  }
}
