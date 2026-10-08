#!/usr/bin/env python3
"""對外輸出檢查: 擋英文檔名/函數名/程式符號外洩. 過程紀律 (禁心算/只認JSON) 是對內的不准見客.
用法: output_lint.py --text-file out.txt [--format text|json] [--strict]   # 有違規 exit 1
--strict 另驗「空泛語/巴納姆」(講了跟沒講一樣), 開發抽查用.
自然語氣 (Phase 3): 可能/也許/大概等可用, --strict 只記「提示」不計違規; 真正擋的是空泛語與推託語.
判準 (換誰都成立=空泛) 見 references/shared/output-quality.md.
"""
import argparse
import json
import re
import sys

# 外洩 (預設檢查)
RULES = [
    (re.compile(r"[A-Za-z_][\w-]*\.(py|sh|ts|mjs|js|md|json|txt)"), "英文檔名外洩"),
    (re.compile(r"\b(divine|hepan_check|zeri_pick|bazi_pai|ziwei_full|time_correct|output_lint|toss_coins|liuyao_core|meihua|cast|liuren|liuren_core|event_cast|qimen|qimen_core|person_cast|fuqi_stars|star_detail|ni_mind|bazi_geju|ziwei_geju|hepan_ni|fuyan|glossary|voice|setup|tiaohou|horoscope)\b"), "內部名外洩"),
    (re.compile(r"patterns\[\]|JSON\.|->|=>|\.json\b.*[抄讀]|[抄讀].*\.json\b"), "程式符號外洩"),
    (re.compile(r"sk-?[A-Za-z0-9]{8,}|/Users/[\w./-]+|/tmp/[\w./-]+"), "本機路徑外洩"),
]

# 自然語氣 (--strict 只記提示, 不計違規): 可用, 提醒確認是否已說明不確定原因.
HEDGE_RULES = [
    (re.compile(r"(可能|也許|或許|大概|恐怕)"), "自然語氣(提示)"),
]

# 空泛/巴納姆 (--strict 才檢查, 計違規): 判準「換誰都成立」見 references/shared/output-quality.md
VAGUE_RULES = [
    (re.compile(r"(因人而異|因個人而異|因情況而異|視情況而定|視狀況而定|見仁見智|每個人不同)"), "空泛語(巴納姆)"),
    (re.compile(r"(無法|不能|難以)(由命盤)?(推算|預測|判斷)[^。！？\n]{0,12}(金額|收入|數字|報酬|標的)"), "推託語(以斷語取代)"),
]

CN_NAMES = {"bazi_pai.py": "八字排盤程式", "ziwei_full.sh": "紫微排盤程式",
            "hepan_check.py": "合盤比對程式", "zeri_pick.py": "擇日掃描程式",
            "divine.py": "六爻起卦程式", "meihua.py": "梅花起卦程式",
            "liuren.py": "六壬排盤程式", "event_cast.py": "四式合盤程式",
            "qimen.py": "奇門排盤程式", "person_cast.py": "問人總盤程式",
            "cast.py": "雙盤排盤程式", "decade.py": "多年運總表程式", "fuqi_stars": "夫妻宮斷語表",
            "tiaohou.json": "調候用神表", "patterns[]": "格局判定結果"}


def _scan(text, strict=False):
    """回 (violations, notes). notes: 自然語氣提示, 只供觀測, 不影響 exit code."""
    hits, notes = [], []
    for i, line in enumerate(text.splitlines(), 1):
        for rx, rule in RULES:
            for m in rx.finditer(line):
                hits.append({"line": i, "token": m.group(0), "rule": rule,
                             "text": line.strip()[:60]})
        if not strict:
            continue
        for rx, rule in VAGUE_RULES:
            for m in rx.finditer(line):
                hits.append({"line": i, "token": m.group(0), "rule": rule,
                             "text": line.strip()[:60]})
        for rx, rule in HEDGE_RULES:
            for m in rx.finditer(line):
                notes.append({"line": i, "token": m.group(0), "rule": rule,
                              "text": line.strip()[:60]})
    return hits, notes


def lint(text, strict=False):
    hits, _ = _scan(text, strict)
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text-file", required=True)
    ap.add_argument("--format", default="text", choices=["text", "json"])
    ap.add_argument("--strict", action="store_true",
                    help="加驗空泛語/巴納姆 (開發抽查用)")
    a = ap.parse_args()
    hits, notes = _scan(open(a.text_file, encoding="utf-8").read(), strict=a.strict)
    if a.format == "json":
        print(json.dumps({"violations": hits, "notes": notes}, ensure_ascii=False, indent=2))
    else:
        for h in hits:
            print(f"L{h['line']} [{h['rule']}] {h['token']}")
        for n in notes:
            print(f"L{n['line']} [提示:自然語氣，確認已說明不確定原因] {n['token']}")
        print(f"共{len(hits)}處" if hits else "乾淨")
    sys.exit(1 if hits else 0)


if __name__ == "__main__":
    main()
