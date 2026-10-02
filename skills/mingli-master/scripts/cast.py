#!/usr/bin/env python3
"""一次產出八字 + 紫微雙盤並附初步交叉檢查. 減少來回呼叫.
用法 (參數同 bazi_pai.py, 另可給 ziwei 運限 --at):
  cast.py --date 1990-08-18 --time 06:30 --city 台北 --gender male [--year 2026] [--at 2026-06-15] [--at-time 14:00] [--format json|text]
輸出: {"bazi": {...}, "ziwei": {...}, "cross_check": {...}}
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
PY = sys.executable  # 用當前 Python 即可 (腳本自帶 vendor lunar_python, 免 venv)


def run_json(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr.strip(), file=sys.stderr)
        sys.exit(r.returncode)
    return json.loads(r.stdout)


def main():
    ap = argparse.ArgumentParser(description="雙盤 orchestrator (八字+紫微+交叉檢查)")
    ap.add_argument("--date", required=True)
    ap.add_argument("--time", default="12:00")
    ap.add_argument("--city", default="")
    ap.add_argument("--lon", type=float, default=None)
    ap.add_argument("--gender", required=True, choices=["male", "female"])
    ap.add_argument("--calendar", default="solar", choices=["solar", "lunar"], help="出生日期曆制")
    ap.add_argument("--leap", action="store_true", help="農曆閏月")
    ap.add_argument("--year", type=int, default=None)
    ap.add_argument("--at", default=None, help="紫微運限陽曆日 YYYY-MM-DD")
    ap.add_argument("--at-time", default="12:00")
    ap.add_argument("--format", default="json", choices=["json", "text"])
    a = ap.parse_args()

    loc = ["--city", a.city] if a.city else (["--lon", str(a.lon)] if a.lon is not None else [])
    cal = ["--calendar", a.calendar] + (["--leap"] if a.leap else [])
    bcmd = [str(PY), str(DIR / "bazi_pai.py"), "--date", a.date, "--time", a.time,
            "--gender", a.gender, "--format", "json", *loc, *cal]
    if a.year:
        bcmd += ["--year", str(a.year)]
    zcmd = [str(DIR / "ziwei_full.sh"), "--date", a.date, "--time", a.time,
            "--gender", a.gender, "--format", "json", *loc, *cal]
    if a.at:
        zcmd += ["--at", a.at, "--at-time", a.at_time]
    elif a.year:
        zcmd += ["--liunian", str(a.year)]

    bazi = run_json(bcmd)
    ziwei = run_json(zcmd)

    bz_zhi = next(p["zhi"] for p in bazi["pillars"] if p["label"] == "時柱")
    checks = {
        "time_branch_match": bz_zhi == ziwei["hour"],
        "bazi_hour": bz_zhi, "ziwei_hour": ziwei["hour"],
        "bazi_verification_pass": bazi.get("verification", {}).get("all_pass"),
        "warnings": list(dict.fromkeys(bazi.get("verification", {}).get("warnings", []) + ziwei.get("warnings", []))),
    }
    out = {"bazi": bazi, "ziwei": ziwei, "cross_check": checks}
    if a.format == "json":
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f'雙盤 {a.date} {a.time} {a.gender}')
        print(f'八字四柱: {" ".join(p["gan"]+p["zhi"] for p in bazi["pillars"])} '
              f'| 日主 {bazi["day_master"]} | {bazi["day_strength"]["level"]} | {bazi["geju"]["name"]}')
        print(f'紫微: 命{ziwei["ming"]["branch"]} 身{ziwei["ming"]["shen"]} {ziwei["ming"]["wuju"]} | {ziwei["ming"]["summary"]["nature"]}')
        print(f'交叉: 時支一致={checks["time_branch_match"]} ({bz_zhi}/{ziwei["hour"]}) '
              f'八字校驗全過={checks["bazi_verification_pass"]} 警告={checks["warnings"] or "無"}')


if __name__ == "__main__":
    main()
