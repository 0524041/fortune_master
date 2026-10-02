#!/usr/bin/env bash
# 【開發/維護用】重建內嵌依賴 (scripts/vendor/lunar_python) 與紫微 bundle，並建立測試 venv。
# 一般使用者「不需要」執行本腳本：repo 已內嵌 lunar_python 與 bundle，只需系統 python3 + node。
# 用法: bash scripts/setup.sh
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${SKILL_DIR}/scripts/.venv"
PY="${VENV_DIR}/bin/python"

echo "==> 前置 (開發需要 python3 + node/npm)"
command -v python3 >/dev/null 2>&1 || { echo "❌ 需要 python3" >&2; exit 2; }
command -v npm >/dev/null 2>&1 || { echo "❌ 需要 Node.js/npm" >&2; exit 2; }

echo "==> 建立測試 venv (取得 pin 版 lunar_python 來源 + 跑 pytest)"
[ -x "${PY}" ] || python3 -m venv "${VENV_DIR}"
"${PY}" -m pip install --quiet --upgrade pip
"${PY}" -m pip install --quiet -r "${SKILL_DIR}/scripts/requirements.txt"

echo "==> 重建 scripts/vendor/lunar_python (pin 版, 純 Python 內嵌)"
SP="$("${PY}" -c 'import site; print(site.getsitepackages()[0])')"
rm -rf "${SKILL_DIR}/scripts/vendor/lunar_python"
cp -R "${SP}/lunar_python" "${SKILL_DIR}/scripts/vendor/lunar_python"
cp "${SP}"/lunar_python-*/licenses/LICENSE "${SKILL_DIR}/scripts/vendor/lunar_python/LICENSE" 2>/dev/null || true
cat > "${SKILL_DIR}/scripts/vendor/lunar_python/VENDOR.md" <<'EOF'
# vendor/lunar_python

- 來源: https://github.com/6tail/lunar-python (PyPI `lunar_python`)
- 版本: 1.4.8 (pin)
- 授權: MIT (見 LICENSE)
- 用途: 八字/六爻/梅花/擇日 的曆法換算。純 Python (無編譯檔)，內嵌以達成「零安裝」。
- 更新: `bash scripts/setup.sh` 從 venv 重新複製此目錄。
EOF

echo "==> 重建紫微 bundle (esbuild 打包 iztro/lunar-javascript 成單一 JS)"
( cd "${SKILL_DIR}/scripts" && npm ci --silent )
"${SKILL_DIR}/scripts/node_modules/.bin/esbuild" "${SKILL_DIR}/scripts/ziwei_full.ts" \
    --bundle --platform=node --format=esm --minify \
    --outfile="${SKILL_DIR}/scripts/ziwei_full.bundle.mjs"

echo "==> 驗證"
bash "${SKILL_DIR}/scripts/check_env.sh"

echo "==> 完成 (開發環境)。一般使用者不需跑本腳本。"
echo "    測試: ${PY} -m pytest -q  (在 ${SKILL_DIR})"
