# 紫微解讀 (全量 patterns, 與 repo 同口徑)

> 流派定位見 `references/schools/ni_mind.md`「紫微斗數流派定位」：**南派（三合）為體、北派（四化）為用、飛星細節為參考**。

- 盤面以 `scripts/ziwei_full.sh --format both` JSON 為準，`patterns[]` 30+格全量來自 `scripts/vendor/ziwei/patterns.ts detectPatterns`（內嵌快照，見 vendor README）。
- 只認 `required` 全滿足才成立；`bonus` 加分、`breaking` 有一即降級並明說，不硬撐大格。
- 四化：本命年干固定 (`sihua.ts getSiHuaByStem`)；大限看宮干 (`getDaXianSiHua`)、流年看年干 (`getLiuNianSiHua`) 疊加。不主斷宮干自化/來因宮，那是 `feixing_ref` 參考。運限 (`--at`) 六層四化由 iztro `horoscope()` 產生，與 vendor 四化表逐年干互校（測試把關）。
- 化忌必指宮位應事；夫妻必兼看福德；官祿喜權、財帛喜祿。
- 單星套 `references/knowledge/star_detail.md`；合盤走 `references/methods/hepan_ni.md` 五步；話術走 `references/schools/ni_mind.md`。

## 運限 (`--at`)

`--at YYYY-MM-DD` 出六層：大限→小限→流年→流月→流日→流時。每層欄位 `ganzhi/palace/branch/mutagen/palaces[]`（+ 流耀 `stars`，流年另有 `dec_star` 將前/歲前十二神）。

- `palaces[]` 是該層十二宮重排，`scope`=運限宮名、`native`=本命宮名、`branch`=地支；`index` 對應本命宮序。
- **分界**：iztro 預設 `divide=normal`（正月初一）；`--horoscope-divide exact` 改立春。與八字（一律立春）在年初/年末會差一輪，近立春須看 `divide` 標示。
- 流時由 `--at-time HH:MM`（預設 12:00 午時）決定；流時命宮不直接等於時支。
- 立場：運限四化疊本命看節點是三合正統，要用；流耀（運/流/月/日/時星）為輔助參考，不主斷。
