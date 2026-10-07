"""奇門遁甲排盤核心 (時家・拆補法・轉盤・陽盤, Standalone 零安裝)。

以節氣＋三元定局，布地盤三奇六儀，定值符值使，轉天盤九星、布八門八神。
時盤供問事，終身盤以生時局＋年干命宮（《奇門遁甲統宗》「人取年干為命」）。

用法:
    from qimen_core import QiMenChart
    chart = QiMenChart(datetime(...))                 # 時盤
    chart = QiMenChart(datetime(...), lifetime=True, year_gan='庚')  # 終身盤
    chart.to_dict() / chart.format_for_ai()

流派: 拆補法定局、轉盤、陽盤（節氣陰陽遁）；八神用現代通行八神。
文獻: 《奇門遁甲統宗》《奇門遁甲元靈經》《奇門法竅》。
"""
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "vendor"))
from lunar_python import Solar  # noqa: E402

TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
HE_GAN = {'甲': '己', '己': '甲', '乙': '庚', '庚': '乙', '丙': '辛', '辛': '丙',
          '丁': '壬', '壬': '丁', '戊': '癸', '癸': '戊'}

# 洛書九宮: 宮號 → (方位, 五行, 八卦)
GONG_INFO = {
    1: ('北', '水', '坎'), 2: ('西南', '土', '坤'), 3: ('東', '木', '震'),
    4: ('東南', '木', '巽'), 5: ('中', '土', '中'), 6: ('西北', '金', '乾'),
    7: ('西', '金', '兌'), 8: ('東北', '土', '艮'), 9: ('南', '火', '離'),
}
# 洛書九宮顯示布局 (3x3, 依 4 9 2 / 3 5 7 / 8 1 6)
GONG_GRID = [[4, 9, 2], [3, 5, 7], [8, 1, 6]]
# 後天八卦順時針八宮 (八門/八神旋轉用, 跳中宮)
RING8 = [1, 8, 3, 4, 9, 2, 7, 6]

# 固定九星 (洛書數 1..9)
STAR_FIXED = {1: '天蓬', 2: '天芮', 3: '天冲', 4: '天辅', 5: '天禽',
              6: '天心', 7: '天柱', 8: '天任', 9: '天英'}
STAR_WX = {'天蓬': '水', '天芮': '土', '天冲': '木', '天辅': '木', '天禽': '土',
           '天心': '金', '天柱': '金', '天任': '土', '天英': '火'}
STAR_LUCK = {'天蓬': '凶', '天芮': '凶', '天冲': '小吉', '天辅': '吉', '天禽': '吉',
             '天心': '吉', '天柱': '凶', '天任': '吉', '天英': '小凶'}
STAR_DESC = {'天蓬': '盜賊、水險、智謀', '天芮': '疾病、師傅、遲滯', '天冲': '衝動、行動、征伐',
             '天辅': '文教、輔佐、溫和', '天禽': '中正、包容、貴人', '天心': '醫藥、謀略、領導',
             '天柱': '口舌、破壞、阻隔', '天任': '穩重、田產、任事', '天英': '文采、虛華、火災'}

# 固定八門 (宮 → 門)
GATE_FIXED = {1: '休', 8: '生', 3: '傷', 4: '杜', 9: '景', 2: '死', 7: '驚', 6: '開'}
GATE_WX = {'休': '水', '生': '土', '傷': '木', '杜': '木', '景': '火', '死': '土', '驚': '金', '開': '金'}
GATE_LUCK = {'休': '吉', '生': '吉', '傷': '凶', '杜': '平', '景': '平', '死': '凶', '驚': '凶', '開': '吉'}
GATE_DESC = {'休': '休息、安穩、求財婚戀', '生': '生財、產業、求財吉', '傷': '傷害、爭鬥、捕獵',
             '杜': '閉塞、隱藏、躲藏', '景': '文書、訊息、遠行', '死': '死喪、田土、弔喪',
             '驚': '驚恐、口舌、官非', '開': '開創、通達、謁貴'}
GATE_ORDER = ['休', '生', '傷', '杜', '景', '死', '驚', '開']

# 八神 (現代通行八神; 陽遁順、陰遁逆 於八宮環)
GOD_ORDER = ['值符', '螣蛇', '太陰', '六合', '白虎', '玄武', '九地', '九天']
GOD_LUCK = {'值符': '吉', '螣蛇': '凶', '太陰': '吉', '六合': '吉',
            '白虎': '凶', '玄武': '凶', '九地': '吉', '九天': '吉'}
