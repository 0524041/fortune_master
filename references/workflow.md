# 總流程與路由 (命理大師主控)

一句定位：**排盤算數歸 script（不心算），知識解讀歸 references（按需讀），多法交叉驗證後才鐵口。**

## 一、意圖路由

| 使用者意圖 | 主要動作 | 按需讀 |
|---|---|---|
| 算命／看命盤（先天格局、個性、一生方向） | 跑 `bazi_pai.py` ＋ `ziwei_full.sh`，兩盤交叉 | `methods/bazi_geju.md`、`methods/ziwei_geju.md`、`schools/ni_mind.md` |
| 看某年運勢 | 紫微 `--at YYYY-MM-DD`（或八字 `--year`） | `methods/ziwei_geju.md` 運限節 |
| 問一件具體事（該不該、能不能、何時） | 起卦：六爻 `scripts/yijing/divine.py` 或梅花 `scripts/yijing/meihua.py` | `yijing/interpretation.md`、`yijing/yongshen.md`、`yijing/meihua.md` |
| 合盤／合婚 | 各跑兩份排盤 → `hepan_check.py` | `methods/hepan_ni.md`、`knowledge/fuqi_stars.md` |
| 擇日（嫁娶/入宅/開業/動土/安葬） | `zeri_pick.py` | `methods/zeri.md` |
| 陽宅風水 | 轉 `fengshui.skill`（本 skill 不含） | — |

分類不明時先問：**你是要看「一生的命」還是「一件具體的事」？** 命＝排盤；事＝起卦。

## 二、收料（一次問 1-2 項）

出生年月日時分、性別、出生城市（或經度）。**曆制必先問清**：國曆還是農曆？農曆要問閏月——未確認前**不排盤**（程式支援 `--calendar lunar [--leap]`）。
起卦另需**實際起卦時間**。不確定就標「未驗」，不腦補。

## 三、交叉驗證 SOP（定盤 → 命內 → 環境 → 事占）

詳見 `methods/fuyan.md`。要點：

1. **定盤**：兩盤年月日時是否一致；讀八字 `verification.checks`（須 `all_pass`）與兩盤 `warnings`；時支不一致就退回重定盤。
2. **命內**：八字 `geju`＋`yongshen`（扶抑＋`tiaohou`）vs 紫微 `patterns`＋四化，方向是否同向？記「一致／衝突」。
3. **環境**：有朝向入住年才查風水（外部 skill），否則記未驗。
4. **事占**：只問具體事才起卦；用卦中用神旺衰回頭挺/駁命盤結論。

輸出一律：**結論定性 + 宮星/干支依據 + 出處 + 置信度 + 翻轉條件**。多法同向＝置信高；衝突＝寫「矛盾未解」。

## 四、紅線（準確性）

1. 數字照抄 JSON（年份用 `years`、調候用 `yongshen.tiaohou`）；格局名用程式判定的，不自創。
2. 校驗未過或有 `warnings` 即標低置信，不硬斷。
3. 不確定明說。腔調見 `knowledge/voice.md`；用語邊界見 `knowledge/output_style.md`。
