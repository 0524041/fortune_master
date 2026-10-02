"""單一真相/資料完整性守衛. 防止 data/*.json 與程式/引擎漂移."""
import json
import re
import subprocess
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
DATA = SKILL / "data"
VENV_PY = str(SKILL / "scripts" / ".venv" / "bin" / "python")
SH = SKILL / "scripts" / "ziwei_full.sh"
GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def test_ganzhi_tables_consistent():
    d = load("ganzhi.json")
    assert d["gan"] == list(GAN) and d["zhi"] == list(ZHI)
    assert set(d["gan_wuxing"]) == set(GAN) and set(d["zhi_wuxing"]) == set(ZHI)
    assert set(d["hidden"]) == set(ZHI)
    for m in ("tian_gan_he", "liu_he", "liu_chong"):
        for a, b in d[m].items():
            assert d[m][b] == a, (m, a, b)  # 對稱
    assert sorted(d["tian_gan_he"]) == sorted(GAN)
    assert sorted(d["liu_he"]) == sorted(ZHI) and sorted(d["liu_chong"]) == sorted(ZHI)
    assert len(d["san_he"]) == 4 and all(len(g) == 3 for g in d["san_he"])
    assert set(d["wu_xing_sheng"].values()) == set("木火土金水")


def test_shensha_tables_complete():
    s = load("shensha.json")
    for k in ("tianyi", "lushen", "wenchang"):
        assert set(s[k]) == set(GAN), k
    assert set(s["yangren"]) <= set(GAN)
    for k in ("taohua", "yima", "huagai", "jiangxing", "guchen", "guasu"):
        assert set(s[k]) == set(ZHI), k
    assert set(s["hongluan"]) == set(ZHI)


def test_zeri_rules_cover_matters():
    z = load("zeri_rules.json")
    assert z["matters"] == list(z["jianchu"])
    for m in z["matters"]:
        assert set(z["jianchu"][m]) == {"plus2", "plus1", "veto", "minus1"}
        assert m in z["yi_kw"] and m in z["lucky"] and m in z["evil"]
    assert set(z["shousi"]) == {str(i) for i in range(1, 13)}


def test_sihua_data_matches_vendor_engine():
    """data/sihua.json == vendor SI_HUA_TABLE (以 iztro 逐年干輸出比對)."""
    data = load("sihua.json")["table"]
    for year in range(2026, 2036):
        stem = GAN[((year - 4) % 10)]
        r = subprocess.run([str(SH), "--date", "1990-08-18", "--hour", "卯",
                            "--gender", "male", "--liunian", str(year), "--format", "json"],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        t = json.loads(r.stdout)["liunian_sihua"]["transforms"]
        assert [t["禄"], t["权"], t["科"], t["忌"]] == data[stem], year


def test_true_solar_agrees_across_tools():
    """真太陽時跨工具一致: 八字 total_corr_min == 紫微 time_src 校正分 (防 py/ts 漂移)."""
    bz = json.loads(subprocess.run(
        [VENV_PY, str(SKILL / "scripts" / "bazi_pai.py"), "--date", "1990-08-18",
         "--time", "06:30", "--city", "台北", "--gender", "male", "--format", "json"],
        capture_output=True, text=True).stdout)
    zw = json.loads(subprocess.run(
        [str(SH), "--date", "1990-08-18", "--time", "06:30", "--city", "台北",
         "--gender", "male", "--format", "json"],
        capture_output=True, text=True).stdout)
    m = re.search(r"校正([-0-9.]+)分", zw["time_src"])
    assert m, zw["time_src"]
    assert abs(float(m.group(1)) - bz["input"]["total_corr_min"]) < 0.01
