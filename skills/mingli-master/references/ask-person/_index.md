# 問人（命理）入口

> 問「這個人的方向」都走這裡。**以命盤為準**：八字＋紫微交叉。
> 輸出怎麼說見 `references/shared/output-quality.md`；驗證見 `references/shared/verification.md`。
> 別拿命盤算「明天這檔漲不漲」——那是問事（`references/ask-event/`）。

## 一、先收料（一次問 1–2 項，別連環砲）

- 出生**年月日時分**、**性別**、**出生城市**（或經度）。
- **曆制**：國曆還是農曆（農曆要問閏月）——**未確認前不排盤**。
- **雙胞胎／多胞胎**：先問同性別或龍鳳胎、排行、時間差——見 `twins.md`（借宮立極／時辰遞推／北派同盤／八字時柱進位）。
- 缺資料標「未驗」，不腦補。

## 二、怎麼選（依問題）— zongpan 分層入口

> 引擎一律走**分層**：先 `summary`（必讀摘要，含基本輸入），再按問題補細節。輸出全為 txt/md。
> 逐行解義見 `zongpan-spec.md`；互動與快取見 `references/shared/interaction.md`。
> 參數說明：`--date --time --city --gender` 四項所有子命令共用；`--calendar lunar --leap` 農曆；雙胞胎見 `twins.md`。

| 問什麼 | 先跑（消費） | 按需補（參數→結果） | 讀什麼 |
|---|---|---|---|
| 總覽：性格／格局／一生方向 | `zongpan.py summary`（3K：輸入/八字/大運/紫微/財官象/格局/大限/財語義/六壬/奇門/警示） | 不夠再 `ziwei --palaces 命宮,遷移,福德`（一宮一行） | **主軸 `pan-reading.md`**＋`bazi.md`＋`ziwei.md`＋**`zongpan-spec.md`**＋`aux-charts.md` |
| 八字細節／身強弱／用神 | `summary` | `bazi`（四柱藏干十神＋五行分＋三得＋用忌調候＋神煞合沖） | `bazi.md`＋`shenqiang.md`；調候 `tiaohou.md` |
| 流年／流月 | `summary` | `bazi --year 2029`（流年干支＋12流月十神） | `bazi.md` §0＋`suiyun.md` |
| 十年運／時間窗 | `summary` | `yun decade --from 2026 --to 2031`（一年一行總表）；`yun year 2029`（單年塊：八字歲運＋紫微運限；`--full` 加流月/流耀） | `suiyun.md`＋`pan-reading.md` §七 |
| 紫微細節／單宮 | `summary` | `ziwei --palaces 財帛,田宅,官祿,福德`（逗號列宮，只出該宮）；`ziwei --patterns`（格局真假：required/bonus/breaking） | `ziwei.md`＋`star_detail.md`＋`fusha.md` |
| 財運 | `summary`（財語義行） | `ziwei --palaces 財帛,田宅,官祿,福德` | `caiyun.md`（來源→守財→應期） |
| 合盤／合婚 | 兩人各 `summary`＋`ziwei` | 合盤比對（`hepan_check` 流程） | `hepan.md`＋`fuqi_stars.md` |
| 輔助盤：過程／方位 | `summary`（六壬/奇門各一行） | `aux liuren [--at-year 2029]`（終身課全文）；`aux qimen`（九宮＋大限每宮9年＋方位） | `aux-charts.md`＋`liuren.md` §十＋`qimen.md` |
| 擇日（嫁娶／入宅／開業／動土） | 本人 `summary`（取八字） | 擇日掃描（`zeri_pick` 流程，`--hours` 出吉時） | `zeri.md` |
| 單日黃曆／吉時 | — | 通書單日（`tongshu_day` 流程） | `zeri.md` 第七節 |

單一細節題（流月、單星、合盤、擇日）可直接跑對應子命令，不必先 summary；總覽題一律 summary 起手。

## 三、流程

收料（含曆制）→ `zongpan summary`（核對首行輸入）→ 判問項→按需子命令→讀對應知識 → 主盤×輔助盤交叉（`aux-charts.md`＋`shared/verification.md`）→ 白話綜合輸出。

```bash
VENV=python3   # 零安裝，依賴已內嵌
$VENV scripts/zongpan.py summary --date 1998-01-05 --time 15:57 --city 台南 --gender male --at 2026-10-08 --year 2026
$VENV scripts/zongpan.py bazi --date … --time … --city … --gender male --year 2029
$VENV scripts/zongpan.py ziwei --date … --time … --city … --gender male --palaces 財帛,田宅,官祿,福德
$VENV scripts/zongpan.py yun year 2029 --date … [--full]
$VENV scripts/zongpan.py yun decade --from 2026 --to 2031 --date …
$VENV scripts/zongpan.py aux liuren --date … [--at-year 2029]
$VENV scripts/zongpan.py aux qimen --date …
```

底層排盤程式（summary 內部會用、除錯才直接跑）：雙盤排盤程式、八字排盤程式、紫微排盤程式、多年運程式。正常流程一律走 zongpan 子命令。

## 四、本軸檔案

- 技法：`pan-reading.md`（**解盤主軸**）、`bazi.md`、`ziwei.md`、`caiyun.md`、`hepan.md`、`zeri.md`
- **輔助盤：`aux-charts.md`（六壬終身課＋奇門終身盤；主盤為骨幹、輔助補維度、不翻轉）**
- 八字進階：`shenqiang.md`（身強弱三得）、`shishen_combo.md`（十神組合）、`waige.md`（從格專旺）、`suiyun.md`（大運流年）、`shensha_use.md`（神煞三鎖）、`taimingshen.md`（胎命身）、`dizhi_relations.md`（刑害分工）
- 紫微進階：`fusha.md`（輔煞夾宮四化）
- 配套：`tiaohou.md`（調候用神＋實戰四步）、`star_detail.md`（單星）、`fuqi_stars.md`（夫妻宮斷語）、`ni_mind.md`（流派立場與口述整理降級標註）、`twins.md`（雙胞胎／多胞胎處理）
- 範例：`examples/`（八字、合盤、擇日）
