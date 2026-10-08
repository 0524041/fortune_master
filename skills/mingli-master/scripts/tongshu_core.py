#!/usr/bin/env python3
"""通書核心 (黃曆/擇日共用). 純事實: 日層 + 十二時辰層 + 個人關係事實.

- 曆法一律走內嵌 lunar_python, 不心算; 規則表讀 data/ (單一真相).
- 本模組**只算事實、不斷吉凶** (評分在 zeri_pick.py, 解讀在 references/ask-person/zeri.md).
- 供 scripts/tongshu_day.py (單日全資訊 CLI) 與 scripts/zeri_pick.py (掃描) 共用.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))          # han.py (統一簡繁層)
sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))  # 內嵌 lunar_python (零安裝)
sys.path.insert(0, str(Path(__file__).resolve().parent / "yijing"))  # 奇門時盤 (選用)
from lunar_python import Solar  # noqa: E402
from lunar_python.util import LunarUtil  # noqa: E402
from han import s2t as tr, s2t_list as tr_list, simplified_leaks  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data"
_ZH = json.loads((DATA / "ganzhi.json").read_text(encoding="utf-8"))
CHONG = _ZH["liu_chong"]
LIUHE = _ZH["liu_he"]
SANHE = _ZH["san_he"]
TIANGAN_HE = _ZH["tian_gan_he"]
GAN_WX = _ZH["gan_wuxing"]
WUXING_KE = _ZH["wu_xing_ke"]

# 十二時辰: (名, 區間標示, 代表時, 代表分). 代表時刻取整點後半, 避開 23:00 子時換日.
HOUR_SLOTS = [
    ("子時", "23:00-01:00", 0, 30), ("丑時", "01:00-03:00", 2, 30),
    ("寅時", "03:00-05:00", 4, 30), ("卯時", "05:00-07:00", 6, 30),
    ("辰時", "07:00-09:00", 8, 30), ("巳時", "09:00-11:00", 10, 30),
    ("午時", "11:00-13:00", 12, 30), ("未時", "13:00-15:00", 14, 30),
    ("申時", "15:00-17:00", 16, 30), ("酉時", "17:00-19:00", 18, 30),
    ("戌時", "19:00-21:00", 20, 30), ("亥時", "21:00-23:00", 22, 30),
]


def _day_lunar(dt):
    return Solar.fromYmdHms(dt.year, dt.month, dt.day, 12, 0, 0).getLunar()


def day_facts(dt):
    """單日通書事實. 欄位對齊傳統黃曆 (宜忌/建除/宿/九星/方位/彭祖/胎神/沖煞/空亡...)."""
    l = _day_lunar(dt)
    xiu = tr(l.getXiu())
    return {
        "date": dt.strftime("%Y-%m-%d"),
        "week": "星期" + tr(l.getWeekInChinese()),
        "lunar_date": tr(l.getMonthInChinese()) + "月" + tr(l.getDayInChinese()),
        "lunar_year": tr(l.getYearInChinese()) + "年",
        "year_pillar": tr(l.getYearInGanZhiExact()),
        "month_pillar": tr(l.getMonthInGanZhiExact()),
        "day_pillar": tr(l.getDayInGanZhiExact()),
        "gan": tr(l.getDayGanExact()), "zhi": tr(l.getDayZhiExact()),
        "month_zhi": tr(l.getMonthZhi()), "year_zhi": tr(l.getYearZhi()),
        "lunar_month": l.getMonth(),
        "ganzhi": tr(l.getDayInGanZhiExact()),
        "nayin": tr(l.getDayNaYin()),
        "jianchu": tr(l.getZhiXing()),
        # 宿頌 (getXiuSong) 為長詩, 簡繁混雜且非擇日必需, 故不輸出; 只取宿名/五行/禽/吉凶.
        "xiu": {"name": xiu, "zheng": tr(l.getZheng()), "animal": tr(l.getAnimal()),
                "luck": tr(l.getXiuLuck())},
        "nine_star": tr(str(l.getDayNineStar())),
        "huangdao": tr(l.getDayTianShen()) + tr(l.getDayTianShenLuck()),
        "huangdao_name": tr(l.getDayTianShen()),
        "huangdao_type": tr(l.getDayTianShenType()),
        "huangdao_good": l.getDayTianShenLuck() == "吉",
        "yi": tr_list(l.getDayYi()), "ji": tr_list(l.getDayJi()),
        "jishen": tr_list(l.getDayJiShen()), "xiongsha": tr_list(l.getDayXiongSha()),
        "directions": {
            "喜神": tr(l.getDayPositionXiDesc()), "陽貴": tr(l.getDayPositionYangGuiDesc()),
            "陰貴": tr(l.getDayPositionYinGuiDesc()), "財神": tr(l.getDayPositionCaiDesc()),
            "福神": tr(l.getDayPositionFuDesc()),
        },
        "xunkong": tr(l.getDayXunKong()),
        "chong": {"desc": tr(l.getDayChongDesc()), "sha": tr(l.getDaySha())},
        "pengzu": {"gan": tr(l.getPengZuGan()), "zhi": tr(l.getPengZuZhi())},
        "taishen": tr(l.getDayPositionTai()),
        "taisui": {"year": tr(l.getYearPositionTaiSuiDesc()),
                   "month": tr(l.getMonthPositionTaiSuiDesc()),
                   "day": tr(l.getDayPositionTaiSuiDesc())},
        "yuexiang": tr(l.getYueXiang()),
        "liuyao": tr(l.getLiuYao()),
        "season": tr(l.getSeason()),
        "festivals": tr_list(l.getFestivals()) + tr_list(l.getOtherFestivals()),
        "jieqi": tr(l.getJieQi()),
    }


def hour_facts(dt, index):
    """單一時辰事實 (index 0=子 ... 11=亥)."""
    name, rng, hh, mm = HOUR_SLOTS[index]
    l = Solar.fromYmdHms(dt.year, dt.month, dt.day, hh, mm, 0).getLunar()
    return {
        "index": index, "name": name, "range": rng,
        "rep": f"{hh:02d}:{mm:02d}",
        "ganzhi": tr(l.getTimeInGanZhi()),
        "gan": tr(l.getTimeGan()), "zhi": tr(l.getTimeZhi()),
        "huangdao_name": tr(l.getTimeTianShen()),
        "huangdao_type": tr(l.getTimeTianShenType()),
        "huangdao_luck": tr(l.getTimeTianShenLuck()),
        "huangdao_good": l.getTimeTianShenLuck() == "吉",
        "chong": {"desc": tr(l.getTimeChongDesc()), "sha": tr(l.getTimeSha())},
        "nayin": tr(l.getTimeNaYin()),
        "xunkong": tr(l.getTimeXunKong()),
        "nine_star": tr(str(l.getTimeNineStar())),
        "xi": tr(l.getTimePositionXiDesc()), "cai": tr(l.getTimePositionCaiDesc()),
        "yi": tr_list(l.getTimeYi()), "ji": tr_list(l.getTimeJi()),
    }


def hours_of_day(dt):
    return [hour_facts(dt, i) for i in range(12)]


def _bazi_pillars(bazi):
    out = {}
    for p in bazi.get("pillars", []):
        out[p.get("label", "")] = (tr(p.get("gan", "")), tr(p.get("zhi", "")))
    return out


def personal_relations(gan, zhi, bazi):
    """事實: 候選干支 (gan,zhi) 與命主八字 (年/日柱) 的關係. 不評分.

    回 {day_master, shishen, chong_year, chong_day, liuhe_day, sanhe_day, gan_he, gan_ke}.
    """
    p = _bazi_pillars(bazi)
    mg, mz = p.get("日柱", ("", ""))
    yz = p.get("年柱", ("", ""))[1]
    if not mg:
        return {}
    rel = {
        "day_master": mg, "day_zhi": mz, "year_zhi": yz,
        "shishen": tr(LunarUtil.SHI_SHEN.get(mg + gan, "")),
        "chong_year": bool(yz) and CHONG.get(zhi) == yz,
        "chong_day": CHONG.get(zhi) == mz,
        "liuhe_day": LIUHE.get(zhi) == mz,
        "sanhe_day": any(zhi in g and mz in g for g in SANHE),
        "gan_he": TIANGAN_HE.get(gan) == mg,
        "gan_ke": False,
    }
    awx, bwx = GAN_WX.get(gan), GAN_WX.get(mg)
    if awx and bwx and (WUXING_KE.get(awx) == bwx or WUXING_KE.get(bwx) == awx):
        rel["gan_ke"] = True
    return rel


def qimen_brief(dt):
    """時家奇門簡表 (值符/值使/局/格局), 供擇時方位行動參考."""
    from qimen_core import QiMenChart
    q = QiMenChart(dt)
    return {"ju": f"{q.yin_yang}遁{q.ju}局", "jieqi": q.jieqi, "yuan": q.yuan,
            "zhifu": f"{q.zhifu_star}({q.zhifu_gong}宮)",
            "zhishi": f"{q.zhishi_gate}門({q.zhishi_gong}宮)",
            "hour_gan_gong": q.hour_gan_gong, "geju": q.geju()}


if __name__ == "__main__":
    import json as _json
    d = datetime.now()
    print(_json.dumps(day_facts(d), ensure_ascii=False, indent=2))
