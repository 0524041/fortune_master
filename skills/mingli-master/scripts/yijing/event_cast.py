#!/usr/bin/env python3
"""問事四式融合排盤 (六爻 + 梅花 + 大六壬 + 奇門遁甲) — 同一時刻一次出四盤，供交叉解讀。

同一件事，多種起課法各自成盤；程式只算「事實」(四柱/卦象/課傳)，不下吉凶。
吉凶綜合、取象、矛盾裁決由 AI 依 references/ask-event/*.md 判讀。

用法:
  event_cast.py --time "2026-10-07 10:30"
      # 預設: summary (必讀摘要: 起卦時間 + 六爻/梅花 各一行 + 交叉)
      --coins 1 2 3 1 0 2        # 六爻手搖 (初爻→上爻)；省略=電腦代搖
      --numbers 17 23            # 梅花報數；省略=以同時間起卦
      --birth 1990 --gender 女   # 可選，只入六壬年命，不排命盤
  event_cast.py --only liuyao             # 單式全文 (六爻)
  event_cast.py --only meihua             # 單式全文 (梅花)
  event_cast.py --with liuren qimen       # summary + 加跑六壬/奇門全文
  event_cast.py --only liuyao meihua liuren qimen   # 四式全展開
  --format text|md|json      # md=精簡, text=保留長文, json=結構化 (隱藏除錯)
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR))
sys.path.insert(0, str(DIR.parent))          # han.py (統一簡繁層)
sys.path.insert(0, str(DIR / "vendor"))

from liuyao_core import LiuYaoChart, toss_coins  # noqa: E402
import meihua as mh  # noqa: E402
from liuren_core import LiuRenChart  # noqa: E402
from qimen_core import QiMenChart  # noqa: E402
from han import s2t, s2t_deep  # noqa: E402


def parse_time(s: str) -> datetime:
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(f'無法解析時間: {s} (請用 YYYY-MM-DD HH:MM)')


def cross_check(ly: dict, mh_d: dict, lr_d: dict, qm_d: dict) -> dict:
    """客觀交叉: 只記一致/分歧之事實，不下吉凶斷語。六壬/奇門未跑時只比對有跑者。"""
    ly_day = ly['bazi'].split()[2]
    lr_day = lr_d.get('sizhu', {}).get('day')
    qm_day = qm_d.get('sizhu', {}).get('day')
    days = [d for d in (ly_day, lr_day, qm_day) if d]
    checks = {
        'day_pillar_match': len(set(days)) == 1,
        'liuyao_day': ly_day,
        'liuren_day': lr_day,
        'qimen_day': qm_day,
        'meihua_inputs': mh_d['inputs'],
        'same_time': True,          # 多盤同起於一個 dt
        'warnings': [],
    }
    if not checks['day_pillar_match']:
        checks['warnings'].append('六爻/六壬/奇門日柱不一致（時刻換日交界：奇門子時換日、六爻六壬午夜換日），結論標低置信')
    return checks


def liuyao_line(lyc) -> str:
    """六爻一行結論: 本卦→變卦, 動爻, 世應."""
    d = lyc.to_dict()
    moving = [k for k, v in d.items() if k.startswith('yao_') and v['origin'].get('is_changed')]
    shi = [k for k, v in d.items() if k.startswith('yao_') and v['origin'].get('is_subject')]
    ying = [k for k, v in d.items() if k.startswith('yao_') and v['origin'].get('is_object')]
    mv = '無動爻(靜卦)' if not moving else '動' + ','.join(str(int(k[-1])) for k in moving) + '爻'
    return f"本卦{d['benguaming']} → {d['bianguaming']}；{mv}；世{shi[0][-1]}應{ying[0][-1]}"


def meihua_line(mhd: dict) -> str:
    d = mhd
    return (f"本卦{d['bengua']['name']}(體{d['ti_yong']['體']['gua']}用{d['ti_yong']['用']['gua']}) → "
            f"變{d['biangua']['name']}；動{d['dong_yao']}爻；{d['ti_yong']['relation']}({d['ti_yong']['judge']})")


def liuren_line(lrc) -> str:
    d = lrc.to_dict()
    sc = d['sanchuan']
    return (f"課體{'/'.join(d['keti'])}；初{sc[0]['pos']}{sc[0]['liuqin']} "
            f"中{sc[1]['pos']}{sc[1]['liuqin']} 末{sc[2]['pos']}{sc[2]['liuqin']}；月將{d['yuejiang']['zhi']}占時{d['hour_zhi']}")


def qimen_line(qmc) -> str:
    d = qmc.to_dict()
    mg = d.get('ming_gong')
    if mg is None:
        # 時盤無命宮: 以值符落宮為主
        gong = d.get('gong', {})
        zf = next((k for k, g in gong.items() if g.get('god') == '值符'), None)
        if zf:
            g = gong[zf]
            return f"{d.get('yin_yang', '')}遁{d['ju']}局；值符{zf}宮({g['bagua']}{g['fangwei']}) {g['gate']}門{g['star']}"
        return f"{d.get('yin_yang', '')}遁{d['ju']}局"
    g = d['gong'][str(mg)]
    return f"{d.get('yin_yang', '')}遁{d['ju']}局；命宮{mg}宮({g['bagua']}{g['fangwei']}) {g['gate']}門{g['star']}{g['god']}"


def main():
    ap = argparse.ArgumentParser(description='問事四式融合排盤 (預設: summary 摘要; --only/--with 取細節)')
    ap.add_argument('--time', nargs='?', const='now', default=None,
                    help='起課時間 (省略=系統現在)')
    ap.add_argument('--coins', nargs='+', type=int, choices=[0, 1, 2, 3],
                    help='六爻六次背面數 (初爻→上爻)；省略=電腦代搖')
    ap.add_argument('--numbers', nargs='+', type=int, help='梅花報數 (兩數或三數)')
    ap.add_argument('--birth', type=int, action='append', default=[], help='問事人出生年 (可重複)')
    ap.add_argument('--gender', action='append', default=[], help='對應性別 男/女')
    ap.add_argument('--only', nargs='+', choices=['liuyao', 'meihua', 'liuren', 'qimen'],
                    help='只給指定式全文 (不出 summary)')
    ap.add_argument('--with', nargs='+', choices=['liuyao', 'meihua', 'liuren', 'qimen'], dest='with_',
                    help='summary + 加跑指定式全文 (用途引導: 過程人事加六壬、方位行動加奇門)')
    ap.add_argument('--format', default=None, choices=['text', 'md', 'json'],
                    help='輸出格式: text=固定文字 (預設)、md=精簡、json=結構化 (隱藏除錯)')
    # 舊旗標 (相容, 不宣傳)
    ap.add_argument('--both', action='store_true', help=argparse.SUPPRESS)
    ap.add_argument('--json', action='store_true', help=argparse.SUPPRESS)
    ap.add_argument('--text', action='store_true', help=argparse.SUPPRESS)
    a = ap.parse_args()

    if len(a.birth) != len(a.gender):
        print('錯誤：--birth 與 --gender 數量須一致', file=sys.stderr)
        sys.exit(1)
    genders = ['男' if g in ('男', 'male') else '女' for g in a.gender]

    dt = datetime.now() if a.time in (None, 'now') else parse_time(a.time)

    # 六爻
    if a.coins and len(a.coins) != 6:
        print('錯誤：--coins 需要剛好 6 個數字 (初爻→上爻)', file=sys.stderr)
        sys.exit(1)
    coins = a.coins if a.coins else toss_coins()
    lyc = LiuYaoChart(dt, coins)

    # 梅花
    if a.numbers and len(a.numbers) not in (2, 3):
        print('錯誤：--numbers 需 2 或 3 個整數', file=sys.stderr)
        sys.exit(1)
    mcast = mh.from_numbers(a.numbers) if a.numbers else mh.from_time(dt)
    mhd = mh.build(mcast)

    # 建盤集合: --only=只建指定; --with/default=建六爻+梅花, 再加 --with
    if a.only:
        need = set(a.only)
    else:
        need = {'liuyao', 'meihua'} | set(a.with_ or [])

    lrc = LiuRenChart(dt, birth=list(zip(a.birth, genders))) if 'liuren' in need or a.birth else None
    qmc = QiMenChart(dt) if 'qimen' in need else None

    ly_d = lyc.to_dict()
    lr_d = lrc.to_dict() if lrc else {}
    qm_d = qmc.to_dict() if qmc else {}
    out = {
        'time': dt.strftime('%Y-%m-%d %H:%M:%S'),
        'liuyao': ly_d,
        'meihua': mhd,
    }
    if lr_d:
        out['liuren'] = lr_d
    if qm_d:
        out['qimen'] = qm_d
    out['cross'] = cross_check(ly_d, mhd, lr_d, qm_d)

    out = s2t_deep(out)

    fmt = a.format
    if fmt is None:
        fmt = 'both' if a.both else ('json' if a.json else 'text')

    # 輸出選擇: --only 指定式全文; --with summary+追加; 預設 summary
    if a.only:
        want_summary = False
        detail = set(a.only)
    else:
        want_summary = True
        detail = set(a.with_ or []) if a.with_ else set()

    if fmt in ('text', 'md') or (fmt == 'json' and a.only):
        if want_summary:
            print("═" * 8 + " 問事摘要 " + "═" * 8)
            print(f"起卦時間：{out['time']}；日柱：{out['cross']['liuyao_day']}")
            print(f"六爻：{liuyao_line(lyc)}")
            print(f"梅花：{meihua_line(mhd)}")
            if lrc:
                print(f"六壬：{liuren_line(lrc)}")
            if qmc:
                print(f"奇門：{qimen_line(qmc)}")
            cc = out['cross']
            print(f"交叉：日柱{'一致' if cc['day_pillar_match'] else '不一致'}"
                  + ("；警示：" + '；'.join(cc['warnings']) if cc['warnings'] else ""))
            if detail:
                print()
        if want_summary is False and not detail:
            detail = {'liuyao'}
        if detail:
            if 'liuyao' in detail:
                print('═' * 8 + ' 六爻 ' + '═' * 8)
                print(s2t(lyc.format_for_ai(fmt='md' if fmt == 'md' else 'text')))
                print()
            if 'meihua' in detail:
                print('═' * 8 + ' 梅花 ' + '═' * 8)
                print(s2t(mh.format_text(mhd, fmt='md' if fmt == 'md' else 'text')))
                print()
            if 'liuren' in detail:
                if lrc is None:
                    lrc = LiuRenChart(dt, birth=list(zip(a.birth, genders)))
                    out['liuren'] = s2t_deep(lrc.to_dict())
                print('═' * 8 + ' 六壬 ' + '═' * 8)
                print(s2t(lrc.format_for_ai()))
                print()
            if 'qimen' in detail:
                if qmc is None:
                    qmc = QiMenChart(dt)
                    out['qimen'] = s2t_deep(qmc.to_dict())
                print('═' * 8 + ' 奇門 ' + '═' * 8)
                print(s2t(qmc.format_for_ai()))
                print()
            cc = out['cross']
            print('─' * 8 + ' 交叉 ' + '─' * 8)
            print(f"同起課時刻：{out['time']}")
            print(f"日柱一致：{cc['day_pillar_match']}（六爻 {cc['liuyao_day']} / 六壬 {cc.get('liuren_day', '-')} / 奇門 {cc.get('qimen_day', '-')}）")
            if cc['warnings']:
                print('警示：' + '；'.join(cc['warnings']))
    if fmt == 'both' or (fmt == 'text' and a.json):
        print()
        print('===== JSON =====')
        print(json.dumps(out, ensure_ascii=False, indent=2))
    elif fmt == 'json':
        print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
