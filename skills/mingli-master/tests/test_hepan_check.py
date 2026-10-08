"""hepan_check.py 測試 (TDD, 邊界=CLI). 期望值皆為手工推演真值, 非程式重算."""
import json
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SCRIPT = SKILL / "scripts" / "hepan_check.py"
FIX = SKILL / "tests" / "fixtures"
VENV_PY = str(Path(__file__).resolve().parent.parent / "scripts" / ".venv" / "bin" / "python")
# 本地 venv 不存在時先跑 bash scripts/setup.sh


def run_hepan(*extra):
    cmd = [VENV_PY, str(SCRIPT),
           "--a-bazi", str(FIX / "a_bazi.json"), "--a-ziwei", str(FIX / "a_ziwei.json"),
           "--b-bazi", str(FIX / "b_bazi.json"), "--b-ziwei", str(FIX / "b_ziwei.json"),
           "--format", "json", *extra]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, f"CLI failed: {r.stderr}"
    return json.loads(r.stdout)


def test_cli_smoke_schema():
    """CLI 能跑, 輸出含 8 檢查鍵 + ref 參考分 (工具不定性)."""
    d = run_hepan()
    assert set(d["checks"]) == {"tianzuo", "fuqi_fude", "sun_moon", "pillars",
                                "wuxing", "daxian", "peach", "huaji"}
    assert set(d["ref"]) == {"score", "note"}


def test_fuqi_fude_both_caution():
    """手工真值: 甲夫妻七杀+福德破军鈴星=caution; 乙夫妻巨门地劫+福德太陽陷陀羅=caution → -1."""
    d = run_hepan()
    f = d["checks"]["fuqi_fude"]
    assert f["a"] == "caution" and f["b"] == "caution"
    assert f["score"] == -1


def test_tianzuo_both_empty():
    """手工真值: A夫妻{七杀} vs B命{天同,天梁}無; B夫妻{巨门} vs A命{武曲}無."""
    d = run_hepan()
    t = d["checks"]["tianzuo"]
    assert t["a_to_b"] is False
    assert t["b_to_a"] is False
    assert t["score"] == 0


def test_sun_moon_a_good_b_bad():
    """手工真值: 男A太陰仆役bright化科=吉; 女B太陽福德dim=差 → score 0."""
    d = run_hepan()
    s = d["checks"]["sun_moon"]
    assert s["a_moon"] == "吉" and s["b_sun"] == "差"
    assert s["score"] == 0


def test_pillars_he_no_chong():
    """手工真值: 日干乙庚合 + 時支卯未半合, 跨柱無沖 → score 2."""
    d = run_hepan()
    p = d["checks"]["pillars"]
    assert any("乙庚合" in h for h in p["he"])
    assert any("卯未" in h for h in p["he"])
    assert p["chong"] == []
    assert p["score"] == 2


def test_wuxing_supply_and_ke():
    """手工真值: B水(33)生A木(40) 補益B→A +1; 日主庚剋乙 -1 → score 0."""
    d = run_hepan()
    w = d["checks"]["wuxing"]
    assert any("B→A" in s and "水生木" in s for s in w["supply"])
    assert "庚剋乙" in w["day_master_rel"]
    assert w["score"] == 0


def test_daxian_not_sync():
    """手工真值: A當前34-43田宅 vs B當前25-34夫妻, 不同宮 → sync False, score 0."""
    d = run_hepan()
    x = d["checks"]["daxian"]
    assert x["sync"] is False
    assert "田宅" in x["a_current"] and "夫妻" in x["b_current"]
    assert x["score"] == 0


def test_peach_lists():
    """手工真值: A天喜咸池在兄弟紅鸞在仆役; B紅鸾在兄弟天姚在遷移 → 純資訊, score 0."""
    d = run_hepan()
    p = d["checks"]["peach"]
    assert "天喜" in str(p["a_peach"]) and "咸池" in str(p["a_peach"])
    assert "紅鸞" in str(p["b_peach"]) or "红鸾" in str(p["b_peach"])
    assert p["score"] == 0


def test_huaji_mutual_into_ming():
    """手工真值: A忌天同落B命宮, B忌武曲落A命宮 → mutual True, score -2."""
    d = run_hepan()
    h = d["checks"]["huaji"]
    assert h["mutual"] is True
    assert any(f["star"] == "天同" and f["palace"] == "命宮" for f in h["a_to_b"])
    assert any(f["star"] == "武曲" and f["palace"] == "命宮" for f in h["b_to_a"])
    assert h["score"] == -2


def test_verdict_hand_total():
    """手工加總: 0-1+0+2+0+0+0-2 = -1 (參考分, 不定性)."""
    d = run_hepan()
    assert d["ref"]["score"] == -1


def test_swap_symmetry():
    """驗證機制: 交換甲乙, 總分不變, 天作/化忌鏡像對調."""
    d1 = run_hepan()
    cmd = [VENV_PY, str(SCRIPT),
           "--a-bazi", str(FIX / "b_bazi.json"), "--a-ziwei", str(FIX / "b_ziwei.json"),
           "--b-bazi", str(FIX / "a_bazi.json"), "--b-ziwei", str(FIX / "a_ziwei.json"),
           "--format", "json"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    d2 = json.loads(r.stdout)
    assert d2["ref"]["score"] == d1["ref"]["score"]
    assert d2["checks"]["tianzuo"]["a_to_b"] == d1["checks"]["tianzuo"]["b_to_a"]
    assert d2["checks"]["huaji"]["mutual"] == d1["checks"]["huaji"]["mutual"]


def test_deterministic_twice():
    """驗證機制: 跑兩次輸出完全一致."""
    assert json.dumps(run_hepan(), sort_keys=True) == json.dumps(run_hepan(), sort_keys=True)


def test_text_format_smoke():
    """驗證機制: text 格式能跑且含參考分行 (不定性)."""
    cmd = [VENV_PY, str(SCRIPT),
           "--a-bazi", str(FIX / "a_bazi.json"), "--a-ziwei", str(FIX / "a_ziwei.json"),
           "--b-bazi", str(FIX / "b_bazi.json"), "--b-ziwei", str(FIX / "b_ziwei.json"),
           "--format", "text"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "【合盤】參考分 -1" in r.stdout
