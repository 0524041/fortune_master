"""
六爻排盤核心演算法 (Standalone)

依賴: lunar_python (pip install lunar_python)
用法:
    from liuyao_core import LiuYaoChart, toss_coins
    chart = LiuYaoChart(datetime.now(), coins)   # coins: 6 個 0-3
    data = chart.to_dict()                        # 結構化資料
    text = chart.format_for_ai()                  # 固定文字格式 (給 AI 解盤)
"""

from datetime import datetime
from pathlib import Path
import json
import random
import sys
from typing import List, Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "vendor"))  # 內嵌 lunar_python (零安裝)
from lunar_python import Lunar, Solar

# ========== 基礎數據 ==========

TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
WUXING = ['木', '木', '火', '火', '土', '土', '金', '金', '水', '水']
DIZHI_WUXING = ['水', '土', '木', '木', '土', '火', '火', '土', '金', '金', '土', '水']

LIUQIN = {
    '同': '兄弟',
    '生': '子孫',
    '克': '妻財',
    '被生': '父母',
    '被克': '官鬼',
}

LIUSHEN_MAP = {
    '甲': ['青龍', '朱雀', '勾陳', '螣蛇', '白虎', '玄武'],
    '乙': ['青龍', '朱雀', '勾陳', '螣蛇', '白虎', '玄武'],
    '丙': ['朱雀', '勾陳', '螣蛇', '白虎', '玄武', '青龍'],
    '丁': ['朱雀', '勾陳', '螣蛇', '白虎', '玄武', '青龍'],
    '戊': ['勾陳', '螣蛇', '白虎', '玄武', '青龍', '朱雀'],
    '己': ['勾陳', '螣蛇', '白虎', '玄武', '青龍', '朱雀'],
    '庚': ['白虎', '玄武', '青龍', '朱雀', '勾陳', '螣蛇'],
    '辛': ['白虎', '玄武', '青龍', '朱雀', '勾陳', '螣蛇'],
    '壬': ['玄武', '青龍', '朱雀', '勾陳', '螣蛇', '白虎'],
    '癸': ['玄武', '青龍', '朱雀', '勾陳', '螣蛇', '白虎'],
}

BAGUA = {
    '乾': {'wuxing': '金', 'shi': 6, 'ying': 3},
    '兌': {'wuxing': '金', 'shi': 5, 'ying': 2},
    '離': {'wuxing': '火', 'shi': 4, 'ying': 1},
    '震': {'wuxing': '木', 'shi': 1, 'ying': 4},
    '巽': {'wuxing': '木', 'shi': 2, 'ying': 5},
    '坎': {'wuxing': '水', 'shi': 3, 'ying': 6},
    '艮': {'wuxing': '土', 'shi': 4, 'ying': 1},
    '坤': {'wuxing': '土', 'shi': 3, 'ying': 6},
}

BAGUA_PATTERN = {
    (1, 1, 1): '乾', (1, 1, 0): '兌', (1, 0, 1): '離', (1, 0, 0): '震',
    (0, 1, 1): '巽', (0, 1, 0): '坎', (0, 0, 1): '艮', (0, 0, 0): '坤',
}

