#!/usr/bin/env python3
"""統一簡繁轉換層 (single source of truth).

方針
----
- **正規語言 = 繁體**。引擎輸出 (lunar_python / iztro) 一律吐簡體, 全部先經此層轉繁,
  再進比對 / 格式化 / 輸出; `data/*.json` 與 `references/` 的規則表已繁體,
  因此**不再需要繁簡雙套字表** (舊 SIMP2TRAD、hepan 的繁簡星名集合等一律移除)。
- **轉換只在引擎邊界做一次** (先轉後比), 不是輸出前才補; 這樣比對在繁體空間進行,
  避免簡繁不一致造成的靜默失效。
- 引擎: 內嵌 `scripts/vendor/opencc` (opencc-python-reimplemented, Apache-2.0, 純 Python),
  零安裝 (免 pip/npm/venv)。找不到時退回內建字表, 只保證已知通書詞彙。

用法 (library)
--------------
    from han import s2t, s2t_list, s2t_deep, norm_palace, is_clean, simplified_leaks
    s2t("命宫")               # → "命宮"
    s2t_deep(obj)             # 遞迴轉所有字串值 (keys 不動)

用法 (CLI, 給 node 輸出過濾)
---------------------------
    node bundle ... | python3 scripts/han.py --filter
"""
import json
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR / "vendor"))

_CONV = None

# 領域例外: opencc 對「本身即正體」的歧義字會誤轉, 轉後修正回本命理領域的正字.
#   醜→丑 (地支) / 啓→啟 (統一正字) / 衝→沖 (相沖, 非衝擊) / 牀→床 (安床)
#   時乾→時干 (奇門時干, opencc 誤轉)
_POST = {"醜": "丑", "啓": "啟", "衝": "沖", "牀": "床", "鬥": "斗",
         "兇": "凶", "佔": "占", "竈": "灶", "幹": "干", "時乾": "時干"}

# 內建後備字表 (opencc 缺席時用; 只覆蓋通書/紫微常用詞彙, 非完整)
_FALLBACK = str.maketrans({
    "开": "開", "闭": "閉", "门": "門", "迁": "遷", "财": "財", "杀": "殺", "冲": "沖",
    "贵": "貴", "马": "馬", "鸡": "雞", "龙": "龍", "仓": "倉", "寿": "壽", "发": "發",
    "丰": "豐", "丽": "麗", "宝": "寶", "显": "顯", "镇": "鎮", "钟": "鐘", "长": "長",
    "阴": "陰", "阳": "陽", "际": "際", "泽": "澤", "满": "滿", "达": "達", "运": "運",
    "远": "遠", "迟": "遲", "惊": "驚", "罗": "羅", "败": "敗", "废": "廢", "兽": "獸",
    "画": "畫", "钩": "鉤", "绞": "絞", "络": "絡", "续": "續", "绝": "絕", "缠": "纏",
    "计": "計", "时": "時", "晓": "曉", "鸣": "鳴", "圣": "聖", "临": "臨", "监": "監",
    "鉴": "鑒", "钦": "欽", "饿": "餓", "饱": "飽", "贪": "貪", "贞": "貞", "禄": "祿",
    "机": "機", "辅": "輔", "庄": "莊", "凤": "鳳", "鸾": "鸞", "乔": "喬", "汤": "湯",
    "沟": "溝", "汉": "漢", "洁": "潔", "浊": "濁", "浏": "瀏", "无": "無", "殓": "殮",
    "启": "啟", "钻": "鑽", "馀": "餘", "订": "訂", "纳": "納", "斋": "齋", "诣": "詣",
    "岁": "歲", "疗": "療", "医": "醫", "针": "針", "驯": "馴", "盖": "蓋", "竖": "豎",
    "坟": "墳", "灵": "靈", "枢": "樞", "猎": "獵", "网": "網", "结": "結", "绳": "繩",
    "纽": "紐", "经": "經", "织": "織", "补": "補", "筑": "築", "厕": "廁", "库": "庫",
    "贮": "貯", "贸": "貿", "货": "貨", "购": "購", "贩": "販", "赊": "賒", "账": "賬",
    "贾": "賈", "赁": "賃", "执": "執", "蚕": "蠶", "风": "風", "颠": "顛", "来": "來",
    "儿": "兒", "孙": "孫", "钱": "錢", "猪": "豬", "兴": "興", "余": "餘", "题": "題",
    "须": "須", "陈": "陳", "黄": "黃", "东": "東", "虚": "虛", "残": "殘", "对": "對",
    "体": "體", "会": "會", "伤": "傷", "动": "動", "胜": "勝", "营": "營", "业": "業",
    "愿": "願", "绿": "綠", "权": "權", "玑": "璣", "瑶": "瑤", "称": "稱", "亩": "畝",
    "图": "圖", "坛": "壇", "准": "準", "乡": "鄉", "产": "產", "亲": "親", "击": "擊",
    "单": "單", "厌": "厭", "厨": "廚", "参": "參", "见": "見", "车": "車", "炉": "爐",
    "宫": "宮", "斗": "鬥", "当": "當", "书": "書", "买": "買", "卖": "賣", "农": "農",
    "军": "軍", "划": "劃", "刘": "劉", "则": "則", "刚": "剛", "创": "創",
})


