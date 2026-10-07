"""大六壬排盤核心 (Standalone, 零安裝)。

以「月將加占時」起天地盤，依九宗門取三傳，布十二天將，附遁干/旬空/六親/神煞/年命/課體。

用法:
    from liuren_core import LiuRenChart
    chart = LiuRenChart(datetime.now(), birth=[(1990, '女')])   # birth 可省略
    chart.to_dict()        # 結構化資料
    chart.format_for_ai()  # 固定文字格式 (給 AI 解盤)

規則出處: 《六壬大全》九宗門、《六壬指南》月將/貴人、《御定六壬直指》課體。
月將以「中氣換將」；天將以「晝夜貴人順逆」布。
"""
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "vendor"))  # 內嵌 lunar_python
from lunar_python import Solar  # noqa: E402

# ========== 基礎數據 ==========

DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
DAYS60 = [TIANGAN[i % 10] + DIZHI[i % 12] for i in range(60)]

DZ_WX = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
         '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'}
TG_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
         '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}

# 日干寄宮
GAN_JI = {'甲': '寅', '乙': '辰', '丙': '巳', '丁': '未', '戊': '巳',
          '己': '未', '庚': '申', '辛': '戌', '壬': '亥', '癸': '丑'}
# 地盤支的寄干 (含寄宮雙干)
JI_GANS = {'寅': ['甲'], '辰': ['乙'], '巳': ['丙', '戊'], '未': ['丁', '己'],
           '申': ['庚'], '戌': ['辛'], '亥': ['壬'], '丑': ['癸']}

JIANG12 = ['貴', '蛇', '朱', '合', '勾', '青', '空', '虎', '常', '玄', '陰', '后']
JIANG_FULL = {'貴': '貴人', '蛇': '螣蛇', '朱': '朱雀', '合': '六合', '勾': '勾陳',
              '青': '青龍', '空': '天空', '虎': '白虎', '常': '太常', '玄': '玄武',
              '陰': '太陰', '后': '天后'}
JIANG_WX = {'貴': '土', '蛇': '火', '朱': '火', '合': '木', '勾': '土', '青': '木',
            '空': '土', '虎': '金', '常': '土', '玄': '水', '陰': '金', '后': '水'}

# 晝貴 / 夜貴 (甲戊庚牛羊、乙己鼠猴、丙丁豬雞、壬癸兔蛇、六辛逢馬虎)
GUI = {'甲': ('丑', '未'), '戊': ('丑', '未'), '庚': ('丑', '未'),
       '乙': ('子', '申'), '己': ('子', '申'),
       '丙': ('亥', '酉'), '丁': ('亥', '酉'),
       '壬': ('巳', '卯'), '癸': ('巳', '卯'),
       '辛': ('午', '寅')}

# 十二神將 (月將)
JIANG_NAME = {'子': '神后', '丑': '大吉', '寅': '功曹', '卯': '太沖', '辰': '天罡',
              '巳': '太乙', '午': '勝光', '未': '小吉', '申': '傳送', '酉': '從魁',
              '戌': '河魁', '亥': '登明'}
# 月將主事 (《占事略決·十二月將所主》)
JIANG_MAIN = {
    '亥': '河神／牢獄鬥訟', '戌': '土神／口舌婦人', '酉': '竈神／移徙搖動',
    '申': '道路神／遠行商賣', '未': '天井／酒食廚膳', '午': '外竈／五穀口舌',
    '巳': '內竈／船車相連', '辰': '土神／疾病死喪', '卯': '社樹／林木船車',
    '寅': '大樹／徵召長史', '丑': '山神／六畜宮土', '子': '北辰／婦女陰私',
}
# 所勝法 (《六壬神定經·釋將傳》): 五氣所勝所憂
SUOSHENG = {'旺': '縣官', '相': '財物', '死': '死喪', '囚': '囚系', '休': '疾病'}
# 中氣 -> 月將 (中氣換將)
QI_TO_JIANG = {'雨水': '亥', '春分': '戌', '谷雨': '酉', '穀雨': '酉', '小滿': '申',
               '夏至': '未', '大暑': '午', '處暑': '巳', '处暑': '巳', '秋分': '辰',
               '霜降': '卯', '小雪': '寅', '冬至': '丑', '大寒': '子'}

