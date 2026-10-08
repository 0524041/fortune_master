"""tongshu_day.py 測試 (TDD, 邊界=CLI). 期望值皆手工真值 (對照天機通書 2026-10-08)."""
import json
import subprocess
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "skills" / "mingli-master"
SCRIPT = SKILL / "scripts" / "tongshu_day.py"
FIX = Path(__file__).resolve().parent / "fixtures"
VENV_PY = str(SKILL / "scripts" / ".venv" / "bin" / "python")


def run(*extra):
    r = subprocess.run([VENV_PY, str(SCRIPT), *extra, "--format", "json"],
                       capture_output=True, text=True)
    assert r.returncode == 0, f"CLI failed: {r.stderr}"
    return json.loads(r.stdout)


def test_day_fields_pinned():
    """手工真值 (2026-10-08): 乙卯日 建除執 宿井木犴 納音大溪水 彭祖 胎神 方位 空亡."""
    d = run("--date", "2026-10-08")["day"]
    assert d["day_pillar"] == "乙卯" and d["year_pillar"] == "丙午" and d["month_pillar"] == "丁酉"
    assert d["jianchu"] == "執"
    assert d["xiu"] == {"name": "井", "zheng": "木", "animal": "犴", "luck": "吉"}
    assert d["nayin"] == "大溪水"
    assert d["huangdao_type"] == "黑道" and d["huangdao_good"] is False
    assert d["directions"]["喜神"] == "西北" and d["directions"]["陽貴"] == "西南"
    assert d["xunkong"] == "子丑"
    assert d["pengzu"] == {"gan": "乙不栽植千株不長", "zhi": "卯不穿井水泉不香"}
    assert d["taishen"].startswith("碓磨門")


def test_hours_complete_and_pinned():
    """十二時辰齊; 子時丙子司命黃道吉 / 午時壬午金匱 / 亥時丁亥玄武黑道."""
    out = run("--date", "2026-10-08")
    hrs = out["hours"]
    assert len(hrs) == 12
    assert hrs[0]["name"] == "子時" and hrs[0]["ganzhi"] == "丙子"
    assert hrs[0]["huangdao_name"] == "司命" and hrs[0]["huangdao_luck"] == "吉"
    assert hrs[6]["ganzhi"] == "壬午" and hrs[6]["huangdao_name"] == "金匱"
    assert hrs[11]["ganzhi"] == "丁亥" and hrs[11]["huangdao_type"] == "黑道"


def test_personal_layer():
    """加 a_bazi (乙卯日/年午): 子時沖生年(午), 酉時沖日柱(卯)."""
    out = run("--date", "2026-10-08", "--bazi", str(FIX / "a_bazi.json"))
    hrs = out["hours"]
    assert hrs[0]["personal"]["甲"]["chong_year"] is True
    assert hrs[9]["personal"]["甲"]["chong_day"] is True
    assert hrs[6]["personal"]["甲"]["shishen"] == "正印"  # 壬午時, 壬對乙為正印


def test_qimen_layer_and_verification():
    """--qimen: 每時辰附奇門; verification 全過且警示節氣交界 (當日寒露)."""
    out = run("--date", "2026-10-08", "--qimen")
    assert all(h.get("qimen") for h in out["hours"])
    assert out["hours"][0]["qimen"]["ju"].endswith("局")
    v = out["verification"]
    assert v["all_pass"] is True
    assert v["checks"]["hours_complete"]["ok"] is True
    assert any("寒露" in w for w in v["warnings"])


def test_text_has_hour_yi_ji():
    """文字輸出每時辰附宜/忌 (2026-10-08 子時宜含作灶)."""
    r = subprocess.run([VENV_PY, str(SCRIPT), "--date", "2026-10-08"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "宜:" in r.stdout and "忌:" in r.stdout
    assert "作灶" in r.stdout


def test_no_simplified_leak():
    """全輸出繁體 (統一簡繁層)."""
    out = run("--date", "2026-10-08", "--bazi", str(FIX / "a_bazi.json"), "--qimen")
    bad = set("开闭杀门财权禄贪贞机辅迁马龙鸡仓废罗败惊艳东黄陈虚残对兴体会伤动胜营业猪蚕来儿孙钱题须绿枢瑶玑灵疗网宫斗当")
    assert not (bad & set(json.dumps(out, ensure_ascii=False)))
