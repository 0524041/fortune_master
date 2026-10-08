#!/usr/bin/env python3
"""問人總入口 (person_cast)：主盤 八字＋紫微，輔助盤 六壬終身課 ＋ 奇門終身盤。

主盤為骨幹（格局定論以主盤為準）；輔助盤補維度：
  - 六壬終身課：一生動態人事、過程與結局（權重低）
  - 奇門終身盤：方位、行動、命宮九宮（權重低）

用法：
  person_cast.py --date 1990-08-18 --time 06:30 --city 台北 --gender male \
      [--calendar solar|lunar] [--leap] [--year 2026] [--at 2026-06-15] [--format json|text]

輸出：{"bazi","ziwei","cross_check","liuren_lifetime","qimen_lifetime","aux_summary"}
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

DIR = Path(__file__).resolve().parent
YJ = DIR / "yijing"
sys.path.insert(0, str(YJ))
sys.path.insert(0, str(DIR.parent / "vendor"))
from liuren_core import LiuRenChart  # noqa: E402
from qimen_core import QiMenChart  # noqa: E402
from time_correct import true_solar  # noqa: E402
from han import s2t_deep  # 統一簡繁層 (輔助盤輸出轉繁)

PY = sys.executable


def run_json(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr.strip(), file=sys.stderr)
        sys.exit(r.returncode)
    return json.loads(r.stdout)


def main():
    ap = argparse.ArgumentParser(description="問人總入口 (八字+紫微主盤 + 六壬/奇門輔助盤)")
    ap.add_argument("--date", required=True)
    ap.add_argument("--time", default="12:00")
    ap.add_argument("--city", default="")
    ap.add_argument("--lon", type=float, default=None)
    ap.add_argument("--gender", required=True, choices=["male", "female"])
    ap.add_argument("--calendar", default="solar", choices=["solar", "lunar"])
    ap.add_argument("--leap", action="store_true")
    ap.add_argument("--year", type=int, default=None)
    ap.add_argument("--at", default=None, help="紫微運限陽曆日 YYYY-MM-DD")
    ap.add_argument("--at-time", default="12:00")
    ap.add_argument("--format", default="text", choices=["json", "text"])
    a = ap.parse_args()

    # 主盤：八字 + 紫微（沿用 cast.py）
    ccmd = [PY, str(DIR / "cast.py"), "--date", a.date, "--time", a.time,
            "--gender", a.gender, "--format", "json", "--calendar", a.calendar]
    if a.city:
        ccmd += ["--city", a.city]
    if a.lon is not None:
        ccmd += ["--lon", str(a.lon)]
    if a.leap:
        ccmd += ["--leap"]
    if a.year:
        ccmd += ["--year", str(a.year)]
    if a.at:
        ccmd += ["--at", a.at, "--at-time", a.at_time]
    main_chart = run_json(ccmd)

    gender_cn = '男' if a.gender == 'male' else '女'
    bdt = datetime.strptime(f"{a.date} {a.time}", "%Y-%m-%d %H:%M")

    # 輔助盤①：六壬終身課（出生時刻起課；本命＝生年、行年＝參考年）
    lr = LiuRenChart(bdt, birth=[(bdt.year, gender_cn)],
                     at_year=a.year or datetime.now().year, lifetime=True)

    # 輔助盤②：奇門終身盤（真太陽時；年干定命宮）
    qdt = bdt
    solar_info = None
    if a.city or a.lon is not None:
        qdt, solar_info = true_solar(bdt, city=a.city or '', lon=a.lon)
    qm = QiMenChart(qdt, lifetime=True)
    qm_d = qm.to_dict()
    if solar_info:
        qm_d['true_solar'] = solar_info

    out = {
        "main": main_chart,
        "liuren_lifetime": lr.to_dict(),
        "qimen_lifetime": qm_d,
        "aux_summary": {
            "role": "主盤(八字+紫微)為骨幹；六壬終身課、奇門終身盤為輔助，權重低、不翻轉主盤格局",
            "liuren_benming": lr.persons[0]['benming'] if lr.persons else None,
            "liuren_xingnian": lr.persons[0]['xingnian'] if lr.persons else None,
            "qimen_ming_gong": qm.ming_gong,
            "qimen_ju": f"{qm.yin_yang}遁{qm.ju}局",
        },
    }

    out = s2t_deep(out)  # 統一簡繁層: 輔助盤輸出轉繁
    if a.format == "json":
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        b = main_chart["bazi"]; z = main_chart["ziwei"]
        print(f"主盤 八字：{' '.join(p['gan'] + p['zhi'] for p in b['pillars'])} | "
              f"日主 {b['day_master']} | {b['day_strength']['level']} | {b['geju']['name']}")
        print(f"主盤 紫微：命{z['ming']['branch']} 身{z['ming']['shen']} {z['ming']['wuju']}")
        print()
        print(lr.format_for_ai())
        print()
        print(qm.format_for_ai())


if __name__ == "__main__":
    main()
