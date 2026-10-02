#!/usr/bin/env python3
"""八字確定性排盤. 曆法一律走 lunar_python + 真太陽時, 不許 LLM 心算.
用法:
  ./scripts/.venv/bin/python scripts/bazi_pai.py --date 1990-08-18 --time 06:30 --city 台北 --gender male
  --lon 121.5 可覆蓋城市經度. --format text|json|both. --year 2026 看該年流年干支.
環境: 自帶 venv (bash scripts/setup.sh, lunar_python pin 版, 八字/六爻/梅花/擇日共用)
"""
import argparse, json, sys
from datetime import datetime, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from time_correct import true_solar
from lunar_python import Lunar, Solar
from lunar_python.util import LunarUtil

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
# 知識/表格一律讀 data/ (單一真相), 不硬編
TIAOHOU = json.loads((DATA_DIR / "tiaohou.json").read_text(encoding="utf-8"))
_GZ = json.loads((DATA_DIR / "ganzhi.json").read_text(encoding="utf-8"))
_SS = json.loads((DATA_DIR / "shensha.json").read_text(encoding="utf-8"))

GAN = _GZ["gan"]
ZHI = _GZ["zhi"]
GAN_WX = _GZ["gan_wuxing"]
ZHI_WX = _GZ["zhi_wuxing"]
HIDDEN = _GZ["hidden"]          # 藏干 (本氣/中氣/餘氣)
LIUHE = _GZ["liu_he"]
LIUCHONG = _GZ["liu_chong"]
SANHE = _GZ["san_he"]

def build_dayun(lunar, gender: str):
    """大運: 起運須數至「節」(非中氣), 3天折1年, 干支由月柱順逆推.
    數值以 lunar_python Yun 為準 (sect=1). 童限(起運前)不列入 pillars."""
    ec = lunar.getEightChar()
    yun = ec.getYun(1 if gender == "male" else 0, 1)
    forward = yun.isForward()
    jie = lunar.getNextJie() if forward else lunar.getPrevJie()
    out = []
    for d in yun.getDaYun(9):
        gz = d.getGanZhi()
        if not gz:  # 童限, 無干支
            continue
        out.append({"step": d.getIndex(), "gan_zhi": gz,
                    "age": f"{d.getStartAge()}-{d.getEndAge()}",
                    "years": f"{d.getStartYear()}-{d.getEndYear()}",
                    "start_age": d.getStartAge(), "xunkong": d.getXunKong()})
        if len(out) == 8:
            break
    return {"direction": "順" if forward else "逆",
            "start_age": out[0]["start_age"] if out else 0,
            "start_years": yun.getStartYear(),
            "start_solar": yun.getStartSolar().toYmd(),
            "base_jieqi": jie.getName(),
            "rule": "起運數至節(非中氣), 3天=1年, 干支月柱順逆推",
            "pillars": out}


def liuyue_pillars(year_gan: str, day_gan: str):
    """該流年 12 流月干支 (五虎遁, 寅月起) + 十神 (以日干論)."""
    yin_stem = {"甲": "丙", "己": "丙", "乙": "戊", "庚": "戊", "丙": "庚",
                "辛": "庚", "丁": "壬", "壬": "壬", "戊": "甲", "癸": "甲"}[year_gan]
    out = []
    for i in range(12):
        g = GAN[(GAN.index(yin_stem) + i) % 10]
        z = ZHI[(ZHI.index("寅") + i) % 12]
        out.append({"month": i + 1, "month_zhi": z, "gan_zhi": f"{g}{z}",
                    "shishen": LunarUtil.SHI_SHEN.get(day_gan + g, "")})
    return out


def _solar_dt(s):
    return datetime(s.getYear(), s.getMonth(), s.getDay(), s.getHour(), s.getMinute())


GEJU_NAME = {"正官": "正官格", "七杀": "七殺格", "正财": "正財格", "偏财": "偏財格",
             "食神": "食神格", "伤官": "傷官格", "正印": "正印格", "偏印": "偏印格",
             "比肩": "建祿格", "劫财": "月刃格"}