LIUSHISI_GUA = {
    ('乾', '乾'): '乾為天', ('坤', '乾'): '天地否', ('震', '乾'): '天雷無妄', ('巽', '乾'): '天風姤',
    ('坎', '乾'): '天水訟', ('離', '乾'): '天火同人', ('艮', '乾'): '天山遁', ('兌', '乾'): '天澤履',
    ('乾', '坤'): '地天泰', ('坤', '坤'): '坤為地', ('震', '坤'): '地雷復', ('巽', '坤'): '地風升',
    ('坎', '坤'): '地水師', ('離', '坤'): '地火明夷', ('艮', '坤'): '地山謙', ('兌', '坤'): '地澤臨',
    ('乾', '震'): '雷天大壯', ('坤', '震'): '雷地豫', ('震', '震'): '震為雷', ('巽', '震'): '雷風恆',
    ('坎', '震'): '雷水解', ('離', '震'): '雷火豐', ('艮', '震'): '雷山小過', ('兌', '震'): '雷澤歸妹',
    ('乾', '巽'): '風天小畜', ('坤', '巽'): '風地觀', ('震', '巽'): '風雷益', ('巽', '巽'): '巽為風',
    ('坎', '巽'): '風水渙', ('離', '巽'): '風火家人', ('艮', '巽'): '風山漸', ('兌', '巽'): '風澤中孚',
    ('乾', '坎'): '水天需', ('坤', '坎'): '水地比', ('震', '坎'): '水雷屯', ('巽', '坎'): '水風井',
    ('坎', '坎'): '坎為水', ('離', '坎'): '水火既濟', ('艮', '坎'): '水山蹇', ('兌', '坎'): '水澤節',
    ('乾', '離'): '火天大有', ('坤', '離'): '火地晉', ('震', '離'): '火雷噬嗑', ('巽', '離'): '火風鼎',
    ('坎', '離'): '火水未濟', ('離', '離'): '離為火', ('艮', '離'): '火山旅', ('兌', '離'): '火澤睽',
    ('乾', '艮'): '山天大畜', ('坤', '艮'): '山地剝', ('震', '艮'): '山雷頤', ('巽', '艮'): '山風蠱',
    ('坎', '艮'): '山水蒙', ('離', '艮'): '山火賁', ('艮', '艮'): '艮為山', ('兌', '艮'): '山澤損',
    ('乾', '兌'): '澤天夬', ('坤', '兌'): '澤地萃', ('震', '兌'): '澤雷隨', ('巽', '兌'): '澤風大過',
    ('坎', '兌'): '澤水困', ('離', '兌'): '澤火革', ('艮', '兌'): '澤山咸', ('兌', '兌'): '兌為澤',
}

GONG_DIZHI = {
    '乾': ['子', '寅', '辰', '午', '申', '戌'],
    '兌': ['巳', '卯', '丑', '亥', '酉', '未'],
    '離': ['卯', '丑', '亥', '酉', '未', '巳'],
    '震': ['子', '寅', '辰', '午', '申', '戌'],
    '巽': ['丑', '亥', '酉', '未', '巳', '卯'],
    '坎': ['寅', '辰', '午', '申', '戌', '子'],
    '艮': ['辰', '午', '申', '戌', '子', '寅'],
    '坤': ['未', '巳', '卯', '丑', '亥', '酉'],
}

BAGUA_BITS = {
    '乾': 0b111, '兌': 0b011, '離': 0b101, '震': 0b001,
    '巽': 0b110, '坎': 0b010, '艮': 0b100, '坤': 0b000,
}
BITS_TO_BAGUA = {v: k for k, v in BAGUA_BITS.items()}

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
HEXAGRAMS_FILE = DATA_DIR / "hexagrams_64.json"
YAOCI_FILE = DATA_DIR / "yaoci_64.json"

_hexagram_cache: Optional[Dict[str, Dict]] = None
_yaoci_cache: Optional[Dict[str, Dict]] = None


def _load_hexagrams() -> Dict[str, Dict]:
    """載入六十四卦知識庫，以傳統卦名 (如 乾為天) 為索引"""
    global _hexagram_cache
    if _hexagram_cache is None:
        with open(HEXAGRAMS_FILE, 'r', encoding='utf-8') as f:
            items = json.load(f)
        _hexagram_cache = {}
        for h in items:
            number = h['number']
            _hexagram_cache[h['name']] = h
            name = h['name']
            if name.endswith('卦'):
                _hexagram_cache[name[:-1]] = h
            # 依卦序對照傳統卦名 (1-8 本宮卦可直接推，其餘用順序表)
            _hexagram_cache.setdefault(_TRAD_NAME_BY_NUM.get(number), h)
    return _hexagram_cache


