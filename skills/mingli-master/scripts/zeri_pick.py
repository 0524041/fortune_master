#!/usr/bin/env python3
"""擇日確定性掃描 v2. 四層: 通書日層 → 個人八字日層 → 紫微日層 → (可選)時辰吉時層.

曆法走 tongshu_core (內嵌 lunar_python), 規則走 data/zeri_rules.json + references/ask-person/zeri.md.
簡繁統一由 han 層處理 (tongshu_core 已轉繁), 本檔不再自帶字表. 不許 LLM 心算挑日子/時辰.

用法:
  zeri_pick.py --matter 入宅 --from 2026-10-01 --to 2026-12-31
               [--bazi A.json [--bazi-b B.json]] [--ziwei Az.json [--ziwei-b Bz.json]]
               [--hours [--hour-top 3] [--qimen]] [--top 10] [--format text|json|both]
"""
import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR))
from tongshu_core import (day_facts, hours_of_day, personal_relations,  # noqa: E402
                          simplified_leaks, qimen_brief, CHONG)
from han import norm_palace, s2t_deep  # noqa: E402

DATA = DIR.parent / "data"
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
SI_HUA = _SI["table"]


def load(p):
    with open(p, encoding="utf-8") as f:
        return s2t_deep(json.load(f))  # 統一簡繁層: 引擎輸出 (八字/紫微) 轉繁


# ── 日層 ──────────────────────────────────────────────────────────
def day_info(dt):
    d = day_facts(dt)
    d.update({"status": "candidate", "score": 0, "plus": [], "veto": [],
              "tongshu": 0, "personal": 0, "ziwei_pt": 0})
    return d


def check_abs(day):
    """L1 絕對否決 (全年任何事項): 月破/歲破/受死/建除破日."""
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
    """L1 事項層: 建除宜忌/通書宜忌否決/加分 + 黃道 + 吉神 + 凶煞否決. 回 (score, plus, veto)."""
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
    lucky_hits = [g for g in LUCKY[matter] if any(g in s for s in day["jishen"])]
    for g in lucky_hits[:2]:
        score += 1
        plus.append(f"吉神{g}+1")
    for e in EVIL[matter]:
        if any(e in s for s in day["xiongsha"]):
            veto.append(f"凶煞{e}忌{matter}")
    return score, plus, veto


def check_personal(day, bazi, tag):
    """L2 個人層: 日支沖日支否決; 日支六合/半三合+1; 日干五合+1; 日干剋-1."""
    score, plus, veto = 0, [], []
    rel = personal_relations(day["gan"], day["zhi"], bazi)
    if not rel:
        return score, plus, veto
    if rel["chong_day"]:
        veto.append(f"{tag}日支沖(流日{day['zhi']}沖命主{rel['day_zhi']})")
        return score, plus, veto
    if rel["liuhe_day"] or rel["sanhe_day"]:
        score += 1
        plus.append(f"{tag}日支{'六合' if rel['liuhe_day'] else '半三合'}{day['zhi']}{rel['day_zhi']}+1")
    if rel["gan_he"]:
        score += 1
        plus.append(f"{tag}日干{rel['day_master']}{day['gan']}合+1")
    elif rel["gan_ke"]:
        score -= 1
        plus.append(f"{tag}日干剋({day['gan']}vs{rel['day_master']})-1")
    return score, plus, veto


def locate_star(chart, star):
    for p in chart.get("palaces", []):
        if any(s["name"] == star for s in p.get("stars", [])):
            return p.get("name")
    return ""


def check_ziwei_day(day, chart, tag):
    """L3 紫微層: 流日干四化. 忌落命/夫妻/遷移-1; 祿/權落命/財帛/官祿+1. 回 (score, plus)."""
    score, plus = 0, []
    trans = SI_HUA.get(day["gan"], ["", "", "", ""])
    lu, quan, _, ji = trans[0], trans[1], trans[2], trans[3]
    if ji:
        pal = norm_palace(locate_star(chart, ji))
        if pal in MING_FU_QIAN:
            score -= 1
            plus.append(f"{tag}流日忌{ji}在{pal}-1")
    for star, kind in ((lu, "祿"), (quan, "權")):
        if not star:
            continue
        pal = norm_palace(locate_star(chart, star))
        if pal in CAI_GUAN:
            score += 1
            plus.append(f"{tag}流日{kind}{star}在{pal}+1")
    return score, plus


