#!/usr/bin/env python3
"""擇日確定性掃描. 三層過濾: 通書層(建除宜忌/月破歲破/神煞) → 個人層(八字日柱) → 紫微層(流日四化).
曆法走 lunar_python, 規則走 references/methods/zeri.md. 不許 LLM 心算挑日子.
用法:
  zeri_pick.py --matter 嫁娶 --from 2026-10-01 --to 2026-12-31 [--bazi A.json [--bazi-b B.json]]
               [--ziwei Az.json [--ziwei-b Bz.json]] [--top 10] [--format text|json|both]
"""
import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))  # 內嵌 lunar_python (零安裝)
from lunar_python import Solar

DATA = Path(__file__).resolve().parent.parent / "data"
_ZH = json.loads((DATA / "ganzhi.json").read_text(encoding="utf-8"))
_SI = json.loads((DATA / "sihua.json").read_text(encoding="utf-8"))
_ZR = json.loads((DATA / "zeri_rules.json").read_text(encoding="utf-8"))

# 規則/干支表一律讀 data/ (單一真相), 不硬編
MATTERS = _ZR["matters"]
JIANCHU = {k: {kk: set(vv) for kk, vv in v.items()} for k, v in _ZR["jianchu"].items()}
YI_KW = _ZR["yi_kw"]
LUCKY = _ZR["lucky"]
EVIL = _ZR["evil"]
SHOUSI = {int(k): v for k, v in _ZR["shousi"].items()}
MING_FU_QIAN = set(_ZR["ziwei_day"]["ji_penalty_in"])
CAI_GUAN = set(_ZR["ziwei_day"]["lu_quan_bonus_in"])
CHONG = _ZH["liu_chong"]
WUXING_KE = _ZH["wu_xing_ke"]
LIUHE = _ZH["liu_he"]
TIANGAN_HE = _ZH["tian_gan_he"]
GAN_WX = _ZH["gan_wuxing"]
SANHE = _ZH["san_he"]
SI_HUA = _SI["table"]


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


# 簡轉繁 (lunar_python 吐簡體, 規則表繁體. 漏一個就是靜默失效.)
SIMP2TRAD = str.maketrans({
    "开": "開", "闭": "閉", "门": "門", "迁": "遷", "财": "財", "杀": "殺",
    "冲": "沖", "贵": "貴", "马": "馬", "鸡": "雞", "龙": "龍", "仓": "倉",
    "寿": "壽", "发": "發", "丰": "豐", "丽": "麗", "宝": "寶", "显": "顯",
    "镇": "鎮", "钟": "鐘", "长": "長", "阴": "陰", "阳": "陽", "际": "際",
    "泽": "澤", "满": "滿", "达": "達", "运": "運", "远": "遠", "迟": "遲",
    "惊": "驚", "罗": "羅", "败": "敗", "废": "廢", "兽": "獸", "画": "畫",
    "钩": "鉤", "绞": "絞", "络": "絡", "续": "續", "绝": "絕", "缠": "纏",
    "计": "計", "时": "時", "晓": "曉", "鸣": "鳴", "吠": "吠", "圣": "聖",
    "临": "臨", "监": "監", "鉴": "鑒", "钦": "欽", "饿": "餓", "饱": "飽",
    "贪": "貪", "贞": "貞", "禄": "祿", "机": "機", "辅": "輔", "庄": "莊",
    "凤": "鳳", "鸾": "鸞", "咸": "咸", "乔": "喬", "汤": "湯", "沟": "溝",
    "汉": "漢", "泽": "澤", "洁": "潔", "洪": "洪", "浊": "濁", "浏": "瀏",
})


def tr(text):
    return text.translate(SIMP2TRAD)


def tr_list(items):
    return [tr(x) for x in items]


def day_info(dt):
    l = Solar.fromYmdHms(dt.year, dt.month, dt.day, 12, 0, 0).getLunar()
    return {"date": dt.strftime("%Y-%m-%d"),
            "ganzhi": tr(l.getDayInGanZhiExact()),
            "gan": tr(l.getDayGanExact()), "zhi": tr(l.getDayZhiExact()),
            "month_zhi": tr(l.getMonthZhi()), "year_zhi": tr(l.getYearZhi()),
            "lunar_month": l.getMonth(),
            "jianchu": tr(l.getZhiXing()),
            "huangdao": tr(l.getDayTianShen()) + tr(l.getDayTianShenLuck()),
            "huangdao_good": l.getDayTianShenLuck() == "吉",
            "yi": tr_list(l.getDayYi()), "ji": tr_list(l.getDayJi()),
            "jishen": tr_list(l.getDayJiShen()), "xiongsha": tr_list(l.getDayXiongSha())}


