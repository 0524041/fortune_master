"""單一真相/資料完整性守衛. 防止 data/*.json 與程式/引擎漂移."""
import json
import re
import subprocess
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "skills" / "mingli-master"
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


def test_shishen_combo_verified():
    """Phase 1: 十神組合 7 條須全 verified (≥5 源), 鍵齊全, 抽查真值."""
    d = load("shishen_combo.json")
    ids = {c["id"] for c in d["combos"]}
    assert ids == {"shishang_zhisha", "shangguan_jianguan", "guanyin_xiangsheng",
                   "caiguan_xiangsheng", "bijie_duocai", "shishang_shengcai",
                   "guansha_hunza"}, ids
    for c in d["combos"]:
        assert c["status"] == "verified", c["id"]
        assert c["source_count"] >= 5 and len(c["sources"]) >= c["source_count"], c["id"]
        for k in ("conditions", "judge", "breakers", "yun"):
            assert c[k], (c["id"], k)
    by_id = {c["id"]: c for c in d["combos"]}
    assert "殺成勢" in by_id["shishang_zhisha"]["conditions"][0]
    assert "合官留殺" in by_id["guansha_hunza"]["judge"]


def test_congge_verified():
    """Phase 1: 從弱/從強/真假從須 verified (≥5 源); 外格雜格留 pending."""
    d = load("congge.json")
    for k in ("cong_ruo", "cong_qiang_zhuanwang", "zhenjia_xingyun"):
        assert d[k]["status"] == "verified", k
        assert d[k]["source_count"] >= 5 and len(d[k]["sources"]) >= 5, k
    assert "透干" in d["cong_ruo"]["conditions"][0]
    assert "官殺" in d["zhenjia_xingyun"]["disputes"][0]
    assert d["pending"] and d["pending"][0]["id"] == "waige_zage"


def test_ziwei_combo_verified():
    """Phase 1: 六吉六煞名單齊全; 火貪五件套鍵齊全; 分宮細則留 pending."""
    d = load("ziwei_combo.json")
    assert len(d["fuxing"]["liu_ji"]) == 6 and "文昌" in d["fuxing"]["liu_ji"]
    assert len(d["liu_sha"]) == 6 and "擎羊" in d["liu_sha"]
    assert len(d["jia_gong"]["jijia"]) == 6 and len(d["jia_gong"]["xiongjia"]) == 5
    tj = d["sha"]["huotan_wujiantao"]
    assert "獨坐" in tj["condition"] and "限運引動" in tj["judge"]
    pend = {p["id"] for p in d["pending"]}
    assert {"B3-2", "B3-3", "B1-6"} <= pend, pend


def test_dizhi_xinghaipo_verified():
    """Phase 1: 六害 6 組、三刑 4 組 verified; 六破留 unverified 備查."""
    d = load("dizhi_xinghaipo.json")
    assert len(d["liu_hai"]["groups"]) == 6 and "子未" in d["liu_hai"]["groups"]
    assert len(d["sanxing"]["groups"]) == 4
    assert d["liu_hai"]["status"] == "verified" and d["sanxing"]["source_count"] >= 5
    assert d["unverified"]["liu_po"]["status"].startswith("pending")
    assert len(d["unverified"]["liu_po"]["groups"]) == 6
