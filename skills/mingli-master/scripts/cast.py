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
sys.path.insert(0, str(DIR))
from twin_adjust import adjust as twin_rebase  # noqa: E402


def run_json(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr.strip(), file=sys.stderr)
        sys.exit(r.returncode)
    return json.loads(r.stdout)


LU_STARS = {"祿", "禄"}
# 注意: ziwei bundle 宮名為簡體 (官禄/财帛/仆役…), 集合須用簡體比對
CAI_GONG_JI = {"财帛", "田宅", "官禄", "福德"}   # 祿入此四宮為吉 (caiyun.md 財務四宮)
CAI_GONG_XIONG = {"财帛", "田宅", "福德"}        # 忌入財帛/田宅為破財點；福德忌主想多易衝動


def caiyun_semantic(bazi, ziwei):
    """Phase 3 財運語義交叉初判 (八字喜忌財 × 紫微祿忌落財宮).
    verdict: 同向/分歧/單邊/缺料；kind: 進財窗/守財/None. LLM 只做覆核."""
    ys = bazi.get("yongshen", {})
    xi, ji = ys.get("xi", []), ys.get("ji", [])
    bazi_side = "喜財" if "財" in xi else ("忌財" if "財" in ji else "中性")
    lu_palace = ji_palace = None
    for p in ziwei.get("palaces", []):
        for s in p.get("stars", []):
            if s.get("siHua") in LU_STARS and lu_palace is None:
                lu_palace = p["name"]
            if s.get("siHua") == "忌" and ji_palace is None:
                ji_palace = p["name"]
    ziwei_side = "中性"
    if lu_palace in CAI_GONG_JI:
        ziwei_side = f"祿入{lu_palace}"
    if ji_palace in CAI_GONG_XIONG:
        ziwei_side = f"忌入{ji_palace}" if ziwei_side == "中性" else f"{ziwei_side}＋忌入{ji_palace}"
    reasons = [f"八字{ys.get('method', '扶抑')[:2]}：{bazi_side}",
               f"紫微本命四化：祿在{lu_palace}、忌在{ji_palace}"]
    good_z = ziwei_side.startswith("祿入")
    bad_z = "忌入" in ziwei_side
    if bazi_side == "喜財" and good_z and not bad_z:
        verdict, kind = "同向", "進財窗"
    elif bazi_side == "忌財" and bad_z and not good_z:
        verdict, kind = "同向", "守財"
    elif bazi_side in ("喜財", "忌財") and (good_z or bad_z):
        verdict, kind = "分歧", "守財"
        reasons.append("兩側打架，結論偏保守，仍給型態與時窗")
    elif bazi_side == "中性" and ziwei_side == "中性":
        verdict, kind = "缺料", None
        reasons.append("八字財中性、祿忌皆未入財宮，此題不斷財運")
    else:
        verdict = "單邊"
        kind = "進財窗" if (bazi_side == "喜財" or good_z) else "守財"
        reasons.append("僅一側表態，置信中")
    return {"verdict": verdict, "kind": kind, "bazi": bazi_side,
            "ziwei": ziwei_side, "reasons": reasons}


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
    ap.add_argument("--twin-order", type=int, default=1,
                    help="雙胞胎排行(同性): 2=老二、3=老三... 預設1=單胎/老大")
    ap.add_argument("--twin-ziwei", default="rebase", choices=["rebase", "shift", "none"],
                    help="紫微雙胞胎法: rebase=借宮立極(預設,星曜不動旋宮名), shift=時辰遞推(整盤重算), none=北派同盤不改")
    a = ap.parse_args()

    loc = ["--city", a.city] if a.city else (["--lon", str(a.lon)] if a.lon is not None else [])
    cal = ["--calendar", a.calendar] + (["--leap"] if a.leap else [])
    bcmd = [str(PY), str(DIR / "bazi_pai.py"), "--date", a.date, "--time", a.time,
            "--gender", a.gender, "--format", "json", *loc, *cal]
    if a.year:
        bcmd += ["--year", str(a.year)]
    if a.twin_order > 1:
        bcmd += ["--twin-order", str(a.twin_order)]
    zcmd = [str(DIR / "ziwei_full.sh"), "--date", a.date, "--time", a.time,
            "--gender", a.gender, "--format", "json", *loc, *cal]
    if a.at:
        zcmd += ["--at", a.at, "--at-time", a.at_time]
    elif a.year:
        zcmd += ["--liunian", str(a.year)]
    if a.twin_order > 1 and a.twin_ziwei == "shift":
        zcmd += ["--hour-shift", str(a.twin_order - 1)]

    bazi = run_json(bcmd)
    ziwei = run_json(zcmd)
    if a.twin_order > 1 and a.twin_ziwei == "rebase":
        try:
            ziwei = twin_rebase(ziwei, a.twin_order)
        except (KeyError, ValueError) as e:
            print(f"錯誤: 紫微借宮變盤失敗: {e}", file=sys.stderr)
            sys.exit(2)

    bz_zhi = next(p["zhi"] for p in bazi["pillars"] if p["label"] == "時柱")
    zw_hour = ziwei["hour"]
    if bazi.get("twin"):   # 變盤: 以真實(原)時支定位盤交叉, 不比對調整後時柱
        bz_zhi = bazi["twin"]["original_hour"][1]
        zw_hour = (ziwei.get("twin") or {}).get("original_hour", zw_hour)
    checks = {
        "time_branch_match": bz_zhi == zw_hour,
        "bazi_hour": bz_zhi, "ziwei_hour": zw_hour,
        "bazi_verification_pass": bazi.get("verification", {}).get("all_pass"),
        "warnings": list(dict.fromkeys(bazi.get("verification", {}).get("warnings", []) + ziwei.get("warnings", []))),
    }
    out = {"bazi": bazi, "ziwei": ziwei, "cross_check": checks}
    out["caiyun_semantic"] = caiyun_semantic(bazi, ziwei)
    if a.twin_order > 1:
        out["twin"] = {
            "order": a.twin_order,
            "bazi": "時柱進位（子平法）",
            "ziwei": {"rebase": "借宮立極（南派；星曜不動、旋宮名）",
                      "shift": "時辰遞推（生時進位、整盤重算）",
                      "none": "北派同盤不改"}[a.twin_ziwei],
            "note": "同性雙胞胎用；龍鳳胎不必調盤（大運/大限順逆自然相反）；兩派不可混用",
        }
    if a.format == "json":
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f'雙盤 {a.date} {a.time} {a.gender}')
        if a.twin_order > 1:
            print(f'雙胞胎排行{a.twin_order}: 八字{out["twin"]["bazi"]}；紫微{out["twin"]["ziwei"]}')
        print(f'八字四柱: {" ".join(p["gan"]+p["zhi"] for p in bazi["pillars"])} '
              f'| 日主 {bazi["day_master"]} | {bazi["day_strength"]["level"]} | {bazi["geju"]["name"]}')
        print(f'紫微: 命{ziwei["ming"]["branch"]} 身{ziwei["ming"]["shen"]} {ziwei["ming"]["wuju"]} | {ziwei["ming"]["summary"]["nature"]}')
        print(f'交叉: 時支一致={checks["time_branch_match"]} ({checks["bazi_hour"]}/{checks["ziwei_hour"]}) '
              f'八字校驗全過={checks["bazi_verification_pass"]} 警告={checks["warnings"] or "無"}')
        cy = out["caiyun_semantic"]
        print(f'財運語義: {cy["verdict"]}{("/" + cy["kind"]) if cy["kind"] else ""} '
              f'(八字{cy["bazi"]} × 紫微{cy["ziwei"]})')


if __name__ == "__main__":
    main()
