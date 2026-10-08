# scripts/vendor — 內嵌第三方 (零安裝用)

本 skill 為了「零安裝」把 runtime 依賴內嵌進來，使用者只需系統 `python3` 與 `node`。

| 目錄/檔案 | 來源 | 版本 | 授權 |
|---|---|---|---|
| `lunar_python/` | https://github.com/6tail/lunar-python | 1.4.8 (pin) | MIT |
| `ziwei/` | iztro 2.5.8 快照 (見 `ziwei/README.md`) | 2.5.8 | MIT |
| `opencc/` | https://github.com/yichen0831/opencc-python (opencc-python-reimplemented) | 0.1.7 | Apache-2.0 |
| `../ziwei_full.bundle.mjs` | esbuild 打包 `ziwei_full.ts`（內含 iztro、lunar-javascript） | — | MIT |

`opencc/` 供 `scripts/han.py`（統一簡繁層，簡→繁）使用，執行期零安裝；`data/*.json` 規則表與引擎輸出統一經此層。

更新方式：`bash scripts/setup.sh`（開發用；會重建 `lunar_python/` 與 bundle）。
