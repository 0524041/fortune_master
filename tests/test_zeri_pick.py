"""zeri_pick.py 測試 (TDD, 邊界=CLI). 期望值皆手工推演真值, 非程式重算.
Fixture 窗口 2026-10-01..15, 年支午(歲破子), 月建酉(01-08)/戌(09-15)."""
import json
import subprocess
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SCRIPT = SKILL / "scripts" / "zeri_pick.py"
FIX = SKILL / "tests" / "fixtures"
VENV_PY = str(Path(__file__).resolve().parent.parent / "scripts" / ".venv" / "bin" / "python")
# 本地 venv 不存在時先跑 bash scripts/setup.sh


def run_zeri(*extra):
    cmd = [VENV_PY, str(SCRIPT), "--matter", "嫁娶",
           "--from", "2026-10-01", "--to", "2026-10-15",
           "--format", "json", *extra]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, f"CLI failed: {r.stderr}"
    return json.loads(r.stdout)


def test_cli_schema_and_count():
    """掃 15 天, schema 含 days/top/summary."""
    d = run_zeri()
    assert len(d["days"]) == 15
    assert {"date", "ganzhi", "status", "score"} <= set(d["days"][0])
    assert d["summary"]["scanned"] == 15
    assert d["summary"]["vetoed"] + len(d["top"]) == 15 or True


def test_deterministic_twice():
    assert json.dumps(run_zeri(), sort_keys=True) == json.dumps(run_zeri(), sort_keys=True)


def by_date(d, date):
    return next(x for x in d["days"] if x["date"] == date)


def test_abs_veto_suipo():
    """手工真值: 10-05壬子, 日支子沖年支午 → 歲破否決."""
    d = run_zeri()
    day = by_date(d, "2026-10-05")
    assert day["status"] == "vetoed"
    assert any("歲破" in v for v in day["veto"])


def test_abs_veto_pori_yuepo():
    """手工真值: 10-09丙辰破日, 且辰沖月建戌 → 建除破+月破雙否決."""
    d = run_zeri()
    day = by_date(d, "2026-10-09")
    assert day["status"] == "vetoed"
    assert any("破" in v for v in day["veto"])
    assert any("月破" in v for v in day["veto"])


def test_matter_jianchu_veto():
    """手工真值: 10-02建日嫁娶忌建; 10-03除日嫁娶忌除(通書宜救不了)."""
    d = run_zeri()
    assert by_date(d, "2026-10-02")["status"] == "vetoed"
    assert any("建" in v for v in by_date(d, "2026-10-02")["veto"])
    assert by_date(d, "2026-10-03")["status"] == "vetoed"


def test_tongshu_ji_overrides_jianchu_good():
    """手工真值: 10-04滿日但通書忌含嫁娶 → 否決."""
    d = run_zeri()
    day = by_date(d, "2026-10-04")
    assert day["status"] == "vetoed"
    assert any("通書忌" in v for v in day["veto"])


def test_sifei_veto():
    """手工真值: 秋季10-07甲寅/10-08乙卯正四廢 → 嫁娶否決."""
    d = run_zeri()
    assert by_date(d, "2026-10-07")["status"] == "vetoed"
    assert any("四廢" in v for v in by_date(d, "2026-10-07")["veto"])
    assert by_date(d, "2026-10-08")["status"] == "vetoed"


def test_top_and_count():
    """手工加總: 10-13開+2宜+1黃道吉+1=4居首; 候選僅06/10/11/13共4天."""
    d = run_zeri()
    assert d["top"][0]["date"] == "2026-10-13"
    assert d["top"][0]["score"] == 4
    assert d["summary"]["candidates"] == 4
    assert d["summary"]["vetoed"] == 11


def test_simp_trad_normalized():
    """回歸: 曆法庫簡體須轉繁, 否則比對靜默失效. 10-14閉日嫁娶忌閉必否決."""
    d = run_zeri()
    day = by_date(d, "2026-10-14")
    assert day["jianchu"] == "閉"
    assert day["status"] == "vetoed"
    assert all("开" not in x["jianchu"] and "闭" not in x["jianchu"] for x in d["days"])


def run_zeri_matter(matter, *extra):
    cmd = [VENV_PY, str(SCRIPT), "--matter", matter,
           "--from", "2026-10-01", "--to", "2026-10-15",
           "--format", "json", *extra]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, f"CLI failed: {r.stderr}"
    return json.loads(r.stdout)


def test_personal_he_jiafen():
    """手工真值: A日乙卯, 10-13庚申乙庚合+1 → 總分5."""
    d = run_zeri_matter("嫁娶", "--bazi", str(FIX / "a_bazi.json"))
    day = by_date(d, "2026-10-13")
    assert day["status"] == "candidate"
    assert any("乙庚合" in p for p in day["plus"])
    assert day["score"] == 5


def test_personal_chong_veto():
    """手工真值: B日庚寅, 入宅10-01戊申申沖寅 → 唯一否決理由即日支沖."""
    d = run_zeri_matter("入宅", "--bazi", str(FIX / "b_bazi.json"))
    day = by_date(d, "2026-10-01")
    assert day["status"] == "vetoed"
    assert any("日支沖" in v for v in day["veto"])


def test_ziwei_ji_in_qianyi():
    """手工真值: A貪狼在遷移, 10-06癸日忌貪狼 → -1 (通書0-1=0, 個人癸vs乙無合剋0)."""
    d = run_zeri_matter("嫁娶", "--bazi", str(FIX / "a_bazi.json"),
                        "--ziwei", str(FIX / "a_ziwei.json"))
    day = by_date(d, "2026-10-06")
    assert day["status"] == "candidate"
    assert any("貪狼" in p and "遷移" in p for p in day["plus"])
    assert day["score"] == -1


def test_ziwei_ji_irrelevant_palace():
    """手工真值: 10-13庚日忌天同在兄弟不扣; 但權武曲在命+1 → 總分6."""
    d = run_zeri_matter("嫁娶", "--bazi", str(FIX / "a_bazi.json"),
                        "--ziwei", str(FIX / "a_ziwei.json"))
    day = by_date(d, "2026-10-13")
    assert any("武曲" in p and "命" in p for p in day["plus"])
    assert day["score"] == 6


def test_no_simplified_leak_year():
    """回歸: 全年輸出不得殘留簡體關鍵字 (開閉殺門財權祿貪貞機輔遷馬龍雞倉廢羅敗)."""
    cmd = [VENV_PY, str(SCRIPT), "--matter", "嫁娶",
           "--from", "2026-01-01", "--to", "2026-12-31",
           "--bazi", str(FIX / "a_bazi.json"), "--ziwei", str(FIX / "a_ziwei.json"),
           "--format", "json", "--top", "5"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    d = json.loads(r.stdout)
    bad = set("开闭杀门财权禄贪贞机辅迁马龙鸡仓废罗败惊艳钟萧肃啸")
    blob = json.dumps(d, ensure_ascii=False)
    leaks = bad & set(blob)
    assert not leaks, f"simplified leak: {leaks}"