GOD_DESC = {'值符': '貴人、主帥、天時', '螣蛇': '虛驚、怪異、反覆', '太陰': '陰柔、暗助、女人',
            '六合': '和合、婚姻、中介', '白虎': '凶傷、爭鬥、道路', '玄武': '盜賊、暗昧、走失',
            '九地': '厚重、田土、守成', '九天': '高遠、出行、揚名'}

# 十干克應 (天盤干, 地盤干) → 格名 (《奇門遁甲元靈經》《奇門法竅》)
KE_YING = {
    ('戊', '乙'): '青龍合靈', ('戊', '丙'): '青龍返首', ('戊', '丁'): '青龍耀明',
    ('戊', '己'): '貴人入獄', ('戊', '庚'): '值符飛宮', ('戊', '辛'): '青龍折足',
    ('戊', '壬'): '青龍入天牢', ('戊', '癸'): '青龍華蓋',
    ('乙', '戊'): '利陰害陽', ('乙', '丙'): '奇儀順遂', ('乙', '丁'): '奇儀相佐',
    ('乙', '己'): '日奇入墓', ('乙', '庚'): '日奇被刑', ('乙', '辛'): '青龍逃走',
    ('乙', '壬'): '日奇入地', ('乙', '癸'): '華蓋逢星',
    ('丙', '戊'): '飛鳥跌穴', ('丙', '乙'): '日月並行', ('丙', '丁'): '星隨月轉',
    ('丙', '己'): '火悖入刑', ('丙', '庚'): '熒入太白', ('丙', '辛'): '日月相會',
    ('丙', '壬'): '火入天羅', ('丙', '癸'): '華蓋悖師',
    ('丁', '戊'): '青龍轉光', ('丁', '乙'): '奇儀相合', ('丁', '丙'): '星隨月轉',
    ('丁', '己'): '朱雀入獄', ('丁', '庚'): '文書阻隔', ('丁', '辛'): '朱雀入獄',
    ('丁', '壬'): '五神互合', ('丁', '癸'): '朱雀投江',
    ('庚', '戊'): '太白天乙伏宮', ('庚', '乙'): '太白逢星', ('庚', '丙'): '太白入熒',
    ('庚', '丁'): '亭亭之格', ('庚', '己'): '刑格', ('庚', '庚'): '太白同宮',
    ('庚', '辛'): '白虎干格', ('庚', '壬'): '小格', ('庚', '癸'): '大格',
    ('辛', '戊'): '困龍被傷', ('辛', '乙'): '白虎猖狂', ('辛', '丙'): '干合悖師',
    ('辛', '丁'): '獄神得奇', ('辛', '己'): '入獄自刑', ('辛', '庚'): '白虎出力',
    ('辛', '壬'): '凶蛇入獄', ('辛', '癸'): '天牢華蓋',
    ('壬', '戊'): '小蛇化龍', ('壬', '乙'): '小蛇得勢', ('壬', '丙'): '水蛇入火',
    ('壬', '丁'): '干合蛇刑', ('壬', '己'): '反吟蛇刑', ('壬', '庚'): '太白擒蛇',
    ('壬', '辛'): '騰蛇相纏', ('壬', '癸'): '幼女奸淫',
    ('癸', '戊'): '天乙會合', ('癸', '乙'): '華蓋逢星', ('癸', '丙'): '華蓋悖師',
    ('癸', '丁'): '螣蛇夭矯', ('癸', '己'): '華蓋地戶', ('癸', '庚'): '太白入網',
    ('癸', '辛'): '網蓋天牢', ('癸', '壬'): '復見騰蛇', ('癸', '癸'): '天網四張',
    ('己', '戊'): '犬遇青龍', ('己', '乙'): '墓神不明', ('己', '丙'): '火悖地戶',
    ('己', '丁'): '朱雀入墓', ('己', '己'): '地戶逢鬼', ('己', '庚'): '利格',
    ('己', '辛'): '遊魂入墓', ('己', '壬'): '地網高張', ('己', '癸'): '地刑玄武',
    # 同干 (伏吟)
    ('戊', '戊'): '伏吟', ('乙', '乙'): '日奇伏吟', ('丙', '丙'): '月奇悖師',
    ('丁', '丁'): '星奇伏吟', ('庚', '庚'): '太白同宮', ('辛', '辛'): '伏吟天庭',
    ('壬', '壬'): '蛇入地羅',
}
GEFU_JI = {'青龍返首', '飛鳥跌穴', '青龍合靈', '青龍耀明', '奇儀順遂', '奇儀相佐',
           '星隨月轉', '青龍轉光', '五神互合', '小蛇化龍', '小蛇得勢', '天乙會合',
           '奇儀相合', '獄神得奇'}
