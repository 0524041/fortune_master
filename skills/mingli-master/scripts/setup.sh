#!/usr/bin/env bash
# 命理 skill 環境安裝：建立自帶虛擬環境並安裝 pin 版依賴
#   八字/六爻/梅花/擇日 共用 Python venv (lunar_python) + 紫微 Node 引擎 (iztro/tsx)
# 需 python3 與 Node.js>=18/npm（硬性）。冪等：已安裝的項目會跳過。
# 用法: bash scripts/setup.sh
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${SKILL_DIR}/scripts/.venv"
PYTHON_BIN="${VENV_DIR}/bin/python"

echo "==> 檢查前置需求 (硬性)"
command -v python3 >/dev/null 2>&1 || { echo "❌ 需要 python3，請先安裝。" >&2; exit 2; }
NODE_MAJOR="$(node -v 2>/dev/null | sed -E 's/^v([0-9]+).*/\1/')"
if [ -z "${NODE_MAJOR}" ] || [ "${NODE_MAJOR}" -lt 18 ] 2>/dev/null; then
    echo "❌ 需要 Node.js >=18（紫微引擎必需）。請安裝後重跑：https://nodejs.org" >&2
    exit 2
fi
command -v npm >/dev/null 2>&1 || { echo "❌ 需要 npm（隨 Node.js 安裝）。" >&2; exit 2; }
echo "   python3 / node $(node -v) / npm $(npm -v) OK"

echo "==> Python 環境"
if [ ! -x "${PYTHON_BIN}" ]; then
    echo "   建立虛擬環境: ${VENV_DIR}"
    python3 -m venv "${VENV_DIR}"
fi
if ! "${PYTHON_BIN}" -c 'import lunar_python' >/dev/null 2>&1; then
    echo "   安裝依賴 (scripts/requirements.txt)"
    "${PYTHON_BIN}" -m pip install --quiet --upgrade pip
    "${PYTHON_BIN}" -m pip install --quiet -r "${SKILL_DIR}/scripts/requirements.txt"
else
    echo "   lunar_python 已存在，跳過"
fi

echo "==> Node 環境 (紫微引擎)"
if [ ! -x "${SKILL_DIR}/scripts/node_modules/.bin/tsx" ]; then
    if [ -f "${SKILL_DIR}/scripts/package-lock.json" ]; then
        ( cd "${SKILL_DIR}/scripts" && npm ci --silent )
    else
        ( cd "${SKILL_DIR}/scripts" && npm install --silent )
    fi
else
    echo "   node 依賴已存在，跳過"
fi

echo "==> 驗證"
bash "${SKILL_DIR}/scripts/check_env.sh"

echo "==> 完成。試跑："
echo "    ${PYTHON_BIN} ${SKILL_DIR}/scripts/cast.py --date 1990-08-18 --time 06:30 --city 台北 --gender male"
echo "    ${SKILL_DIR}/scripts/ziwei_full.sh --date 1990-08-18 --hour 卯 --gender male"
