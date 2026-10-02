#!/usr/bin/env bash
# 統一入口：自動帶 NODE_PATH 跑全量紫微 (直呼本地 tsx, 免 npx 啟動稅)
DIR="$(cd "$(dirname "$0")" && pwd)"
TSX="$DIR/node_modules/.bin/tsx"
if [ ! -x "$TSX" ]; then
    echo "錯誤: 紫微引擎未安裝 (找不到 node_modules)。請先執行: bash \"$DIR/setup.sh\" (需 Node.js >=18)" >&2
    exit 2
fi
export NODE_PATH="$DIR/node_modules:${NODE_PATH}"
exec "$TSX" "$DIR/ziwei_full.ts" "$@"