XING = {'子': '卯', '卯': '子', '寅': '巳', '巳': '申', '申': '寅', '丑': '戌',
        '戌': '未', '未': '丑', '辰': '辰', '午': '午', '酉': '酉', '亥': '亥'}
HE_GAN = {'甲': '己', '己': '甲', '乙': '庚', '庚': '乙', '丙': '辛', '辛': '丙',
          '丁': '壬', '壬': '丁', '戊': '癸', '癸': '戊'}
SANHE_FRONT = {'寅': '午', '午': '戌', '戌': '寅', '申': '子', '子': '辰', '辰': '申',
               '巳': '酉', '酉': '丑', '丑': '巳', '亥': '卯', '卯': '未', '未': '亥'}
YIMA = {'寅': '申', '申': '寅', '巳': '亥', '亥': '巳', '子': '寅', '午': '申',
        '卯': '巳', '酉': '亥', '辰': '寅', '戌': '申', '丑': '亥', '未': '巳'}
MENG = {'寅', '申', '巳', '亥'}
ZHONG = {'子', '午', '卯', '酉'}

SANHE_SETS = [{'亥', '卯', '未'}, {'寅', '午', '戌'}, {'巳', '酉', '丑'}, {'申', '子', '辰'}]
WX_HEJU = {'木': '曲直', '火': '炎上', '土': '稼穡', '金': '從革', '水': '潤下'}

# 六親縮寫
LIUQIN_FULL = {'父': '父母', '兄': '兄弟', '子': '子孫', '財': '妻財', '官': '官鬼'}


def zi(z: str) -> int:
    return DIZHI.index(z)


def chong(z: str) -> str:
    return DIZHI[(zi(z) + 6) % 12]


def wxz(z: str) -> str:
    return DZ_WX[z]


def wxg(g: str) -> str:
    return TG_WX[g]


def yang_gan(g: str) -> bool:
    return TIANGAN.index(g) % 2 == 0


def yang_zhi(z: str) -> bool:
    return zi(z) % 2 == 0


def xunshou(dg: str) -> str:
    g = TIANGAN.index(dg[0]); z = zi(dg[1])
    return DIZHI[(z - g) % 12]


def wangxiang(month_zhi: str) -> Dict[str, str]:
    """月令五氣旺相死囚休 (《六壬神定經》): 旺=月支五行, 相=我生, 死=我剋, 囚=剋我, 休=生我。"""
    w = wxz(month_zhi)
    qiu = next(k for k, v in KE.items() if v == w)      # 剋我
    xiu = next(k for k, v in SHENG.items() if v == w)   # 生我
    return {'旺': w, '相': SHENG[w], '死': KE[w], '囚': qiu, '休': xiu}


def kongwang(dg: str) -> List[str]:
    x = zi(xunshou(dg))
    return [DIZHI[(x + 10) % 12], DIZHI[(x + 11) % 12]]


def dungan(dg: str, z: str) -> Optional[str]:
    """遁干: 該支在日旬中所配天干; 空亡則 None。"""
    x = zi(xunshou(dg)); off = (zi(z) - x) % 12
    return TIANGAN[off] if off < 10 else None


def liuqin(dg: str, z: str) -> str:
    dw = wxg(dg[0]); zw = wxz(z)
    if dw == zw:
        return '兄'
    if SHENG[zw] == dw:
        return '父'
    if SHENG[dw] == zw:
        return '子'
    if KE[dw] == zw:
        return '財'
    return '官'


# ========== 天地盤 / 四課 ==========

def tianpan(shift: int) -> Dict[str, str]:
    """天盤: tianpan[地盤支] = 天盤支。shift = 月將 - 占時。"""
    return {d: DIZHI[(zi(d) + shift) % 12] for d in DIZHI}


def four_lessons(dg: str, shift: int) -> Tuple[List[str], List[str]]:
    """四課 (京房): 回 (上神[4,3,2,1], 下神/干[4,3,2,1])。
    第一課=干陽神(日干寄宮之上神)、第二課=干陰神、第三課=支陽神、第四課=支陰神。"""
    tp = tianpan(shift); g = dg[0]; z = dg[1]; ji = GAN_JI[g]
    k1s = tp[ji]; k2s = tp[k1s]; k3s = tp[z]; k4s = tp[k3s]
    return [k4s, k3s, k2s, k1s], [k3s, z, k1s, g]


