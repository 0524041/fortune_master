#!/usr/bin/env python3
"""對外輸出檢查: 擋英文檔名/函數名/程式符號外洩. 過程紀律 (禁心算/只認JSON) 是對內的不准見客.
用法: output_lint.py --text-file out.txt [--format text|json] [--strict]   # 有違規 exit 1
--strict 另驗「空泛語/巴納姆/免責濫用」(命盤題講了跟沒講一樣), 開發抽查用.
中文名對照見 references/knowledge/output_style.md; 空泛判準見 references/knowledge/pan_output.md.
"""
import argparse
import json
import re
import sys

# 外洩 (預設檢查)
RULES = [
    (re.compile(r"[A-Za-z_][\w-]*\.(py|sh|ts|mjs|js|md|json|txt)"), "英文檔名外洩"),
    (re.compile(r"\b(divine|hepan_check|zeri_pick|bazi_pai|ziwei_full|time_correct|output_lint|toss_coins|liuyao_core|meihua|cast|fuqi_stars|star_detail|ni_mind|bazi_geju|ziwei_geju|hepan_ni|fuyan|glossary|voice|setup|tiaohou|horoscope)\b"), "內部名外洩"),
    (re.compile(r"patterns\[\]|JSON\.|->|=>|\.json\b.*[抄讀]|[抄讀].*\.json\b"), "程式符號外洩"),
    (re.compile(r"sk-?[A-Za-z0-9]{8,}|/Users/[\w./-]+|/tmp/[\w./-]+"), "本機路徑外洩"),
]

# 空泛/巴納姆/免責濫用 (--strict 才檢查; 命盤題套 knowledge/pan_output.md 反巴納姆禁令)
VAGUE_RULES = [
    (re.compile(r"(可能|也許|或許|大概|恐怕)"), "模糊斷語(voice 禁)"),
    (re.compile(r"(因人而異|因情況而異|視情況而定|見仁見智|每個人不同)"), "空泛語(巴納姆)"),
    (re.compile(r"(無法|不能|難以)(由命盤)?(推算|預測|判斷)[^。！？\n]{0,12}(金額|收入|數字|報酬|標的)"), "推託語(以斷語取代)"),
    (re.compile(r"不構成(任何)?投資建議"), "免責語(限六爻投資題)"),
]

CN_NAMES = {"bazi_pai.py": "八字排盤程式", "ziwei_full.sh": "紫微排盤程式",
            "hepan_check.py": "合盤比對程式", "zeri_pick.py": "擇日掃描程式",
            "divine.py": "六爻起卦程式", "meihua.py": "梅花起卦程式",
            "cast.py": "雙盤排盤程式", "fuqi_stars": "夫妻宮斷語表",
            "tiaohou.json": "調候用神表", "patterns[]": "格局判定結果"}


def lint(text, strict=False):
    hits = []
    rules = RULES + VAGUE_RULES if strict else RULES
    for i, line in enumerate(text.splitlines(), 1):
        for rx, rule in rules:
            for m in rx.finditer(line):
                hits.append({"line": i, "token": m.group(0), "rule": rule,
                             "text": line.strip()[:60]})
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text-file", required=True)
    ap.add_argument("--format", default="text", choices=["text", "json"])
    ap.add_argument("--strict", action="store_true",
                    help="加驗空泛語/巴納姆/免責濫用 (開發抽查用)")
    a = ap.parse_args()
    hits = lint(open(a.text_file, encoding="utf-8").read(), strict=a.strict)
    if a.format == "json":
        print(json.dumps({"violations": hits}, ensure_ascii=False, indent=2))
    else:
        for h in hits:
            print(f"L{h['line']} [{h['rule']}] {h['token']}")
        print(f"共{len(hits)}處" if hits else "乾淨")
    sys.exit(1 if hits else 0)


if __name__ == "__main__":
    main()
