# 八字取格參考 (數值以 bazi_pai.py JSON 為準)

> 雙胞胎（同性）：**時柱進位**（子平法），用 `cast.py --twin-order N` 或 `bazi_pai.py --twin-order N`；細節見 `twins.md`。

0. 逐柱本質 (`pillars[]`)：`nayin` 納音、`dishi` 長生十二運、`shishen_zhi` 支十神、`hidden_shishen` 藏干十神、`xunkong` 旬空。四柱外 `extras`：胎元/胎息/命宮/身宮。`--year` 另出 `liunian.liuyue[12]`（五虎遁流月＋十神）。全走 lunar_python，禁心算。
0b. 大運起運數至**節**（非中氣），3天折1年，數值以 `dayun` 的 `age/years/start_solar/base_jieqi` 為準。
0c. 格局/用神/神煞直接讀 JSON：`geju`（月令取格＋`evidence`/`breaking`）、`yongshen`（`primary/xi/ji` 為扶抑；`tiaohou` 為窮通寶鑑調候，見 `references/ask-person/tiaohou.md`）、`shensha.found`（僅參考）。禁自創格局名、禁心算調候。
0d. 校驗：`verification.checks` 四項須全過；`verification.warnings` 有值即標低置信。`ziwei_full` 的 `warnings` 同理。
1. 身強弱：直接讀 `day_strength` (`score/level/xi/ji`)，規則見 JSON `rule` 欄。禁另行心算。注意：五行分高≠身強 (例盤A木40但月令失令，評分-3判中和)。
2. 取格：月支藏干透出者為格 (如甲申月透庚為七殺格, 透壬為偏印格)。不透則取月支本氣。
3. 用神：先取 `yongshen.xi/ji`（扶抑）初判，再合 `yongshen.tiaohou`（窮通寶鑑調候，`references/ask-person/tiaohou.md`）與格局細修。寒暖偏枯之局調候權重提高。寫明 `扶抑用神X / 調候用神Y, 忌神Z`。
4. 看大運流年：大運干支是否補用神或犯忌神 + 與原局合沖 (見 `relations`)。如用神木, 逢申酉金運即官殺剋身。
5. 講全四要素就好 (順序自由)：格局名、成立條件 (透干/月令)、用忌、大運轉折點。