# 十干墓宮 (三奇六儀入墓用): 甲未坤2、乙丙戊戌乾6、丁己庚丑艮8、辛壬辰巽4、癸未坤2
GAN_MU = {'甲': 2, '乙': 6, '丙': 6, '丁': 8, '戊': 6, '己': 8, '庚': 8, '辛': 4, '壬': 4, '癸': 2}
# 八門墓宮: 休生死墓巽4、傷杜墓坤2、景墓乾6、驚開墓艮8
GATE_MU = {'休': 4, '生': 4, '死': 4, '傷': 2, '杜': 2, '景': 6, '驚': 8, '開': 8}

# 地盤三奇六儀 布序 (陽遁順、陰遁逆)
YI_ORDER = ['戊', '己', '庚', '辛', '壬', '癸', '丁', '丙', '乙']
XUNSHOU_YI = {'甲子': '戊', '甲戌': '己', '甲申': '庚', '甲午': '辛', '甲辰': '壬', '甲寅': '癸'}

# 節氣 → (上元, 中元, 下元) 局數 (拆補法)
JIEQI_JU = {
    '冬至': (1, 7, 4), '小寒': (2, 8, 5), '大寒': (3, 9, 6),
    '立春': (8, 5, 2), '雨水': (9, 6, 3), '驚蟄': (1, 7, 4), '惊蛰': (1, 7, 4),
    '春分': (3, 9, 6), '清明': (4, 1, 7), '穀雨': (5, 2, 8), '谷雨': (5, 2, 8),
    '立夏': (4, 1, 7), '小滿': (5, 2, 8), '小满': (5, 2, 8), '芒種': (6, 3, 9), '芒种': (6, 3, 9),
    '夏至': (9, 3, 6), '小暑': (8, 2, 5), '大暑': (7, 1, 4),
    '立秋': (2, 5, 8), '處暑': (1, 4, 7), '处暑': (1, 4, 7), '白露': (9, 3, 6),
    '秋分': (7, 1, 4), '寒露': (6, 9, 3), '霜降': (5, 8, 2),
    '立冬': (6, 9, 3), '小雪': (5, 8, 2), '大雪': (4, 7, 1),
}
YANG_JIEQI = {'冬至', '小寒', '大寒', '立春', '雨水', '驚蟄', '惊蛰', '春分', '清明', '穀雨', '谷雨',
              '立夏', '小滿', '小满', '芒種', '芒种'}
JIEQI_24 = list(JIEQI_JU.keys())


def _num(m: int) -> int:
    """洛書數 1..9 循環。"""
    return (m - 1) % 9 + 1


def _ring_pos(gong: int) -> int:
    """宮號在八宮環 (RING8) 的位置; 中宮5寄坤2。"""
    return RING8.index(2 if gong == 5 else gong)


def _xunshou(gz: str) -> str:
    g = TIANGAN.index(gz[0]); z = DIZHI.index(gz[1])
    return '甲' + DIZHI[(z - g) % 12]


def prev_jieqi(dt: datetime) -> Tuple[str, str]:
    """回 (節氣名, 時間字串): 起課時刻之前最近的 24 節氣。"""
    solar = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, 0)
    lunar = solar.getLunar()
    table = lunar.getJieQiTable()
    best = None; best_name = None
    for name, s in table.items():
        if name not in JIEQI_JU:
            continue
        st = datetime(s.getYear(), s.getMonth(), s.getDay(), s.getHour(), s.getMinute())
        if st <= dt and (best is None or st > best):
            best = st; best_name = name
    if best is None:  # 退回用前一個中氣
        q = lunar.getPrevQi()
        return (q.getName(), q.getSolar().toYmdHms())
    return best_name, best.strftime('%Y-%m-%d %H:%M')


def yuan_of_day(day_gz: str) -> Tuple[str, str]:
    """由日干支的符頭定三元 (子午卯酉上元/寅申巳亥中元/辰戌丑未下元)。回 (元, 符頭干支)。"""
    g = TIANGAN.index(day_gz[0]); z = DIZHI.index(day_gz[1])
    off = g % 5
    fz = (z - off) % 12
    futou = TIANGAN[(g - off) % 10] + DIZHI[fz]
    if DIZHI[fz] in '子午卯酉':
        return '上元', futou
    if DIZHI[fz] in '寅申巳亥':
        return '中元', futou
    return '下元', futou