def _zei(xia: str, shang: str) -> bool:
    """下賊上: 下神剋上神。"""
    xw = wxg(xia) if xia in TIANGAN else wxz(xia)
    return KE[xw] == wxz(shang)


def _ke(shang: str, xia: str) -> bool:
    """上剋下: 上神剋下神。"""
    xw = wxg(xia) if xia in TIANGAN else wxz(xia)
    return KE[wxz(shang)] == xw


# ========== 三傳 (九宗門) ==========

def _shehai_score(c: str, shift: int) -> int:
    """涉害深淺: 自候選上神之天盤宮位逆數至其地盤本家, 數沿途地盤支(含寄干)
    與候選者相剋(任一方向)之次數。九宗門涉害流派不一, 此處採與驗證基準一致之計法。"""
    tp = tianpan(shift); inv = {v: k for k, v in tp.items()}
    s = zi(inv[c]); e = zi(c); cnt = 0; k = (s - 1) % 12
    cw = wxz(c)
    while k != e:
        d = DIZHI[k]
        for x in [wxz(d)] + [wxg(g) for g in JI_GANS.get(d, [])]:
            if KE[x] == cw or KE[cw] == x:
                cnt += 1
        k = (k - 1) % 12
    return cnt


def _pick(cands: List[str], dg: str, shift: int) -> Tuple[str, str]:
    """比用/涉害擇一; 回 (初傳支, 課式名)。"""
    uniq: List[str] = []
    for c in cands:
        if c not in uniq:
            uniq.append(c)
    if len(uniq) == 1:
        return uniq[0], 'single'
    yg = yang_gan(dg[0])
    bi = [c for c in uniq if yang_zhi(c) == yg]
    if len(bi) == 1:
        return bi[0], '比用'
    pool = bi if bi else uniq
    sc = {c: _shehai_score(c, shift) for c in pool}
    mn = min(sc.values())
    top = [c for c in pool if sc[c] == mn]
    if len(top) > 1:
        # 季 > 孟 > 仲; 複等則剛日取干上、柔日取支上 (御定/主流軟體口徑)
        order = {'季': 0, '孟': 1, '仲': 2}

        def rk(z):
            return order['孟' if z in MENG else '仲' if z in ZHONG else '季']
        best = min(rk(c) for c in top)
        top = [c for c in top if rk(c) == best]
    if len(top) > 1:
        sh, _ = four_lessons(dg, shift)
        top = [sh[3] if yg else sh[1]]
    return top[0], '涉害'


def _follow(c0: str, shift: int) -> List[str]:
    tp = tianpan(shift)
    c1 = tp[c0]; c2 = tp[c1]
    return [c0, c1, c2]


def _fuyin(dg: str, sh: List[str], xi: List[str]) -> List[str]:
    zei_c = [sh[i] for i in range(4) if _zei(xi[i], sh[i])]
    ke_c = [sh[i] for i in range(4) if _ke(sh[i], xi[i])]
    cand = zei_c or ke_c
    if cand:
        c0 = cand[0]
    else:
        c0 = sh[3] if yang_gan(dg[0]) else sh[1]
    if XING[c0] == c0:
        c1 = sh[1] if c0 == sh[3] else sh[3]
    else:
        c1 = XING[c0]
    if XING[c1] == c1:
        c2 = chong(c1)
    else:
        c2 = XING[c1]
        if c2 == c0:
            c2 = chong(c1)
    return [c0, c1, c2]


def _special(dg: str, shift: int, sh: List[str], tp: Dict[str, str]) -> List[str]:
    g = dg[0]; z = dg[1]; yang = yang_gan(g)
    if GAN_JI[g] == z:  # 八專
        a = sh[3] if yang else sh[1]
        c0 = DIZHI[(zi(a) + 2) % 12] if yang else DIZHI[(2 * zi(a) + 3) % 12]
        return [c0, sh[3], sh[3]]
    if len(set(sh)) <= 3:  # 別責 (四課不全)
        if yang:
            c0 = tp[GAN_JI[HE_GAN[g]]]
        else:
            c0 = SANHE_FRONT[z]
        return [c0, sh[3], sh[3]]
    inv = {v: k for k, v in tp.items()}
    if yang:  # 昴星 陽日仰取
        return [tp['酉'], sh[1], sh[3]]
    return [inv['酉'], sh[3], sh[1]]