def _converter():
    global _CONV
    if _CONV is None:
        try:
            import opencc  # 內嵌 scripts/vendor/opencc
            _CONV = opencc.OpenCC("s2t")
        except Exception:
            _CONV = False
    return _CONV


def s2t(text):
    """簡→繁 (引擎輸出用). 非字串原樣回傳; 轉後套領域例外修正."""
    if not isinstance(text, str) or not text:
        return text
    c = _converter()
    out = c.convert(text) if c else text.translate(_FALLBACK)
    for a, b in _POST.items():
        if a in out:
            out = out.replace(a, b)
    return out


def s2t_list(items):
    return [s2t(x) for x in items]


def s2t_deep(obj):
    """遞迴轉換所有字串值 (dict 的 keys 不動, 避免破壞查表鍵)."""
    if isinstance(obj, str):
        return s2t(obj)
    if isinstance(obj, list):
        return [s2t_deep(x) for x in obj]
    if isinstance(obj, dict):
        return {k: s2t_deep(v) for k, v in obj.items()}
    return obj


def norm_palace(name):
    """宮名正規化: 轉繁並去尾綴「宮」(命宮→命, 財帛宮→財帛)."""
    return s2t(name).rstrip("宮") if isinstance(name, str) else name


def is_clean(obj):
    """輸出無簡體殘留 (以 curated 集判定)."""
    return not simplified_leaks(obj)


# 殘留偵測字集 (驗證用; 單一維護點). 只放**確定是簡體**的字, 不含繁簡同形或領域正體字.
# 註: 不用 opencc STCharacters 自動判定 —— 簡體把多個正體併成一個字 (出/松/占/冬/采… 皆正體),
#     自動判定會大量誤報; 故此集為 curated, 僅供測試/verification, 轉換本體一律走 opencc。
SIMP_BAD = set(
    "开闭杀门财权禄贪贞机辅迁马龙鸡仓废罗败惊艳钟萧肃啸东黄陈虚残对兴体会伤动胜营业"
    "猪蚕来儿孙钱题须绿枢瑶玑灵疗网准称亩图坛坟阳阴宫当书买卖农军划刘则刚创"
    "专乌习亏仪佣养内兽冲击剑匮医单厌厕厨参发坏墙处头娄学宁宝寝将尝帐带并库庙"
    "张强归愿执扫护挂摇敌斋断时晓权杨桥殓毕气涂涧渐渔游满灭灯灾炉猎玑疮盖祸离种"
    "穷竖筑纯纳织经结绘络绝续肠腊艺节药莲蚁蛰蜡补见观触订讼词诸谢负货贵贼车轸还进"
    "远酱针钏钗钻锋错问阵隐难雳顺饰驱驿鸟鸣"
)


def _values(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, list):
        for x in obj:
            yield from _values(x)
    elif isinstance(obj, dict):
        for v in obj.values():      # 只掃值; keys 為識別字 (如引擎欄位 "禄"/"权")
            yield from _values(v)


def simplified_leaks(obj):
    """回傳殘留簡體字 (空=乾淨). 只掃字串值, curated 集見上註."""
    blob = "".join(_values(obj))
    return sorted(set(blob) & SIMP_BAD)


def _filter_stream():
    """stdin → 繁體 stdout. 若是 JSON 只轉值 (keys 不動, 免得 t["禄"] 這類取鍵壞掉);
    否則當純文字整段轉."""
    data = sys.stdin.read()
    try:
        obj = json.loads(data)
    except Exception:
        sys.stdout.write(s2t(data))
        return
    json.dump(s2t_deep(obj), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def main():
    import argparse
    ap = argparse.ArgumentParser(description="統一簡繁轉換層 (簡→繁)")
    ap.add_argument("--filter", action="store_true", help="讀 stdin 全轉繁後寫 stdout (給 node 輸出過濾)")
    ap.add_argument("text", nargs="*", help="直接轉換的字串")
    a = ap.parse_args()
    if a.filter:
        _filter_stream()
    elif a.text:
        print(" ".join(s2t(t) for t in a.text))
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
