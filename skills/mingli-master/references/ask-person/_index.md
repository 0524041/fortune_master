# 問人（命理）入口

> 問「這個人的方向」都走這裡。**以命盤為準**：八字＋紫微交叉。
> 輸出怎麼說見 `references/shared/output-quality.md`；驗證見 `references/shared/verification.md`。
> 別拿命盤算「明天這檔漲不漲」——那是問事（`references/ask-event/`）。

## 一、先收料（一次問 1–2 項，別連環砲）

- 出生**年月日時分**、**性別**、**出生城市**（或經度）。
- **曆制**：國曆還是農曆（農曆要問閏月）——**未確認前不排盤**。
- **雙胞胎／多胞胎**：先問同性別或龍鳳胎、排行、時間差——見 `twins.md`（借宮立極／時辰遞推／北派同盤／八字時柱進位）。
- 缺資料標「未驗」，不腦補。

## 二、怎麼選（依問題）

| 問什麼 | 跑什麼 | 讀什麼 |
|---|---|---|
| 總覽：性格／格局／一生方向 | `scripts/cast.py`（一次出八字＋紫微＋初步交叉） | **主軸 `pan-reading.md`**＋`bazi.md`＋`ziwei.md`＋`ni_mind.md` |
| 八字細節／流年 | `scripts/bazi_pai.py`（`--year` 出流年＋12 流月） | `bazi.md`；調候 `tiaohou.md` |
| 紫微細節／運限 | `scripts/ziwei_full.sh`（`--at YYYY-MM-DD` 出運限六層） | `ziwei.md`；單星 `star_detail.md` |
| 財運／財富 | 財帛＋田宅＋官祿＋財星（雙盤交叉） | `caiyun.md` |
| 合盤／合婚 | 兩人各排盤 → `scripts/hepan_check.py` | `hepan.md`＋`fuqi_stars.md` |
| 擇日（嫁娶／入宅／開業／動土） | `scripts/zeri_pick.py` | `zeri.md` |

## 三、流程

收料（含曆制）→ 排盤 → 讀對應知識 → 雙盤交叉（`shared/verification.md`）→ 白話綜合輸出。

```bash
VENV=python3   # 零安裝，依賴已內嵌
$VENV scripts/cast.py --date 1990-08-18 --time 06:30 --city 台北 --gender male --at 2026-06-15
$VENV scripts/cast.py --calendar lunar --date 1990-07-28 --time 06:30 --city 台北 --gender male  # 農曆（閏月加 --leap）
$VENV scripts/bazi_pai.py --date 1990-08-18 --time 06:30 --city 台北 --gender male --year 2026 --format json
./scripts/ziwei_full.sh --date 1990-08-18 --hour 卯 --gender male --at 2026-06-15 --format json
```

## 四、本軸檔案

- 技法：`pan-reading.md`（**解盤主軸**）、`bazi.md`、`ziwei.md`、`caiyun.md`、`hepan.md`、`zeri.md`
- 配套：`tiaohou.md`（調候用神）、`star_detail.md`（單星）、`fuqi_stars.md`（夫妻宮斷語）、`ni_mind.md`（流派立場：南派為體、北派四化為用）、`twins.md`（雙胞胎／多胞胎處理）
- 範例：`examples/`（八字、合盤、擇日）
