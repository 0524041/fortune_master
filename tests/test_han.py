"""統一簡繁轉換層 han.py 測試. 期望值皆手工真值."""
import json
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "skills" / "mingli-master"
HAN = SKILL / "scripts" / "han.py"
sys.path.insert(0, str(SKILL / "scripts"))
import han  # noqa: E402


def test_s2t_basic():
    """手工真值: 引擎常用詞 簡→繁."""
    assert han.s2t("命宫") == "命宮"
    assert han.s2t("七杀巨门廉贞陀罗") == "七殺巨門廉貞陀羅"
    assert han.s2t("临官长生剑锋金") == "臨官長生劍鋒金"
    assert han.s2t("开市入宅财神") == "開市入宅財神"


def test_s2t_context_aware():
    """opencc 詞組轉換: 天干不誤轉為天乾, 咸池不誤轉."""
    assert han.s2t("天干地支") == "天干地支"
    assert han.s2t("咸池") == "咸池"


def test_s2t_idempotent():
    """已繁體者冪等 (不變)."""
    for t in ["命宮財帛官祿僕役遷移七殺", "黃道吉日", "碓磨門外正東"]:
        assert han.s2t(t) == t
        assert han.s2t(han.s2t(t)) == han.s2t(t)


def test_domain_post_fixes():
    """領域例外: opencc 會誤轉的正體字/詞, 統一層修正回命理正字."""
    assert han.s2t("丑") == "丑" and han.s2t("子丑") == "子丑" and han.s2t("丑時") == "丑時"
    assert han.s2t("斗") == "斗" and han.s2t("斗木獬") == "斗木獬"
    assert han.s2t("凶") == "凶" and han.s2t("勾陈凶") == "勾陳凶"
    assert han.s2t("占大门") == "占大門" and han.s2t("作灶") == "作灶"
    assert han.s2t("启钻") == "啟鑽" and han.s2t("冲煞") == "沖煞" and han.s2t("安床") == "安床"


def test_norm_palace():
    assert han.norm_palace("命宫") == "命"
    assert han.norm_palace("財帛宮") == "財帛"
    assert han.norm_palace("僕役") == "僕役"


def test_s2t_deep_values_only():
    """只轉字串值, keys 不動."""
    obj = {"name": "命宫", "list": ["七杀", 3, True], "sub": {"star": "廉贞"}}
    out = han.s2t_deep(obj)
    assert list(out.keys()) == ["name", "list", "sub"]
    assert out["name"] == "命宮" and out["sub"]["star"] == "廉貞"
    assert out["list"][1] == 3 and out["list"][2] is True


def test_is_clean_and_leaks():
    dirty = {"p": "命宫", "s": "七杀"}
    clean = han.s2t_deep(dirty)
    assert han.is_clean(clean)
    assert not han.is_clean(dirty)
    assert "宫" in han.simplified_leaks(dirty)
    assert han.simplified_leaks(clean) == []


def test_cli_filter():
    """CLI --filter: 逐段轉繁, JSON 結構不壞."""
    r = subprocess.run([sys.executable, str(HAN), "--filter"],
                       input='{"name":"命宫","star":"七杀"}', capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout) == {"name": "命宮", "star": "七殺"}


def test_cli_args():
    r = subprocess.run([sys.executable, str(HAN), "命宫", "七杀"], capture_output=True, text=True)
    assert r.returncode == 0
    assert r.stdout.strip() == "命宮 七殺"