# 卦序 -> 傳統卦名 (上卦+下卦)，與 LIUSHISI_GUA 對應
_TRAD_NAME_BY_NUM = {
    1: '乾為天', 2: '坤為地', 3: '水雷屯', 4: '山水蒙', 5: '水天需', 6: '天水訟',
    7: '地水師', 8: '水地比', 9: '風天小畜', 10: '天澤履', 11: '地天泰', 12: '天地否',
    13: '天火同人', 14: '火天大有', 15: '地山謙', 16: '雷地豫', 17: '澤雷隨', 18: '山風蠱',
    19: '地澤臨', 20: '風地觀', 21: '火雷噬嗑', 22: '山火賁', 23: '山地剝', 24: '地雷復',
    25: '天雷無妄', 26: '山天大畜', 27: '山雷頤', 28: '澤風大過', 29: '坎為水', 30: '離為火',
    31: '澤山咸', 32: '雷風恆', 33: '天山遁', 34: '雷天大壯', 35: '火地晉', 36: '地火明夷',
    37: '風火家人', 38: '火澤睽', 39: '水山蹇', 40: '雷水解', 41: '山澤損', 42: '風雷益',
    43: '澤天夬', 44: '天風姤', 45: '澤地萃', 46: '地風升', 47: '澤水困', 48: '水風井',
    49: '澤火革', 50: '火風鼎', 51: '震為雷', 52: '艮為山', 53: '風山漸', 54: '雷澤歸妹',
    55: '雷火豐', 56: '火山旅', 57: '巽為風', 58: '兌為澤', 59: '風水渙', 60: '水澤節',
    61: '風澤中孚', 62: '雷山小過', 63: '水火既濟', 64: '火水未濟',
}


def get_hexagram(name: str) -> Optional[Dict]:
    """依卦名取得卦象知識 (卦辭/象傳/諸事/愛情/事業/財運/建議/詳解)"""
    return _load_hexagrams().get(name)


# 卦序 -> 傳統卦名 (上卦+下卦)，與 LIUSHISI_GUA 對應
_NAME_TO_NUM = {v: k for k, v in _TRAD_NAME_BY_NUM.items()}


def _load_yaoci() -> Dict[str, Dict]:
    """載入六十四卦爻辭庫，以卦序號與傳統卦名 (如 風天小畜)、單名 (小畜) 為索引。
    底本：《周易正義》武英殿十三經注疏本（中文維基文庫轉寫，逐卦鎖定 oldid）。
    """
    global _yaoci_cache
    if _yaoci_cache is None:
        with open(YAOCI_FILE, 'r', encoding='utf-8') as f:
            items = json.load(f)
        _yaoci_cache = {}
        for idx, h in enumerate(items):
            num = h.get('number', idx + 1)
            _yaoci_cache[str(num)] = h
            _yaoci_cache[h['name']] = h            # 風天小畜
            if h.get('short'):
                _yaoci_cache[h['short']] = h        # 小畜
    return _yaoci_cache


def get_yaoci(gua_name: str) -> Optional[Dict]:
    """依卦名取得該卦全部爻辭 (底本《周易正義》); 另附 edition / source_url。"""
    return _load_yaoci().get(gua_name) or _load_yaoci().get(str(_NAME_TO_NUM.get(gua_name, '')))


def get_yao_text(gua_name: str, position: int) -> Optional[Dict]:
    """取某卦第 position 爻 (1=初爻..6=上爻) 的爻辭 {'pos','text'}; 無資料回 None。"""
    entry = get_yaoci(gua_name)
    if not entry or not (1 <= position <= 6):
        return None
    return entry['yao'][position - 1]


def get_yong_text(gua_name: str) -> Optional[Dict]:
    """取乾坤的用九/用六爻辭; 其他卦回 None。"""
    entry = get_yaoci(gua_name)
    return entry.get('yong') if entry else None


# ========== 工具函數 ==========

def toss_coins() -> List[int]:
    """
    擲三枚硬幣六次 (電腦模擬)，返回 6 個 0-3 數字 = 每次背面朝上數量
    0: 三字 (老陽, 動) | 1: 二字一背 (少陽, 靜)
    2: 一字二背 (少陰, 靜) | 3: 三背 (老陰, 動)
    """
    return [sum(random.choice([0, 1]) for _ in range(3)) for _ in range(6)]


def coins_to_yao(coin: int) -> tuple:
    """硬幣結果 -> (is_yang, is_moving)"""
    if coin == 0:
        return (True, True)
    elif coin == 1:
        return (True, False)
    elif coin == 2:
        return (False, False)
    else:
        return (False, True)


def get_wuxing_relation(source: str, target: str) -> str:
    """五行生克關係: 同/生/克/被生/被克"""
    wuxing_order = ['木', '火', '土', '金', '水']
    s_idx = wuxing_order.index(source)
    t_idx = wuxing_order.index(target)
    if s_idx == t_idx:
        return '同'
    elif (s_idx + 1) % 5 == t_idx:
        return '生'
    elif (s_idx + 2) % 5 == t_idx:
        return '克'
    elif (s_idx - 1) % 5 == t_idx:
        return '被生'
    else:
        return '被克'


