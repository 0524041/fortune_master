# Changelog

本 repo 版本以 git tag 標記（語意化版號）。

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
