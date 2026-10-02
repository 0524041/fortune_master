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
    parser.add_argument('--time', type=parse_time, help='起卦時間 (預設現在)')
    parser.add_argument('--text', action='store_true', help='輸出固定文字格式 (預設)')
    parser.add_argument('--json', action='store_true', help='輸出結構化 JSON')
    parser.add_argument('--both', action='store_true', help='同時輸出文字與 JSON')
    args = parser.parse_args()

    if args.coins and args.random:
        print('錯誤：--coins 與 --random 不能同時使用', file=sys.stderr)
        sys.exit(1)

    coins = args.coins if args.coins else (toss_coins() if args.random else toss_coins())
    if args.coins and len(coins) != 6:
        print('錯誤：--coins 需要剛好 6 個數字 (初爻→上爻)', file=sys.stderr)
        sys.exit(1)

    dt = args.time or datetime.now()
    chart = LiuYaoChart(dt, coins)

    want_text = args.text or args.both or not (args.json or args.both)
    if want_text:
        print(chart.format_for_ai())
    if args.json or args.both:
        if want_text and (args.json or args.both):
            print()
            print("===== JSON =====")
        print(json.dumps(chart.to_dict(), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