CHONG = LIUCHONG


def analyze_geju(pillars, day_gan):
    """月令取格 (bazi_geju.md #2): 月支藏干透於年/月/時干者為格, 本氣優先; 不透取本氣."""
    mz = pillars[1][1]
    hidden = HIDDEN[mz]
    tian = [pillars[0][0], pillars[1][0], pillars[3][0]]  # 年/月/時干 (不含日主)
    tiers = ["本氣", "中氣", "餘氣"] if len(hidden) == 3 else (["本氣", "中氣"] if len(hidden) == 2 else ["本氣"])
    source, shishen, hit = None, None, ""
    for i, h in enumerate(hidden):
        if h in tian:
            source, shishen, hit = tiers[i], LunarUtil.SHI_SHEN.get(day_gan + h, ""), h
            break
    if shishen is None:
        hit = hidden[0]
        source, shishen = "本氣(不透)", LunarUtil.SHI_SHEN.get(day_gan + hit, "")
    breaking = [f"月支{mz}被{p[1]}沖" for i, p in enumerate(pillars)
                if i != 1 and CHONG.get(p[1]) == mz]
    return {"name": GEJU_NAME.get(shishen, shishen + "格"), "shishen": shishen,
            "month_zhi": mz, "source": source,
            "evidence": f"月令{mz}藏{','.join(hidden)}, 取{source}干{hit}為{shishen}",
            "breaking": breaking}


def analyze_yongshen(day_gan, month_zhi, strength):
    """用神: 扶抑為主 (day_strength.xi/ji), 調候為輔 (窮通寶鑑表, 日干+月支)."""
    entry = TIAOHOU["table"].get(day_gan + month_zhi)
    tiaohou = None
    if entry:
        tiaohou = {"primary": entry["primary"], "full": entry["full"],
                   "note": entry.get("note", ""), "source": TIAOHOU["name"],
                   "key": day_gan + month_zhi}
    return {"method": "扶抑為主(身強弱xi/ji), 調候為輔(窮通寶鑑表)",
            "xi": strength["xi"], "ji": strength["ji"],
            "tiaohou": tiaohou, "primary": strength["xi"][0]}


# 八字神煞表 (讀 data/shensha.json; 傳統參考, 三合派不主斷)
TIANYI = _SS["tianyi"]
LUSHEN = _SS["lushen"]
YANGREN = _SS["yangren"]        # 陽干帝旺, 陰干從略
WENCHANG = _SS["wenchang"]
TAOHUA = _SS["taohua"]
YIMA = _SS["yima"]
HUAGAI = _SS["huagai"]
JIANGXING = _SS["jiangxing"]
HONGLUAN = _SS["hongluan"]
TIANXI = {k: ZHI[(ZHI.index(v) + 6) % 12] for k, v in HONGLUAN.items()}
GUCHEN = _SS["guchen"]
GUASU = _SS["guasu"]


def analyze_shensha(pillars, day_gan):
    """核心八字神煞: 天乙貴人/祿神/羊刃/文昌(日干); 桃花/驛馬/華蓋/將星(年支+日支);
    紅鸞/天喜/孤辰/寡宿(年支). 只列四柱命中的神煞."""
    labels = ["年", "月", "日", "時"]
    zhis = [p[1] for p in pillars]
    year_zhi, day_zhi = zhis[0], zhis[2]
    found = []

    def hit(name, targets, basis):
        t = targets if isinstance(targets, list) else [targets]
        at = [labels[i] for i, z in enumerate(zhis) if z in t]
        if at:
            found.append({"name": name, "basis": basis, "target": t, "at": at})

    hit("天乙貴人", TIANYI.get(day_gan, []), f"日干{day_gan}")
    hit("祿神", LUSHEN.get(day_gan, ""), f"日干{day_gan}")
    if YANGREN.get(day_gan):
        hit("羊刃", YANGREN[day_gan], f"日干{day_gan}")
    hit("文昌", WENCHANG.get(day_gan, ""), f"日干{day_gan}")
    for basis, z in ((f"年支{year_zhi}", year_zhi), (f"日支{day_zhi}", day_zhi)):
        hit("桃花", TAOHUA.get(z, ""), basis)
        hit("驛馬", YIMA.get(z, ""), basis)
        hit("華蓋", HUAGAI.get(z, ""), basis)
        hit("將星", JIANGXING.get(z, ""), basis)
    hit("紅鸞", HONGLUAN.get(year_zhi, ""), f"年支{year_zhi}")
    hit("天喜", TIANXI.get(year_zhi, ""), f"年支{year_zhi}")
    hit("孤辰", GUCHEN.get(year_zhi, ""), f"年支{year_zhi}")
    hit("寡宿", GUASU.get(year_zhi, ""), f"年支{year_zhi}")
    return {"found": found, "note": "神煞為傳統參考, 三合派不主斷; at 指該支落於哪柱"}


