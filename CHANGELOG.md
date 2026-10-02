# Changelog

本 repo 版本以 git tag 標記（語意化版號）。

## v0.5.1

- **主軸更明確（治分流不穩）**：`SKILL.md` 主軸改為「命＝人的常數（看生日、長期不變）／卜＝事的變數（看當下起卦、一事一卦、事畢卦止）」＋三秒判準＋**同主題雙問法對照表**（財／感情／事業／健康／官司）；補混合題規則與「交錯使用、取其意不取其名」。分流表加「先問到什麼」（問人：生日時分／性別／城市／曆制；問事：一事一問＋題型）。
- **輸出品質拉回常駐**：`SKILL.md` 常駐「輸出四條」——先直答／每句掛依據／能給應期就給／禁模糊（可能也許大概較像）與萬用話。`shared/output-quality.md` 同步明文禁模糊斷語，並補**占卜版反巴納姆對照**（氛圍話→具體象）。
- **取象題 SOP**：`liuyao.md` 分題型（成敗／時機／取象）＋六親六神取象規則（子孫＝飲食、父母＝場所訊息、兄弟＝第三人分帳…）＋「兩法交叉要綜合（同向／分歧）」；`meihua.md`、`questioning.md`、`ask-event/_index.md` 同步（起卦前先確認題型）。
- **時間依據原理**：問事以「**心動即占**」為前提，當下時間即時空氣場座標；**梅花**時間起卦＝農曆年支＋月＋日＋時支（程式換算），**六爻**以月建／日辰為旺衰背景（卦象來自搖卦，手搖優先）。起卦用當地時鐘、**不做真太陽時校正**；子時／整點交界記精確分鐘。依據優先序：心動＞銅錢＞外應報數＞當下時間。
- 測試：**100 條**（新增梅花農曆換算、六爻含時柱兩個回歸測試）。

## v0.5.0

- **易經補料**：六爻盤面新增【動爻爻辭】（底本《周易正義》武英殿十三經注疏本；64 卦×6 爻＋乾坤用九用六；新資料檔 `data/yaoci_64.json`，逐卦鎖定維基文庫 oldid、回讀原頁並跨來源校對）；無動爻時明示依月日旺衰／世應／用神推斷，不以「無動爻」當無訊號。梅花盤面補本卦／互卦／變卦的卦辭、象傳、諸事，並算好互卦／變卦對體的生剋疊加（不再讓 AI 心算）。
- **輸出品質統一**：`pan_output`＋`voice`＋`output_style` 合併為 `references/shared/output-quality.md`（先直答、每句掛依據、能給應期就給、反巴納姆、白話少反轉）。移除強制投資免責、健康就醫、翻轉條件與輸出格式模板；免責與健康提醒改由 agent 自行斟酌。
- **結構重整（按需載入）**：`references/` 改按軸分 `ask-person/`（八字／紫微／合盤／擇日／財運）、`ask-event/`（六爻／梅花／用神／起卦前引導）、`shared/`（輸出品質／交叉驗證／術語）；各軸新增 `_index.md` 入口。`workflow`＋`fuyan` 合併為 `shared/verification.md`。`SKILL.md` 由 82 行瘦身至 39 行，只留主軸（問人／問事）、分流、環境、3 條準確性強約束。
- 測試：98 條（新增爻辭完整性、動爻爻辭輸出、靜卦提示、梅花補料與五行疊加）。

## v0.4.2

- **修正「講了跟沒講一樣」**：命盤／流年新增輸出模板 `references/knowledge/pan_output.md`（定調→依據→應期→動作→翻轉），並把「結論先行、必給應期與可執行動作、禁巴納姆」寫進常駐層 `SKILL.md` 紅線。
- **免責收窄**：投資免責只限六爻／梅花**起卦問投資**；命盤／流年財運題不挾帶「不構成投資建議」。
- **新增財運 SOP** `references/methods/caiyun.md`：來源→守財→應期三問，串接紫微財務四宮與八字任財。
- `scripts/output_lint.py` 加 `--strict`：另驗空泛語／巴納姆／免責濫用（預設不變，向後相容）。
- 測試：新增 strict lint 案（共 93 條）。

## v0.4.1

- 六爻／梅花起卦**時間預設系統現在**（現在問＝現在起卦），不再要求使用者先給時間；`--time` 保留給「使用者提供實際起卦時刻」。
- `meihua.py` 無參數即時間起卦（系統現在）；`divine.py` 本已預設系統現在。
- 文件（SKILL.md / workflow / questioning）同步。

