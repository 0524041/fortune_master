#!/usr/bin/env python3
"""問事四式融合排盤 (六爻 + 梅花 + 大六壬 + 奇門遁甲) — 同一時刻一次出四盤，供交叉解讀。

同一件事，三種起課法各自成盤；程式只算「事實」(四柱/卦象/課傳)，不下吉凶。
吉凶綜合、取象、矛盾裁決由 AI 依 references/ask-event/*.md 判讀。

用法:
  event_cast.py --time "2026-10-07 10:30"
      --coins 1 2 3 1 0 2        # 六爻手搖 (初爻→上爻)；省略=電腦代搖
      --numbers 17 23            # 梅花報數；省略=以同時間起卦
      --birth 1990 --gender 女   # 可選，只入六壬年命，不排命盤
      --format json|text

輸出: {"time","liuyao","meihua","liuren","cross"}
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
    """客觀交叉: 只記一致/分歧之事實，不下吉凶斷語。"""
    ly_day = ly['bazi'].split()[2]
    lr_day = lr_d['sizhu']['day']
    qm_day = qm_d['sizhu']['day']
    checks = {
        'day_pillar_match': ly_day == lr_day == qm_day,
        'liuyao_day': ly_day,
        'liuren_day': lr_day,
        'qimen_day': qm_day,
        'meihua_inputs': mh_d['inputs'],
        'same_time': True,          # 四盤同起於一個 dt
        'warnings': [],
    }
    if not checks['day_pillar_match']:
        checks['warnings'].append('六爻/六壬/奇門日柱不一致（時刻換日交界：奇門子時換日、六爻六壬午夜換日），結論標低置信')
    return checks


def main():
    ap = argparse.ArgumentParser(description='問事四式融合排盤 (六爻+梅花+六壬+奇門)')
    ap.add_argument('--time', nargs='?', const='now', default=None,
                    help='起課時間 (省略=系統現在)')
    ap.add_argument('--coins', nargs='+', type=int, choices=[0, 1, 2, 3],
                    help='六爻六次背面數 (初爻→上爻)；省略=電腦代搖')
    ap.add_argument('--numbers', nargs='+', type=int, help='梅花報數 (兩數或三數)')
    ap.add_argument('--birth', type=int, action='append', default=[], help='問事人出生年 (可重複)')
    ap.add_argument('--gender', action='append', default=[], help='對應性別 男/女')
    ap.add_argument('--format', default='text', choices=['text', 'json', 'both'])
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

    # 六壬
    lrc = LiuRenChart(dt, birth=list(zip(a.birth, genders)))

    # 奇門遁甲（時盤）
    qmc = QiMenChart(dt)

    ly_d = lyc.to_dict(); lr_d = lrc.to_dict(); qm_d = qmc.to_dict()
    out = {
        'time': dt.strftime('%Y-%m-%d %H:%M:%S'),
        'liuyao': ly_d,
        'meihua': mhd,
        'liuren': lr_d,
        'qimen': qm_d,
        'cross': cross_check(ly_d, mhd, lr_d, qm_d),
    }

    out = s2t_deep(out)  # 統一簡繁層
    if a.format in ('text', 'both'):
        print('═' * 8 + ' 六爻 ' + '═' * 8)
        print(s2t(lyc.format_for_ai()))
        print()
        print('═' * 8 + ' 梅花 ' + '═' * 8)
        print(s2t(mh.format_text(mhd)))
        print()
        print('═' * 8 + ' 六壬 ' + '═' * 8)
        print(s2t(lrc.format_for_ai()))
        print()
        print('═' * 8 + ' 奇門 ' + '═' * 8)
        print(s2t(qmc.format_for_ai()))
        print()
        print('─' * 8 + ' 交叉 ' + '─' * 8)
        cc = out['cross']
        print(f"同起課時刻：{out['time']}")
        print(f"四盤日柱一致：{cc['day_pillar_match']}（六爻 {cc['liuyao_day']} / 六壬 {cc['liuren_day']} / 奇門 {cc['qimen_day']}）")
        if cc['warnings']:
            print('警示：' + '；'.join(cc['warnings']))
    if a.format == 'both':
        print()
        print('===== JSON =====')
    if a.format in ('json', 'both'):
        print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
