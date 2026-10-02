"""ziwei_full 時辰測試 (TDD, 邊界=CLI .sh). 真太陽時與八字同源."""
import json
import subprocess
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SH = SKILL / "scripts" / "ziwei_full.sh"


def run_zw(*extra):
    cmd = [str(SH), *extra, "--format", "json"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, f"CLI failed: {r.stderr[-500:]}"
    return json.loads(r.stdout)


def test_true_solar_boundary():
    """手工真值: 1990-08-18 06:59台北, 校正+2.6分→07:01→辰時 (八字同時柱亦為辰)."""
    d = run_zw("--date", "1990-08-18", "--time", "06:59", "--city", "台北",
               "--gender", "male")
    assert d["hour"] == "辰"
    assert "true_solar" in d


def test_true_solar_no_cross():
    """對照: 06:30台北校正後06:32仍卯時."""
    d = run_zw("--date", "1990-08-18", "--time", "06:30", "--city", "台北",
               "--gender", "male")
    assert d["hour"] == "卯"


def test_hour_branch_still_works():
    """向後相容: --hour 地支直給."""
    d = run_zw("--date", "1990-08-18", "--hour", "卯", "--gender", "male")
    assert d["hour"] == "卯"


def test_cross_bazi_shizhi():
    """交叉驗證: 同一瞬間八字時支 == 紫微時支 (06:59台北→辰)."""
    import subprocess as sp
    vpy = str(SKILL / "scripts" / ".venv" / "bin" / "python")
    cmd = [vpy, str(SKILL / "scripts" / "bazi_pai.py"),
           "--date", "1990-08-18", "--time", "06:59", "--city", "台北",
           "--gender", "male", "--format", "json"]
    r = sp.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    bz = json.loads(r.stdout)
    shizhi = next(p["zhi"] for p in bz["pillars"] if p["label"] == "時柱")
    d = run_zw("--date", "1990-08-18", "--time", "06:59", "--city", "台北",
               "--gender", "male")
    assert d["hour"] == shizhi == "辰"


def test_patterns_pinned():
    """上游 patterns.ts 一改輸出靜默漂移, 釘死 fixture 格局集合 (手工核對過)."""
    a = run_zw("--date", "1990-08-18", "--hour", "卯", "--gender", "male",
               "--liunian", "2026")
    assert sorted(g["name"] for g in a["patterns"]) == \
        ["府相朝垣", "廉贞天相格", "武贪格", "火贪格", "紫府同宫", "铃贪格"]
    b = run_zw("--date", "1992-03-15", "--hour", "未", "--gender", "female",
               "--liunian", "2026")
    assert sorted(g["name"] for g in b["patterns"]) == \
        ["天同天梁格", "天梁化禄入命", "天马在迁", "机月同梁", "武曲七杀"]


# ── 運限六層 (大限/小限/流年/流月/流日/流時) ─────────────────────

AT = "2026-06-15"
BASE = ("--date", "1990-08-18", "--hour", "卯", "--gender", "male")


def run_horoscope(*extra):
    return run_zw(*BASE, "--at", AT, *extra)


def test_horoscope_absent_by_default():
    """向後相容: 未給 --at 時 JSON 不出 horoscope 鍵."""
    d = run_zw(*BASE)
    assert "horoscope" not in d


def test_horoscope_six_levels_pinned():
    """手工真值: 1990-08-18 卯男 @2026-06-15(午時), 六層干支/落宮/四化釘死."""
    h = run_horoscope()["horoscope"]
    assert h["at"] == "2026-6-15"
    assert h["divide"] == "normal"
    expect = {
        "daxian": ("癸未", "田宅", "未", "破军", "贪狼"),
        "xiaoxian": ("庚辰", "命宫", "辰", "太阳", "天同"),
        "liunian": ("丙午", "福德", "午", "天同", "廉贞"),
        "liuyue": ("甲午", "官禄", "申", "廉贞", "太阳"),
        "liuri": ("庚申", "官禄", "申", "太阳", "天同"),
        "liushi": ("壬午", "夫妻", "寅", "天梁", "武曲"),
    }
    for key, (gz, palace, branch, lu, ji) in expect.items():
        L = h[key]
        assert L["ganzhi"] == gz, (key, L["ganzhi"])
        assert L["palace"] == palace and L["branch"] == branch, (key, L)
        assert L["mutagen"]["祿"] == lu and L["mutagen"]["忌"] == ji, (key, L["mutagen"])


def test_horoscope_palace_reorder_aligned():
    """流年十二宮重排: index 4(午/福德) 應為流年命宮, 且 native 對齊本命宮."""
    h = run_horoscope()["horoscope"]["liunian"]
    assert len(h["palaces"]) == 12
    assert h["palaces"][4] == {"scope": "命宫", "native": "福德", "branch": "午"}
    # 運限命宮落宮 == 命宮所在的 native 宮
    assert h["palace"] == "福德" and h["branch"] == "午"


def test_horoscope_at_time_changes_liushi():
    """--at-time 06:00 → 卯時, 流時(己卯,命落疾厄亥); 預設 12:00 → 流時壬午命落夫妻寅."""
    h = run_horoscope("--at-time", "06:00")["horoscope"]
    assert h["liushi"]["ganzhi"] == "己卯"
    assert h["liushi"]["branch"] == "亥"
    d = run_horoscope()["horoscope"]
    assert d["liushi"]["ganzhi"] == "壬午" and d["liushi"]["branch"] == "寅"


def test_horoscope_xiaoxian_nominal_age():
    """小限虛歲: 1990 生 @2026 → 37."""
    h = run_horoscope()["horoscope"]
    assert h["xiaoxian"]["nominalAge"] == 37


def test_horoscope_dec_star_full():
    """流年將前/歲前十二神各 12 顆."""
    ds = run_horoscope()["horoscope"]["liunian"]["dec_star"]
    assert len(ds["jiangqian12"]) == 12 and len(ds["suiqian12"]) == 12
    assert ds["jiangqian12"][4] == "将星"


def test_horoscope_deterministic():
    assert json.dumps(run_horoscope(), sort_keys=True) == \
        json.dumps(run_horoscope(), sort_keys=True)


def test_horoscope_divide_flag():
    assert run_horoscope("--horoscope-divide", "exact")["horoscope"]["divide"] == "exact"


def test_horoscope_liunian_matches_vendor_sihua():
    """跨庫一致: iztro 流年四化 == vendor SI_HUA_TABLE 流年四化 (丙午)."""
    h = run_horoscope()["horoscope"]["liunian"]["mutagen"]
    v = run_zw(*BASE, "--liunian", "2026")["liunian_sihua"]["transforms"]
    assert h == {"祿": v["禄"], "權": v["权"], "科": v["科"], "忌": v["忌"]}


def test_horoscope_sihua_table_all_stems():
    """校驗: 2026-2035 (涵蓋10天干) 逐年 iztro 流年四化 == vendor 四化表."""
    for year in range(2026, 2036):
        h = run_zw(*BASE, "--at", f"{year}-06-15")["horoscope"]["liunian"]["mutagen"]
        v = run_zw(*BASE, "--liunian", str(year))["liunian_sihua"]["transforms"]
        assert h == {"祿": v["禄"], "權": v["权"], "科": v["科"], "忌": v["忌"]}, year


def test_horoscope_bad_at_clean_error():
    """--at 格式錯須乾淨報錯 (exit!=0, 無 traceback)."""
    cmd = [str(SH), *BASE, "--at", "2026/06/15", "--format", "json"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode != 0
    assert "Traceback" not in r.stderr
    assert "YYYY-MM-DD" in r.stderr or "--at" in r.stderr


def test_warnings_near_hour_boundary():
    """低置信: 06:59台北→真太陽時07:01近辰時交界, 須警示; 06:30無."""
    d = run_zw("--date", "1990-08-18", "--time", "06:59", "--city", "台北",
               "--gender", "male")
    assert any("時辰交界" in w for w in d["warnings"])
    d2 = run_zw("--date", "1990-08-18", "--time", "06:30", "--city", "台北",
                "--gender", "male")
    assert d2["warnings"] == []