def get_liuqin(gong_wuxing: str, yao_wuxing: str) -> str:
    """依卦宮五行與爻五行取六親"""
    return LIUQIN.get(get_wuxing_relation(gong_wuxing, yao_wuxing), '未知')


def get_kongwang(day_gan: str, day_zhi: str) -> List[str]:
    """計算日空亡"""
    gan_idx = TIANGAN.index(day_gan)
    zhi_idx = DIZHI.index(day_zhi)
    xun_start = (zhi_idx - gan_idx) % 12
    return [DIZHI[(xun_start + 10) % 12], DIZHI[(xun_start + 11) % 12]]


# ========== 核心排盤類 ==========

class LiuYaoChart:
    """六爻排盤核心類"""

    def __init__(self, dt: datetime, yaogua: Optional[List[int]] = None):
        """
        dt: 起卦時間
        yaogua: 搖卦結果 (6 個 0-3 數字)，不提供則隨機生成
        """
        self.dt = dt
        self.yaogua = yaogua if yaogua else toss_coins()

        solar = Solar.fromDate(dt)
        self.lunar = Lunar.fromSolar(solar)

        self.year_gan = self.lunar.getYearGan()
        self.year_zhi = self.lunar.getYearZhi()
        self.month_gan = self.lunar.getMonthGan()
        self.month_zhi = self.lunar.getMonthZhi()
        self.day_gan = self.lunar.getDayGan()
        self.day_zhi = self.lunar.getDayZhi()
        self.hour_gan = self.lunar.getTimeGan()
        self.hour_zhi = self.lunar.getTimeZhi()

        self.bazi = (f"{self.year_gan}{self.year_zhi} {self.month_gan}{self.month_zhi} "
                     f"{self.day_gan}{self.day_zhi} {self.hour_gan}{self.hour_zhi}")

        self.kongwang = get_kongwang(self.day_gan, self.day_zhi)

        self._parse_yaos()
        self._build_chart()

    def _parse_yaos(self):
        self.yaos = []
        for coin in self.yaogua:
            is_yang, is_moving = coins_to_yao(coin)
            self.yaos.append({'coin': coin, 'is_yang': is_yang, 'is_moving': is_moving})

    def _get_gua_pattern(self, yaos: List[dict], start: int, end: int) -> tuple:
        return tuple(1 if yaos[i]['is_yang'] else 0 for i in range(start, end))

    def _find_gong_and_shi(self, upper_name: str, lower_name: str) -> tuple:
        """尋宮安世 (京房八宮)"""
        up = BAGUA_BITS[upper_name]
        low = BAGUA_BITS[lower_name]

        if up == low:
            return upper_name, 6, '本宮卦'

        for gong_name, gong_val in BAGUA_BITS.items():
            seq = [((gong_val, gong_val), 6)]
            curr_low = gong_val ^ 0b001
            seq.append(((gong_val, curr_low), 1))
            curr_low = curr_low ^ 0b010
            seq.append(((gong_val, curr_low), 2))
            curr_low = curr_low ^ 0b100
            seq.append(((gong_val, curr_low), 3))
            curr_up = gong_val ^ 0b001
            seq.append(((curr_up, curr_low), 4))
            curr_up = curr_up ^ 0b010
            seq.append(((curr_up, curr_low), 5))
            curr_up = curr_up ^ 0b001
            seq.append(((curr_up, curr_low), 4))
            curr_low = gong_val
            seq.append(((curr_up, curr_low), 3))

            gua_types = ['本宮卦', '一世卦', '二世卦', '三世卦', '四世卦', '五世卦', '遊魂卦', '歸魂卦']
            for idx, ((outer, inner), shi) in enumerate(seq):
                if outer == up and inner == low:
                    return gong_name, shi, gua_types[idx]
        return '乾', 6, '本宮卦'

    def _build_chart(self):
        lower_pattern = self._get_gua_pattern(self.yaos, 0, 3)
        upper_pattern = self._get_gua_pattern(self.yaos, 3, 6)

        self.lower_gua = BAGUA_PATTERN.get(lower_pattern, '坤')
        self.upper_gua = BAGUA_PATTERN.get(upper_pattern, '坤')
        self.bengua_name = LIUSHISI_GUA.get((self.lower_gua, self.upper_gua), '未知卦')

        # 變卦
        changed_yaos = []
        has_change = False
        for yao in self.yaos:
            if yao['is_moving']:
                has_change = True
                changed_yaos.append({'is_yang': not yao['is_yang'], 'is_moving': False})
            else:
                changed_yaos.append(yao.copy())

        if has_change:
            bian_lower = self._get_gua_pattern(changed_yaos, 0, 3)
            bian_upper = self._get_gua_pattern(changed_yaos, 3, 6)
            self.bian_lower_gua = BAGUA_PATTERN.get(bian_lower, '坤')
            self.bian_upper_gua = BAGUA_PATTERN.get(bian_upper, '坤')
            self.biangua_name = LIUSHISI_GUA.get((self.bian_lower_gua, self.bian_upper_gua), '未知卦')
        else:
            self.biangua_name = None
            self.bian_lower_gua = None
            self.bian_upper_gua = None

        # 尋宮安世
        self.gong, self.shi_pos, self.gua_type = self._find_gong_and_shi(self.upper_gua, self.lower_gua)
        self.gong_wuxing = BAGUA[self.gong]['wuxing']

        # 安應爻
        self.ying_pos = (self.shi_pos + 3) if self.shi_pos <= 3 else (self.shi_pos - 3)

        # 六神
        self.liushen = LIUSHEN_MAP.get(self.day_gan, LIUSHEN_MAP['甲'])

        # 納甲
        lower_dizhi_list = GONG_DIZHI.get(self.lower_gua, GONG_DIZHI['乾'])
        upper_dizhi_list = GONG_DIZHI.get(self.upper_gua, GONG_DIZHI['乾'])

        if has_change and self.biangua_name:
            bian_lower_dizhi_list = GONG_DIZHI.get(self.bian_lower_gua, GONG_DIZHI['乾'])
            bian_upper_dizhi_list = GONG_DIZHI.get(self.bian_upper_gua, GONG_DIZHI['乾'])

        for i, yao in enumerate(self.yaos):
            pos = i + 1
            yao['zhi'] = lower_dizhi_list[i] if i < 3 else upper_dizhi_list[i]

            zhi_idx = DIZHI.index(yao['zhi'])
            yao['wuxing'] = DIZHI_WUXING[zhi_idx]
            yao['liuqin'] = get_liuqin(self.gong_wuxing, yao['wuxing'])
            yao['liushen'] = self.liushen[i] if i < len(self.liushen) else '青龍'
            yao['is_shi'] = (pos == self.shi_pos)
            yao['is_ying'] = (pos == self.ying_pos)
            yao['line'] = '⚊' if yao['is_yang'] else '⚋'
            yao['is_kong'] = yao['zhi'] in self.kongwang

            if yao['is_moving'] and self.biangua_name:
                variant_zhi = bian_lower_dizhi_list[i] if i < 3 else bian_upper_dizhi_list[i]
                variant_zhi_idx = DIZHI.index(variant_zhi)
                variant_wuxing = DIZHI_WUXING[variant_zhi_idx]
                variant_liuqin = get_liuqin(self.gong_wuxing, variant_wuxing)
                yao['variant'] = {
                    'is_yang': not yao['is_yang'],
                    'zhi': variant_zhi,
                    'wuxing': variant_wuxing,
                    'liuqin': variant_liuqin,
                }

    def get_shensha(self) -> List[Dict[str, Any]]:
        """計算神煞: 驛馬/桃花/日祿/貴人"""
        shensha = []
        yima_map = {'寅': '申', '申': '寅', '巳': '亥', '亥': '巳', '子': '寅', '午': '申',
                    '卯': '巳', '酉': '亥', '辰': '寅', '戌': '申', '丑': '亥', '未': '巳'}
        yima = yima_map.get(self.day_zhi, '')
        if yima:
            shensha.append({'name': '驛馬', 'zhi': [yima]})

        taohua_map = {'寅': '卯', '午': '卯', '戌': '卯', '申': '酉', '子': '酉', '辰': '酉',
                      '巳': '午', '酉': '午', '丑': '午', '亥': '子', '卯': '子', '未': '子'}
        taohua = taohua_map.get(self.day_zhi, '')
        if taohua:
            shensha.append({'name': '桃花', 'zhi': [taohua]})

        lu_map = {'甲': '寅', '乙': '卯', '丙': '巳', '戊': '巳', '丁': '午', '己': '午',
                  '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'}
        lu = lu_map.get(self.day_gan, '')
        if lu:
            shensha.append({'name': '日祿', 'zhi': [lu]})

        guiren_map = {
            '甲': ['丑', '未'], '戊': ['丑', '未'], '庚': ['丑', '未'],
            '乙': ['子', '申'], '己': ['子', '申'],
            '丙': ['亥', '酉'], '丁': ['亥', '酉'],
            '壬': ['巳', '卯'], '癸': ['巳', '卯'],
            '辛': ['午', '寅'],
        }
        guiren = guiren_map.get(self.day_gan, [])
        if guiren:
            shensha.append({'name': '貴人', 'zhi': guiren})

        return shensha

    def _get_pure_gua_lines(self, gong_name: str) -> List[Dict[str, Any]]:
        """本宮卦六爻信息 (用於查伏神)"""
        lower_dizhi = GONG_DIZHI.get(gong_name, [])
        full_dizhi = lower_dizhi + lower_dizhi
        gong_wuxing = BAGUA[gong_name]['wuxing']
        lines = []
        for zhi in full_dizhi:
            zhi_idx = DIZHI.index(zhi)
            wuxing = DIZHI_WUXING[zhi_idx]
            lines.append({'zhi': zhi, 'wuxing': wuxing, 'liuqin': get_liuqin(gong_wuxing, wuxing)})
        return lines

    def _find_fushen(self):
        """查找伏神: 本卦缺的六親從本宮卦對位補上"""
        present_liuqins = {yao['liuqin'] for yao in self.yaos}
        all_liuqins = {'兄弟', '子孫', '妻財', '父母', '官鬼'}
        missing_liuqins = all_liuqins - present_liuqins

        if missing_liuqins:
            pure_lines = self._get_pure_gua_lines(self.gong)
            for i, yao in enumerate(self.yaos):
                pure_line = pure_lines[i]
                if pure_line['liuqin'] in missing_liuqins:
                    yao['fushen'] = {
                        'liuqin': pure_line['liuqin'],
                        'zhi': pure_line['zhi'],
                        'wuxing': pure_line['wuxing'],
                    }

    def to_dict(self) -> Dict[str, Any]:
        """結構化輸出 (JSON 可序列化)"""
        self._find_fushen()

        result = {
            'yaogua': self.yaogua,
            'time': self.dt.strftime('%Y-%m-%d %H:%M:%S'),
            'bazi': self.bazi,
            'kongwang': ''.join(self.kongwang),
            'guashen': self.gong,
            'benguaming': self.bengua_name,
            'bianguaming': self.biangua_name or '無變卦',
            'gua_type': self.gua_type,
            'shensha': self.get_shensha(),
        }

        yao_names = ['yao_1', 'yao_2', 'yao_3', 'yao_4', 'yao_5', 'yao_6']
        for i, yao in enumerate(self.yaos):
            yao_data = {
                'liushen': yao['liushen'],
                'origin': {
                    'relative': yao['liuqin'],
                    'zhi': yao['zhi'],
                    'wuxing': yao['wuxing'],
                    'line': yao['line'],
                    'is_subject': yao['is_shi'],
                    'is_object': yao['is_ying'],
                    'is_changed': yao['is_moving'],
                },
            }
            if yao.get('variant'):
                yao_data['variant'] = {
                    'relative': yao['variant']['liuqin'],
                    'zhi': yao['variant']['zhi'],
                    'wuxing': yao['variant']['wuxing'],
                }
            if yao.get('fushen'):
                yao_data['origin']['fushen'] = {
                    'relative': yao['fushen']['liuqin'],
                    'zhi': yao['fushen']['zhi'],
                    'wuxing': yao['fushen']['wuxing'],
                }
            result[yao_names[i]] = yao_data

        return result

    def format_for_ai(self) -> str:
        """
        固定文字格式輸出 (供 AI 解盤 / 後續詢問各種事項)

        【基本資訊】 → 起卦時間 / 干支 / 空亡 / 神煞
        【卦象結構】 → 本卦 / 變卦 / 六神 / 伏神 / 世應 / 動爻表
        【本卦/變卦】→ 卦辭 / 象傳 / 諸事 / 愛情 / 事業 / 財運 / 建議 / 詳解
        """
        self._find_fushen()

        lines = []
        lines.append("【基本資訊】")
        lines.append(f"起卦時間：{self.dt.strftime('%Y年%m月%d日 %H:%M')}")
        lines.append(f"干支：{self.bazi}  (日空: {''.join(self.kongwang)})")
        shensha_str = " ".join([f"{s['name']}-{','.join(s['zhi'])}" for s in self.get_shensha()])
        lines.append(f"神煞：{shensha_str}")
        lines.append("")

        ben_gong_info = f"{self.gong}宮: {self.bengua_name} ({self.gua_type})"
        bian_gong_info = ""
        if self.biangua_name:
            bg_gong, _, _ = self._find_gong_and_shi(self.bian_upper_gua, self.bian_lower_gua)
            bian_gong_info = f"{bg_gong}宮: {self.biangua_name}"

        lines.append("【卦象結構】")
        lines.append(f"本卦：{ben_gong_info:<20} 變卦：{bian_gong_info}")
        lines.append("-" * 60)
        lines.append("六神  伏神        本      卦                  變      卦")
        lines.append("-" * 60)

        for i in range(5, -1, -1):
            yao = self.yaos[i]

            ls = f"{yao['liushen']}"
            fs = ""
            if yao.get('fushen'):
                fs = f"{yao['fushen']['liuqin']}{yao['fushen']['zhi']}{yao['fushen']['wuxing']}"

            ben_marks = []
            if yao['is_shi']:
                ben_marks.append('世')
            if yao['is_ying']:
                ben_marks.append('應')

            ben_info = f"{yao['liuqin']}{yao['zhi']}{yao['wuxing']}"
            ben_line = '▅▅▅▅▅' if yao['is_yang'] else '▅▅　▅▅'
            if yao['is_moving']:
                ben_line += " O" if yao['is_yang'] else " X"

            bian_str = ""
            if yao.get('variant'):
                bian_info = f"{yao['variant']['liuqin']}{yao['variant']['zhi']}{yao['variant']['wuxing']}"
                bian_line = '▅▅▅▅▅' if yao['variant']['is_yang'] else '▅▅　▅▅'
                bian_str = f"→ {bian_info} {bian_line}"

            lines.append(f"{ls:<4} {fs:<10} {ben_info:<8} {ben_line:<8} {','.join(ben_marks):<4} {bian_str}")

        lines.append("-" * 60)
        lines.append("")

        # 動爻爻辭（底本《周易正義》）: 供解卦引用，不心算、不編造
        moving = [i for i, y in enumerate(self.yaos) if y['is_moving']]
        lines.append("【動爻爻辭】")
        if moving:
            for i in moving:
                yao_ci = get_yao_text(self.bengua_name, i + 1)
                label = yao_ci['pos'] if yao_ci else f"第{i + 1}爻"
                text = yao_ci['text'] if yao_ci else "（無爻辭資料）"
                lines.append(f"第{i + 1}爻（{label}）：{text}")
            if len(moving) == 6:
                yong = get_yong_text(self.bengua_name)
                if yong:
                    lines.append(f"{yong['pos']}：{yong['text']}")
        else:
            lines.append("無動爻（靜卦：依月日旺衰、世應、用神推斷趨勢與應期，不以「無動爻」當作無訊號）")
        lines.append("")

        for label, gua_name in (("本卦", self.bengua_name), ("變卦", self.biangua_name)):
            if not gua_name or gua_name == '未知卦':
                continue
            hexagram = get_hexagram(gua_name)
            if not hexagram:
                continue
            lines.append(f"【{label}：{gua_name}】")
            if hexagram.get('core_text'):
                lines.append(f"卦辭：{hexagram['core_text']}")
            if hexagram.get('xiang_text'):
                lines.append(f"象傳：{hexagram['xiang_text']}")
            if hexagram.get('general'):
                lines.append(f"諸事：{hexagram['general']}")
            if hexagram.get('love'):
                lines.append(f"愛情：{hexagram['love']}")
            if hexagram.get('career'):
                lines.append(f"事業：{hexagram['career']}")
            if hexagram.get('wealth'):
                lines.append(f"財運：{hexagram['wealth']}")
            if hexagram.get('advice'):
                lines.append(f"建議：{hexagram['advice']}")
            if hexagram.get('detailed_explanation'):
                lines.append(f"詳解：{hexagram['detailed_explanation']}")
            lines.append("")

        return "\n".join(lines).strip()
