#!/usr/bin/env python3
"""合盤確定性比對. 吃現成 JSON (bazi_pai.py / ziwei_full.sh 輸出), 只比對不排盤.
用法:
  hepan_check.py --a-bazi A.json --a-ziwei Az.json --b-bazi B.json --b-ziwei Bz.json [--format text|json|both]
輸出為證據＋參考分 (各項score相加, 僅供參考; 定性由解讀決定, 工具不定高低).
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from han import s2t_deep, norm_palace  # noqa: E402  # 統一簡繁層

CHECKS = ["tianzuo", "fuqi_fude", "sun_moon", "pillars",
          "wuxing", "daxian", "peach", "huaji"]

_ZH = json.loads((Path(__file__).resolve().parent.parent / "data" / "ganzhi.json").read_text(encoding="utf-8"))
TIANGAN_HE = _ZH["tian_gan_he"]
LIUHE = _ZH["liu_he"]
LIUCHONG = _ZH["liu_chong"]
SANHE_FULL = _ZH["san_he"]
WUXING_KE = _ZH["wu_xing_ke"]
WUXING_SHENG = _ZH["wu_xing_sheng"]
GAN_WX = _ZH["gan_wuxing"]
# 星名一律繁體 (引擎輸出已由 han.s2t_deep 統一轉繁, 不再需要繁簡雙套)
SHA_STARS = {"擎羊", "陀羅", "火星", "鈴星", "地空", "地劫",
             "七殺", "破軍", "廉貞", "巨門"}
PEACH_STARS = {"紅鸞", "天喜", "咸池", "天姚"}


def load(p):
    with open(p, encoding="utf-8") as f:
        return s2t_deep(json.load(f))  # 統一簡繁層: 引擎輸出 (八字/紫微) 轉繁


def major_stars(palace):
    return [s["name"] for s in palace.get("stars", []) if s.get("type") == "major"]


def find_palace(chart, name):
    for p in chart.get("palaces", []):
        if norm_palace(p.get("name")) == norm_palace(name):
            return p
    return None


def check_tianzuo(az, bz):
    """天作之合: 甲夫妻主星==乙命主星 且反向亦然為雙向(+2), 單向+1, 無0."""
    a_fuqi = set(major_stars(find_palace(az, "夫妻") or {}))
    b_ming = set(major_stars(find_palace(bz, "命宮") or find_palace(bz, "命") or {}))
    b_fuqi = set(major_stars(find_palace(bz, "夫妻") or {}))
    a_ming = set(major_stars(find_palace(az, "命宮") or find_palace(az, "命") or {}))
    a_to_b = bool(a_fuqi & b_ming)
    b_to_a = bool(b_fuqi & a_ming)
    score = (1 if a_to_b else 0) + (1 if b_to_a else 0)
    return {"a_to_b": a_to_b, "b_to_a": b_to_a,
            "a_fuqi_stars": sorted(a_fuqi), "b_ming_stars": sorted(b_ming),
            "b_fuqi_stars": sorted(b_fuqi), "a_ming_stars": sorted(a_ming),
            "score": score}


def palace_status(chart, palace_name):
    """夫妻/福德狀態: 主星見煞(七杀破军廉貞巨門四煞空劫)或主星落陷 → caution, 否則 stable."""
    p = find_palace(chart, palace_name) or {}
    stars = p.get("stars", [])
    hits = [s["name"] for s in stars
            if s["name"] in SHA_STARS or (s.get("type") == "major" and s.get("brightness") == "dim")]
    return ("caution" if hits else "stable"), hits


def check_fuqi_fude(az, bz):
    """夫妻+福德: 雙方stable +1, 一方caution 0, 雙方caution -1."""
    a1, a1h = palace_status(az, "夫妻")
    a2, a2h = palace_status(az, "福德")
    b1, b1h = palace_status(bz, "夫妻")
    b2, b2h = palace_status(bz, "福德")
    a = "caution" if "caution" in (a1, a2) else "stable"
    b = "caution" if "caution" in (b1, b2) else "stable"
    score = {"stable-stable": 1, "caution-caution": -1}.get(f"{a}-{b}", 0)
    return {"a": a, "b": b,
            "a_fuqi_hits": a1h, "a_fude_hits": a2h,
            "b_fuqi_hits": b1h, "b_fude_hits": b2h, "score": score}


def check_sun_moon(az, bz, a_gender="male", b_gender="female"):
    """男看太陰(妻) 女看太陽(夫): 吉+1/平0/差-1 兩方相加."""
    a_label, a_pal, a_hua, a_sc = judge_luminary(az, "moon")
    b_label, b_pal, b_hua, b_sc = judge_luminary(bz, "sun")
    return {"a_moon": a_label, "a_moon_palace": a_pal, "a_moon_hua": a_hua,
            "b_sun": b_label, "b_sun_palace": b_pal, "b_sun_hua": b_hua,
            "score": a_sc + b_sc}


def judge_luminary(chart, which):
    names = {"moon": ("太陰", "太阴"), "sun": ("太陽", "太阳")}[which]
    for p in chart.get("palaces", []):
        for s in p.get("stars", []):
            if s["name"] in names and s.get("type") == "major":
                hua = s.get("siHua") or ""
                base = {"bright": 1, "dim": -1}.get(s.get("brightness"), 0)
                if hua == "忌":
                    base -= 1
                return ("吉" if base > 0 else ("差" if base < 0 else "平")), p.get("name"), hua, base
    return "缺", "", "", 0


def pillars_of(bazi):
    return [(p["gan"], p["zhi"]) for p in bazi.get("pillars", [])]


def check_pillars(ab, bb):
    """柱合沖(同位逐柱比): 天干五合+1/項, 地支六合+1/項, 半三合+1/項, 六沖-1/項."""
    ap, bp = pillars_of(ab), pillars_of(bb)
    he, chong = [], []
    for (ag, az_), (bg, bz_) in zip(ap, bp):
        if TIANGAN_HE.get(ag) == bg:
            he.append(f"{ag}{bg}合")
        if LIUHE.get(az_) == bz_:
            he.append(f"{az_}{bz_}六合")
        elif LIUCHONG.get(az_) == bz_:
            chong.append(f"{az_}{bz_}六沖")
        else:
            for grp in SANHE_FULL:
                if az_ in grp and bz_ in grp:
                    he.append(f"{az_}{bz_}半三合")
                    break
    return {"he": he, "chong": chong, "score": len(he) - len(chong)}


def top2(score):
    return sorted(score, key=lambda k: -score[k])[:2]


def check_wuxing(ab, bb):
    """五行互補: 一方top2生另一方top2記補益方向(+1); 日主相剋-1, 相合/比和0."""
    a_sc, b_sc = ab.get("wuxing_score", {}), bb.get("wuxing_score", {})
    at, bt = top2(a_sc), top2(b_sc)
    supply = []
    if any(WUXING_SHENG.get(x) in bt for x in at):
        supply.append(f"A→B({','.join(x + '生' + WUXING_SHENG[x] for x in at if WUXING_SHENG.get(x) in bt)})")
    if any(WUXING_SHENG.get(x) in at for x in bt):
        supply.append(f"B→A({','.join(x + '生' + WUXING_SHENG[x] for x in bt if WUXING_SHENG.get(x) in at)})")
    ag = pillars_of(ab)[2][0]
    bg = pillars_of(bb)[2][0]
    awx, bwx = GAN_WX[ag], GAN_WX[bg]
    if WUXING_KE.get(bwx) == awx or WUXING_KE.get(awx) == bwx:
        killer, victim = (bg, ag) if WUXING_KE.get(bwx) == awx else (ag, bg)
        rel, rel_sc = f"{killer}剋{victim}", -1
    elif TIANGAN_HE.get(ag) == bg:
        rel, rel_sc = f"{ag}{bg}合", 0
    elif awx == bwx:
        rel, rel_sc = f"{ag}{bg}比和", 0
    else:
        rel, rel_sc = f"{ag}{bg}({awx}/{bwx})", 0
    return {"a_top": at, "b_top": bt, "supply": supply,
            "day_master_rel": rel, "score": (1 if supply else 0) + rel_sc}


def current_daxian(chart):
    dx = chart.get("daxian", [])
    i = chart.get("currentDaXianIndex", 0)
    if 0 <= i < len(dx):
        d = dx[i]
        rng = d.get("age", "")
        if not rng and "startAge" in d:
            rng = f"{d['startAge']}-{d['endAge']}"
        return d.get("palaceName", ""), rng
    return "", ""


def check_daxian(az, bz):
    """大限同步: 當前大限同宮+1; 任一方大限落夫妻且該宮主星化忌-1."""
    an, ar = current_daxian(az)
    bn, br = current_daxian(bz)
    sync = bool(an) and an == bn
    score, notes = (1 if sync else 0), []
    for tag, chart, name, rng in (("A", az, an, ar), ("B", bz, bn, br)):
        if norm_palace(name) == "夫妻":
            p = find_palace(chart, "夫妻") or {}
            ji = [s["name"] for s in p.get("stars", []) if s.get("siHua") == "忌"]
            if ji:
                score -= 1
                notes.append(f"{tag}大限夫妻逢{','.join(ji)}化忌")
    return {"a_current": f"{ar}{an}", "b_current": f"{br}{bn}",
            "sync": sync, "notes": notes, "score": score}


def peach_of(chart):
    out = {}
    for p in chart.get("palaces", []):
        hits = [s["name"] for s in p.get("stars", []) if s["name"] in PEACH_STARS]
        if hits:
            out[p.get("name")] = hits
    return out


def check_peach(az, bz):
    """桃花會: 列雙方桃花星落宮, 純資訊不評分(0)."""
    return {"a_peach": peach_of(az), "b_peach": peach_of(bz), "score": 0}


def native_ji(chart):
    si = chart.get("native_sihua", {})
    for k in ("忌",):
        if si.get(k):
            return si[k]
    return ""


def locate_star(chart, star):
    for p in chart.get("palaces", []):
        if any(s["name"] == star for s in p.get("stars", [])):
            return p.get("name")
    return ""


def check_huaji(az, bz):
    """化忌互飛: 甲生年忌星落乙何宮, 反向亦然. 互忌-2, 單向忌入對方命/夫妻-1/邊, 餘0."""
    a_ji, b_ji = native_ji(az), native_ji(bz)
    a_to_b = [{"star": a_ji, "palace": locate_star(bz, a_ji)}] if a_ji else []
    b_to_a = [{"star": b_ji, "palace": locate_star(az, b_ji)}] if b_ji else []
    def hit(entries):
        return any(norm_palace(e["palace"]) in ("命", "夫妻") for e in entries)

    a_hit, b_hit = hit(a_to_b), hit(b_to_a)
    mutual = a_hit and b_hit
    score = -2 if mutual else (-1 if (a_hit or b_hit) else 0)
    return {"a_ji": a_ji, "b_ji": b_ji, "a_to_b": a_to_b, "b_to_a": b_to_a,
            "mutual": mutual, "score": score}


def main():
    ap = argparse.ArgumentParser(description="合盤確定性比對")
    ap.add_argument("--a-bazi", required=True)
    ap.add_argument("--a-ziwei", required=True)
    ap.add_argument("--b-bazi", required=True)
    ap.add_argument("--b-ziwei", required=True)
    ap.add_argument("--format", default="text", choices=["text", "json", "both"])
    a = ap.parse_args()

    ab, az = load(a.a_bazi), load(a.a_ziwei)
    bb, bz = load(a.b_bazi), load(a.b_ziwei)

    checks = {
        "tianzuo": check_tianzuo(az, bz),
        "fuqi_fude": check_fuqi_fude(az, bz),
        "sun_moon": check_sun_moon(az, bz),
        "pillars": check_pillars(ab, bb),
        "wuxing": check_wuxing(ab, bb),
        "daxian": check_daxian(az, bz),
        "peach": check_peach(az, bz),
        "huaji": check_huaji(az, bz),
    }
    score = sum(c["score"] for c in checks.values())
    out = {"checks": checks,
           "ref": {"score": score, "note": "參考分(各項相加)，定性由解讀決定"},
           "engine": "hepan_check v2"}

    if a.format in ("text", "both"):
        print(f"【合盤】參考分 {score} (定性由解讀決定)")
        t = checks["tianzuo"]
        print(f"1 天作互涉({t['score']}): 甲→乙{t['a_to_b']} 乙→甲{t['b_to_a']}")
        f = checks["fuqi_fude"]
        print(f"2 夫妻福德({f['score']}): 甲{f['a']}{f['a_fuqi_hits']}/{f['a_fude_hits']} 乙{f['b']}{f['b_fuqi_hits']}/{f['b_fude_hits']}")
        s = checks["sun_moon"]
        print(f"3 日月({s['score']}): 甲太陰{s['a_moon']}{s['a_moon_palace']}{s['a_moon_hua']} 乙太陽{s['b_sun']}{s['b_sun_palace']}{s['b_sun_hua']}")
        p = checks["pillars"]
        print(f"4 柱合沖({p['score']}): 合{p['he'] or '無'} 沖{p['chong'] or '無'}")
        w = checks["wuxing"]
        print(f"5 五行({w['score']}): 甲{w['a_top']} 乙{w['b_top']} 補益{w['supply'] or '無'} 日主{w['day_master_rel']}")
        x = checks["daxian"]
        print(f"6 大限({x['score']}): 甲{x['a_current']} 乙{x['b_current']} 同步{x['sync']} {x['notes']}")
        h = checks["huaji"]
        print(f"7 化忌({h['score']}): 甲忌{h['a_ji']}→乙{h['a_to_b']} 乙忌{h['b_ji']}→甲{h['b_to_a']} 互忌{h['mutual']}")
        pk = checks["peach"]
        print(f"8 桃花({pk['score']}): 甲{pk['a_peach']} 乙{pk['b_peach']}")
    if a.format in ("json", "both"):
        if a.format == "both":
            print("===== JSON =====")
        print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