def sanchuan(dg: str, shift: int) -> Tuple[List[str], str]:
    """三傳 + 課式大類。"""
    shift %= 12
    sh, xi = four_lessons(dg, shift)
    tp = tianpan(shift)
    if shift == 0:
        return _fuyin(dg, sh, xi), '伏吟'
    zei_c = [sh[i] for i in range(4) if _zei(xi[i], sh[i])]
    ke_c = [sh[i] for i in range(4) if _ke(sh[i], xi[i])]
    cand = zei_c or ke_c
    if cand:
        c0, sub = _pick(cand, dg, shift)
        kind = '重審' if (zei_c and sub == 'single') else ('元首' if sub == 'single' else sub)
        return _follow(c0, shift), kind
    if shift == 6:
        return [YIMA[dg[1]], sh[1], sh[3]], '返吟'
    if GAN_JI[dg[0]] == dg[1]:
        return _special(dg, shift, sh, tp), '八專'
    gwx = wxg(dg[0])
    yk = [s for s in sh if KE[wxz(s)] == gwx]
    rk = [s for s in sh if KE[gwx] == wxz(s)]
    pool = yk if yk else rk
    if pool:
        c0, _sub = _pick(pool, dg, shift)
        return _follow(c0, shift), ('蒿矢' if yk else '彈射')
    chuan = _special(dg, shift, sh, tp)
    kind = '昴星' if len(set(sh)) >= 4 else '別責'
    return chuan, kind


# ========== 十二天將 ==========

def tianjiang(tp: Dict[str, str], dg: str, daynight: str) -> Dict[str, str]:
    """回 {天盤支: 天將}。daynight: 'day' 晝 / 'night' 夜。"""
    g = dg[0]
    gui = GUI[g][0 if daynight == 'day' else 1]
    inv = {v: k for k, v in tp.items()}
    gui_di = zi(inv[gui])
    shun = gui_di in [zi(x) for x in '亥子丑寅卯辰']  # 天門至地戶順布
    out = {}
    for n, name in enumerate(JIANG12):
        tz = DIZHI[(zi(gui) + n) % 12] if shun else DIZHI[(zi(gui) - n) % 12]
        out[tz] = name
    return out


# ========== 神煞 ==========

def _sanhe_idx(z: str) -> int:
    if '申子辰'.find(z) >= 0:
        return 0
    if '寅午戌'.find(z) >= 0:
        return 1
    if '巳酉丑'.find(z) >= 0:
        return 2
    return 3


def _siji_idx(z: str) -> int:
    return {'寅': 0, '卯': 0, '辰': 0, '巳': 1, '午': 1, '未': 1,
            '申': 2, '酉': 2, '戌': 2, '亥': 3, '子': 3, '丑': 3}[z]


def _sanyuan_idx(z: str) -> int:
    if z in '寅申巳亥':
        return 0
    if z in '子午卯酉':
        return 1
    return 2


T_XUETANG = {'甲': '亥', '乙': '午', '丙': '寅', '丁': '酉', '戊': '寅',
             '己': '申', '庚': '巳', '辛': '子', '壬': '申', '癸': '卯'}
T_RIDE = {'甲': '寅', '乙': '申', '丙': '巳', '丁': '亥', '戊': '巳',
          '己': '寅', '庚': '申', '辛': '巳', '壬': '亥', '癸': '巳'}
T_RILU = {'甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳',
          '己': '午', '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'}
T_YANGREN = {'甲': '卯', '乙': '寅', '丙': '午', '丁': '巳', '戊': '午',
             '己': '巳', '庚': '酉', '辛': '申', '壬': '子', '癸': '亥'}
T_POSUI = ['酉', '巳', '丑']
T_TAOHUA = ['酉', '卯', '午', '子']
T_YIMA = ['寅', '申', '亥', '巳']
T_TIANXI = ['戌', '丑', '辰', '未']
YANG_SEQ = ['子', '寅', '辰', '午', '申', '戌']


