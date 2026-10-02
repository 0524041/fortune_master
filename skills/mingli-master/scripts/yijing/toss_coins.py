#!/usr/bin/env python3
"""
六爻起卦腳本

以三枚硬幣搖卦六次，每次輸入「背面朝上的數量」(0-3)，產生一組爻象。

規則 (錢幣法)：
  0 = 三字     → 老陽 (動爻) ⚊ O
  1 = 二字一背 → 少陽 (靜爻) ⚊
  2 = 一字二背 → 少陰 (靜爻) ⚋
  3 = 三背     → 老陰 (動爻) ⚋ X

用法：
  互動起卦 (逐爻輸入) :
    python toss_coins.py
  電腦隨機起卦 :
    python toss_coins.py --random
  指定起卦結果 (跳過互動) :
    python toss_coins.py --coins 1 2 3 1 0 2
  以 JSON 格式輸出 (供 divine.py 或後續程式使用) :
    python toss_coins.py --random --json

輸出：
  預設印出一行格式化的爻象說明 (初爻→上爻)；
  搭配 --json 輸出 {"yaogua": [0-3 六個數字]}。
"""

import argparse
import json
import sys

COIN_DESC = {
    0: '三字(老陽,動)',
    1: '二字一背(少陽,靜)',
    2: '一字二背(少陰,靜)',
    3: '三背(老陰,動)',
}


def prompt_coins() -> list:
    """互動式起卦：逐爻請使用者輸入背面數量 (初爻→上爻)"""
    coins = []
    print('請準備三枚硬幣，依序搖卦六次（初爻 → 上爻）。')
    print('每次輸入「背面朝上的數量」：0=三字(老陽) 1=二字一背(少陽) 2=一字二背(少陰) 3=三背(老陰)')
    print()
    for i in range(6):
        while True:
            try:
                raw = input(f'第 {i+1} 爻 (初爻=1，上爻=6)，輸入 0-3：').strip()
                if raw in ('r', 'R', 'rand', '隨機'):
                    coin = random_toss()
                else:
                    coin = int(raw)
                if coin not in (0, 1, 2, 3):
                    raise ValueError
                break
            except (ValueError, EOFError):
                print('  無效輸入，請輸入 0、1、2 或 3（或 r 隨機）')
        coins.append(coin)
        print(f'  → 第 {i+1} 爻：{coin} ({COIN_DESC[coin]})')
    return coins


def random_toss() -> int:
    """電腦模擬擲三枚硬幣一次，回傳背面數量"""
    import random
    return sum(random.choice([0, 1]) for _ in range(3))


def random_coins() -> list:
    """電腦隨機起卦六次"""
    return [random_toss() for _ in range(6)]


def format_coins(coins: list) -> str:
    """爻象說明：初爻→上爻，含陰陽與動靜標記"""
    lines = []
    for i, coin in enumerate(coins):
        yang, moving = (True, True) if coin == 0 else \
                       (True, False) if coin == 1 else \
                       (False, False) if coin == 2 else (False, True)
        symbol = ('⚊' if yang else '⚋') + (' O' if moving and yang else ' X' if moving else '')
        lines.append(f'第 {i+1} 爻 (初爻=1)：{coin} = {COIN_DESC[coin]} {symbol}')
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='六爻起卦 (三枚硬幣法)')
    parser.add_argument('--random', action='store_true', help='電腦隨機起卦，不互動')
    parser.add_argument('--coins', nargs='+', type=int, choices=[0, 1, 2, 3],
                        help='直接指定六次背面數量 (初爻→上爻)')
    parser.add_argument('--json', action='store_true', help='以 JSON 輸出 (僅含 yaogua)')
    args = parser.parse_args()

    if args.coins:
        if len(args.coins) != 6:
            print('錯誤：--coins 需要剛好 6 個數字 (初爻→上爻)', file=sys.stderr)
            sys.exit(1)
        coins = args.coins
    elif args.random:
        coins = random_coins()
    else:
        coins = prompt_coins()

    if args.json:
        print(json.dumps({'yaogua': coins}, ensure_ascii=False))
    else:
        print(format_coins(coins))
        print()
        print('將以上結果交給 divine.py 排盤：')
        print(f'  python divine.py --coins {" ".join(map(str, coins))}')


if __name__ == '__main__':
    main()
