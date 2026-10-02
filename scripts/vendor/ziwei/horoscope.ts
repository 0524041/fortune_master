/**
 * 紫微運限 (大限/小限/流年/流月/流日/流時) — 建於 iztro `astrolabe.horoscope(date, timeIndex)`.
 *
 * 與 algorithm.ts 同一 iztro 快照 (v2.5.8), 但**不屬上游 5 檔快照**: 本檔為 mingli skill 自建,
 * 直接呼叫 iztro horoscope 補齊原 ziwei_full 只算「流年四化」的缺口。
 *
 * 立場: 倪師三合. 運限四化疊本命看節點屬三合正統; 流曜為輔助參考.
 * 分界: iztro 預設 horoscopeDivide='normal' (正月初一); 可傳 'exact' 改立春分界.
 */
import { astro } from 'iztro';

export type Divide = 'normal' | 'exact';

export interface HoroscopeLevel {
  /** 層名: 大限/小限/流年/流月/流日/流時 */
  name: string;
  /** 該層干支 (如 丙午) */
  ganzhi: string;
  /** 該層命宮落本命哪一宮 (如 田宅) */
  palace: string;
  /** 落宮地支 (如 午) */
  branch: string;
  /** 該層四化, 鍵用繁體: 祿/權/科/忌 */
  mutagen: { 祿: string; 權: string; 科: string; 忌: string };
  /** 該層十二宮重排: scope=運限宮名, native=本命宮名, branch=地支 (index 0..11 對應本命宮序) */
  palaces: Array<{ scope: string; native: string; branch: string }>;
  /** 該層流耀, 鍵為 `運限宮名(地支)` → 星名陣列; 無則省略 */
  stars?: Record<string, string[]>;
}

export interface HoroscopeOut {
  /** 陽曆日期 (iztro 回傳格式 YYYY-M-D) */
  at: string;
  /** 農曆日期 (中文) */
  lunar: string;
  divide: Divide;
  daxian: HoroscopeLevel;
  xiaoxian: HoroscopeLevel & { nominalAge: number };
  liunian: HoroscopeLevel & {
    dec_star: { jiangqian12: string[]; suiqian12: string[] };
  };
  liuyue: HoroscopeLevel;
  liuri: HoroscopeLevel;
  liushi: HoroscopeLevel;
}

export interface HoroscopeBirth {
  year: number; month: number; day: number; hour: number; gender: 'male' | 'female';
}

const MUT_KEYS = ['祿', '權', '科', '忌'] as const;

function toLevel(item: any, astrolabe: any): HoroscopeLevel {
  const natal = astrolabe.palaces?.[item.index] ?? {};
  const palaces = (item.palaceNames ?? []).map((scope: string, i: number) => ({
    scope,
    native: astrolabe.palaces?.[i]?.name ?? '',
    branch: astrolabe.palaces?.[i]?.earthlyBranch ?? '',
  }));
  const mutagen: any = {};
  MUT_KEYS.forEach((k, i) => { mutagen[k] = item.mutagen?.[i] ?? ''; });
  const out: HoroscopeLevel = {
    name: item.name ?? '',
    ganzhi: `${item.heavenlyStem ?? ''}${item.earthlyBranch ?? ''}`,
    palace: natal.name ?? '',
    branch: natal.earthlyBranch ?? '',
    mutagen,
    palaces,
  };
  if (Array.isArray(item.stars)) {
    const stars: Record<string, string[]> = {};
    item.stars.forEach((arr: any[], i: number) => {
      const names = (arr ?? []).map((s: any) => s?.name).filter(Boolean);
      if (names.length) {
        const scope = item.palaceNames?.[i] ?? '';
        const zhi = astrolabe.palaces?.[i]?.earthlyBranch ?? '';
        stars[`${scope}(${zhi})`] = names;
      }
    });
    if (Object.keys(stars).length) out.stars = stars;
  }
  return out;
}

/**
 * 生成六層運限. atDate 為陽曆 YYYY-MM-DD; atTimeIndex 0=早子..11=亥, 12=晚子.
 * divide 只影響運限分界, 不動本命 yearDivide.
 */
export function generateHoroscope(
  birth: HoroscopeBirth,
  atDate: string,
  atTimeIndex: number,
  divide: Divide = 'normal',
): HoroscopeOut {
  astro.config({ horoscopeDivide: divide } as any);
  const astrolabe: any = astro.bySolar(
    `${birth.year}-${birth.month}-${birth.day}`,
    birth.hour,
    birth.gender === 'female' ? '女' : '男',
    true,
    'zh-CN',
  );
  const h: any = astrolabe.horoscope(atDate, atTimeIndex);
  const j: any = h.toJSON();
  return {
    at: j.solarDate,
    lunar: j.lunarDate,
    divide,
    daxian: toLevel(j.decadal, astrolabe),
    xiaoxian: { ...toLevel(j.age, astrolabe), nominalAge: j.age?.nominalAge ?? 0 },
    liunian: {
      ...toLevel(j.yearly, astrolabe),
      dec_star: {
        jiangqian12: j.yearly?.yearlyDecStar?.jiangqian12 ?? [],
        suiqian12: j.yearly?.yearlyDecStar?.suiqian12 ?? [],
      },
    },
    liuyue: toLevel(j.monthly, astrolabe),
    liuri: toLevel(j.daily, astrolabe),
    liushi: toLevel(j.hourly, astrolabe),
  };
}
