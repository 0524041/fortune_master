# 問事（占卜）入口

> 問「這件事的走向」都走這裡。**以卦象為準**：六爻＋梅花，隨機起卦、一事一卦、事畢卦止。
> 起卦前先讀 `questioning.md`；輸出怎麼說見 `references/shared/output-quality.md`。
> 別拿一卦算「我一輩子賺多少」——那是問人（`references/ask-person/`）。

## 一、起卦前（重要）

- **一次只問一件事**；問題不明確先引導（領域／具體選項／目前處境），別急著起卦。
- 時間**預設系統現在**（現在問＝現在起卦），**不用問使用者**；只有他提供**實際起卦時刻**才用 `--time`。
- 問公共標的（大盤／某股漲跌）取不到「你的」用神 → 改問「我」的財運／該不該進出／什麼時機進出。

## 二、選法

| 需求 | 用 | 讀 |
|---|---|---|
| 具體成敗、時間點、細節（面試／官司／病情） | **六爻** `scripts/yijing/divine.py` | `liuyao.md`＋`yongshen.md` |
| 快速判方向大勢、觸機、象義 | **梅花** `scripts/yijing/meihua.py` | `meihua.md` |
| 兩者並用互參 | 同向＝信心高；分歧＝回現實錨定再判 | — |

## 三、流程

引導聚焦（`questioning.md`）→ 起卦 → 取用神／體用 → 讀盤面（卦辭、動爻爻辭照抄）→ 交叉 → 白話直答。

```bash
VENV=python3   # 零安裝，依賴已內嵌
$VENV scripts/yijing/divine.py --random          # 六爻（時間=系統現在；--time 指定實際起卦時刻）
$VENV scripts/yijing/meihua.py                    # 梅花（預設時間起卦=系統現在；亦可 --numbers／--random）
```

## 四、本軸檔案

- `questioning.md`：起卦前引導（適不適合起卦、怎麼問、六爻 vs 梅花）
- `liuyao.md`：六爻解讀流程＋盤面欄位意義＋各領域該回答什麼
- `yongshen.md`：用神對照表＋六親／六神含義＋斷卦要點
- `meihua.md`：梅花讀盤（本／互／變、體用生剋、盤面欄位）
