#!/usr/bin/env python3
"""通書單日全資訊 CLI. 把內嵌 lunar_python 的黃曆面 (日層 + 十二時辰層) 攤成 JSON/text,
供 AI 判讀與擇日選時. 純事實, 不斷吉凶.

用法:
  tongshu_day.py --date 2026-10-08 [--bazi A.json] [--bazi-b B.json] [--qimen]
                 [--format text|json|both]

  --bazi  給八字 JSON (bazi_pai.py 輸出) → 各時辰附「個人關係事實」(沖/合/十神, 不評分)
  --qimen 各時辰附時家奇門簡表 (值符/值使/局/格局; 方位行動用)
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR))
from tongshu_core import (day_facts, hours_of_day, personal_relations,  # noqa: E402
                          simplified_leaks, qimen_brief)


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def verify(out):
    checks, warnings = {}, []
    hrs = out["hours"]
    checks["hours_complete"] = {"ok": len(hrs) == 12, "n": len(hrs)}
    checks["day_pillar_len"] = {"ok": len(out["day"]["day_pillar"]) == 2}
    checks["hour_ganzhi_len"] = {"ok": all(len(h["ganzhi"]) == 2 for h in hrs)}
    leaks = simplified_leaks(out)
    checks["simp_trad_clean"] = {"ok": not leaks, "leaks": leaks}
    if out.get("bazi_given"):
        has_day = any(h.get("personal") for h in hrs)
        checks["personal_layer"] = {"ok": has_day}
        if not has_day:
            warnings.append("八字缺日柱: 個人層略過")
    else:
        warnings.append("未提供八字: 個人關係事實略過 (加 --bazi)")
    if out.get("qimen_given"):
        checks["qimen_layer"] = {"ok": all(h.get("qimen") for h in hrs)}
    if out["day"].get("jieqi"):
        warnings.append(f"當日逢節氣「{out['day']['jieqi']}」交界: 時辰層可能跨節氣/跨奇門局")
    checks["all_pass"] = all(c["ok"] for c in checks.values() if "ok" in c)
    return {"checks": checks, "warnings": warnings, "all_pass": checks["all_pass"]}


def main():
    ap = argparse.ArgumentParser(description="通書單日全資訊")
    ap.add_argument("--date", required=True, help="國曆 YYYY-MM-DD")
    ap.add_argument("--bazi", default=None, help="八字 JSON (甲)")
    ap.add_argument("--bazi-b", default=None, help="八字 JSON (乙)")
    ap.add_argument("--qimen", action="store_true", help="各時辰附時家奇門簡表")
    ap.add_argument("--format", default="text", choices=["text", "json", "both"])
    a = ap.parse_args()

    dt = datetime.strptime(a.date, "%Y-%m-%d")
    bazis = []
    if a.bazi:
        bazis.append(("甲", load(a.bazi)))
    if a.bazi_b:
        bazis.append(("乙", load(a.bazi_b)))

    day = day_facts(dt)
    hours = hours_of_day(dt)
    for h in hours:
        if bazis:
            h["personal"] = {tag: personal_relations(h["gan"], h["zhi"], bz) for tag, bz in bazis}
        if a.qimen:
            hh, mm = (int(x) for x in h["rep"].split(":"))
            h["qimen"] = qimen_brief(datetime(dt.year, dt.month, dt.day, hh, mm))
    out = {"date": a.date, "day": day, "hours": hours,
           "bazi_given": bool(bazis), "qimen_given": a.qimen,
           "verification": verify({"date": a.date, "day": day, "hours": hours,
                                   "bazi_given": bool(bazis), "qimen_given": a.qimen}),
           "engine": "tongshu_day v1 (lunar_python)"}

    if a.format in ("text", "both"):
        d = day
        print(f"【通書】{d['date']} {d['week']} {d['lunar_date']}  {d['year_pillar']}年 {d['month_pillar']}月 {d['day_pillar']}日")
        print(f"納音 {d['nayin']}｜建除 {d['jianchu']}｜宿 {d['xiu']['name']}{d['xiu']['zheng']}{d['xiu']['animal']}({d['xiu']['luck']})"
              f"｜九星 {d['nine_star']}｜{d['huangdao']}({d['huangdao_type']})")
        print(f"宜: {' '.join(d['yi'])}")
        print(f"忌: {' '.join(d['ji'])}")
        print(f"吉神: {'、'.join(d['jishen'])}｜凶煞: {'、'.join(d['xiongsha'])}")
        dirs = d["directions"]
        print(f"方位 喜神{dirs['喜神']} 陽貴{dirs['陽貴']} 陰貴{dirs['陰貴']} 財神{dirs['財神']} 福神{dirs['福神']}"
              f"｜空亡 {d['xunkong']}｜沖{d['chong']['desc']} 煞{d['chong']['sha']}")
        print(f"彭祖 {d['pengzu']['gan']} / {d['pengzu']['zhi']}｜胎神 {d['taishen']}")
        print("【時辰】")
        for h in hours:
            line = (f"{h['name']} {h['range']} {h['ganzhi']} {h['huangdao_name']}{h['huangdao_type']}{h['huangdao_luck']}"
                    f" 沖{h['chong']['desc']} 煞{h['chong']['sha']} 喜{h['xi']} 財{h['cai']}")
            if h.get("personal"):
                notes = []
                for tag, r in h["personal"].items():
                    flags = [k for k in ("chong_year", "chong_day", "liuhe_day", "sanhe_day", "gan_he", "gan_ke") if r.get(k)]
                    notes.append(f"{tag}十神{r.get('shishen','')}{('/'+'/'.join(flags)) if flags else ''}")
                line += "｜" + " ".join(notes)
            if h.get("qimen"):
                q = h["qimen"]
                line += f"｜奇門{q['ju']} 值符{q['zhifu']} 值使{q['zhishi']}"
                if q["geju"]:
                    more = f"(+{len(q['geju']) - 4})" if len(q["geju"]) > 4 else ""
                    line += f" 格{'、'.join(q['geju'][:4])}{more}"
            print(line)
            print(f"    宜: {'、'.join(h['yi']) or '無'}｜忌: {'、'.join(h['ji']) or '無'}")
        v = out["verification"]
        print(f"驗證: {'通過' if v['all_pass'] else '未過'}"
              + (f"｜⚠ {'; '.join(v['warnings'])}" if v["warnings"] else ""))
    if a.format in ("json", "both"):
        if a.format == "both":
            print("===== JSON =====")
        print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
