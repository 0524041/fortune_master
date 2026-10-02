#!/usr/bin/env python3
"""梅花易數起卦 (時間起卦 / 數字起卦 / 隨機). Deterministic, 不心算.
依賴 lunar_python (共用本 skill venv). 卦名/五行表自 scripts/yijing/liuyao_core.py 重用.

用法:
  meihua.py --time "2026-08-01 10:30"        # 時間起卦 (公曆, 內部轉農曆)
  meihua.py --numbers 17 23                   # 數字起卦 (兩數)
  meihua.py --numbers 17 23 5                 # 數字起卦 (三數: 上/下/動)
  meihua.py --random                          # 隨機起卦
  meihua.py --time "..." --json               # 結構化輸出
"""
import argparse
import json
import random
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from liuyao_core import LIUSHISI_GUA, BAGUA  # noqa: E402
from lunar_python import Solar  # noqa: E402

DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
NUM2GUA = {1: '乾', 2: '兌', 3: '離', 4: '震', 5: '巽', 6: '坎', 7: '艮', 8: '坤'}
GUA_BITS = {'乾': (1, 1, 1), '兌': (1, 1, 0), '離': (1, 0, 1), '震': (1, 0, 0),
            '巽': (0, 1, 1), '坎': (0, 1, 0), '艮': (0, 0, 1), '坤': (0, 0, 0)}
BITS2GUA = {v: k for k, v in GUA_BITS.items()}
SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}


def _gua_name(lower: str, upper: str) -> str:
    return LIUSHISI_GUA.get((lower, upper), f'{upper}上{lower}下')


def _relation(ti_wx: str, yong_wx: str) -> tuple:
    """(關係, 吉凶). 體=ti, 用=yong."""
    if ti_wx == yong_wx:
        return '體用比和', '吉'
    if SHENG.get(yong_wx) == ti_wx:
        return '用生體', '吉'
    if SHENG.get(ti_wx) == yong_wx:
        return '體生用', '洩（耗）'
    if KE.get(ti_wx) == yong_wx:
        return '體剋用', '吉'
    return '用剋體', '凶'


def from_time(dt: datetime) -> dict:
    s = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, 0)
    lunar = s.getLunar()
    yzn = DIZHI.index(lunar.getYearZhi()) + 1
    month, day = abs(lunar.getMonth()), lunar.getDay()
    tzn = DIZHI.index(lunar.getTimeZhi()) + 1
    base = yzn + month + day
    up = base % 8 or 8
    low = (base + tzn) % 8 or 8
    dong = (base + tzn) % 6 or 6
    return {'method': '時間起卦', 'inputs': {
        'lunar': f'{lunar.getYearInChinese()}年{month}月{day}日',
        'zhi': {'年支數': yzn, '月': month, '日': day, '時支數': tzn}},
        'up_num': up, 'low_num': low, 'dong': dong}


def from_numbers(nums: list) -> dict:
    a, b = nums[0], nums[1]
    up = a % 8 or 8
    low = b % 8 or 8
    c = nums[2] if len(nums) >= 3 else (a + b)
    dong = c % 6 or 6
    return {'method': '數字起卦', 'inputs': {'numbers': nums},
            'up_num': up, 'low_num': low, 'dong': dong}


def from_random() -> dict:
    a, b, c = random.randint(1, 999), random.randint(1, 999), random.randint(1, 999)
    d = from_numbers([a, b, c])
    d['method'] = '隨機起卦'
    return d


def build(cast: dict) -> dict:
    upper, lower = NUM2GUA[cast['up_num']], NUM2GUA[cast['low_num']]
    dong = cast['dong']
    lines = list(GUA_BITS[lower]) + list(GUA_BITS[upper])  # index0=初爻
    # 互卦: 下互=2,3,4爻; 上互=3,4,5爻
    hu_low = BITS2GUA[(lines[1], lines[2], lines[3])]
    hu_up = BITS2GUA[(lines[2], lines[3], lines[4])]
    # 變卦: 動爻變
    blines = lines[:]
    blines[dong - 1] ^= 1
    b_low = BITS2GUA[(blines[0], blines[1], blines[2])]
    b_up = BITS2GUA[(blines[3], blines[4], blines[5])]
    # 體用: 動爻所在卦為用
    if dong <= 3:
        ti, yong = upper, lower
    else:
        ti, yong = lower, upper
    rel, luck = _relation(BAGUA[ti]['wuxing'], BAGUA[yong]['wuxing'])
    return {
        'method': cast['method'], 'inputs': cast['inputs'],
        'bengua': {'upper': upper, 'lower': lower, 'name': _gua_name(lower, upper)},
        'hugua': {'upper': hu_up, 'lower': hu_low, 'name': _gua_name(hu_low, hu_up)},
        'biangua': {'upper': b_up, 'lower': b_low, 'name': _gua_name(b_low, b_up)},
        'dong_yao': dong,
        'ti_yong': {'體': {'gua': ti, 'wuxing': BAGUA[ti]['wuxing']},
                    '用': {'gua': yong, 'wuxing': BAGUA[yong]['wuxing']},
                    'relation': rel, 'judge': luck},
        'lines': lines,  # 初爻→上爻, 1=陽 0=陰
    }


def format_text(d: dict) -> str:
    ln = ''.join('▅▅▅▅▅' if x else '▅▅　▅▅' for x in d['lines'])
    out = [f"【梅花易數】{d['method']}",
           f"輸入: {d['inputs']}",
           f"本卦: {d['bengua']['name']}（上{d['bengua']['upper']} 下{d['bengua']['lower']}）  動爻: 第{d['dong_yao']}爻",
           f"互卦: {d['hugua']['name']}（上{d['hugua']['upper']} 下{d['hugua']['lower']}）",
           f"變卦: {d['biangua']['name']}（上{d['biangua']['upper']} 下{d['biangua']['lower']}）",
           f"體用: 體{d['ti_yong']['體']['gua']}({d['ti_yong']['體']['wuxing']}) / "
           f"用{d['ti_yong']['用']['gua']}({d['ti_yong']['用']['wuxing']}) → {d['ti_yong']['relation']}（{d['ti_yong']['judge']}）",
           f"爻象(初→上): {ln}"]
    return '\n'.join(out)


def parse_time(s: str) -> datetime:
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(f'無法解析時間: {s} (請用 YYYY-MM-DD HH:MM)')


def main():
    ap = argparse.ArgumentParser(description='梅花易數起卦')
    ap.add_argument('--time', type=parse_time, help='時間起卦 (公曆 YYYY-MM-DD HH:MM)')
    ap.add_argument('--numbers', nargs='+', type=int, help='數字起卦 (兩數或三數)')
    ap.add_argument('--random', action='store_true', help='隨機起卦')
    ap.add_argument('--text', action='store_true')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--both', action='store_true')
    a = ap.parse_args()
    n = sum(bool(x) for x in [a.time, a.numbers, a.random])
    if n != 1:
        print('錯誤：--time / --numbers / --random 需擇一', file=sys.stderr)
        sys.exit(1)
    if a.numbers and len(a.numbers) not in (2, 3):
        print('錯誤：--numbers 需 2 或 3 個整數', file=sys.stderr)
        sys.exit(1)
    cast = from_time(a.time) if a.time else (from_numbers(a.numbers) if a.numbers else from_random())
    d = build(cast)
    want_text = a.text or a.both or not (a.json or a.both)
    if want_text:
        print(format_text(d))
    if a.json or a.both:
        if want_text:
            print('\n===== JSON =====')
        print(json.dumps(d, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
