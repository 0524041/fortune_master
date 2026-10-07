#!/usr/bin/env python3
"""奇門遁甲排盤 (時家・拆補法・轉盤・陽盤)。

用法：
  時盤 (預設為現在) :
    python qimen.py
    python qimen.py --time "2026-10-07 10:30"
  終身盤 (以出生時刻起局，年干定命宮，一宮9年大限) :
    python qimen.py --lifetime --time "1990-08-18 06:30" --gender 男
  真太陽時校正 (終身盤建議給出生地) :
    python qimen.py --lifetime --time "1990-08-18 06:30" --gender 男 --city 台北
  輸出格式 :
    --text  固定文字格式 (預設) / --json 結構化 / --both 兩者

輸出 (--text)：
  【奇門遁甲】 四柱 / 節氣·三元·局 / 值符值使 / 格局
  【九宮】     宮 八卦方位｜地盤干/天盤干 九星 八門 八神
  【大限】     命宮起、順時針、每宮9年 (終身盤)
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR))
sys.path.insert(0, str(DIR.parent))
sys.path.insert(0, str(DIR.parent / "vendor"))
from qimen_core import QiMenChart  # noqa: E402
from time_correct import true_solar  # noqa: E402


def parse_time(s: str) -> datetime:
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(f'無法解析時間: {s} (請用 YYYY-MM-DD HH:MM)')


def main():
    ap = argparse.ArgumentParser(description='奇門遁甲排盤 (時家/終身盤)')
    ap.add_argument('--time', nargs='?', const='now', default=None,
                    help='起局時間 (省略=系統現在; 終身盤請給出生時刻)')
    ap.add_argument('--lifetime', action='store_true', help='終身盤模式 (年干定命宮、一宮9年)')
    ap.add_argument('--gender', choices=['男', '女', 'male', 'female'], default=None,
                    help='性別 (終身盤備註用)')
    ap.add_argument('--city', default=None, help='出生地/起局地 (真太陽時校正)')
    ap.add_argument('--lon', type=float, default=None, help='經度 (與 --city 二選一)')
    ap.add_argument('--text', action='store_true')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--both', action='store_true')
    a = ap.parse_args()

    dt = datetime.now() if a.time in (None, 'now') else parse_time(a.time)
    solar_info = None
    if a.city or a.lon is not None:
        dt, solar_info = true_solar(dt, city=a.city or '', lon=a.lon)

    chart = QiMenChart(dt, lifetime=a.lifetime)
    d = chart.to_dict()
    if solar_info:
        d['true_solar'] = solar_info

    want_text = a.text or a.both or not (a.json or a.both)
    if want_text:
        print(chart.format_for_ai())
        if solar_info:
            print(f"（真太陽時校正：{solar_info['input']} → {solar_info['true_solar']}，"
                  f"{solar_info['city']} 經度差 {solar_info['lon_corr_min']} 分＋均時差 {solar_info['eot_min']} 分）")
    if a.json or a.both:
        if want_text:
            print()
            print('===== JSON =====')
        print(json.dumps(d, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
