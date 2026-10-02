"""易經 (六爻 + 梅花) 測試. 邊界=CLI, 期望值手工推演真值."""
import json
import subprocess
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
YJ = SKILL / "scripts" / "yijing"
VENV_PY = str(SKILL / "scripts" / ".venv" / "bin" / "python")


def run(script, *args):
    r = subprocess.run([VENV_PY, str(YJ / script), *args],
                       capture_output=True, text=True)
    assert r.returncode == 0, f"{script} failed: {r.stderr[-500:]}"
    return json.loads(r.stdout)


def test_liuyao_schema_and_bengua():
    """六爻: --coins 全1(少陽) 六爻皆陽 → 乾為天; schema 完整."""
    d = run("divine.py", "--coins", "1", "1", "1", "1", "1", "1",
            "--time", "2026-08-01 10:30", "--json")
    assert {"benguaming", "bianguaming", "bazi", "kongwang"} <= set(d)
    assert "乾" in d["benguaming"]


def test_liuyao_deterministic():
    a = run("divine.py", "--coins", "1", "2", "3", "1", "0", "2", "--time", "2026-08-01 10:30", "--json")
    b = run("divine.py", "--coins", "1", "2", "3", "1", "0", "2", "--time", "2026-08-01 10:30", "--json")
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_liuyao_bazi_matches_bazi_pai():
    """六爻時刻四柱 == 八字排盤四柱 (共用 lunar_python, 同源)."""
    d = run("divine.py", "--coins", "1", "1", "1", "1", "1", "1",
            "--time", "2026-08-01 10:30", "--json")
    r = subprocess.run([VENV_PY, str(SKILL / "scripts" / "bazi_pai.py"),
                        "--date", "2026-08-01", "--time", "10:30", "--lon", "120",
                        "--gender", "male", "--format", "json"],
                       capture_output=True, text=True)
    bz = json.loads(r.stdout)
    mine = " ".join(p["gan"] + p["zhi"] for p in bz["pillars"])
    assert d["bazi"] == mine


def test_meihua_numbers_known():
    """梅花: 17 23 → 天山遁, 動4爻, 互天風姤, 變風山漸, 體艮(土)用乾(金) 體生用."""
    d = run("meihua.py", "--numbers", "17", "23", "--json")
    assert d["bengua"]["name"] == "天山遁"
    assert d["hugua"]["name"] == "天風姤"
    assert d["biangua"]["name"] == "風山漸"
    assert d["dong_yao"] == 4
    assert d["ti_yong"]["relation"] == "體生用"


def test_meihua_time_known():
    """梅花: 時間起卦 2026-08-01 10:30 → 地水師, 動2爻, 體坤用坎 體剋用(吉)."""
    d = run("meihua.py", "--time", "2026-08-01 10:30", "--json")
    assert d["bengua"]["name"] == "地水師"
    assert d["dong_yao"] == 2
    assert d["ti_yong"]["relation"] == "體剋用" and d["ti_yong"]["judge"] == "吉"


def test_meihua_deterministic():
    a = run("meihua.py", "--numbers", "17", "23", "5", "--json")
    b = run("meihua.py", "--numbers", "17", "23", "5", "--json")
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_meihua_defaults_to_now_time():
    """無參數 → 預設以系統現在時間起卦 (不再要求使用者先給時間)."""
    d = run("meihua.py", "--json")
    assert d["method"] == "時間起卦"


def test_meihua_conflicting_methods():
    """--numbers 與 --random 同時給 → 報錯."""
    r = subprocess.run([VENV_PY, str(YJ / "meihua.py"), "--numbers", "1", "2",
                        "--random", "--json"], capture_output=True, text=True)
    assert r.returncode != 0 and "不能同時" in r.stderr


def test_divine_defaults_to_now():
    """六爻無參數 → 隨機起卦 + 系統現在時間."""
    d = run("divine.py", "--json")
    assert d.get("benguaming")
    assert d.get("time")
