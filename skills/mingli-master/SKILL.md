---
name: mingli-master
description: |
  命理大師：問人（八字＋紫微交叉）與問事（六爻＋梅花交叉）兩軸。排盤算數全走腳本(不心算)，知識按需載入，多法交叉後白話直說。
  觸發: 算命/命盤/排盤/八字/紫微/斗數/格局/用神/調候/身強弱/大運/流年/流月/流日/小限/神煞/合盤/合婚/感情婚姻/擇日/入宅/開業/動土/起卦/卜卦/算卦/解卦/占卜/六爻/金錢卦/文王卦/易經/梅花易數/卦象/感情/事業/財運/健康/考試/失物/農曆/國曆/時辰/真太陽時/時辰校正.
  陽宅風水走 fengshui.skill (本 skill 不含).
license: MIT
compatibility: 零安裝。只需系統 python3 與 Node.js>=18；依賴 (lunar_python 與 iztro) 已內嵌於 scripts/vendor 與 ziwei_full.bundle.mjs，不需 pip/npm/venv。用 bash scripts/check_env.sh 檢查。
metadata:
  version: 0.5.0
  author: willywu (0524041)
  repository: https://github.com/0524041/fortune_master
---

# 命理大師

## 主軸（唯一分流：問人 or 問事）

- **問人（命理）**：問「這個人的方向」——性格、格局、大運、流年、合婚、擇日。**以命盤為準**（八字＋紫微交叉）。
- **問事（占卜）**：問「這件事的走向」——成敗、時機、細節、尋物、官司。**以卦象為準**（六爻＋梅花，隨機起卦、一事一卦、事畢卦止）。
- **誤用擋門**：別拿命盤算「明天這檔漲不漲」（那是問事）；別拿一卦算「我一輩子賺多少」（那是問人）。
- 分類不明先問一句：「你要看**一生的命**，還是**一件具體的事**？」

## 分流（只讀你這一軸）

| 使用者在問 | 入口 | 引擎 |
|---|---|---|
| 人：命、運、合婚、擇日 | `references/ask-person/_index.md` | 八字／紫微／合盤／擇日 |
| 事：成敗、時機、尋物、官司 | `references/ask-event/_index.md` | 六爻／梅花 |

## 環境（零安裝）

`bash scripts/check_env.sh` → 應顯示「環境就緒 ✅」。python3（八字／六爻／梅花／擇日）、node>=18（紫微）；依賴已內嵌，免 pip／npm／venv。

## 強約束（常駐，只放不能忘的）

1. 算數歸 script，**不心算**；數字、格局名、卦名、卦辭爻辭**照抄程式輸出**，不編造、不自創。
2. 收料**曆制（國曆／農曆閏月）未確認不排盤**；校驗未過或有 `warnings` 標低置信；問事**一事一問**、起卦時間預設現在。
3. **輸出品質統一**見 `references/shared/output-quality.md`（先直答、白話、少反轉、禁巴納姆）；交叉驗證見 `references/shared/verification.md`。各分支不重複寫。