# ── 時辰吉時層 ────────────────────────────────────────────────────
def check_hour(hour, matter, bazis, ziweis):
    """時辰層: 通書時宜/時忌 + 黃道黑道 + 個人(沖生年/日柱否決; 合/半三合/干合+1, 干剋-1)
    + 紫微流時四化. 回 (score, plus, veto)."""
    score, plus, veto = 0, [], []
    if any(kw in hour["ji"] for kw in YI_KW[matter]):
        veto.append(f"時忌含{matter}")
    elif any(kw in hour["yi"] for kw in YI_KW[matter]):
        score += 1
        plus.append("時宜含+1")
    if hour["huangdao_good"]:
        score += 1
        plus.append(f"時{hour['huangdao_name']}黃道+1")
    else:
        score -= 1
        plus.append(f"時{hour['huangdao_name']}黑道-1")
    for tag, bz in bazis:
        rel = personal_relations(hour["gan"], hour["zhi"], bz)
        if not rel:
            continue
        if rel["chong_year"]:
            veto.append(f"{tag}時支沖生年({hour['zhi']}沖{rel['year_zhi']})")
        if rel["chong_day"]:
            veto.append(f"{tag}時支沖日柱({hour['zhi']}沖{rel['day_zhi']})")
        if rel["liuhe_day"] or rel["sanhe_day"]:
            score += 1
            plus.append(f"{tag}時支{'六合' if rel['liuhe_day'] else '半三合'}+1")
        if rel["gan_he"]:
            score += 1
            plus.append(f"{tag}時干{hour['gan']}合命主+1")
        elif rel["gan_ke"]:
            score -= 1
            plus.append(f"{tag}時干剋-1")
    for tag, zw in ziweis:
        trans = SI_HUA.get(hour["gan"], ["", "", "", ""])
        ji = trans[3]
        if ji:
            pal = norm_palace(locate_star(zw, ji))
            if pal in MING_FU_QIAN:
                score -= 1
                plus.append(f"{tag}流時忌{ji}在{pal}-1")
        for star, kind in ((trans[0], "祿"), (trans[1], "權")):
            if not star:
                continue
            pal = norm_palace(locate_star(zw, star))
            if pal in CAI_GUAN:
                score += 1
                plus.append(f"{tag}流時{kind}{star}在{pal}+1")
    return score, plus, veto


def score_hours(dt, matter, bazis, ziweis, hour_top, want_qimen):
    scored = []
    for h in hours_of_day(dt):
        sc, pl, vt = check_hour(h, matter, bazis, ziweis)
        h = {**h, "score": sc, "plus": pl, "veto": vt,
             "status": "candidate" if not vt else "vetoed"}
        scored.append(h)
    cands = sorted([x for x in scored if x["status"] == "candidate"],
                   key=lambda x: (-x["score"], x["index"]))
    top = cands[:hour_top]
    if want_qimen:
        for h in top:
            hh, mm = (int(x) for x in h["rep"].split(":"))
            h["qimen"] = qimen_brief(datetime(dt.year, dt.month, dt.day, hh, mm))
    return scored, top


# ── 驗證 ──────────────────────────────────────────────────────────
def verify(days, matter, bazis, ziweis, hours_flag):
    checks, warnings = {}, []
    checks["matter_valid"] = {"ok": matter in MATTERS}
    checks["day_pillars_present"] = {"ok": all(len(d["ganzhi"]) == 2 for d in days)}
    leaks = simplified_leaks(days)
    checks["simp_trad_clean"] = {"ok": not leaks, "leaks": leaks}
    checks["veto_has_reason"] = {
        "ok": all(d["veto"] for d in days if d["status"] == "vetoed")}
    if hours_flag:
        cand_days = [d for d in days if d["status"] == "candidate"]
        checks["hours_complete"] = {"ok": all(len(d.get("hours", [])) == 12 for d in cand_days)}
        checks["top_hours_have_score"] = {
            "ok": all("score" in h for d in cand_days for h in d.get("top_hours", []))}
    if not bazis:
        warnings.append("未提供八字: 個人層與吉時個人化略過 (加 --bazi)")
    if not ziweis:
        warnings.append("未提供紫微: 紫微層略過 (加 --ziwei)")
    checks["all_pass"] = all(c["ok"] for c in checks.values() if "ok" in c)
    return {"checks": checks, "warnings": warnings, "all_pass": checks["all_pass"]}


