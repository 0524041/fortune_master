#!/usr/bin/env bash
# 環境檢查 (唯讀). 零安裝: 只需系統 python3 與 node>=18; 依賴已內嵌.
# 用法: bash scripts/check_env.sh
set -uo pipefail
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENDOR="${SKILL_DIR}/scripts/vendor"
BUNDLE="${SKILL_DIR}/scripts/ziwei_full.bundle.mjs"
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
    miss "Node.js >=18" "安裝 Node.js https://nodejs.org"
fi

if command -v python3 >/dev/null 2>&1 \
   && python3 -c "import sys; sys.path.insert(0,'${VENDOR}'); import lunar_python" >/dev/null 2>&1; then
    pass "內嵌 lunar_python (scripts/vendor)"
else
    miss "內嵌 lunar_python" "缺 scripts/vendor/lunar_python（重抓 repo 或跑 setup.sh）"
fi

if [ -f "${BUNDLE}" ]; then
    pass "紫微 bundle ($(du -h "$BUNDLE" | cut -f1))"
else
    miss "紫微 bundle" "缺 scripts/ziwei_full.bundle.mjs（跑 setup.sh 重建）"
fi

if [ "${fail}" -eq 0 ]; then
    echo "==> 環境就緒 ✅（零安裝：無需 pip / npm / venv）"
else
    echo "==> 尚未就緒 ❌"
fi
exit "${fail}"
