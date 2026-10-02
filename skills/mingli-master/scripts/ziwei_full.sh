#!/usr/bin/env bash
# 統一入口：自動帶 NODE_PATH 跑全量紫微 (直呼本地 tsx, 免 npx 啟動稅)
DIR="$(dirname "$0")"
export NODE_PATH="$DIR/node_modules:${NODE_PATH}"
exec "$DIR/node_modules/.bin/tsx" "$DIR/ziwei_full.ts" "$@"
