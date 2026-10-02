#!/usr/bin/env bash
# 紫微排盤入口. 零安裝: 優先跑預打包 bundle (純 node, 免 node_modules).
# 找不到 bundle 時退回 tsx (開發用).
DIR="$(cd "$(dirname "$0")" && pwd)"
BUNDLE="$DIR/ziwei_full.bundle.mjs"
if [ -f "$BUNDLE" ]; then
    command -v node >/dev/null 2>&1 || { echo "錯誤: 需要 Node.js >=18（紫微引擎）。" >&2; exit 2; }
    exec node "$BUNDLE" "$@"
fi
TSX="$DIR/node_modules/.bin/tsx"
if [ -x "$TSX" ]; then
    export NODE_PATH="$DIR/node_modules:${NODE_PATH}"
    exec "$TSX" "$DIR/ziwei_full.ts" "$@"
fi
echo "錯誤: 找不到紫微引擎 (bundle 或 node_modules)。開發者請跑: bash \"$DIR/setup.sh\"" >&2
exit 2