def main():
    ap = argparse.ArgumentParser(description="擇日確定性掃描 (日層+個人+紫微+吉時)")
    ap.add_argument("--matter", required=True, choices=MATTERS)
    ap.add_argument("--from", dest="date_from", required=True)
    ap.add_argument("--to", dest="date_to", required=True)
    ap.add_argument("--bazi", default=None)
    ap.add_argument("--bazi-b", default=None)
    ap.add_argument("--ziwei", default=None)
    ap.add_argument("--ziwei-b", default=None)
    ap.add_argument("--hours", action="store_true", help="候選日加掃 12 時辰, 出吉時")
    ap.add_argument("--hour-top", type=int, default=3, help="每日列前 N 吉時")
    ap.add_argument("--hour-detail", action="store_true", help="文字輸出印候選日全部 12 時辰 (含否決理由與宜/忌; 隱含 --hours)")
    ap.add_argument("--qimen", action="store_true", help="吉時附時家奇門簡表 (方位行動)")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--format", default="text", choices=["text", "json", "both"])
    a = ap.parse_args()

    want_hours = a.hours or a.hour_detail
    d0 = datetime.strptime(a.date_from, "%Y-%m-%d")
    d1 = datetime.strptime(a.date_to, "%Y-%m-%d")
    bazis = [("甲", load(a.bazi))] if a.bazi else []
    if a.bazi_b:
        bazis.append(("乙", load(a.bazi_b)))
    ziweis = [("甲", load(a.ziwei))] if a.ziwei else []
    if a.ziwei_b:
        ziweis.append(("乙", load(a.ziwei_b)))

    days = []
    dt = d0
    while dt <= d1:
        info = day_info(dt)
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
        elif want_hours:
            info["hours"], info["top_hours"] = score_hours(
                dt, a.matter, bazis, ziweis, a.hour_top, a.qimen)
        days.append(info)
        dt += timedelta(days=1)

    cands = [d for d in days if d["status"] == "candidate"]
    cands.sort(key=lambda d: (-d["score"], d["date"]))
    out = {"matter": a.matter, "from": a.date_from, "to": a.date_to,
           "days": days, "top": cands[:a.top],
           "summary": {"scanned": len(days), "vetoed": len(days) - len(cands),
                       "candidates": len(cands)},
           "verification": verify(days, a.matter, bazis, ziweis, want_hours),
           "engine": "zeri_pick v2 (tongshu_core + zeri.md)"}

    if a.format in ("text", "both"):
        print(f"【擇日-{a.matter}】掃描{len(days)}天 候選{len(cands)} 否決{len(days) - len(cands)}")
        for t in cands[:a.top]:
            print(f"{t['date']} {t['ganzhi']}{t['jianchu']} {t['huangdao']} {t['score']}分")
            for p in t["plus"][:6]:
                print(f"  + {p}")
            if a.hour_detail:
                for h in t.get("hours", []):
                    mark = "○" if h["status"] == "candidate" else "✕"
                    print(f"  {mark}{h['name']} {h['range']} {h['ganzhi']} "
                          f"{h['huangdao_name']}{h['huangdao_luck']} {h['score']}分"
                          f"｜宜: {'、'.join(h['yi']) or '無'}｜忌: {'、'.join(h['ji']) or '無'}")
                    if h["veto"]:
                        print(f"      否決: {'; '.join(h['veto'])}")
            else:
                for h in t.get("top_hours", []):
                    line = f"  ▸吉時 {h['name']} {h['range']} {h['ganzhi']} {h['huangdao_name']}{h['huangdao_luck']} {h['score']}分"
                    if h.get("qimen"):
                        line += f"｜奇門{h['qimen']['ju']} 值使{h['qimen']['zhishi']}"
                    print(line)
                    print(f"      宜: {'、'.join(h['yi']) or '無'}｜忌: {'、'.join(h['ji']) or '無'}")
        vetoed = [d for d in days if d["status"] == "vetoed"]
        if vetoed:
            print(f"-- 否決{len(vetoed)}天 (前5) --")
            for v in vetoed[:5]:
                print(f"{v['date']} {v['ganzhi']}{v['jianchu']}: {'; '.join(v['veto'][:2])}")
        ver = out["verification"]
        print(f"驗證: {'通過' if ver['all_pass'] else '未過'}"
              + (f"｜⚠ {'; '.join(ver['warnings'])}" if ver["warnings"] else ""))
    if a.format in ("json", "both"):
        if a.format == "both":
            print("===== JSON =====")
        print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
