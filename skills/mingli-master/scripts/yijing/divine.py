#!/usr/bin/env python3
"""
六爻排盤主程式：起卦 → 排盤 → 固定格式輸出

用法：
  排盤 (使用起卦結果或隨機) :
    python divine.py --coins 1 2 3 1 0 2
    python divine.py --random
  指定起卦時間 (預設為現在) :
    python divine.py --coins 1 1 1 1 1 1 --time "2026-08-01 10:30"
  輸出格式 :
    --text  固定文字格式 (預設，供 AI 解盤/後續詢問)
    --json  結構化 JSON (含卦盤全部資訊)
    --both  兩者皆輸出

輸出固定格式 (--text)：
  【基本資訊】  起卦時間 / 干支 / 日空 / 神煞
  【卦象結構】  本卦 / 變卦 / 六神 / 伏神 / 世應 / 動爻表
  【本卦：XX】 卦辭 / 象傳 / 諸事 / 愛情 / 事業 / 財運 / 建議 / 詳解
  【變卦：XX】 同上
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "vendor"))  # 內嵌 lunar_python (零安裝)
from liuyao_core import LiuYaoChart, toss_coins  # noqa: E402


def parse_time(s: str) -> datetime:
    """解析 --time 參數，支援 YYYY-MM-DD HH:MM 或 YYYY-MM-DD"""
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(f'無法解析時間: {s} (請用 YYYY-MM-DD HH:MM)')


def main():
    parser = argparse.ArgumentParser(description='六爻排盤 (起卦 → 排盤 → 固定格式輸出)')
    parser.add_argument('--coins', nargs='+', type=int, choices=[0, 1, 2, 3],
                        help='六次背面數量 (初爻→上爻)，省略則隨機')
    parser.add_argument('--random', action='store_true', help='電腦隨機起卦')
    parser.add_argument('--time', nargs='?', const='now', default=None,
                        help='起卦時間 (省略=系統現在; 使用者提供實際起卦時刻才給值)')
    parser.add_argument('--format', choices=['text', 'md', 'json'], default=None,
                        help='輸出格式: text=固定文字 (預設)、md=精簡 markdown、json=結構化')
    # 舊旗標 (相容, 不宣傳)
    parser.add_argument('--text', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--json', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--both', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.coins and args.random:
        print('錯誤：--coins 與 --random 不能同時使用', file=sys.stderr)
        sys.exit(1)

    coins = args.coins if args.coins else (toss_coins() if args.random else toss_coins())
    if args.coins and len(coins) != 6:
        print('錯誤：--coins 需要剛好 6 個數字 (初爻→上爻)', file=sys.stderr)
        sys.exit(1)

    dt = datetime.now() if args.time in (None, 'now') else parse_time(args.time)
    chart = LiuYaoChart(dt, coins)

    # 格式決策: --format 優先; 舊 --text/--json/--both 相容
    fmt = args.format
    if fmt is None:
        if args.both:
            fmt = 'both'
        elif args.json:
            fmt = 'json'
        else:
            fmt = 'text'
    want_text = fmt in ('text', 'md', 'both')
    want_json = fmt in ('json', 'both')
    if want_text:
        print(chart.format_for_ai(fmt='md' if fmt == 'md' else 'text'))
    if want_json:
        if want_text:
            print()
            print("===== JSON =====")
        print(json.dumps(chart.to_dict(), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
