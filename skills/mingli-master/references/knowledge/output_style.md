# 對外用語邊界 (只擋外洩，不管排版)

## 一、中文名對照 (寫給人看時用中文)

- bazi_pai.py → 八字排盤程式；ziwei_full.sh → 紫微排盤程式
- hepan_check.py → 合盤比對程式；zeri_pick.py → 擇日掃描程式；divine.py → 六爻起卦程式；meihua.py → 梅花起卦程式；cast.py → 雙盤排盤程式
- patterns[] → 格局判定結果；fuqi_stars → 夫妻宮斷語表；tiaohou.json → 調候用神表；JSON數據 → 排盤數據
- 不寫：英文檔名、函數名、`[]`/`->`程式符號、本機路徑、過程口令。

## 二、數字用法 (準確性，唯一硬規則)

年份、干支、分數照抄 script 輸出 (`years` 欄)，不心算。
如：戊午運31-40歲 (2020-2029年走戊午運)。

## 三、排版自由

表格、粗體、標題、列表、引文儘管用，lint 只檢查第一節那四類外洩，不管格式。
開發時可用 `scripts/output_lint.py --text-file` 抽查，不必每 turn 跑；`--strict` 另驗空泛語／巴納姆／免責濫用（判準見 `pan_output.md`）。
