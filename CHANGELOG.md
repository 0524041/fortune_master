# Changelog

本 repo 版本以 git tag 標記（語意化版號）。

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
