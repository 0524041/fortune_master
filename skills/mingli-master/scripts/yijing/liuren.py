#!/usr/bin/env python3
"""大六壬排盤主程式：月將加時 → 天地盤 → 四課 → 三傳 → 十二天將。

用法：
  正時起課 (預設為現在) :
    python liuren.py
    python liuren.py --time "2026-10-07 10:30"
  附問事人年命 (可選，僅供落點佐證) :
    python liuren.py --time "2026-10-07 10:30" --birth 1990 --gender 女
  輸出格式 :
    --text  固定文字格式 (預設)
    --json  結構化 JSON
    --both  兩者皆輸出

輸出固定格式 (--text)：
  【大六壬】 起課時間 / 四柱 / 月將 / 占時 / 第幾局 / 晝夜 / 旬空 / 課體
  【三傳】   初/中/末：支 遁干 六親 式神 旬空
  【四課】   上下神 + 式神
  【天地盤】 天盤 + 十二天將 / 地盤
  【神煞】   日干/日支/月/旬 諸神煞落點
  【年命】   本命 / 行年 (有給生日才顯示)
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))          # han.py (統一簡繁層)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "vendor"))
from liuren_core import LiuRenChart  # noqa: E402
from han import s2t, s2t_deep  # noqa: E402


def parse_time(s: str) -> datetime:
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(f'無法解析時間: {s} (請用 YYYY-MM-DD HH:MM)')


def main():
    ap = argparse.ArgumentParser(description='大六壬排盤 (月將加時 → 四課三傳 → 十二天將)')
    ap.add_argument('--time', nargs='?', const='now', default=None,
                    help='起課時間 (省略=系統現在; 使用者提供實際起課時刻才給值)')
    ap.add_argument('--birth', type=int, action='append', default=[],
                    help='問事人出生年 (可重複，最多兩個)')
    ap.add_argument('--gender', action='append', default=[],
                    help='對應 --birth 的性別 (男/女)')
    ap.add_argument('--lifetime', action='store_true',
                    help='終身課模式: 以 --time 為出生時刻起課，三傳讀一生；命主生年預設同 --time 之年')
    ap.add_argument('--at-year', type=int, default=None,
                    help='行年參考年 (預設為起課年/今年)')
    ap.add_argument('--twin', type=int, default=1,
                    help='雙胞胎次客序 (1=正課、2=二客、3=三客; 古法換將不換時, 低置信)')
    ap.add_argument('--text', action='store_true')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--both', action='store_true')
    a = ap.parse_args()

    if a.birth and len(a.birth) != len(a.gender):
        print('錯誤：--birth 與 --gender 數量須一致', file=sys.stderr)
        sys.exit(1)
    if len(a.birth) > 2:
        print('錯誤：年命最多兩個 (主客)', file=sys.stderr)
        sys.exit(1)
    for g in a.gender:
        if g not in ('男', '女', 'male', 'female'):
            print('錯誤：--gender 須為 男/女', file=sys.stderr)
            sys.exit(1)
    genders = ['男' if g in ('男', 'male') else '女' for g in a.gender]

    dt = datetime.now() if a.time in (None, 'now') else parse_time(a.time)
    birth = list(zip(a.birth, genders))
    if a.lifetime and not birth:
        if not genders:
            print('錯誤：--lifetime 需 --gender 男/女 (命主性別)', file=sys.stderr)
            sys.exit(1)
        birth = [(dt.year, genders[0])]
    chart = LiuRenChart(dt, birth=birth, at_year=a.at_year, lifetime=a.lifetime, twin=a.twin)

    want_text = a.text or a.both or not (a.json or a.both)
    if want_text:
        print(s2t(chart.format_for_ai()))  # 統一簡繁層
    if a.json or a.both:
        if want_text:
            print()
            print('===== JSON =====')
        print(json.dumps(s2t_deep(chart.to_dict()), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