def shensha(year_gz: Optional[str], mon_gz: Optional[str], day_gz: str) -> List[Dict[str, Any]]:
    day_gan = day_gz[0]; day_zhi = day_gz[1]
    year_zhi = year_gz[-1] if year_gz else None
    mon_zhi = mon_gz[-1] if mon_gz else None
    xz = zi(xunshou(day_gz))
    dsh = _sanhe_idx(day_zhi)
    d3e = _sanyuan_idx(day_zhi)
    out: List[Dict[str, Any]] = [
        {'name': '學堂', 'pos': T_XUETANG[day_gan], 'cat': '日干', 'luck': '吉', 'desc': '聰俊高科，利考試仕途'},
        {'name': '破碎', 'pos': T_POSUI[d3e], 'cat': '日支', 'luck': '凶', 'desc': '主破壞、不成'},
        {'name': '日德', 'pos': T_RIDE[day_gan], 'cat': '日干', 'luck': '吉', 'desc': '福佑之神，凡占大吉'},
        {'name': '日祿', 'pos': T_RILU[day_gan], 'cat': '日干', 'luck': '吉', 'desc': '食祿、財源'},
        {'name': '羊刃', 'pos': T_YANGREN[day_gan], 'cat': '日干', 'luck': '凶', 'desc': '靜吉動凶，主血光'},
        {'name': '桃花', 'pos': T_TAOHUA[dsh], 'cat': '日支', 'luck': '凶', 'desc': '主淫亂，感情問題'},
        {'name': '驛馬', 'pos': T_YIMA[dsh], 'cat': '日支', 'luck': '中', 'desc': '遷動、出行、奔波'},
        {'name': '閉口', 'pos': DIZHI[(xz - 3) % 12], 'cat': '旬', 'luck': '凶', 'desc': '私密，病不食，運不通'},
        {'name': '旬丁', 'pos': DIZHI[(xz + 3) % 12], 'cat': '旬', 'luck': '中', 'desc': '速動，怪異'},
    ]
    if mon_zhi:
        shengqi = DIZHI[(zi(mon_zhi) - 2) % 12]
        siqi = chong(shengqi)
        tianma = YANG_SEQ[(3 + (zi(mon_zhi) - zi('寅')) % 12) % 6]
        out += [
            {'name': '生氣', 'pos': shengqi, 'cat': '月', 'luck': '吉', 'desc': '解凶增吉，成就新事'},
            {'name': '死氣', 'pos': siqi, 'cat': '月', 'luck': '凶', 'desc': '占病凶'},
            {'name': '死神', 'pos': DIZHI[(zi(siqi) - 1) % 12], 'cat': '月', 'luck': '凶', 'desc': '占病凶，乘虎尤忌'},
            {'name': '月破', 'pos': chong(mon_zhi), 'cat': '月', 'luck': '凶', 'desc': '破壞，無成'},
            {'name': '天醫', 'pos': DIZHI[(zi(mon_zhi) + 8) % 12], 'cat': '月', 'luck': '吉', 'desc': '醫藥、醫生'},
            {'name': '天馬', 'pos': tianma, 'cat': '月', 'luck': '中', 'desc': '遷動、詔命、出行'},
            {'name': '天喜', 'pos': T_TIANXI[_siji_idx(mon_zhi)], 'cat': '月', 'luck': '吉', 'desc': '喜慶、恩澤、財喜'},
        ]
    return out


# ========== 年命 / 行年 ==========

def year_to_gz(year: int) -> str:
    return DAYS60[((year - 1984) % 60 + 600) % 60]


def cike_yuejiang(yuejiang: str, n: int) -> Optional[str]:
    """次客法 (古法, 《占事略決》/《六壬神定經》): 數人同時同課時「換將不換時」。
    n=1 正課(用正將); n=2 二客; n=3 三客。陰將二客=前五(+5)、三客=後三(-3);
    陽將二客=後三(-3)、三客=前五(+5)。古籍自承此法「多不驗」，僅作備用、標低置信。"""
    if n <= 1:
        return yuejiang
    yang = yang_zhi(yuejiang)
    off = {2: (5 if not yang else -3), 3: (-3 if not yang else 5)}.get(n)
    if off is None:
        return None
    return DIZHI[(zi(yuejiang) + off) % 12]