def verify(data, corr, lunar):
    """確定性校驗: 四項不變式 + 低置信警告 (跨日/時辰交界/節氣交界). 供紅線把關."""
    tc = data["input"]
    pillars = data["pillars"]
    dayun = data["dayun"]
    checks, warnings = {}, []

    # 1) 真太陽時可逆: 校正後回推鐘錶時間誤差 < 1 分
    in_dt = datetime.strptime(tc["input"], "%Y-%m-%d %H:%M")
    ts_dt = datetime.strptime(tc["true_solar"], "%Y-%m-%d %H:%M")
    back = ts_dt - timedelta(minutes=tc["total_corr_min"])
    diff_min = abs((back - in_dt).total_seconds()) / 60
    checks["true_solar_reversible"] = {"ok": diff_min <= 1.0, "back_min": round(diff_min, 3)}

    # 2) 時支自洽: 四柱時支 == 真太陽時落支
    mins = ts_dt.hour * 60 + ts_dt.minute
    branch = ZHI[((mins + 60) % 1440) // 120]
    checks["hour_branch_consistent"] = {
        "ok": branch == pillars[3]["zhi"], "expected": branch, "got": pillars[3]["zhi"]}

    # 3) 大運基準節氣: 必為 12 節, 距出生 0..32 天, 起運日 > 出生日
    forward = dayun["direction"] == "順"
    jie = lunar.getNextJie() if forward else lunar.getPrevJie()
    gap_days = abs((_solar_dt(jie.getSolar()) - corr).total_seconds()) / 86400
    start_dt = datetime.strptime(dayun["start_solar"], "%Y-%m-%d")
    checks["dayun_jieqi_between"] = {
        "ok": gap_days <= 32 and start_dt > corr and jie.getName() == dayun["base_jieqi"],
        "jie": jie.getName(), "gap_days": round(gap_days, 2)}

    # 4) 納音對表
    bad = [p["gan"] + p["zhi"] for p in pillars
           if LunarUtil.NAYIN.get(p["gan"] + p["zhi"]) != p["nayin"]]
    checks["nayin_table"] = {"ok": not bad, "bad": bad}

    # 低置信警告
    if data.get("warn"):
        warnings.append(data["warn"])
    bounds = [0] + list(range(60, 1440, 120))
    nearest = min(min(abs(mins - b), 1440 - abs(mins - b)) for b in bounds)
    if nearest <= 10:
        warnings.append(f"近時辰交界(距{nearest}分)")
    nj, pj = _solar_dt(lunar.getNextJie().getSolar()), _solar_dt(lunar.getPrevJie().getSolar())
    jie_gap = min(abs((nj - corr).total_seconds()), abs((pj - corr).total_seconds())) / 86400
    if jie_gap <= 1:
        warnings.append(f"近節氣交界({jie_gap:.2f}天)")
    checks["all_pass"] = all(c["ok"] for c in checks.values() if isinstance(c, dict) and "ok" in c)
    return {"checks": checks, "warnings": warnings, "all_pass": checks["all_pass"]}

def wuxing_score(pillars):
    sc = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    for g, z in pillars:
        sc[GAN_WX[g]] += 10
        hid = HIDDEN[z]
        weights = [10] if len(hid) == 1 else [6, 3, 1]
        for h, w in zip(hid, weights):
            sc[GAN_WX[h]] += w
    return sc

def _rel(me_wx, other_wx):
    """other相對me的五行關係: 同/生我/我生/剋我/我剋."""
    if other_wx == me_wx:
        return "同"
    if other_wx == {"木": "水", "火": "木", "土": "火", "金": "土", "水": "金"}[me_wx]:
        return "生我"
    if {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}[me_wx] == other_wx:
        return "我生"
    if {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}[me_wx] == other_wx:
        return "我剋"
    return "剋我"


def day_strength(pillars, day_gan):
    """扶抑打分 v1: 同黨(比劫)+印(生我)為+, 官殺財食傷為-.
    天干10分, 藏干本氣6/中氣3/餘氣1 (與 wuxing_score 同權重).
    >5身強, <-5身弱,  else中和. 身強喜剋洩耗忌生扶; 身弱反之; 中和喜印比忌官殺."""
    me_wx = GAN_WX[day_gan]
    plus = minus = 0
    for g, z in pillars:
        if g != day_gan:
            if _rel(me_wx, GAN_WX[g]) in ("同", "生我"):
                plus += 10
            else:
                minus += 10
        hid = HIDDEN[z]
        weights = [10] if len(hid) == 1 else [6, 3, 1]
        for h, w in zip(hid, weights):
            r = _rel(me_wx, GAN_WX[h])
            if r in ("同", "生我"):
                plus += w
            else:
                minus += w
    score = plus - minus
    if score > 5:
        level, xi, ji = "身強", ["官殺", "食傷", "財"], ["比劫", "印"]
    elif score < -5:
        level, xi, ji = "身弱", ["比劫", "印"], ["官殺", "食傷", "財"]
    else:
        level, xi, ji = "中和", ["印", "比劫"], ["官殺"]
    return {"score": score, "level": level, "xi": xi, "ji": ji,
            "rule": "同黨+印−官殺財食傷, 天干10/藏干6-3-1, ±5分界"}


def relations(zhis):
    out, seen = [], set()
    s = set(zhis)
    for a, b in LIUHE.items():
        key = frozenset((a, b))
        if a in s and b in s and key not in seen:
            seen.add(key)
            out.append(f"{a}{b}六合")
    for a, b in LIUCHONG.items():
        key = frozenset((a, b))
        if a in s and b in s and key not in seen:
            seen.add(key)
            out.append(f"{a}{b}六沖")
    for grp in SANHE:
        if all(g in s for g in grp):
            out.append(f"{''.join(grp)}三合局")
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="依 --calendar: 國曆 YYYY-MM-DD 或農曆 YYYY-MM-DD")
    ap.add_argument("--time", default="12:00", help="HH:MM")
    ap.add_argument("--calendar", default="solar", choices=["solar", "lunar"], help="日期曆制 (預設 solar)")
    ap.add_argument("--leap", action="store_true", help="農曆閏月")
    ap.add_argument("--city", default="")
    ap.add_argument("--lon", type=float, default=None)
    ap.add_argument("--gender", required=True, choices=["male", "female"])
    ap.add_argument("--format", default="text", choices=["text", "json", "both"])
    ap.add_argument("--year", type=int, default=None, help="流年年份")
    a = ap.parse_args()

    hh, mm = (int(x) for x in a.time.split(":"))
    if a.calendar == "lunar":
        y, mo, da = (int(x) for x in a.date.split("-"))
        try:
            sol = Lunar.fromYmdHms(y, -mo if a.leap else mo, da, hh, mm, 0).getSolar()
        except Exception as e:
            print(f"錯誤: 農曆日期無效 ({a.date}{' 閏月' if a.leap else ''}): {e}", file=sys.stderr)
            sys.exit(2)
        base = datetime(sol.getYear(), sol.getMonth(), sol.getDay(), hh, mm)
    else:
        base = datetime.strptime(f"{a.date} {a.time}", "%Y-%m-%d %H:%M")
    try:
        corr, tc = true_solar(base, city=a.city, lon=a.lon)
    except ValueError as e:
        print(f"錯誤: {e} (須給 --city 出生城市 或 --lon 經度, 無預設值以免靜默錯盤)",
              file=sys.stderr)
        sys.exit(2)
    warn = "⚠ 真太陽時跨日, 日柱以校正後為準" if corr.date() != base.date() else ""
    s = Solar.fromYmdHms(corr.year, corr.month, corr.day, corr.hour, corr.minute, 0)
    lunar = s.getLunar()
    pillars = [(lunar.getYearGan(), lunar.getYearZhi()), (lunar.getMonthGan(), lunar.getMonthZhi()),
               (lunar.getDayGan(), lunar.getDayZhi()), (lunar.getTimeGan(), lunar.getTimeZhi())]
    ec = lunar.getEightChar()
    day_gan = pillars[2][0]
    # 逐柱本質資訊 (納音/十神支/藏干十神/長生十二運/旬空) 全走 lunar_python, 不心算
    cols = [
        ("年柱", ec.getYearGan, ec.getYearZhi, ec.getYearShiShenGan, ec.getYearShiShenZhi,
         ec.getYearHideGan, ec.getYearNaYin, ec.getYearDiShi, ec.getYearXunKong),
        ("月柱", ec.getMonthGan, ec.getMonthZhi, ec.getMonthShiShenGan, ec.getMonthShiShenZhi,
         ec.getMonthHideGan, ec.getMonthNaYin, ec.getMonthDiShi, ec.getMonthXunKong),
        ("日柱", ec.getDayGan, ec.getDayZhi, ec.getDayShiShenGan, ec.getDayShiShenZhi,
         ec.getDayHideGan, ec.getDayNaYin, ec.getDayDiShi, ec.getDayXunKong),
        ("時柱", ec.getTimeGan, ec.getTimeZhi, ec.getTimeShiShenGan, ec.getTimeShiShenZhi,
         ec.getTimeHideGan, ec.getTimeNaYin, ec.getTimeDiShi, ec.getTimeXunKong),
    ]
    pillar_data = []
    for label, fgan, fzhi, fss, fssz, fhid, fnayin, fdishi, fxk in cols:
        hid = fhid()
        pillar_data.append({
            "label": label, "gan": fgan(), "zhi": fzhi(),
            "shishen": fss(), "shishen_zhi": fssz(),
            "hidden": hid, "hidden_shishen": [LunarUtil.SHI_SHEN.get(day_gan + h, "") for h in hid],
            "nayin": fnayin(), "dishi": fdishi(), "xunkong": fxk(),
        })
    extras = {
        "taiyuan": {"gan_zhi": ec.getTaiYuan(), "nayin": ec.getTaiYuanNaYin()},
        "taixi": {"gan_zhi": ec.getTaiXi(), "nayin": ec.getTaiXiNaYin()},
        "minggong": {"gan_zhi": ec.getMingGong(), "nayin": ec.getMingGongNaYin()},
        "shengong": {"gan_zhi": ec.getShenGong(), "nayin": ec.getShenGongNaYin()},
    }
    score = wuxing_score(pillars)
    strength = day_strength(pillars, day_gan)
    geju = analyze_geju(pillars, day_gan)
    yongshen = analyze_yongshen(day_gan, pillars[1][1], strength)
    shensha = analyze_shensha(pillars, day_gan)
    dayun = build_dayun(lunar, a.gender)
    rel = relations([z for _, z in pillars])
    data = {"input": tc, "warn": warn, "gender": a.gender,
            "calendar": a.calendar,
            "birth_input": {"date": a.date, "calendar": a.calendar, "leap": a.leap},
            "pillars": pillar_data,
            "day_master": f"{day_gan}{GAN_WX[day_gan]}",
            "wuxing_score": score, "day_strength": strength,
            "geju": geju, "yongshen": yongshen, "shensha": shensha,
            "extras": extras,
            "relations": rel, "dayun": dayun,
            "engine": "lunar_python+true_solar(EoT近似,誤差<1分)"}
    data["verification"] = verify(data, corr, lunar)
    if a.year:
        # 取年中(6/1)定年干支: 立春時刻每年浮動, 固定2/4取法在立春日晚會錯年柱
        ly = Solar.fromYmdHms(a.year, 6, 1, 12, 0, 0).getLunar()
        ygan = ly.getYearGan()
        data["liunian"] = {"year": a.year, "gan_zhi": f"{ygan}{ly.getYearZhi()}",
                           "shishen": LunarUtil.SHI_SHEN.get(day_gan + ygan, ""),
                           "liuyue": liuyue_pillars(ygan, day_gan)}
    if a.format in ("text", "both"):
        p = data["pillars"]
        print(f"【八字】{a.gender} {tc['input']} ({tc['city']} lon{tc['lon']}) -> 真太陽時 {tc['true_solar']} (經差{tc['lon_corr_min']}分+均時差{tc['eot_min']}分)")
        if warn:
            print(warn)
        print(f"四柱: {' '.join(x['gan']+x['zhi'] for x in p)}  日主:{data['day_master']}")
        print(f"十神(干): {' '.join(x['shishen'] for x in p)}")
        print(f"藏干: {' | '.join(x['zhi']+':'+','.join(x['hidden'])+'('+'/'.join(x['hidden_shishen'])+')' for x in p)}")
        print(f"納音: {' '.join(x['label']+x['nayin'] for x in p)}")
        print(f"長生: {' '.join(x['zhi']+x['dishi'] for x in p)}  旬空: {' '.join(x['zhi']+x['xunkong'] for x in p)}")
        print(f"胎元{extras['taiyuan']['gan_zhi']} 胎息{extras['taixi']['gan_zhi']} 命宮{extras['minggong']['gan_zhi']} 身宮{extras['shengong']['gan_zhi']}")
        print(f"五行分: {score}  關係: {'、'.join(rel) if rel else '無明顯合沖'}")
        print(f"身強弱: {strength['level']}{strength['score']}分 喜{'+'.join(strength['xi'])} 忌{'+'.join(strength['ji'])}")
        print(f"格局: {geju['name']} ({geju['evidence']})" +
              (f" 破格:{';'.join(geju['breaking'])}" if geju['breaking'] else ""))
        print(f"用神: 扶抑{'+'.join(yongshen['xi'])}為主" +
              (f" | 調候{yongshen['tiaohou']['primary']}為主(全{'/'.join(yongshen['tiaohou']['full'])}, {yongshen['tiaohou']['note']})" if yongshen['tiaohou'] else "") +
              f" 忌{'+'.join(yongshen['ji'])}")
        if shensha["found"]:
            print("神煞: " + "、".join(f"{x['name']}({'/'.join(x['at'])}柱)" for x in shensha["found"]))
        print(f"大運({dayun['direction']}排,{dayun['start_age']}歲起運[{dayun['start_solar']}],基準{dayun['base_jieqi']}): " +
              " | ".join(f"{d['age']}歲{d['gan_zhi']}" for d in dayun["pillars"][:4]))
        if a.year:
            lny = data["liunian"]
            print(f"流年{lny['year']}{lny['gan_zhi']}({lny['shishen']}): " +
                  " | ".join(f"{m['month_zhi']}{m['gan_zhi']}{m['shishen']}" for m in lny["liuyue"]))
        v = data["verification"]
        ck = v["checks"]
        print(f"校驗: {'全通過' if v['all_pass'] else '有項目未過'} "
              f"| 真太陽時可逆{ck['true_solar_reversible']['ok']} "
              f"時支自洽{ck['hour_branch_consistent']['ok']} "
              f"大運節氣{ck['dayun_jieqi_between']['ok']} 納音{ck['nayin_table']['ok']}")
        if v["warnings"]:
            print(f"⚠ 低置信: {'; '.join(v['warnings'])}")
    if a.format in ("json", "both"):
        if a.format == "both":
            print("\n===== JSON =====")
        print(json.dumps(data, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
