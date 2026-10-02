#!/usr/bin/env bash
# 命理 skill 環境安裝：建立自帶虛擬環境並安裝 pin 版依賴 (八字/六爻/梅花/擇日共用)
# 用法: bash scripts/setup.sh   (在 skill 根目錄或任意目錄執行皆可)
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${SKILL_DIR}/scripts/.venv"
PYTHON_BIN="${VENV_DIR}/bin/python"

echo "==> 建立虛擬環境: ${VENV_DIR}"
if [ ! -d "${VENV_DIR}" ]; then
    python3 -m venv "${VENV_DIR}"
fi

echo "==> 安裝依賴 (見 scripts/requirements.txt)"
"${PYTHON_BIN}" -m pip install --quiet --upgrade pip
"${PYTHON_BIN}" -m pip install --quiet -r "${SKILL_DIR}/scripts/requirements.txt"

echo "==> 驗證安裝"
"${PYTHON_BIN}" -c "import lunar_python; print('lunar_python OK')"
"${PYTHON_BIN}" -m pytest --version >/dev/null && echo "pytest OK"

echo "==> 安裝 Node 依賴 (紫微引擎 iztro / lunar-javascript / tsx)"
if command -v npm >/dev/null 2>&1; then
    if [ -f "${SKILL_DIR}/scripts/package-lock.json" ]; then
        ( cd "${SKILL_DIR}/scripts" && npm ci --silent )
    else
        ( cd "${SKILL_DIR}/scripts" && npm install --silent )
    fi
    echo "   node deps OK ($(node -v 2>/dev/null || echo 'node?'))"
else
    echo "   ⚠ 找不到 npm：紫微排盤 (ziwei_full.sh) 需要 Node.js + npm。"
    echo "     請安裝 Node.js (>=18) 後重跑本腳本；八字/六爻/梅花/擇日不受影響。"
fi

echo "==> 完成。使用方式："
echo "    ${VENV_DIR}/bin/python ${SKILL_DIR}/scripts/cast.py --date 1990-08-18 --time 06:30 --city 台北 --gender male   # 雙盤"
echo "    ${VENV_DIR}/bin/python ${SKILL_DIR}/scripts/yijing/meihua.py --time \"2026-08-01 10:30\"                      # 梅花"