def xingnian(birth_year: int, gender: str, at_year: int) -> str:
    """行年: 男一歲起丙寅順行、女一歲起壬申逆行。"""
    age = at_year - birth_year + 1
    idx = (2 + age - 1) % 60 if gender == '男' else ((8 - (age - 1)) % 60 + 600) % 60
    return DAYS60[idx]


# ========== 課體 ==========

def compute_keti(chuan: List[str], sh: List[str], xi: List[str], dg: str,
                 shift: int, kind: str) -> List[str]:
    """課體標籤 (九宗門細分 + 三合局 + 連茹間傳 + 諸格)。規則見 references/ask-event/liuren-classics.md 第七節。"""
    zx = [zi(c) for c in chuan]; c0 = chuan[0]
    g, z = dg[0], dg[1]
    yang = yang_gan(g)
    tags = [kind]
    # 九宗門細分
    if kind == '涉害':
        tags.append('見機' if c0 in MENG else ('察微' if c0 in ZHONG else '綴瑕'))
    if kind == '比用':
        tags.append('知一')
    if kind == '昴星':
        tags.append('虎視' if yang else '冬蛇掩目')
    if kind == '別責':
        tags.append('蕪淫')
    if kind == '八專':
        tags.append('帷薄')
        if len(set(chuan)) == 1:
            tags.append('獨足')
    if kind == '伏吟':
        tags.append('自任' if yang else '自信')
    # 返吟：shift=6；有克者走賊克分支 (kind 為元首/重審等)，此處補回「返吟」
    if shift == 6:
        has_ke = any(_zei(xi[i], sh[i]) or _ke(sh[i], xi[i]) for i in range(4))
        if kind != '返吟':
            tags = ['返吟'] + tags
        tags.append('無依' if has_ke else '無親')
    # 三合局 (亥卯未=曲直 等) / 三交 / 稼穡 (三傳皆土)
    sset = set(chuan)
    SANHE_NAME2 = {frozenset({'亥', '卯', '未'}): '曲直', frozenset({'寅', '午', '戌'}): '炎上',
                   frozenset({'巳', '酉', '丑'}): '從革', frozenset({'申', '子', '辰'}): '潤下'}
    if len(sset) == 3 and frozenset(sset) in SANHE_NAME2:
        tags.append(SANHE_NAME2[frozenset(sset)])
        if c0 in ZHONG:
            tags.append('三交')
    if all(wxz(c) == '土' for c in chuan):
        tags.append('稼穡')
    # 連茹 / 進茹 / 退茹 / 間傳
    g1 = (zx[1] - zx[0]) % 12; g2 = (zx[2] - zx[1]) % 12
    if g1 == 1 and g2 == 1:
        tags += ['連茹', '進茹']
    elif g1 == 11 and g2 == 11:
        tags += ['連茹', '退茹']
    elif g1 == g2 == 2:
        tags.append('間傳')
    # 元胎 (三傳全孟)
    if all(c in MENG for c in chuan):
        tags.append('元胎')
    # 亂首 (支剋干)
    if KE[wxz(z)] == wxg(g):
        tags.append('亂首')
    # 龍戰 (卯酉日、用起卯酉)
    if z in '卯酉' and c0 in ('卯', '酉'):
        tags.append('龍戰')
    # 勵德 (日德／日祿發用)
    if c0 in (T_RIDE[g], T_RILU[g]):
        tags.append('勵德')
    # 無祿 (四上剋下) / 絕紀 (四下賊上)
    if all(_ke(sh[i], xi[i]) for i in range(4)):
        tags.append('無祿')
    if all(_zei(xi[i], sh[i]) for i in range(4)):
        tags.append('絕紀')
    # 斬關 (三傳見魁罡且發功曹)
    if ('戌' in chuan or '辰' in chuan) and '寅' in chuan:
        tags.append('斬關')
    # 高蓋駟馬 (用起驛馬、傳見車乘卯、終華蓋子)
    if c0 == YIMA[z] and chuan[1] == '卯' and chuan[2] == '子':
        tags.append('高蓋駟馬')
    # 鑄印乘軒 (用巳、傳戌、終卯)
    if c0 == '巳' and chuan[1] == '戌' and chuan[2] == '卯':
        tags.append('鑄印乘軒')
    # 斲輪織綬 (用起車乘卯、傳見印綬戌)
    if c0 == '卯' and '戌' in chuan:
        tags.append('斲輪織綬')
    return list(dict.fromkeys(tags))


