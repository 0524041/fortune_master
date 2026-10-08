#!/usr/bin/env python3
"""南派紫微「借宮立極」變盤 (同性雙胞胎老二以上)。

同一張星盤、**星曜不動**，只旋轉十二宮名：老二以原盤「兄弟宮」為新命宮，
老三再進一位（夫妻宮）…；大限自新命宮起、沿用原局起運歲。
（另有「時辰遞推法」= 生時進位整盤重算，見 ziwei_full.sh --hour-shift。）

用法:
  ziwei_full.sh ... --format json > z.json
  twin_adjust.py --ziwei z.json --order 2 > rebased.json
  cat z.json | twin_adjust.py --ziwei - --order 2
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from han import s2t_deep  # noqa: E402  # 統一簡繁層

ZHI = '子丑寅卯辰巳午未申酉戌亥'
SEQ = ['命宮', '兄弟', '夫妻', '子女', '財帛', '疾厄', '遷移', '僕役', '官祿', '田宅', '福德', '父母']


def _branch(p):
    return ZHI.index(p['gz'][-1])


def adjust(d, order):
    """就地旋轉宮名與大限；order=1 原盤不動。"""
    shift = max(0, order - 1)
    if shift == 0:
        d.setdefault('twin', None)
        return d
    palaces = d['palaces']
    by_branch = {_branch(p): p for p in palaces}
    ming_b = ZHI.index(d['ming']['branch'])
    if by_branch[ming_b]['name'] != '命宮':
        raise ValueError('輸入盤面命宮標記不一致，非 ziwei_full 原始輸出？')
    bro_b = next(b for b, p in by_branch.items() if p['name'] == '兄弟')
    dir_ = (bro_b - ming_b) % 12          # 宮名排列方向: 兄弟 = 命 + dir
    if dir_ not in (1, 11):
        raise ValueError(f'宮序方向異常: {dir_}')
    new_ming = (ming_b + dir_ * shift) % 12
    # 新宮名(b) = 舊宮名(b - dir*shift)；星曜/宮干留在原支不動
    old_names = {b: p['name'] for b, p in by_branch.items()}
    for b, p in by_branch.items():
        p['name'] = old_names[(b - dir_ * shift) % 12]
    d['ming']['branch'] = ZHI[new_ming]

    # 大限: 沿原方向、自新命宮起，沿用原局起運歲 (五行局不變)
    dx = d.get('daxian') or []
    if len(dx) >= 2:
        dd = (dx[1]['palaceBranch'] - dx[0]['palaceBranch']) % 12
        if dd not in (1, 11):
            raise ValueError(f'大限方向異常: {dd}')
        start_age = dx[0]['startAge']
        name_by_branch = {_branch(p): p['name'] for p in palaces}
        d['daxian'] = [
            {'startAge': start_age + 10 * i, 'endAge': start_age + 10 * i + 9,
             'palaceBranch': (new_ming + i * dd) % 12,
             'palaceName': name_by_branch[(new_ming + i * dd) % 12]}
            for i in range(len(dx))
        ]

    note = ('借宮立極(南派): 星曜不動、十二宮名旋轉；大限自新命宮起、沿用原局起運歲；'
            '身宮支不動；格局與運限仍以原命宮判定，僅供參考')
    if d.get('horoscope'):
        d.pop('horoscope')
        note += '；已移除 horoscope，運限需以變盤命宮重排'
    d['twin'] = {'method': '借宮立極（南派）', 'order': order, 'shift': shift,
                 'original_ming': ZHI[ming_b], 'adjusted_ming': ZHI[new_ming], 'note': note}
    d['warnings'] = list(dict.fromkeys(
        (d.get('warnings') or []) + [f'雙胞胎借宮立極: 命{ZHI[ming_b]}→命{ZHI[new_ming]}']))
    return d


def main():
    ap = argparse.ArgumentParser(description='紫微借宮立極變盤 (同性雙胞胎老二以上)')
    ap.add_argument('--ziwei', required=True, help='紫微排盤程式 --format json 的輸出檔；- 代表 stdin')
    ap.add_argument('--order', type=int, required=True, help='排行: 2=老二(借兄弟宮)、3=老三(借夫妻宮)…')
    a = ap.parse_args()
    src = sys.stdin if a.ziwei == '-' else open(a.ziwei, encoding='utf-8')
    try:
        d = s2t_deep(json.load(src))  # 統一簡繁層: 引擎輸出轉繁後再變盤
    except Exception as e:
        print(f'錯誤: 無法讀取紫微 JSON: {e}', file=sys.stderr)
        sys.exit(2)
    try:
        d = adjust(d, a.order)
    except (KeyError, ValueError) as e:
        print(f'錯誤: 借宮變盤失敗: {e}', file=sys.stderr)
        sys.exit(2)
    print(json.dumps(d, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