def check_abs(day):
    """L1 絕對否決 (全年任何事項): 月破/歲破/受死/建除破日. 回否決理由 list."""
    veto = []
    if CHONG.get(day["zhi"]) == day["month_zhi"]:
        veto.append(f"月破(日支{day['zhi']}沖月建{day['month_zhi']})")
    if CHONG.get(day["zhi"]) == day["year_zhi"]:
        veto.append(f"歲破(日支{day['zhi']}沖年支{day['year_zhi']})")
    if SHOUSI.get(day["lunar_month"]) == day["zhi"]:
        veto.append(f"受死日(農曆{day['lunar_month']}月逢{day['zhi']})")
    if day["jianchu"] == "破":
        veto.append("建除破日(大凶)")
    return veto


def check_matter(day, matter):
    """L1 事項層: 建除宜忌/通書宜忌否決/加分 + 黃道 + 吉神 + 凶煞否決.
    回 (score, plus[], veto[])."""
    jc = JIANCHU[matter]
    score, plus, veto = 0, [], []
    j = day["jianchu"]
    if j in jc["veto"]:
        veto.append(f"建除{j}日忌{matter}")
    elif j in jc["plus2"]:
        score += 2
        plus.append(f"建除{j}日大吉+2")
    elif j in jc["plus1"]:
        score += 1
        plus.append(f"建除{j}日次吉+1")
    elif j in jc["minus1"]:
        score -= 1
        plus.append(f"建除{j}日凶-1")
    if any(kw in day["ji"] for kw in YI_KW[matter]):
        veto.append(f"通書忌含{matter}({','.join(day['ji'][:3])})")
    elif any(kw in day["yi"] for kw in YI_KW[matter]):
        score += 1
        plus.append("通書宜含+1")
    score += 1 if day["huangdao_good"] else -1
    plus.append(f"黃道{day['huangdao']}{'+1' if day['huangdao_good'] else '-1'}")
    lucky_hits = [g for g in LUCKY[matter]
                  if any(g in s for s in day["jishen"])]
    for g in lucky_hits[:2]:
        score += 1
        plus.append(f"吉神{g}+1")
    for e in EVIL[matter]:
        if any(e in s for s in day["xiongsha"]):
            veto.append(f"凶煞{e}忌{matter}")
    return score, plus, veto


def day_pillar(bazi):
    for p in bazi.get("pillars", []):
        if p.get("label") == "日柱":
            return tr(p["gan"]), tr(p["zhi"])
    return "", ""


def check_personal(day, bazi, tag):
    """L2 個人層: 日支沖日支否決; 日支六合/半三合+1; 日干五合+1; 日干剋-1.
    回 (score, plus[], veto[])."""
    score, plus, veto = 0, [], []
    mg, mz = day_pillar(bazi)
    if not mg:
        return score, plus, veto
    if CHONG.get(day["zhi"]) == mz:
        veto.append(f"{tag}日支沖(流日{day['zhi']}沖命主{mz})")
        return score, plus, veto
    if LIUHE.get(day["zhi"]) == mz:
        score += 1
        plus.append(f"{tag}日支六合{day['zhi']}{mz}+1")
    else:
        for grp in SANHE:
            if day["zhi"] in grp and mz in grp:
                score += 1
                plus.append(f"{tag}日支半三合{day['zhi']}{mz}+1")
                break
    if TIANGAN_HE.get(day["gan"]) == mg:
        score += 1
        plus.append(f"{tag}日干{mg}{day['gan']}合+1")
    elif GAN_WX.get(day["gan"]) and GAN_WX.get(mg) and (
            WUXING_KE.get(GAN_WX[day["gan"]]) == GAN_WX[mg]
            or WUXING_KE.get(GAN_WX[mg]) == GAN_WX[day["gan"]]):
        score -= 1
        plus.append(f"{tag}日干剋({day['gan']}vs{mg})-1")
    return score, plus, veto


def locate_star(chart, star):
    for p in chart.get("palaces", []):
        if any(s["name"] == star for s in p.get("stars", [])):
            return p.get("name")
    return ""


