# fortune_master

命理大師 **Agent Skill** 集合。目前含一個 skill：[`skills/mingli-master/`](skills/mingli-master/)。

## 這是什麼

`mingli-master` 是「命理大師總控」skill：

- **算命**：八字 ＋ 紫微斗數（**南派三合為體、北派四化為用**），雙盤交叉驗證。
- **算事（占卜）**：易經六爻、梅花易數（隨機起卦，起卦前先引導問題）。
- **合盤／合婚**、**擇日**。
- 排盤算數全走腳本（**不心算**），知識與解讀放 `references/`，共用表放 `data/`。
- 陽宅風水不在此 skill（走 `fengshui` skill）。

## 安裝

本 skill 同時是 **Claude Code 外掛**（`.claude-plugin/`）與**標準 Agent Skill**（`SKILL.md`，符合 [agentskills.io](https://agentskills.io) 開放標準）。先 clone，再選你的 agent：

```bash
git clone git@github.com:0524041/fortune_master.git
REPO="$PWD/fortune_master"
```

### 安裝依賴（所有 agent 都要，只需一次）

```bash
bash "$REPO/skills/mingli-master/scripts/setup.sh"
```

需要 `python3` 與 `node` (>=18)／`npm`。缺 node 時紫微不可用，其餘（八字/六爻/梅花/擇日）仍可跑。

### Claude Code

**外掛（建議，可自動更新）**——在 Claude Code 內：

```
/plugin marketplace add 0524041/fortune_master
/plugin install mingli-master@fortune-master
```

**或當個人／專案 skill**（不透過外掛）：

```bash
ln -s "$REPO/skills/mingli-master" ~/.claude/skills/mingli-master      # 個人（所有專案）
# 專案內：ln -s "$REPO/skills/mingli-master" .claude/skills/mingli-master
```

### OpenCode

```bash
ln -s "$REPO/skills/mingli-master" ~/.config/opencode/skills/mingli-master   # 全域
# 專案內：.opencode/skills/mingli-master
```

OpenCode 也會讀 `~/.claude/skills/` 與 `~/.agents/skills/` 這兩個相容別名。

### Codex（OpenAI）

Codex 有外掛系統，而且**讀得懂本 repo 的 `.claude-plugin/marketplace.json`**，可直接外掛安裝：

```bash
codex plugin marketplace add 0524041/fortune_master
codex plugin add mingli-master@fortune-master
codex plugin list        # 應顯示 mingli-master@fortune-master
```

或不經外掛、當一般 skill：

```bash
ln -s "$REPO/skills/mingli-master" ~/.agents/skills/mingli-master            # 使用者層
# 專案內：.agents/skills/mingli-master（Codex 會由 CWD 往上掃到 repo 根）
```

Codex 支援 symlink；用 `$mingli-master` 或 `/skills` 呼叫。
> 實測：外掛安裝後，`codex exec` 的 skill 清單會出現 `mingli-master:mingli-master`。
> 注意：用**本地路徑**加入市集時，Codex 會連 `.venv`/`node_modules` 一起複製（肥大）；用 **GitHub 來源**（如上）則乾淨。

### Pi

```bash
ln -s "$REPO/skills/mingli-master" ~/.agents/skills/mingli-master            # 或專案內 .agents/skills/
# 或直接用旗標載入：pi --skill "$REPO/skills/mingli-master"
```

用 `/skill:mingli-master` 呼叫。

### Gemini CLI

```bash
ln -s "$REPO/skills/mingli-master" ~/.gemini/skills/mingli-master            # 使用者層
# 專案內：.gemini/skills/mingli-master
```

或直接安裝：

```bash
gemini skills install https://github.com/0524041/fortune_master.git --path skills/mingli-master --consent
gemini skills list          # 確認列出 mingli-master
```

### 其他 Agent Skills 相容工具

任何實作 [agentskills.io](https://agentskills.io) 的工具（Cursor、Goose、Roo Code、OpenHands…），只要把它指向 `skills/mingli-master/`，或連到該工具的 skills 目錄即可；多數也吃 `.agents/skills/`（專案）與 `~/.agents/skills/`（使用者）。

### 驗證

- **Claude 外掛**：`claude plugin validate .` 與 `claude plugin validate ./skills/mingli-master` → 皆 `Validation passed`。
- **Codex**：`codex plugin marketplace add 0524041/fortune_master` → `codex plugin add mingli-master@fortune-master`；`codex plugin list` 應顯示該外掛，`codex exec` 的 skill 清單應含 `mingli-master:mingli-master`。
- **Gemini**：`gemini skills list` → 應列出 `mingli-master [Enabled]`。
- **通則**：`SKILL.md` 的 `name` 須等於資料夾名並符合 `^[a-z0-9]+(-[a-z0-9]+)*$`；`description` ≤ 1024 字（本 skill 符合，286 字）。

## 使用

完整說明見 [`skills/mingli-master/SKILL.md`](skills/mingli-master/SKILL.md)。常用：

```bash
V=skills/mingli-master/scripts/.venv/bin/python

# 雙盤（八字＋紫微）＋交叉檢查
$V skills/mingli-master/scripts/cast.py --date 1990-08-18 --time 06:30 --city 台北 --gender male
# 農曆出生（閏月加 --leap）
$V skills/mingli-master/scripts/cast.py --calendar lunar --date 1990-07-28 --time 06:30 --city 台北 --gender male
# 運限
skills/mingli-master/scripts/ziwei_full.sh --date 1990-08-18 --hour 卯 --gender male --at 2026-06-15
# 六爻／梅花
$V skills/mingli-master/scripts/yijing/divine.py --random --time "2026-08-01 10:30"
$V skills/mingli-master/scripts/yijing/meihua.py --time "2026-08-01 10:30"
```

## 結構

```
fortune_master/
├─ .claude-plugin/marketplace.json   # Claude Code 外掛市集目錄（列出本 repo 的外掛）
├─ README.md  LICENSE  CHANGELOG.md  VERSION  .gitignore
└─ skills/
   └─ mingli-master/                 # 既是 Agent Skill，也是 Claude 外掛
      ├─ .claude-plugin/plugin.json  # 外掛 manifest（name/version/license）
      ├─ SKILL.md                    # skill 入口（name/description/license/compatibility/metadata）
      ├─ references/                 # 知識與 SOP（按需讀）：schools/methods/knowledge/yijing/examples
      ├─ data/                       # 結構化表（干支/四化/神煞/調候/擇日規則/64卦/城市）
      ├─ scripts/                    # 排盤：bazi_pai.py, ziwei_full.sh(+vendor), yijing/, hepan_check.py, zeri_pick.py, cast.py
      └─ tests/                      # 回歸測試
```

## 測試

```bash
cd skills/mingli-master
bash scripts/setup.sh              # 首次
scripts/.venv/bin/python -m pytest -q
```

## 版本

- 頂層 `VERSION` 檔與 **git tag**（語意化版號，如 `v0.2.1`）。
- Skill 本身：`SKILL.md` 的 `metadata.version`（Agent Skills 規格無頂層 `version` 欄位，版本放 `metadata`）。
- 外掛：`skills/mingli-master/.claude-plugin/plugin.json` 的 `version`。

發新版：改 `VERSION` 與 `CHANGELOG.md`、同步上述版本欄位 → `git commit` → `git tag -a vX.Y.Z` → `git push --tags`。

## 授權

[MIT](LICENSE)
