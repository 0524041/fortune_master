"""decade.py 測試 (TDD, 邊界=CLI). 多年運總表: 一年一行, 八字流年＋紫微運限對照."""
import json
import subprocess
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SCRIPT = SKILL / "scripts" / "decade.py"
VENV_PY = str(Path(__file__).resolve().parent.parent / "scripts" / ".venv" / "bin" / "python")


def run_decade(*extra, fmt="json"):
    cmd = [VENV_PY, str(SCRIPT), "--date", "1998-01-05", "--time", "15:57",
           "--city", "台南", "--gender", "male", "--format", fmt, *extra]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, f"CLI failed: {r.stderr[-500:]}"
    return r.stdout


def test_json_schema_and_range():
    """2021-2023 三年, schema 含 input/years; 每年八字＋紫微欄位齊."""
    d = json.loads(run_decade("--from", "2021", "--to", "2023"))
    assert [r["year"] for r in d["years"]] == [2021, 2022, 2023]
    for r in d["years"]:
        assert {"liunian", "shishen", "dayun"} <= set(r["bazi"])
        assert {"daxian_palace", "liunian_palace", "liunian_ganzhi", "liunian_ji"} <= set(r["ziwei"])


def test_known_values_2026():
    """手工真值抽查: 2026 丙午(偏财) / 大運庚戌 / 流年父母 / 流忌廉贞 (與單發引擎一致)."""
    d = json.loads(run_decade("--from", "2026", "--to", "2026"))
    r = d["years"][0]
    assert r["bazi"]["liunian"] == "丙午" and r["bazi"]["shishen"] == "偏财"
    assert r["bazi"]["dayun"] == "庚戌"
    assert r["ziwei"]["liunian_palace"] == "父母" and r["ziwei"]["liunian_ji"] == "廉贞"


def test_text_one_line_per_year():
    """text 格式: 標頭 + 一年一行."""
    out = run_decade("--from", "2021", "--to", "2022", fmt="text")
    lines = [l for l in out.splitlines() if l.strip()]
    assert len(lines) == 3 and lines[0].startswith("多年運")
    assert lines[1].startswith("2021") and lines[2].startswith("2022")


def test_bad_range_rejected():
    """--to 早於 --from 須乾淨報錯."""
    cmd = [VENV_PY, str(SCRIPT), "--date", "1998-01-05", "--time", "15:57",
           "--city", "台南", "--gender", "male",
           "--from", "2030", "--to", "2021", "--format", "json"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode != 0
    assert "Traceback" not in r.stderr
