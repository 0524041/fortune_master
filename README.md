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

```bash
# 1) 連結到 agent 的 skills 目錄（Claude / OpenCode 皆讀 <skills-dir>/<name>/SKILL.md）
ln -s "$PWD/skills/mingli-master" ~/.config/opencode/skills/mingli-master

# 2) 安裝依賴（Python venv + Node）
bash skills/mingli-master/scripts/setup.sh
```

需要 `python3` 與 `node` (>=18)／`npm`。缺 node 時紫微不可用，其餘（八字/六爻/梅花/擇日）仍可跑。

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
├─ README.md  LICENSE  CHANGELOG.md  VERSION  .gitignore
└─ skills/
   └─ mingli-master/
      ├─ SKILL.md              # skill 入口（name/description）
      ├─ references/           # 知識與 SOP（按需讀）：schools/methods/knowledge/yijing/examples
      ├─ data/                 # 結構化表（干支/四化/神煞/調候/擇日規則/64卦/城市）
      ├─ scripts/              # 排盤：bazi_pai.py, ziwei_full.sh(+vendor), yijing/, hepan_check.py, zeri_pick.py, cast.py
      └─ tests/                # 回歸測試
```

## 測試

```bash
cd skills/mingli-master
bash scripts/setup.sh              # 首次
scripts/.venv/bin/python -m pytest -q
```

## 版本

見 `VERSION` 與 git tag（語意化版號，如 `v0.1.0`）。Agent Skill 規格本身無 version 欄位，版本以 tag 管理。

## 授權

[MIT](LICENSE)