def ju_number(jieqi: str, yuan: str) -> int:
    idx = {'上元': 0, '中元': 1, '下元': 2}[yuan]
    return JIEQI_JU[jieqi][idx]


def dipan(yin_yang: str, ju: int) -> Dict[int, str]:
    """地盤三奇六儀: {宮: 干}。陽遁自局數宮順布, 陰遁逆布。"""
    out = {}
    for i, yi in enumerate(YI_ORDER):
        if yin_yang == '陽':
            gong = _num(ju + i)
        else:
            gong = _num(ju - i)
        out[gong] = yi
    return out


def _ring_rotate(base: Dict[int, Any], offset: int) -> Dict[int, Any]:
    """八宮環 (RING8) 旋轉 offset 格。"""
    out = {}
    for i, gong in enumerate(RING8):
        out[gong] = base[RING8[(i - offset) % 8]]
    return out


class QiMenChart:
    def __init__(self, dt: datetime, lifetime: bool = False,
                 year_gan: Optional[str] = None, year_zhi: Optional[str] = None):
        self.dt = dt
        self.lifetime = lifetime
        solar = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, 0)
        self.lunar = solar.getLunar()
        self.year_gz = self.lunar.getYearInGanZhi()
        self.mon_gz = self.lunar.getMonthInGanZhi()
        # 奇門採子時換日 (23:00 起算次日); 時干支沿用 lunar (夜子時用次日子干)
        day_date = (dt + timedelta(hours=1)).date() if dt.hour == 23 else dt.date()
        self.day_gz = Solar.fromYmd(day_date.year, day_date.month, day_date.day).getLunar().getDayInGanZhi()
        self.hour_gz = self.lunar.getTimeInGanZhi()
        self.year_gan = year_gan or self.year_gz[0]
        self.year_zhi = year_zhi or self.year_gz[1]
        self.jieqi, self.jieqi_time = prev_jieqi(dt)
        self.yin_yang = '陽' if self.jieqi in YANG_JIEQI else '陰'
        self.yuan, self.futou = yuan_of_day(self.day_gz)
        self.ju = ju_number(self.jieqi, self.yuan)
        self._build()

    def _build(self):
        self.dipan = dipan(self.yin_yang, self.ju)  # {宮: 儀/奇}
        # 旬首與值符值使
        self.xunshou = _xunshou(self.hour_gz)
        self.zhifu_yi = XUNSHOU_YI[self.xunshou]
        self.zhifu_gong = next(g for g, v in self.dipan.items() if v == self.zhifu_yi)
        self.zhifu_star = STAR_FIXED[self.zhifu_gong]
        # 值使門: 旬首落中五宮時無固定門, 寄坤二 (與值使宮同例)
        self.zhishi_gate = GATE_FIXED[2 if self.zhifu_gong == 5 else self.zhifu_gong]
        # 時干落宮 (甲用旬首儀)
        hour_gan = self.hour_gz[0]
        tg_yi = self.zhifu_yi if hour_gan == '甲' else hour_gan
        self.hour_gan_gong = next(g for g, v in self.dipan.items() if v == tg_yi)
        # 天盤 (轉盤): 九星/儀 旋轉 offset = 時干宮 - 值符宮 (洛書數)
        off = (self.hour_gan_gong - self.zhifu_gong) % 9
        self.tianpan_yi = {g: self.dipan[_num(g - off)] for g in range(1, 10)}
        self.tianpan_star = {g: STAR_FIXED[_num(g - off)] for g in range(1, 10)}
        # 八門: 值使隨時宮 → 洛書數移位 (陽順陰逆)
        n = (DIZHI.index(self.hour_gz[1]) - DIZHI.index(self.xunshou[1])) % 12
        step = n if self.yin_yang == '陽' else -n
        zhishi_gong = _num(self.zhifu_gong + step)
        if zhishi_gong == 5:      # 中宮無門, 寄坤二
            zhishi_gong = 2
        self.zhishi_gong = zhishi_gong
        gate_off = (_ring_pos(zhishi_gong) - _ring_pos(self.zhifu_gong)) % 8
        self.tianpan_gate = _ring_rotate(GATE_FIXED, gate_off)
        # 八神: 值符神隨值符星落宮 (時干宮), 陽順陰逆 於八宮環
        i0 = _ring_pos(self.hour_gan_gong)
        self.tianpan_god = {}
        for k, god in enumerate(GOD_ORDER):
            idx = (i0 + k) % 8 if self.yin_yang == '陽' else (i0 - k) % 8
            self.tianpan_god[RING8[idx]] = god
        # 終身盤命宮 (年干落宮, 甲用旬首儀)
        self.ming_gong = None
        self.qin_gong = {}
        if self.lifetime:
            self.ming_gong = self._gan_gong(self.year_gan)
            self.day_gan_gong = self._gan_gong(self.day_gz[0])
            # 六親宮: 年干父、年干合干母、月干兄弟、日干本人、時干子女
            self.qin_gong = {
                '父': self.ming_gong,
                '母': self._gan_gong(HE_GAN[self.year_gan]),
                '兄弟': self._gan_gong(self.mon_gz[0]),
                '本人': self.day_gan_gong,
                '子女': self._gan_gong(self.hour_gz[0]),
            }

    def _gan_gong(self, gan: str) -> int:
        yi = self.zhifu_yi if gan == '甲' else gan
        for g, v in self.dipan.items():
            if v == yi:
                return g
        return self.zhifu_gong

    def _daxian(self) -> List[Dict[str, Any]]:
        """大限: 命宮起、順時針八宮、每宮 9 年。"""
        if self.ming_gong is None:
            return []
        start = self.ming_gong if self.ming_gong in RING8 else 2  # 中宮寄坤2
        i0 = RING8.index(start)
        out = []
        for k in range(8):
            gong = RING8[(i0 + k) % 8]
            out.append({'gong': gong, 'age': f'{k * 9}-{k * 9 + 8}歲'})
        return out

    # ---- 格局 ----
    def geju(self) -> List[str]:
        tags = []
        # 伏吟 / 反吟
        if all(self.tianpan_yi[g] == self.dipan[g] for g in range(1, 10)):
            tags.append('伏吟')
        gate_off = (_ring_pos(self.zhishi_gong) - _ring_pos(self.zhifu_gong)) % 8
        if gate_off == 4:
            tags.append('反吟')
        # 十干克應 (天盤干 + 地盤干)
        for g in range(1, 10):
            pair = (self.tianpan_yi[g], self.dipan[g])
            if pair in KE_YING:
                mark = '吉' if KE_YING[pair] in GEFU_JI else '凶'
                tags.append(f"{KE_YING[pair]}[{pair[0]}+{pair[1]}·{mark}]")
        # 門迫 (門剋宮)
        for g in RING8:
            gate = self.tianpan_gate[g]
            if _ke(GATE_WX[gate], GONG_INFO[g][1]):
                tags.append(f'{gate}門迫{g}宮')
        # 三奇得使: 乙丙丁 天盤干 臨 開休生三吉門
        for g in RING8:
            if self.tianpan_yi[g] in ('乙', '丙', '丁') and self.tianpan_gate[g] in ('開', '休', '生'):
                tags.append(f"{self.tianpan_yi[g]}奇得使{g}宮")
        # 六儀擊刑
        JIXING = {'戊': 3, '己': 2, '庚': 8, '辛': 9, '壬': 4, '癸': 4}
        for g in RING8:
            yi = self.tianpan_yi[g]
            if JIXING.get(yi) == g:
                tags.append(f'{yi}儀擊刑')
        # 三奇入墓 / 六儀入墓 (天盤干落墓宮)
        for g in range(1, 10):
            yi = self.tianpan_yi[g]
            if GAN_MU.get(yi) == g:
                tags.append(f"{yi}{'奇' if yi in '乙丙丁' else '儀'}入墓")
        # 八門入墓 (天盤門落墓宮)
        for g in RING8:
            gate = self.tianpan_gate[g]
            if GATE_MU.get(gate) == g:
                tags.append(f'{gate}門入墓')
        # 五不遇時 (時干剋日干, 同陰陽)
        if self.hour_gz[0] == TIANGAN[(TIANGAN.index(self.day_gz[0]) + 6) % 10]:
            tags.append('五不遇時')
        # 天網四張 (時干癸)
        if self.hour_gz[0] == '癸':
            tags.append('天網四張')
        # 三遁 (簡式: 天盤奇臨對應吉門)
        for g in RING8:
            yi, gate = self.tianpan_yi[g], self.tianpan_gate[g]
            if yi == '丙' and gate == '生':
                tags.append('天遁')
            elif yi == '乙' and gate == '開':
                tags.append('地遁')
            elif yi == '丁' and gate == '休':
                tags.append('人遁')
        # 玉女守門 (丁奇臨值使門)
        for g in RING8:
            if self.tianpan_yi[g] == '丁' and g == self.zhishi_gong:
                tags.append('玉女守門')
        return list(dict.fromkeys(tags))

    # ---- 輸出 ----
    def to_dict(self) -> Dict[str, Any]:
        sizhu = {'year': self.year_gz, 'month': self.mon_gz, 'day': self.day_gz, 'hour': self.hour_gz}
        gong = {}
        for g in range(1, 10):
            gong[g] = {
                'gong': g, 'bagua': GONG_INFO[g][2], 'fangwei': GONG_INFO[g][0], 'wuxing': GONG_INFO[g][1],
                'dipan_gan': self.dipan[g],
                'tianpan_gan': self.tianpan_yi.get(g),
                'star': self.tianpan_star.get(g),
                'gate': self.tianpan_gate.get(g) if g in RING8 else '（中宮無門）',
                'god': self.tianpan_god.get(g) if g in RING8 else '（中宮無神）',
            }
        return {
            'time': self.dt.strftime('%Y-%m-%d %H:%M:%S'),
            'lifetime': self.lifetime,
            'sizhu': sizhu,
            'jieqi': self.jieqi, 'jieqi_time': self.jieqi_time,
            'yin_yang': self.yin_yang, 'yuan': self.yuan, 'futou': self.futou, 'ju': self.ju,
            'xunshou': self.xunshou, 'zhifu_yi': self.zhifu_yi,
            'zhifu_star': self.zhifu_star, 'zhifu_gong': self.zhifu_gong,
            'zhishi_gate': self.zhishi_gate, 'zhishi_gong': self.zhishi_gong,
            'hour_gan_gong': self.hour_gan_gong,
            'gong': gong,
            'geju': self.geju(),
            'ming_gong': self.ming_gong,
            'day_gan_gong': getattr(self, 'day_gan_gong', None),
            'qin_gong': self.qin_gong,
            'daxian': self._daxian(),
        }

    def format_for_ai(self) -> str:
        d = self.to_dict()
        L = []
        L.append('【奇門遁甲】' + ('（終身盤）' if self.lifetime else '（時盤）'))
        sz = d['sizhu']
        L.append(f"起局時間：{self.dt.strftime('%Y年%m月%d日 %H:%M')}（{sz['year']}年 {sz['month']}月 {sz['day']}日 {sz['hour']}時）")
        L.append(f"{self.yin_yang}遁 {self.ju} 局（{self.jieqi} {self.yuan}，符頭 {self.futou}）　"
                 f"旬首 {self.xunshou}（{self.zhifu_yi}）")
        L.append(f"值符：{self.zhifu_star}（{self.zhifu_gong}宮）　值使：{self.zhishi_gate}門（{self.zhishi_gong}宮）　"
                 f"時干落 {self.hour_gan_gong}宮")
        if self.geju():
            L.append(f"格局：{'、'.join(self.geju())}")
        if self.lifetime and self.ming_gong:
            L.append(f"命宮（年干 {self.year_gan} 落宮）：{self.ming_gong}宮（{GONG_INFO[self.ming_gong][2]}{GONG_INFO[self.ming_gong][0]}）")
            if self.qin_gong:
                qg = '　'.join(f"{k}{v}宮" for k, v in self.qin_gong.items())
                L.append(f"六親宮（年干父/合干母/月干兄弟/日干本人/時干子女；雙胞胎看兄弟宮與本人宮）：{qg}")
        L.append('')
        L.append('【九宮】（宮 八卦方位 五行｜地盤干／天盤干 九星 八門 八神）')
        for row in GONG_GRID:
            cells = []
            for g in row:
                c = d['gong'][g]
                cells.append(f"{g}宮{c['bagua']}{c['fangwei']}｜{c['dipan_gan']}/{c['tianpan_gan']} "
                             f"{c['star']} {c['gate']} {c['god']}")
            L.append('　'.join(cells))
        if self.lifetime and d['daxian']:
            L.append('')
            L.append('【大限】（命宮起、順時針、每宮9年）')
            L.append('　'.join(f"{x['age']}→{x['gong']}宮" for x in d['daxian']))
        return '\n'.join(L)


def _ke(a: str, b: str) -> bool:
    KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}
    return KE.get(a) == b
