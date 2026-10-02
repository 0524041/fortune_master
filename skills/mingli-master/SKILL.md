---
name: mingli-master
description: |
  命理大師總控. 多流派多功能：八字、紫微斗數、易經六爻、梅花易數，含合盤、擇日、流年運限、神煞調候。排盤算數全走腳本(不心算)，多法交叉驗證後鐵口直斷。
  觸發: 算命/命盤/排盤/八字/紫微/斗數/格局/用神/調候/身強弱/大運/流年/流月/流日/小限/神煞/合盤/合婚/感情婚姻/擇日/入宅/開業/動土/起卦/卜卦/算卦/解卦/占卜/六爻/金錢卦/文王卦/易經/梅花易數/卦象/感情/事業/財運/健康/考試/失物/農曆/國曆/時辰/真太陽時/時辰校正.
  陽宅風水走 fengshui.skill (本 skill 不含); 單事隨機占卜走本 skill 的六爻/梅花.
license: MIT
compatibility: 需 python3 與 Node.js>=18/npm；首次執行 bash scripts/setup.sh 安裝依賴 (lunar_python 與 iztro)。缺 node 時紫微不可用，其餘（八字/六爻/梅花/擇日）仍可跑。
metadata:
  version: 0.2.1
  author: willywu (0524041)
  repository: https://github.com/0524041/fortune_master
---

# 命理大師 (總控：排盤算數歸腳本，知識解讀歸 references，多法交叉驗證)

一句話：**命＝排盤（八字＋紫微交叉）；事＝起卦（六爻／梅花，隨機）；合盤、擇日另走。**
全域決策樹與交叉驗證 SOP 見 `references/workflow.md`（動手前先讀）。

## 環境（首次使用）

```bash
bash scripts/setup.sh   # 建 Python venv（lunar_python pin 版）+ npm install Node 依賴（紫微引擎）
```
需要 `python3` 與 `node`(>=18)／`npm`。**缺 node 時紫微不可用**，其餘（八字/六爻/梅花/擇日）仍可跑。

## 收料（一次問 1-2 項）

出生**年月日時分、性別、出生城市**（或經度）。**曆制（國曆／農曆，閏月）未確認前不排盤**——先問清，再跑（`scripts/*` 支援 `--calendar lunar [--leap]`）。問事另需**實際起卦時間**。缺資料就標「未驗」，不腦補。

## 路由表

| 意圖 | 跑什麼 | 按需讀 |
|---|---|---|
| 算命／看命盤 | `scripts/cast.py`（一次出八字＋紫微＋初步交叉檢查） | `methods/bazi_geju.md`、`methods/ziwei_geju.md`、`schools/ni_mind.md` |
| 八字細節 | `scripts/bazi_pai.py`（真太陽時＋四柱＋納音/長生/十神支/旬空＋胎元命宮身宮＋身強弱＋格局/用神/神煞＋大運＋校驗；`--year` 出流年＋12流月） | `methods/bazi_geju.md`；調候 `knowledge/tiaohou.md` |
| 紫微細節 | `scripts/ziwei_full.sh`（十二宮＋全量格局＋本命/大限/流年四化；引擎內嵌 `scripts/vendor/ziwei/`） | `methods/ziwei_geju.md`；單星 `knowledge/star_detail.md`；流派 `schools/ni_mind.md` |
| 流年運限 | `scripts/ziwei_full.sh --at YYYY-MM-DD`（大限/小限/流年/流月/流日/流時六層） | `methods/ziwei_geju.md` 運限節 |
| 算事・六爻 | 起卦 `scripts/yijing/toss_coins.py` → 排盤 `scripts/yijing/divine.py` | **先讀 `yijing/questioning.md`**；解卦 `yijing/interpretation.md`、`yijing/yongshen.md`；卦辭 `data/hexagrams_64.json` |
| 算事・梅花 | `scripts/yijing/meihua.py`（時間／數字／隨機起卦） | **先讀 `yijing/questioning.md`**；`yijing/meihua.md` |
| 合盤／合婚 | 各跑兩份排盤 → `scripts/hepan_check.py` | `methods/hepan_ni.md`；夫妻星 `knowledge/fuqi_stars.md` |
| 擇日 | `scripts/zeri_pick.py`（通書→個人→紫微三層掃描） | `methods/zeri.md` |
| 陽宅風水 | 轉 `fengshui.skill`（本 skill 不含） | — |

> **起卦鐵則**：問題不明確先引導，勿急起卦（`yijing/questioning.md`）；一次只問一件事、記實際起卦時間。
> **紫微流派**：南派（三合）為體、北派（四化）為用、飛星細節僅參考（`schools/ni_mind.md`）。

## 命令

```bash
VENV=./scripts/.venv/bin/python        # 首次: bash scripts/setup.sh (venv 已含 lunar_python, 供八字/六爻/梅花/擇日共用)
$VENV scripts/cast.py --date 1990-08-18 --time 06:30 --city 台北 --gender male --at 2026-06-15   # 雙盤+交叉檢查
$VENV scripts/cast.py --calendar lunar --date 1990-07-28 --time 06:30 --city 台北 --gender male  # 農曆出生 (閏月加 --leap)
$VENV scripts/bazi_pai.py --date 1990-08-18 --time 06:30 --city 台北 --gender male --year 2026 --format json
./scripts/ziwei_full.sh --date 1990-08-18 --hour 卯 --gender male --at 2026-06-15 --format json
$VENV scripts/yijing/divine.py --random --time "2026-08-01 10:30"        # 六爻
$VENV scripts/yijing/meihua.py --time "2026-08-01 10:30"                 # 梅花
$VENV scripts/hepan_check.py --a-bazi A.json --a-ziwei Az.json --b-bazi B.json --b-ziwei Bz.json --format json
$VENV scripts/zeri_pick.py --matter 嫁娶 --from 2026-10-01 --to 2026-12-31 --bazi A.json --ziwei Az.json --top 10
```

## 交叉驗證（鐵口的前提）

定盤 → 命內 → 環境 → 事占，四步見 `references/workflow.md` 與 `methods/fuyan.md`：
兩盤時支一致、`verification.checks` 全過、`warnings` 為空 → 高置信；八字用神調候與紫微格局四化同向 → 加權。
衝突一律寫「矛盾未解」，寧可少斷。

## 紅線（準確性）

1. 數字照抄 JSON（年份用 `years`、調候用 `yongshen.tiaohou`）；格局名／卦名用程式判定的，不自創。
2. 校驗未過或有 `warnings` 即標低置信；兩盤時支不一致退回重定盤。
3. 不確定明說。腔調見 `knowledge/voice.md`，對外用語邊界見 `knowledge/output_style.md`。
