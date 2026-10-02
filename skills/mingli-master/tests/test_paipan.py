"""排盤本體測試 (TDD, 邊界=CLI). 期望值皆獨立手算/查表真值."""
import json
import subprocess
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SCRIPT = SKILL / "scripts" / "bazi_pai.py"
VENV_PY = str(Path(__file__).resolve().parent.parent / "scripts" / ".venv" / "bin" / "python")
# 本地 venv 不存在時先跑 bash scripts/setup.sh


def run_bazi(*extra):
    cmd = [VENV_PY, str(SCRIPT), *extra, "--format", "json"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, f"CLI failed: {r.stderr}"
    return json.loads(r.stdout)


def test_liunian_lichun_boundary():
    """2024立春在2/4 16:27, 全年流年須為甲辰 (固定2/4 12:00取法會錯成癸卯)."""
    d = run_bazi("--date", "1990-08-18", "--time", "06:30", "--city", "台北",
                 "--gender", "male", "--year", "2024")
    assert d["liunian"]["gan_zhi"] == "甲辰"


def test_liunian_control_years():
    """對照: 2023癸卯, 2025乙巳."""
    for year, expect in (("2023", "癸卯"), ("2025", "乙巳")):
        d = run_bazi("--date", "1990-08-18", "--time", "06:30", "--city", "台北",
                     "--gender", "male", "--year", year)
        assert d["liunian"]["gan_zhi"] == expect


def run_bazi_json(*extra):
    cmd = [VENV_PY, str(SCRIPT), *extra, "--format", "json"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, f"CLI failed: {r.stderr}"
    return json.loads(r.stdout)


def test_day_strength_a_zhonghe():
    """手工真值: A乙木, 同黨33(甲10+卯10+卯10+壬3印…計入生我) 異黨36 → -3 中和.
    喜印比, 忌官殺."""
    d = run_bazi_json("--date", "1990-08-18", "--time", "06:30", "--city", "台北",
                      "--gender", "male")
    s = d["day_strength"]
    assert s["score"] == -3
    assert s["level"] == "中和"
    assert s["xi"] == ["印", "比劫"] and s["ji"] == ["官殺"]


def test_day_strength_b_shenruo():
    """手工真值: B庚金, 同黨+生我14, 異黨56 → -42 身弱. 喜比劫印, 忌官殺食傷財."""
    d = run_bazi_json("--date", "1992-03-15", "--time", "14:00", "--city", "台南",
                      "--gender", "female")
    s = d["day_strength"]
    assert s["score"] == -42
    assert s["level"] == "身弱"
    assert s["xi"] == ["比劫", "印"] and s["ji"] == ["官殺", "食傷", "財"]


def test_unknown_city_clean_error():
    """無預設城市: 未給--city/--lon 須乾淨報錯 (exit!=0, 無traceback)."""
    cmd = [VENV_PY, str(SCRIPT), "--date", "1990-08-18", "--time", "06:30",
           "--gender", "male", "--format", "json"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode != 0
    assert "Traceback" not in r.stderr
    assert "出生城市" in r.stderr or "city" in r.stderr.lower()


def test_dayun_civil_years():
    """修正後真值: 起運須數至「節」白露(1990-09-08), 約21天→7年, 首柱乙酉 8歲起 1997-2006.
    (舊版誤用中氣處暑, 少算約16天, 起運早6年成 1991-2000, 已修)."""
    d = run_bazi_json("--date", "1990-08-18", "--time", "06:30", "--city", "台北",
                      "--gender", "male")
    first = d["dayun"]["pillars"][0]
    assert first["gan_zhi"] == "乙酉"
    assert first["years"] == "1997-2006" and first["age"] == "8-17"
    fourth = d["dayun"]["pillars"][3]
    assert fourth["gan_zhi"] == "戊子" and fourth["years"] == "2027-2036"
    assert d["dayun"]["direction"] == "順"
    assert d["dayun"]["start_solar"] == "1997-08-18"


JIE_12 = {"立春", "惊蛰", "清明", "立夏", "芒种", "小暑",
          "立秋", "白露", "寒露", "立冬", "大雪", "小寒"}


def test_dayun_base_is_jie_not_qi():
    """校驗: 大運起運基準必為 12 節 (非中氣). 舊版回 處暑 為 bug."""
    for args in (("1990-08-18", "06:30", "台北", "male"),
                 ("1992-03-15", "14:00", "台南", "female")):
        d = run_bazi_json("--date", args[0], "--time", args[1], "--city", args[2],
                          "--gender", args[3])
        assert d["dayun"]["base_jieqi"] in JIE_12, d["dayun"]["base_jieqi"]


def test_pillar_essence_fields():
    """逐柱本質資訊: 納音/長生/旬空/十神支/藏干十神 (A庚午甲申乙卯己卯)."""
    d = run_bazi_json("--date", "1990-08-18", "--time", "06:30", "--city", "台北",
                      "--gender", "male")
    p = d["pillars"]
    assert [x["nayin"] for x in p] == ["路旁土", "泉中水", "大溪水", "城头土"]
    assert [x["dishi"] for x in p] == ["长生", "胎", "临官", "临官"]
    assert [x["xunkong"] for x in p] == ["戌亥", "午未", "子丑", "申酉"]
    assert p[0]["shishen_zhi"] == ["食神", "偏财"]
    assert p[0]["hidden_shishen"] == ["食神", "偏财"]
    assert p[1]["shishen_zhi"] == ["正官", "正印", "正财"]


def test_extras_four_palaces():
    """胎元/胎息/命宮/身宮 (A: 乙亥/庚戌/壬午/戊子)."""
    d = run_bazi_json("--date", "1990-08-18", "--time", "06:30", "--city", "台北",
                      "--gender", "male")
    e = d["extras"]
    assert (e["taiyuan"]["gan_zhi"], e["taixi"]["gan_zhi"]) == ("乙亥", "庚戌")
    assert (e["minggong"]["gan_zhi"], e["shengong"]["gan_zhi"]) == ("壬午", "戊子")
    assert e["minggong"]["nayin"] == "杨柳木"


def test_liunian_liuyue_wuhudun():
    """流年 2026 丙午(伤官); 流月五虎遁 丙年庚寅起: 1庚寅正官…5甲午劫财…12辛丑七杀."""
    d = run_bazi_json("--date", "1990-08-18", "--time", "06:30", "--city", "台北",
                      "--gender", "male", "--year", "2026")
    ln = d["liunian"]
    assert ln["gan_zhi"] == "丙午" and ln["shishen"] == "伤官"
    m = ln["liuyue"]
    assert len(m) == 12
    assert m[0]["gan_zhi"] == "庚寅" and m[0]["shishen"] == "正官"
    assert m[4]["gan_zhi"] == "甲午" and m[4]["shishen"] == "劫财"
    assert m[11]["gan_zhi"] == "辛丑" and m[11]["shishen"] == "七杀"


def test_verification_all_pass():
    """校驗: 正常命例四項不變式全過 (真太陽時可逆/時支自洽/大運節氣/納音)."""
    for date, time, city, gender in (("1990-08-18", "06:30", "台北", "male"),
                                     ("1992-03-15", "14:00", "台南", "female")):
        d = run_bazi_json("--date", date, "--time", time, "--city", city, "--gender", gender)
        v = d["verification"]
        assert v["all_pass"] is True, (date, v)
        assert all(c["ok"] for c in v["checks"].values()
                   if isinstance(c, dict) and "ok" in c)


def test_verification_warns_near_hour_boundary():
    """低置信: 06:59台北→真太陽時07:01, 距時辰交界1分, 須警示."""
    d = run_bazi_json("--date", "1990-08-18", "--time", "06:59", "--city", "台北",
                      "--gender", "male")
    assert any("時辰交界" in w for w in d["verification"]["warnings"])
    d2 = run_bazi_json("--date", "1990-08-18", "--time", "06:30", "--city", "台北",
                       "--gender", "male")
    assert d2["verification"]["warnings"] == []


def test_geju_month_command():
    """取格: A 月令申本氣庚透年干→正官格; B 月令卯本氣乙不透→正財格."""
    a = run_bazi_json("--date", "1990-08-18", "--time", "06:30", "--city", "台北",
                      "--gender", "male")
    g = a["geju"]
    assert g["name"] == "正官格" and g["shishen"] == "正官"
    assert g["source"] == "本氣" and "庚" in g["evidence"] and g["breaking"] == []
    b = run_bazi_json("--date", "1992-03-15", "--time", "14:00", "--city", "台南",
                      "--gender", "female")
    assert b["geju"]["name"] == "正財格" and "不透" in b["geju"]["source"]


def test_yongshen_fuyi_and_tiaohou():
    """用神: 扶抑(身強弱xi) + 調候(窮通寶鑑表). A 乙日申月 → 丙癸己, 丙為主."""
    a = run_bazi_json("--date", "1990-08-18", "--time", "06:30", "--city", "台北",
                      "--gender", "male")
    assert a["yongshen"]["primary"] == "印"  # 扶抑主導
    t = a["yongshen"]["tiaohou"]
    assert t["key"] == "乙申" and t["primary"] == "丙" and t["full"] == ["丙", "癸", "己"]
    w = run_bazi_json("--date", "1990-12-20", "--time", "12:00", "--city", "台北",
                      "--gender", "male")
    assert w["geju"]["month_zhi"] == "子"
    assert w["yongshen"]["tiaohou"]["key"].endswith("子")


def test_tiaohou_table_complete():
    """調候資料檔完整性: 10干×12支=120, 每格 primary 為有效天干且在 full 內."""
    d = json.loads((SKILL / "data" / "tiaohou.json").read_text(encoding="utf-8"))
    t = d["table"]
    gan, zhi = "甲乙丙丁戊己庚辛壬癸", "寅卯辰巳午未申酉戌亥子丑"
    assert len(t) == 120
    assert set(t) == {g + z for g in gan for z in zhi}
    for k, v in t.items():
        assert v["primary"] in v["full"] and v["primary"] in gan and v["full"], k


def test_shensha_core_table():
    """神煞 (A乙日, 午年卯日): 天乙貴人(乙→子申, 命中月申)、祿神(乙→卯)、
    文昌(乙→午, 年午)、桃花(午→卯)、驛馬(午→申)、將星(午→午)、天喜(午→卯)、孤辰(午→申)."""
    d = run_bazi_json("--date", "1990-08-18", "--time", "06:30", "--city", "台北",
                      "--gender", "male")
    found = {x["name"]: x for x in d["shensha"]["found"]}
    assert set(found) == {"天乙貴人", "祿神", "文昌", "桃花", "驛馬", "將星", "天喜", "孤辰"}
    assert found["天乙貴人"]["at"] == ["月"] and found["天乙貴人"]["target"] == ["子", "申"]
    assert found["祿神"]["at"] == ["日", "時"]
    assert "羊刃" not in found  # 乙為陰干, 本表從略
