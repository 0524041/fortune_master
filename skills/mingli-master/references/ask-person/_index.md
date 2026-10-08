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
| 總覽：性格／格局／一生方向 | `scripts/person_cast.py`（一次出八字＋紫微＋六壬終身課＋奇門終身盤） | **主軸 `pan-reading.md`**＋`bazi.md`＋`ziwei.md`＋`ni_mind.md`＋**`aux-charts.md`** |
| 總覽（輕量，不含輔助盤） | `scripts/cast.py`（只有八字＋紫微＋初步交叉） | `pan-reading.md` |
| 八字細節／流年 | `scripts/bazi_pai.py`（`--year` 出流年＋12 流月） | `bazi.md`；調候 `tiaohou.md` |
| 多年運／時間窗（前五年後五年） | `scripts/decade.py`（`--from A --to B`，一年一行：八字流年＋紫微運限） | `pan-reading.md` 步驟 7；**禁逐年迴圈呼叫引擎** |
| 紫微細節／運限 | `scripts/ziwei_full.sh`（`--at YYYY-MM-DD` 出運限六層） | `ziwei.md`；單星 `star_detail.md` |
| 財運／財富 | 財帛＋田宅＋官祿＋財星（雙盤交叉） | `caiyun.md` |
| 合盤／合婚 | 兩人各排盤 → `scripts/hepan_check.py` | `hepan.md`＋`fuqi_stars.md` |
| 擇日（嫁娶／入宅／開業／動土） | `scripts/zeri_pick.py`（`--hours` 出吉時） | `zeri.md` |
| 單日黃曆全資訊／吉時 | `scripts/tongshu_day.py`（日層＋十二時辰＋可選八字/奇門） | `zeri.md` 第七節 |

## 三、流程

收料（含曆制）→ 排盤（總覽一律 `person_cast.py`，含輔助盤）→ 讀對應知識 → 主盤×輔助盤交叉（`aux-charts.md`＋`shared/verification.md`）→ 白話綜合輸出。

> 只有使用者明確說「不用輔助盤」或只需要單一細節（流月、單星、合盤、擇日），才改用 `cast.py`／`bazi_pai.py`／`ziwei_full.sh` 等單一腳本。

```bash
VENV=python3   # 零安裝，依賴已內嵌
$VENV scripts/person_cast.py --date 1990-08-18 --time 06:30 --city 台北 --gender male --at 2026-06-15  # 總覽預設：主盤＋六壬/奇門輔助盤
$VENV scripts/cast.py --date 1990-08-18 --time 06:30 --city 台北 --gender male --at 2026-06-15  # 輕量：只有八字＋紫微
$VENV scripts/cast.py --calendar lunar --date 1990-07-28 --time 06:30 --city 台北 --gender male  # 農曆（閏月加 --leap）
$VENV scripts/bazi_pai.py --date 1990-08-18 --time 06:30 --city 台北 --gender male --year 2026 --format json
$VENV scripts/decade.py --date 1990-08-18 --time 06:30 --city 台北 --gender male --from 2021 --to 2030  # 多年運總表（禁逐年迴圈）
./scripts/ziwei_full.sh --date 1990-08-18 --hour 卯 --gender male --at 2026-06-15 --format json
$VENV scripts/zeri_pick.py --matter 入宅 --from 2026-10-01 --to 2026-12-31 --bazi a.json --hours --qimen  # 擇日＋吉時
$VENV scripts/tongshu_day.py --date 2026-10-08 --bazi a.json --qimen  # 單日黃曆全資訊
```

## 四、本軸檔案

- 技法：`pan-reading.md`（**解盤主軸**）、`bazi.md`、`ziwei.md`、`caiyun.md`、`hepan.md`、`zeri.md`
- **輔助盤：`aux-charts.md`（六壬終身課＋奇門終身盤；主盤為骨幹、輔助補維度、不翻轉）**
- 八字進階：`shenqiang.md`（身強弱三得）、`shishen_combo.md`（十神組合）、`waige.md`（從格專旺）、`suiyun.md`（大運流年）、`shensha_use.md`（神煞三鎖）、`taimingshen.md`（胎命身）、`dizhi_relations.md`（刑害分工）
- 紫微進階：`fusha.md`（輔煞夾宮四化）
- 配套：`tiaohou.md`（調候用神＋實戰四步）、`star_detail.md`（單星）、`fuqi_stars.md`（夫妻宮斷語）、`ni_mind.md`（流派立場與口述整理降級標註）、`twins.md`（雙胞胎／多胞胎處理）
- 範例：`examples/`（八字、合盤、擇日）