## v0.4.0

- **零安裝**：內嵌 `scripts/vendor/lunar_python`（純 Python、MIT、1.0M）與 `scripts/ziwei_full.bundle.mjs`（esbuild 打包 iztro/lunar-javascript、MIT、~880K）。**執行期只需系統 `python3` + `node`，免 pip/npm/venv。**
- 所有 Python 腳本改由 `scripts/vendor` 匯入 lunar_python；`cast.py` 改用當前 Python 直呼子工具。
- `ziwei_full.sh` 優先跑預打包 bundle（純 `node`），找不到才退回 tsx（開發）。
- `check_env.sh` 改檢查 python3／node／內嵌依賴；`setup.sh` 改為**開發用**（重建 vendor 與 bundle）。
- 測試：新增零安裝驗證（系統 python3 跑八字、純 node 跑 bundle）；共 90 條。

## v0.3.0

- 新增 `scripts/check_env.sh`：唯讀環境檢查（python3 / Node.js>=18 / npm / venv+lunar_python / node_modules），列出缺項並回傳退出碼。
- `scripts/setup.sh` 強化：硬性檢查 python3 與 Node.js>=18/npm（缺 node 直接失敗）；冪等（已裝則跳過）；結尾自動跑 `check_env.sh` 驗證。
- `scripts/ziwei_full.sh`：缺 `node_modules` 時給明確指引（不自動安裝）。
- SKILL.md / README 明示：**安裝外掛不會自動裝依賴**，首次使用前必須跑 `setup.sh`。
- 測試：新增 `test_check_env_passes_when_set_up`（共 87 條）。

## v0.2.2

- README 補 Codex 外掛安裝（Codex 讀 `.claude-plugin/marketplace.json`）與本地來源的肥大快取注意事項。
- 實測驗證：`codex plugin marketplace add` → `codex plugin add mingli-master@fortune-master` 安裝成功，`codex exec` 的 skill 清單出現 `mingli-master:mingli-master`；確認 Codex 可載入本 skill（無需另做 Codex 專屬外掛）。

## v0.2.1

- README 補各 agent 的安裝設定（Claude Code 外掛／skill、OpenCode、Codex、Pi、Gemini CLI、其他 agentskills.io 工具），附驗證方法。
- 驗證：`claude plugin validate`（marketplace 與 plugin 皆 passed）；`gemini skills list` 顯示 `mingli-master [Enabled]`；frontmatter 符合 OpenCode/Pi 限制（name 合規、description 286 字 ≤ 1024）。

## v0.2.0

- 發佈包裝：加入 Claude Code 外掛市集（`.claude-plugin/marketplace.json`）與外掛 manifest（`skills/mingli-master/.claude-plugin/plugin.json`），同時相容 Agent Skills 開放標準與 OpenCode 等。
- `SKILL.md` frontmatter 補上規格欄位：`license`、`compatibility`、`metadata`（version/author/repository）。
- README 補跨工具安裝矩陣（Claude Code 外掛／Claude、OpenCode、Codex `.agents/skills`）。
- `setup.sh` 有 lock 時改用 `npm ci`（依賴可重現）；`package-lock.json` 入版控。

## v0.1.0

首個版本。`mingli-master` skill：

- **八字**：真太陽時、四柱、納音/長生/十神支/旬空、胎元/胎息/命宮/身宮、身強弱、格局（月令取格）、用神（扶抑＋窮通寶鑑 120 格調候）、神煞、大運、校驗、流年＋12 流月。
- **紫微斗數**（南派三合為體、北派四化為用）：十二宮、全量格局、本命/大限/流年四化、運限六層（大限/小限/流年/流月/流日/流時）。
- **易經**：六爻（起卦＋排盤＋解卦 SOP）、梅花易數（時間/數字/隨機起卦、體用生剋）。
- **合盤**（8 項比對＋參考分）、**擇日**（通書→個人→紫微三層掃描）。
- 曆制支援：國曆/農曆（＋閏月）。
- 架構：排盤歸腳本、知識歸 `references/`、共用表歸 `data/`（單一真相）；86 條回歸測試。
- 已知發現並修正：八字大運起運由「中氣」改為「節」（原誤差 6 年）。