# ========== 主類 ==========

class LiuRenChart:
    def __init__(self, dt: datetime, birth: Optional[List[Tuple[int, str]]] = None,
                 at_year: Optional[int] = None, lifetime: bool = False, twin: int = 1):
        self.dt = dt
        self.at_year = at_year or dt.year
        self.lifetime = lifetime
        self.twin = twin
        solar = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, 0)
        self.lunar = solar.getLunar()
        self.year_gz = self.lunar.getYearInGanZhi()
        self.mon_gz = self.lunar.getMonthInGanZhi()
        self.day_gz = self.lunar.getDayInGanZhi()
        self.hour_zhi = self.lunar.getTimeZhi()
        self.hour_gz = self.lunar.getTimeInGanZhi()
        self.yuejiang = self._yuejiang()
        if twin > 1:
            shifted = cike_yuejiang(self.yuejiang, twin)
            if shifted:
                self.yuejiang = shifted
        self.hour_idx = zi(self.hour_zhi)
        self.yuejiang_idx = zi(self.yuejiang)
        self.shift = (self.yuejiang_idx - self.hour_idx) % 12
        self.ju = ((self.hour_idx - self.yuejiang_idx) % 12) + 1  # 第 n 局
        self.daynight = 'day' if 3 <= self.hour_idx <= 8 else 'night'  # 卯至申為晝，酉至寅為夜
        self.birth = birth or []
        self._build()

    def _yuejiang(self) -> str:
        qi = self.lunar.getPrevQi()
        name = qi.getName() if qi else ''
        return QI_TO_JIANG.get(name, '子')

    def _build(self):
        tp = tianpan(self.shift)
        self.tianpan = tp
        self.sh, self.xi = four_lessons(self.day_gz, self.shift)
        sc, kind = sanchuan(self.day_gz, self.shift)
        self.chuan = sc
        self.kind = kind
        self.kongwang = kongwang(self.day_gz)
        self.jiang = tianjiang(tp, self.day_gz, self.daynight)
        self.keti = compute_keti(sc, self.sh, self.xi, self.day_gz, self.shift, kind)
        self.shensha = shensha(self.year_gz, self.mon_gz, self.day_gz)
        self.wangxiang = wangxiang(self.mon_gz[-1])
        # 年命
        self.persons = []
        for (yr, gd) in self.birth:
            self.persons.append({
                'gender': gd, 'birth_year': yr,
                'benming': year_to_gz(yr),
                'benming_zhi': year_to_gz(yr)[1],
                'xingnian': xingnian(yr, gd, self.at_year),
                'xingnian_zhi': xingnian(yr, gd, self.at_year)[1],
            })
        # 四課式神
        self.sike_jiang = [self.jiang[self.sh[i]] for i in range(4)]

    # ---- 輸出 ----
    def _chuan_row(self, i: int) -> Dict[str, Any]:
        z = self.chuan[i]
        return {'pos': z, 'gan': dungan(self.day_gz, z), 'liuqin': LIUQIN_FULL[liuqin(self.day_gz, z)],
                'jiang': self.jiang[z], 'kong': z in self.kongwang}

    def to_dict(self) -> Dict[str, Any]:
        return {
            'time': self.dt.strftime('%Y-%m-%d %H:%M:%S'),
            'lifetime': self.lifetime,
            'at_year': self.at_year,
            'twin': self.twin,
            'sizhu': {'year': self.year_gz, 'month': self.mon_gz, 'day': self.day_gz, 'hour': self.hour_gz},
            'yuejiang': {'zhi': self.yuejiang, 'name': JIANG_NAME[self.yuejiang],
                         'main': JIANG_MAIN.get(self.yuejiang, ''),
                         'qi': self.lunar.getPrevQi().getName() if self.lunar.getPrevQi() else ''},
            'hour_zhi': self.hour_zhi,
            'daynight': '晝占' if self.daynight == 'day' else '夜占',
            'ju': self.ju,
            'kongwang': self.kongwang,
            'wangxiang': self.wangxiang,
            'suosheng': SUOSHENG,
            'sike': {'shang': self.sh, 'xia': self.xi, 'jiang': self.sike_jiang},
            'sanchuan': [self._chuan_row(i) for i in range(3)],
            'tianpan': {d: {'tian': self.tianpan[d], 'jiang': self.jiang[self.tianpan[d]]} for d in DIZHI},
            'keti': self.keti,
            'kind': self.kind,
            'shensha': self.shensha,
            'persons': self.persons,
        }

    def format_for_ai(self) -> str:
        d = self.to_dict()
        L = []
        L.append('【大六壬】' + ('（終身課）' if self.lifetime else ''))
        sz = d['sizhu']
        L.append(f"起課時間：{self.dt.strftime('%Y年%m月%d日 %H:%M')}（{sz['year']}年 {sz['month']}月 {sz['day']}日 {sz['hour']}時）")
        if self.lifetime:
            L.append("終身課：以出生時刻起課，三傳為一生大勢；本命＝一生之應、行年＝逐年之應；傳凶而年命有救可轉福。")
        yj = d['yuejiang']
        gs = self.sh[3]  # 干上神 = 第一課上神
        L.append(f"月將：{yj['zhi']}（{yj['name']}，{yj.get('main', '')}，中氣 {yj['qi']} 後換將）　占時：{d['hour_zhi']}　"
                 f"第{self.ju}局　{d['daynight']}　旬空：{''.join(d['kongwang'])}　干上神：{gs}")
        if self.twin > 1:
            L.append(f"※ 次客法（第{self.twin}客，換將不換時；古法，低置信）：月將改用 {self.yuejiang}。"
                     f"雙胞胎同課時，首選以各人年命區分（龍鳳胎行年異）；同卵同性同命則六壬不可分，依主盤八字紫微。")
        wx = d['wangxiang']
        L.append(f"月令五氣（旺相死囚休）：旺{wx['旺']}　相{wx['相']}　死{wx['死']}　囚{wx['囚']}　休{wx['休']}"
                 f"（所勝所憂：旺→縣官、相→財物、死→死喪、囚→囚系、休→疾病）")
        L.append(f"課體：{'、'.join(d['keti'])}")
        L.append('')
        L.append('【三傳】')
        for i, lbl in enumerate(['初傳', '中傳', '末傳']):
            row = d['sanchuan'][i]
            gan = row['gan'] or '（空亡無干）'
            kong = '　旬空' if row['kong'] else ''
            L.append(f"{lbl}：{row['pos']}（遁干 {gan}，{row['liuqin']}，式神 {JIANG_FULL[row['jiang']]}{kong}）")
        L.append('')
        L.append('【四課】(上神/下神，式神)')
        labels = ['第四課', '第三課', '第二課', '第一課']
        for i in range(4):
            L.append(f"{labels[i]}：{self.sh[i]} ／ {self.xi[i]}　{JIANG_FULL[self.sike_jiang[i]]}")
        L.append('')
        L.append('【天地盤】(天盤 遁干 + 天將 / 地盤)')
        PAN = ['巳', '午', '未', '申', '辰', '卯', '酉', '戌', '寅', '丑', '子', '亥']
        for dgp in PAN:
            tz = self.tianpan[dgp]
            fg = dungan(self.day_gz, tz)
            fgs = f"遁{fg} " if fg else ''
            L.append(f"　{dgp}：{tz}（{fgs}{JIANG_FULL[self.jiang[tz]]}）")
        L.append('')
        ss = '　'.join(f"{s['name']}::{s['pos']}" for s in d['shensha'])
        L.append('【神煞】')
        L.append(ss)
        if d['persons']:
            L.append('')
            hdr = '【年命】(本命為一生之應、行年為逐年之應)' if self.lifetime else '【年命】(問事人落點，僅佐證，非本盤主體)'
            L.append(hdr)
            for p in d['persons']:
                L.append(f"　{p['gender']}　本命 {p['benming']}　行年（{self.at_year}年）{p['xingnian']}")
        return '\n'.join(L)
