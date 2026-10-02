# vendor/ziwei 快照說明

內嵌自 `workspace/ziwei-doushu/lib/ziwei/` 的 5 個檔案 (types/constants/sihua/algorithm/patterns)，
快照日期 2026-09-13。原因：原 repo 目錄在執行環境被系統拒讀 (EPERM)，tsx
解析 import 時讀不到它的 `package.json` 即炸；內嵌後 skill 自包含。

- 运行时只用此快照，不再跨目錄 import。
- 上游有更新時，手动同步一次 + 重跑 `tests/test_ziwei_full.py` (格局 pin 會抓住漂移)。
- `horoscope.ts` 為 **mingli 自建**（非上游 5 檔之一）：包裝 iztro `astrolabe.horoscope()` 出運限六層，見 `references/methods/ziwei_geju.md` 運限節。
- 知識引用 (`TIANJI_QUOTES`/古籍/`heming-knowledge`) 仍指向原 repo，僅供 LLM 閱讀。
