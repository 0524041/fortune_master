"""曆制 (國曆/農曆/閏月) 測試. 農曆輸入須與等價國曆排盤一致."""
import json
import subprocess
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
VENV_PY = str(SKILL / "scripts" / ".venv" / "bin" / "python")
SH = SKILL / "scripts" / "ziwei_full.sh"


def bazi(*extra):
    r = subprocess.run([VENV_PY, str(SKILL / "scripts" / "bazi_pai.py"),
                        "--time", "12:00", "--city", "台北", "--gender", "male",
                        "--format", "json", *extra], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def ziwei(*extra):
    r = subprocess.run([str(SH), "--time", "12:00", "--city", "台北",
                        "--gender", "male", "--format", "json", *extra],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def pillars(d):
    return [p["gan"] + p["zhi"] for p in d["pillars"]]


def test_bazi_lunar_matches_solar():
    """農曆 2020-04-15 == 國曆 2020-05-07 (四柱一致), 且標 calendar=lunar."""
    lu = bazi("--calendar", "lunar", "--date", "2020-04-15")
    so = bazi("--date", "2020-05-07")
    assert pillars(lu) == pillars(so)
    assert lu["calendar"] == "lunar" and so["calendar"] == "solar"
    assert lu["birth_input"] == {"date": "2020-04-15", "calendar": "lunar", "leap": False}


def test_bazi_leap_month_matches_solar():
    """農曆閏 2020 閏4月15 == 國曆 2020-06-06."""
    leap = bazi("--calendar", "lunar", "--leap", "--date", "2020-04-15")
    so = bazi("--date", "2020-06-06")
    assert pillars(leap) == pillars(so)
    assert leap["birth_input"]["leap"] is True


def test_ziwei_lunar_matches_solar():
    """紫微: 農曆 2020-04-15 == 國曆 2020-05-07 (命/身/局一致)."""
    lu = ziwei("--calendar", "lunar", "--date", "2020-04-15")
    so = ziwei("--date", "2020-05-07")
    assert lu["date"] == so["date"] == "2020-5-7"
    assert (lu["ming"]["branch"], lu["ming"]["shen"], lu["ming"]["wuju"]) == \
        (so["ming"]["branch"], so["ming"]["shen"], so["ming"]["wuju"])
    assert lu["calendar"] == "lunar"


def test_cast_lunar_cross_check():
    """cast 農曆: 二盤時支一致、校驗全過."""
    r = subprocess.run([VENV_PY, str(SKILL / "scripts" / "cast.py"),
                        "--calendar", "lunar", "--date", "2020-04-15", "--time", "12:00",
                        "--city", "台北", "--gender", "male", "--format", "json"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    cc = json.loads(r.stdout)["cross_check"]
    assert cc["time_branch_match"] is True and cc["bazi_verification_pass"] is True


def test_invalid_leap_month_clean_error():
    """無效閏月須乾淨報錯 (exit!=0, 無 traceback)."""
    r = subprocess.run([VENV_PY, str(SKILL / "scripts" / "bazi_pai.py"),
                        "--calendar", "lunar", "--leap", "--date", "1985-06-15",
                        "--time", "12:00", "--lon", "120", "--gender", "male",
                        "--format", "json"], capture_output=True, text=True)
    assert r.returncode != 0
    assert "Traceback" not in r.stderr
    assert "農曆" in r.stderr


def test_ziwei_invalid_leap_clean_error():
    r = subprocess.run([str(SH), "--calendar", "lunar", "--leap", "--date", "1985-06-15",
                        "--time", "12:00", "--lon", "120", "--gender", "male",
                        "--format", "json"], capture_output=True, text=True)
    assert r.returncode != 0
    assert "Traceback" not in r.stderr
    assert "農曆" in r.stderr
