#!/usr/bin/env python3
"""多年運總表 (問人時間窗問題專用). 一次輸出 N 年的八字流年＋紫微運限對照.

背景: 回答「前五年後五年」這類時間窗問題時, 不必逐年各跑一次
bazi_pai.py / ziwei_full.sh (N 年 = 2N 次呼叫). 此腳本一次跑完,
輸出一年一行的緊湊對照表, LLM 直接讀表解盤.

用法:
  decade.py --date 1998-01-05 --time 15:57 --city 台南 --gender male --from 2021 --to 2030 [--format text|json]
  decade.py --date 1998-01-05 --time 15:57 --lon 120.2 --gender male --from 2021 --to 2026 --at-md 06-01
輸出 text (一年一行):
  年 八字流年(十神) 大運柱 | 紫微大限宮 流年宮(干支) 流年四化忌星
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
PY = sys.executable  # 與 cast.py 同: 用當前 Python (腳本自帶 vendor, 免 venv)


def run_json(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr.strip(), file=sys.stderr)
        sys.exit(r.returncode)
    return json.loads(r.stdout)


def covering_dayun(pillars, year):
    """找出涵蓋該年的大運柱 (years 形如 "1997-2006")."""
    for p in pillars:
        try:
            a, b = p["years"].split("-")
            if int(a) <= year <= int(b):
                return p
        except (KeyError, ValueError):
            continue
    return None


def main():
    ap = argparse.ArgumentParser(description="多年運總表 (八字流年＋紫微運限, 一年一行)")
    ap.add_argument("--date", required=True)
    ap.add_argument("--time", default="12:00")
    ap.add_argument("--city", default="")
    ap.add_argument("--lon", type=float, default=None)
    ap.add_argument("--gender", required=True, choices=["male", "female"])
    ap.add_argument("--calendar", default="solar", choices=["solar", "lunar"])
    ap.add_argument("--leap", action="store_true")
    ap.add_argument("--from", dest="yfrom", type=int, required=True)
    ap.add_argument("--to", dest="yto", type=int, required=True)
    ap.add_argument("--at-md", default="06-01", help="紫微運限取樣月日 (預設 06-01, 年中)")
    ap.add_argument("--divide", default="exact", choices=["exact", "normal"],
                    help="紫微分界: exact=立春 (預設, 與八字同界) / normal=正月初一")
    ap.add_argument("--format", default="text", choices=["text", "json"])
    a = ap.parse_args()

    if a.yto < a.yfrom:
        print("錯誤: --to 不可早於 --from", file=sys.stderr)
        sys.exit(2)
    if a.yto - a.yfrom > 30:
        print("錯誤: 年窗最多 30 年", file=sys.stderr)
        sys.exit(2)

    loc = ["--city", a.city] if a.city else ((["--lon", str(a.lon)]) if a.lon is not None else [])
    cal = ["--calendar", a.calendar] + (["--leap"] if a.leap else [])

    rows = []
    for y in range(a.yfrom, a.yto + 1):
        b = run_json([PY, str(DIR / "bazi_pai.py"), "--date", a.date, "--time", a.time,
                      "--gender", a.gender, "--format", "json", *loc, *cal,
                      "--year", str(y)])
        z = run_json([str(DIR / "ziwei_full.sh"), "--date", a.date, "--time", a.time,
                      "--gender", a.gender, *loc, *cal,
                      "--liunian", str(y), "--at", f"{y}-{a.at_md}",
                      "--horoscope-divide", a.divide, "--format", "json"])
        dy = covering_dayun(b["dayun"]["pillars"], y)
        rows.append({
            "year": y,
            "bazi": {
                "liunian": b["liunian"]["gan_zhi"],
                "shishen": b["liunian"]["shishen"],
                "dayun": (dy["gan_zhi"] if dy else None),
                "dayun_years": (dy["years"] if dy else None),
            },
            "ziwei": {
                "daxian_palace": z["horoscope"]["daxian"]["palace"],
                "daxian_ganzhi": z["horoscope"]["daxian"]["ganzhi"],
                "liunian_palace": z["horoscope"]["liunian"]["palace"],
                "liunian_ganzhi": z["horoscope"]["liunian"]["ganzhi"],
                "liunian_ji": z["horoscope"]["liunian"]["mutagen"].get("忌"),
            },
        })

    out = {"input": {"date": a.date, "time": a.time, "gender": a.gender,
                     "from": a.yfrom, "to": a.yto},
           "years": rows}

    if a.format == "json":
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"多年運 {a.date} {a.time} {a.gender} {a.yfrom}-{a.yto} "
              f"(紫微分界={'立春' if a.divide == 'exact' else '正月初一'})")
        for r in rows:
            b, z = r["bazi"], r["ziwei"]
            print(f"{r['year']} {b['liunian']}({b['shishen']}) 大運{b['dayun']} | "
                  f"大限{z['daxian_palace']}({z['daxian_ganzhi']}) "
                  f"流年{z['liunian_palace']}({z['liunian_ganzhi']}) 流忌{z['liunian_ji']}")


if __name__ == "__main__":
    main()
