#!/usr/bin/env bash
# 紫微排盤入口. 零安裝: 優先跑預打包 bundle (純 node, 免 node_modules).
# 找不到 bundle 時退回 tsx (開發用).
# 輸出統一經 han.py --filter 簡→繁 (iztro 吐簡體; 統一簡繁層 single source of truth).
DIR="$(cd "$(dirname "$0")" && pwd)"
TRAD="python3 $DIR/han.py --filter"
if [ -f "$DIR/ziwei_full.bundle.mjs" ]; then
    command -v node >/dev/null 2>&1 || { echo "錯誤: 需要 Node.js >=18（紫微引擎）。" >&2; exit 2; }
    node "$DIR/ziwei_full.bundle.mjs" "$@" | $TRAD
    exit "${PIPESTATUS[0]}"
fi
TSX="$DIR/node_modules/.bin/tsx"
if [ -x "$TSX" ]; then
    export NODE_PATH="$DIR/node_modules:${NODE_PATH}"
    "$TSX" "$DIR/ziwei_full.ts" "$@" | $TRAD
    exit "${PIPESTATUS[0]}"
fi
echo "錯誤: 找不到紫微引擎 (bundle 或 node_modules)。開發者請跑: bash \"$DIR/setup.sh\"" >&2
exit 2
