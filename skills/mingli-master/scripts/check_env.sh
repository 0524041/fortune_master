#!/usr/bin/env bash
# 環境檢查 (唯讀，不安裝任何東西). 全部就緒 exit 0；否則列出缺項並 exit 1.
# 用法: bash scripts/check_env.sh
set -uo pipefail
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PY="${SKILL_DIR}/scripts/.venv/bin/python"
TSX="${SKILL_DIR}/scripts/node_modules/.bin/tsx"
fail=0
pass() { printf '  ✅ %s\n' "$1"; }
miss() { printf '  ❌ %s → %s\n' "$1" "$2"; fail=1; }

echo "命理大師環境檢查 (${SKILL_DIR})"

if command -v python3 >/dev/null 2>&1; then
    pass "python3 ($(python3 --version 2>&1 | awk '{print $2}'))"
else
    miss "python3" "安裝 Python 3"
fi

NODE_MAJOR="$(node -v 2>/dev/null | sed -E 's/^v([0-9]+).*/\1/')"
if [ -n "${NODE_MAJOR}" ] && [ "${NODE_MAJOR}" -ge 18 ] 2>/dev/null; then
    pass "node $(node -v) (>=18)"
else
    miss "Node.js >=18" "安裝 Node.js https://nodejs.org (紫微引擎必需)"
fi

if command -v npm >/dev/null 2>&1; then
    pass "npm ($(npm -v 2>/dev/null))"
else
    miss "npm" "隨 Node.js 安裝"
fi

if [ -x "${VENV_PY}" ] && "${VENV_PY}" -c 'import lunar_python' >/dev/null 2>&1; then
    pass "Python venv + lunar_python"
else
    miss "Python venv / lunar_python" "跑 bash scripts/setup.sh"
fi

if [ -x "${TSX}" ]; then
    pass "Node 依賴 (iztro / tsx)"
else
    miss "Node 依賴 iztro / tsx" "跑 bash scripts/setup.sh"
fi

if [ "${fail}" -eq 0 ]; then
    echo "==> 環境就緒 ✅"
else
    echo "==> 尚未就緒，請修上方項目（安裝: bash scripts/setup.sh）❌"
fi
exit "${fail}"
