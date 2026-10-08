"""問人總盤 zongpan 分層輸出測試. 邊界=CLI, 斷關鍵行不斷 JSON 鍵."""
import subprocess
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "skills" / "mingli-master"
VENV_PY = str(SKILL / "scripts" / ".venv" / "bin" / "python")
SC = SKILL / "scripts"
BASE = ["--date", "1998-01-05", "--time", "15:57", "--city", "台南", "--gender", "male"]


def run(*args):
    r = subprocess.run([VENV_PY, str(SC / "zongpan.py"), *args],
                       capture_output=True, text=True)
    assert r.returncode == 0, f"zongpan failed: {r.stderr[-400:]}"
    return r.stdout


def test_summary_first_line_contains_input():
    """必讀摘要首行含基本輸入 (日期/時間/城市/性別/曆制/真太陽)."""
    out = run("summary", *BASE, "--at", "2026-10-08", "--year", "2026")
    first = out.splitlines()[0]
    assert first.startswith("# 問人總盤摘要")
    assert "1998-01-05" in first and "15:57" in first and "台南" in first
    assert "男" in first and "國曆" in first and "真太陽" in first


def test_summary_key_lines():
    """摘要含八字/大運/紫微/財語義/警示關鍵行."""
    out = run("summary", *BASE, "--at", "2026-10-08", "--year", "2026")
    for key in ("八字：", "大運逆10歲起", "紫微：", "財官象：", "財語義：", "六壬：", "奇門", "警示："):
        assert key in out, f"missing {key}"
    assert "月刃格" in out and "己酉30-39" in out


def test_summary_size_within_budget():
    """3K 標準: 摘要 ≤ 3.2KB."""
    out = run("summary", *BASE, "--at", "2026-10-08", "--year", "2026")
    assert len(out.encode("utf-8")) <= 3200


def test_ziwei_palaces_filter():
    """--palaces 只輸出指定宮, 一宮一行."""
    out = run("ziwei", *BASE, "--palaces", "財帛,田宅")
    lines = [l for l in out.splitlines() if l.strip()]
    assert len(lines) == 2
    assert lines[0].startswith(("財帛", "田宅")) and lines[1].startswith(("財帛", "田宅"))
    assert "官祿" not in out


def test_ziwei_patterns_section_only():
    """--patterns 只出格局段."""
    out = run("ziwei", *BASE, "--patterns")
    assert "【格局】" in out
    assert "日月同宮" in out and "機月同梁" in out
    assert "命宮(乙巳)" not in out


def test_yun_year_block():
    """yun year: 年標題 + 八字歲運 + 紫微運限 (流耀預設不給)."""
    out = run("yun", "year", "2029", *BASE)
    assert "## 2029 年" in out
    assert "八字歲運：流年2029己酉(正官)" in out
    assert "大限(癸卯)" in out and "流年(己酉)" in out
    assert "流耀" not in out


def test_yun_year_full_adds_liuyue():
    """yun year --full: 加流月/流耀."""
    out = run("yun", "year", "2029", *BASE, "--full")
    assert "流耀" in out or "流月" in out


def test_yun_decade_six_years():
    """yun decade: 6 年一年一行."""
    out = run("yun", "decade", *BASE, "--from", "2026", "--to", "2031")
    data = [l for l in out.splitlines() if l[:4].isdigit()]
    assert len(data) == 6
    assert "2027 丁未(正財)" in out and "流忌巨門" in out


def test_aux_liuren_lifetime():
    """aux liuren: 終身課含課體/三傳/年命."""
    out = run("aux", "liuren", *BASE, "--at-year", "2026")
    assert "【大六壬】" in out and "重審" in out
    assert "本命 戊寅" in out and "行年（2026年）甲午" in out


def test_aux_qimen_lifetime():
    """aux qimen: 終身盤含命宮九宮與時干 (無錯字時乾)."""
    out = run("aux", "qimen", *BASE)
    assert "【奇門遁甲】（終身盤）" in out
    assert "時干落" in out and "時乾" not in out
    assert "命宮" in out


def test_summary_text_and_json_still_available():
    """person_cast: --format text/json 仍可用 (相容, 不宣傳)."""
    r = subprocess.run([VENV_PY, str(SC / "person_cast.py"), *BASE, "--format", "text"],
                       capture_output=True, text=True)
    assert r.returncode == 0
    assert "主盤 八字" in r.stdout
    r2 = subprocess.run([VENV_PY, str(SC / "person_cast.py"), *BASE, "--format", "json"],
                        capture_output=True, text=True)
    assert r2.returncode == 0
    assert r2.stdout.lstrip().startswith("{")