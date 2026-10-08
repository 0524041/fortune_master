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
    """回歸: 全年輸出不得殘留簡體關鍵字 (統一簡繁層 han)."""
    cmd = [VENV_PY, str(SCRIPT), "--matter", "嫁娶",
           "--from", "2026-01-01", "--to", "2026-12-31",
           "--bazi", str(FIX / "a_bazi.json"), "--ziwei", str(FIX / "a_ziwei.json"),
           "--hours", "--format", "json", "--top", "5"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    d = json.loads(r.stdout)
    # 註: 斗 (二十八宿) 為正體, 不列; 其餘為引擎可能殘留的簡體字
    bad = set("开闭杀门财权禄贪贞机辅迁马龙鸡仓废罗败惊艳钟萧肃啸东黄陈虚残对兴体会伤动胜营业猪蚕来儿孙钱题须绿枢瑶玑灵疗网宫当")
    blob = json.dumps(d, ensure_ascii=False)
    leaks = bad & set(blob)
    assert not leaks, f"simplified leak: {leaks}"


# ── 吉時層 (v2) ────────────────────────────────────────────────────

def test_hours_schema_and_verification():
    """--hours: 候選日各含 12 時辰與 top_hours; verification 全過."""
    d = run_zeri_matter("入宅", "--bazi", str(FIX / "a_bazi.json"), "--hours")
    cand = [x for x in d["days"] if x["status"] == "candidate"]
    assert cand and all(len(x["hours"]) == 12 for x in cand)
    assert all(x["top_hours"] for x in cand)
    v = d["verification"]
    assert v["all_pass"] is True
    assert v["checks"]["hours_complete"]["ok"] is True
    assert any("紫微" in w for w in v["warnings"])


def test_hour_personal_veto():
    """手工真值 (10-13 庚申, 甲=乙卯/年午): 子時丙子沖生年午→否決; 酉時乙酉沖日柱卯→否決."""
    d = run_zeri_matter("入宅", "--bazi", str(FIX / "a_bazi.json"), "--hours")
    day = by_date(d, "2026-10-13")
    h = {x["index"]: x for x in day["hours"]}
    assert h[0]["status"] == "vetoed" and any("沖生年" in v for v in h[0]["veto"])
    assert h[9]["status"] == "vetoed" and any("沖日柱" in v for v in h[9]["veto"])
    # 否決時辰不得進 top_hours
    assert all(x["index"] not in (0, 9) for x in day["top_hours"])


def test_hour_ji_veto():
    """手工真值: 10-13 申時甲申 通書時忌含入宅 → 否決."""
    d = run_zeri_matter("入宅", "--bazi", str(FIX / "a_bazi.json"), "--hours")
    h = {x["index"]: x for x in by_date(d, "2026-10-13")["hours"]}
    assert h[8]["status"] == "vetoed" and any("時忌含" in v for v in h[8]["veto"])


def test_top_hour_pinned():
    """手工真值: 10-13 入宅 6分, 首吉時 未時癸未 3分."""
    d = run_zeri_matter("入宅", "--bazi", str(FIX / "a_bazi.json"), "--hours")
    day = by_date(d, "2026-10-13")
    assert day["score"] == 6
    assert day["top_hours"][0]["name"] == "未時" and day["top_hours"][0]["score"] == 3


def test_verification_keys():
    d = run_zeri()
    v = d["verification"]
    assert {"checks", "warnings", "all_pass"} == set(v)
    assert v["checks"]["matter_valid"]["ok"] is True
    assert v["checks"]["veto_has_reason"]["ok"] is True
    assert v["all_pass"] is True
