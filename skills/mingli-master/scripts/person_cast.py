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
    ap.add_argument("--format", default="md", choices=["json", "text", "md"],
                    help="md=必讀摘要 (預設)、text=文字全文、json=結構化 (隱藏除錯)")
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

    if a.format == "md":
        print(render_summary(out, a, lr, qm, main_chart))
    elif a.format == "json":
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


def render_summary(out: dict, a, lr, qm, main_chart: dict) -> str:
    """Layer 0 必讀摘要（md）：含基本輸入首行，8-11 行情報。目標 2.5-3K。"""
    b = main_chart["bazi"]; z = main_chart["ziwei"]
    cc = main_chart.get("cross_check", {})
    cy = main_chart.get("caiyun_semantic", {})

    gender_cn = '男' if a.gender == 'male' else '女'
    cal_cn = '國曆' if a.calendar == 'solar' else '農曆'
    true_solar = (b.get('input') or {}).get('true_solar', '')
    lines = []
    lines.append(f"# 問人總盤摘要 {a.date} {a.time} {a.city or '未給城市'} {gender_cn} {cal_cn}"
                 + (f" 真太陽{true_solar[11:16]}" if true_solar else ""))

    # 八字行
    pillars = ' '.join(p['gan'] + p['zhi'] for p in b['pillars'])
    ds = b['day_strength']; ys = b['yongshen']
    tiao = ys.get('tiaohou', {})
    xi = ''.join(ys.get('xi', [])); ji = ''.join(ys.get('ji', []))
    rel = '/'.join(b.get('relations', [])) if b.get('relations') else '無'
    shensha = ''.join(s['name'] for s in b.get('shensha', {}).get('found', [])[:3])
    sd = b.get('strength_classic', {})
    lines.append(f"八字：{pillars}｜日主{b['day_master']}｜身強{ds['score']}分{ds['level']}｜"
                 f"喜{xi}忌{ji}｜調候{tiao.get('primary', '')}{'/'.join(tiao.get('full', [])[1:]) or ''}｜"
                 f"{b['geju']['name']}{b['geju'].get('shishen', '')}｜{rel}｜{shensha}")
    if sd.get('summary'):
        lines.append(f"　三得：{sd['summary']}")

    # 大運
    dy = b.get('dayun', {})
    runs = ' → '.join(f"{p['gan_zhi']}{p['age']}({p['years']})" for p in dy.get('pillars', [])[:4])
    lines.append(f"大運{dy.get('direction', '')}{dy.get('start_age', '')}歲起：{runs}")

    # 紫微行
    ming = z['ming']; ns = z.get('native_sihua', {})

    def palace(name, maxlen=40):
        for p in z.get('palaces', []):
            if p['name'] == name:
                return ''.join(s['name'] + ('化' + s['siHua'][0] if s.get('siHua') else '')
                               for s in p.get('stars', []) if s.get('type') in ('major', 'lucky', 'sha'))[:maxlen]
        return ''

    def palace_names(name):
        for p in z.get('palaces', []):
            if p['name'] == name:
                return ' '.join(s['name'] for s in p.get('stars', []) if s.get('type') == 'major') or '空宮'
        return ''

    def sihua_of(star):
        """生年四化落宮."""
        for p in z.get('palaces', []):
            for s in p.get('stars', []):
                if s['name'] == star and s.get('siHua'):
                    return f"{s['name']}{s['siHua'][0]}{p['name']}"
        return ''

    sihua_str = ' '.join(filter(None, (sihua_of(ns.get(k)) for k in ('禄', '权', '科', '忌'))))
    lines.append(f"紫微：命{ming['branch']}{palace('命宮')}｜身{ming['shen']}{palace('官祿')}｜"
                 f"{ming['wuju']}｜生年{ns.get('stem', '')}：{sihua_str}")

    # 財官象
    def borrow(name):
        """空宮借對宮主星 (對宮=相隔六宮)."""
        order = [p['name'] for p in z.get('palaces', [])]
        idx = order.index(name) if name in order else -1
        if idx < 0:
            return ''
        opp = order[(idx + 6) % 12]
        return f"借{opp}{palace_names(opp)}"

    def palace_or_borrow(name):
        stars = palace_names(name)
        return stars if stars != '空宮' else borrow(name)

    lines.append(f"財官象：財帛{palace_or_borrow('財帛')}｜官祿{palace_or_borrow('官祿')}｜遷移{palace_or_borrow('遷移')}")

    # 紫微格局 (good 級取前3)
    pats = [p['name'] for p in z.get('patterns', []) if p.get('level') == 'good'][:3]
    if pats:
        lines.append(f"格局：{'·'.join(pats)}（紫微；詳見 ziwei show --patterns）")

    # 大限＋流年
    h = z.get('horoscope', {})
    dx = h.get('daxian', {}); ln = h.get('liunian', {})
    dx_sihua = z.get('daxian_sihua', {}).get('transforms', {})
    dx_idx = z.get('currentDaXianIndex')
    dx_age = ''
    if dx_idx is not None:
        for d in z.get('daxian', []):
            if d.get('palaceName') == dx.get('palace'):
                dx_age = f"{d.get('startAge', '')}-{d.get('endAge', '')}歲"
                break
    lmut = ln.get('mutagen', {})
    dx_stars = palace(dx.get('palace', ''), 16)
    b_ln = b.get('liunian', {})
    b_ln_str = f"｜流年{b_ln.get('gan_zhi', '')}{b_ln.get('shishen', '')}" if b_ln else ''
    lines.append(f"大限{dx_age}{dx.get('palace', '')}{dx.get('ganzhi', '')}{dx_stars}｜"
                 f"限四化祿{dx_sihua.get('禄', '')}權{dx_sihua.get('权', '')}"
                 f"科{dx_sihua.get('科', '')}忌{dx_sihua.get('忌', '')}｜流年{ln.get('palace', '')}{ln.get('ganzhi', '')}"
                 f"忌{lmut.get('忌', '')}{b_ln_str}")

    # 財語義
    if cy:
        lines.append(f"財語義：{cy.get('verdict', '')}{('/' + cy['kind']) if cy.get('kind') else ''}"
                     f"（八字{cy.get('bazi', '')}×紫微{cy.get('ziwei', '')}）")

    # 六壬、奇門
    aux = out.get('aux_summary', {})
    lr_d = out.get('liuren_lifetime', {})
    san = lr_d.get('sanchuan', [])
    san_str = ' '.join(f"{['初', '中', '末'][i]}{s.get('pos', '')}{s.get('liuqin', '')}" for i, s in enumerate(san[:3]))
    kong = ''.join(lr_d.get('kongwang', []))
    sike = lr_d.get('sike', {}).get('shang', [])
    lines.append(f"六壬：{'/'.join(lr_d.get('keti', []))}｜{san_str}｜旬空{kong}"
                 f"｜干上{sike[0] if sike else ''}｜本命{aux.get('liuren_benming', '')}行年{aux.get('liuren_xingnian', '')}")

    qm_d = out.get('qimen_lifetime', {})
    mg = qm_d.get('ming_gong')
    qm_line = f"奇門{qm_d.get('yin_yang', '')}遁{qm_d.get('ju', '')}局"
    gong_map = qm_d.get('gong', {})

    def _gong(gk):
        """gong 記憶體鍵為 int、JSON 化後為 str; 兩種都吃."""
        for k in (str(gk), gk, int(gk) if str(gk).isdigit() else None):
            if k in gong_map:
                return gong_map[k]
        return None

    if mg is not None:
        g = _gong(mg)
        if g:
            qm_line += f"：命{mg}宮{g.get('bagua', '')}{g.get('fangwei', '')}{g.get('gate', '')}門{g.get('star', '')}{g.get('god', '')}"
    # 各大限宮 (取前4)
    dx_list = []
    try:
        for dxg in qm_d.get('daxian', [])[:4]:
            g = _gong(dxg.get('gong'))
            if g:
                dx_list.append(f"{dxg.get('age', '')}行{dxg.get('gong')}宮{g.get('fangwei', '')}{g.get('gate', '')}門")
        if dx_list:
            qm_line += '｜' + '｜'.join(dx_list)
    except (ValueError, KeyError):
        pass
    # 忌方: 死門/白虎/擊刑所在
    for gk, g in gong_map.items():
        if g.get('gate') in ('死', '驚') and g.get('god') in ('白虎', '玄武'):
            qm_line += f"｜忌{g.get('fangwei', '')}{g.get('gate', '')}"
            break
    lines.append(qm_line)

    # 警示
    if cc.get('warnings'):
        lines.append(f"警示：{'；'.join(cc['warnings'])}")
    return '\n'.join(lines)


if __name__ == "__main__":
    main()