def short_palace(name):
    return tr(name).rstrip("宫宮") if name else ""


def check_ziwei_day(day, chart, tag):
    """L3 紫微層: 流日干四化. 忌落命/夫妻/遷移-1; 祿/權落命/財帛/官祿+1.
    回 (score, plus[])."""
    score, plus = 0, []
    trans = SI_HUA.get(day["gan"], ["", "", "", ""])
    lu, quan, _, ji = trans[0], trans[1], trans[2], trans[3]
    if ji:
        pal = short_palace(locate_star(chart, ji))
        if pal in ("命", "夫妻", "遷移"):
            score -= 1
            plus.append(f"{tag}流日忌{tr(ji)}在{pal}-1")
    for star, kind in ((lu, "祿"), (quan, "權")):
        if not star:
            continue
        pal = short_palace(locate_star(chart, star))
        if pal in ("命", "財帛", "官祿"):
            score += 1
            plus.append(f"{tag}流日{kind}{tr(star)}在{pal}+1")
    return score, plus


def main():
    ap = argparse.ArgumentParser(description="擇日確定性掃描")
    ap.add_argument("--matter", required=True, choices=MATTERS)
    ap.add_argument("--from", dest="date_from", required=True)
    ap.add_argument("--to", dest="date_to", required=True)
    ap.add_argument("--bazi", default=None)
    ap.add_argument("--bazi-b", default=None)
    ap.add_argument("--ziwei", default=None)
    ap.add_argument("--ziwei-b", default=None)
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--format", default="text", choices=["text", "json", "both"])
    a = ap.parse_args()

    d0 = datetime.strptime(a.date_from, "%Y-%m-%d")
    d1 = datetime.strptime(a.date_to, "%Y-%m-%d")
    bazis = []
    if a.bazi:
        bazis.append(("甲", load(a.bazi)))
    if a.bazi_b:
        bazis.append(("乙", load(a.bazi_b)))
    ziweis = []
    if a.ziwei:
        ziweis.append(("甲", load(a.ziwei)))
    if a.ziwei_b:
        ziweis.append(("乙", load(a.ziwei_b)))
    days = []
    dt = d0
    while dt <= d1:
        info = day_info(dt)
        info.update({"status": "candidate", "score": 0, "plus": [], "veto": [],
                     "tongshu": 0, "personal": 0, "ziwei_pt": 0})
        veto = check_abs(info)
        if not veto:
            sc, pl, vt = check_matter(info, a.matter)
            info["tongshu"] = sc
            info["score"] += sc
            info["plus"] += pl
            veto = vt
        for tag, bz in bazis:
            if veto:
                break
            sc, pl, vt = check_personal(info, bz, tag)
            info["personal"] += sc
            info["score"] += sc
            info["plus"] += pl
            veto = vt
        if not veto:
            for tag, zw in ziweis:
                sc, pl = check_ziwei_day(info, zw, tag)
                info["ziwei_pt"] += sc
                info["score"] += sc
                info["plus"] += pl
        if veto:
            info["status"] = "vetoed"
            info["veto"] = veto
        days.append(info)
        dt += timedelta(days=1)

    cands = [d for d in days if d["status"] == "candidate"]
    cands.sort(key=lambda d: (-d["score"], d["date"]))
    out = {"matter": a.matter, "from": a.date_from, "to": a.date_to,
           "days": days, "top": cands[:a.top],
           "summary": {"scanned": len(days), "vetoed": len(days) - len(cands),
                       "candidates": len(cands)},
           "engine": "zeri_pick v1 (lunar_python + zeri.md)"}

    if a.format in ("text", "both"):
        print(f"【擇日-{a.matter}】掃描{len(days)}天 候選{len(cands)} 否決{len(days) - len(cands)}")
        for t in cands[:a.top]:
            print(f"{t['date']} {t['ganzhi']}{t['jianchu']} {t['huangdao']} {t['score']}分")
            for p in t["plus"][:6]:
                print(f"  + {p}")
        vetoed = [d for d in days if d["status"] == "vetoed"]
        if vetoed:
            print(f"-- 否決{len(vetoed)}天 (前5) --")
            for v in vetoed[:5]:
                print(f"{v['date']} {v['ganzhi']}{v['jianchu']}: {'; '.join(v['veto'][:2])}")
    if a.format in ("json", "both"):
        if a.format == "both":
            print("===== JSON =====")
        print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
