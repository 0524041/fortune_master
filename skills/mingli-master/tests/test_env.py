"""本地 venv 測試: skill 自帶環境, 不依賴六爻絕對路徑."""
import subprocess
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
VENV_PY = SKILL / "scripts" / ".venv" / "bin" / "python"
PINNED = "1.4.8"


def test_local_venv_exists():
    assert VENV_PY.exists(), f"本地 venv 不存在, 先跑 bash scripts/setup.sh ({VENV_PY})"


def test_lunar_version_pinned():
    r = subprocess.run(
        [str(VENV_PY), "-c", "from importlib.metadata import version; print(version('lunar_python'))"],
        capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == PINNED, f"lunar_python 須 pin {PINNED}, 實為 {r.stdout.strip()}"


def test_ganzhi_consistent_with_liuyao():
    """守衛: 同一時間戳本地排盤干支 == 六爻 divine 干支 (版本漂移即抓到).
    六爻已併入本 skill (scripts/yijing), 用同一 venv."""
    dt = "2026-08-01 10:30"
    r1 = subprocess.run([str(VENV_PY), str(SKILL / "scripts" / "bazi_pai.py"),
                         "--date", "2026-08-01", "--time", "10:30", "--lon", "120",
                         "--gender", "male", "--format", "json"],
                        capture_output=True, text=True)
    assert r1.returncode == 0, r1.stderr
    mine = " ".join(p["gan"] + p["zhi"] for p in
                    __import__("json").loads(r1.stdout)["pillars"])
    r2 = subprocess.run([str(VENV_PY), str(SKILL / "scripts" / "yijing" / "divine.py"),
                         "--coins", "1", "1", "1", "1", "1", "1",
                         "--time", dt, "--json"],
                        capture_output=True, text=True)
    assert r2.returncode == 0, r2.stderr
    theirs = __import__("json").loads(r2.stdout.split("===== JSON =====")[-1])["bazi"]
    assert mine == theirs, f"漂移: 本地{mine} vs 六爻{theirs}"


def test_city_suffix_alias():
    """別名: 桃園市/基隆市/苗栗市須解析 (使用者自然輸入), 且與本名同經度."""
    import sys
    sys.path.insert(0, str(SKILL / "scripts"))
    from time_correct import FLAT
    assert FLAT["桃園市"] == FLAT["桃園"]
    assert FLAT["基隆市"] == FLAT["基隆"]
    assert FLAT["苗栗市"] == FLAT["苗栗"]
    assert FLAT["台北市"] == FLAT["台北"]


def test_fuqi_stars_complete():
    """配套知識完整性: 夫妻宮14星斷語表須在skill內 (hepan_ni只剩註解會讀空)."""
    import re
    s = (SKILL / "references" / "ask-person" / "fuqi_stars.md").read_text(encoding="utf-8")
    for star in ["紫微", "天機", "太陽", "武曲", "天同", "廉貞", "天府",
                 "太陰", "貪狼", "巨門", "天相", "天梁", "七殺", "破軍"]:
        assert re.search(rf"^## {star}$", s, re.M), star


def test_glossary_covers_fixture_vocab():
    """配套知識完整性: fixture 出現過的術語必須在 glossary 有定義 (防白話斷鏈)."""
    import json
    g = (SKILL / "references" / "shared" / "glossary.md").read_text(encoding="utf-8")
    vocab = set()
    for f in ["a_bazi.json", "b_bazi.json"]:
        d = json.loads((SKILL / "tests" / "fixtures" / f).read_text(encoding="utf-8"))
        for p in d["pillars"]:
            vocab.add(p["shishen"])
        vocab.update(d["day_strength"]["xi"] + d["day_strength"]["ji"])
    vocab.update(["化祿", "化權", "化科", "化忌", "六合", "六沖", "三合",
                  "建", "除", "滿", "平", "定", "執", "破", "危", "成", "收", "開", "閉",
                  "命宮", "夫妻宮", "福德宮", "財帛", "官祿", "遷移", "大限", "流年",
                  "用神", "天作之合", "互化忌", "真太陽時",
                  # 新功能術語 (八字本質/運限/神煞)
                  "格局", "月令取格", "調候", "納音", "長生十二運", "旬空", "胎元", "身宮",
                  "流月", "流日", "流時", "小限", "流耀",
                  "神煞", "天乙貴人", "桃花", "驛馬", "華蓋", "將星",
                  "孤辰", "寡宿", "羊刃", "祿神", "文昌", "紅鸞", "天喜",
                  # Phase 1 知識補血 (十神組合/從格/紫微輔煞/刑害)
                  "從格", "專旺", "食傷制殺", "傷官見官", "官殺混雜",
                  "夾宮", "疊忌", "六害", "三刑",
                  # 易經 (六爻/梅花)
                  "六爻", "六親", "六神", "世爻", "應爻", "動爻", "變卦", "互卦", "體用", "空亡", "入墓"])
    missing = [v for v in vocab if v not in g and v != "日主"]
    assert not missing, f"glossary 缺詞: {missing}"


def test_output_lint_flags_leaks():
    """輸出規範: 壞樣本須抓到檔名/函數名/程式符號外洩 (bazi_pai.py等)."""
    import subprocess
    r = subprocess.run([str(SKILL / "scripts" / ".venv" / "bin" / "python"),
                        str(SKILL / "scripts" / "output_lint.py"),
                        "--text-file", str(SKILL / "tests" / "fixtures" / "bad_sample.txt"),
                        "--format", "json"],
                       capture_output=True, text=True)
    assert r.returncode != 0
    import json
    hits = {h["token"] for h in json.loads(r.stdout)["violations"]}
    for tok in ["bazi_pai.py", "ziwei_full.sh", "patterns[]", "fuqi_stars",
                "hepan_check.py", "zeri_pick.py", "divine.py"]:
        assert tok in hits, tok


def test_output_lint_clean_passes():
    """乾淨樣本 (中文名對照) 須零違規."""
    import subprocess
    r = subprocess.run([str(SKILL / "scripts" / ".venv" / "bin" / "python"),
                        str(SKILL / "scripts" / "output_lint.py"),
                        "--text-file", str(SKILL / "tests" / "fixtures" / "clean_sample.txt"),
                        "--format", "json"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout


def test_output_lint_strict_flags_vague():
    """--strict 須抓空泛語/巴納姆; 非 strict 不抓 (向後相容)."""
    import subprocess
    import json
    args = [str(SKILL / "scripts" / ".venv" / "bin" / "python"),
            str(SKILL / "scripts" / "output_lint.py"),
            "--text-file", str(SKILL / "tests" / "fixtures" / "vague_sample.txt"),
            "--format", "json"]
    r = subprocess.run(args, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout           # 非 strict: 無外洩 -> 乾淨
    r2 = subprocess.run(args + ["--strict"], capture_output=True, text=True)
    assert r2.returncode != 0
    hits = {h["token"] for h in json.loads(r2.stdout)["violations"]}
    for tok in ["因人而異", "無法由命盤推算收入金額"]:
        assert tok in hits, tok


def test_output_lint_strict_allows_marked_probability():
    """Phase 2 置信制: 帶置信標記的或然判斷須放行 (strict exit 0、零違規);
    無標記的模糊仍擋 (鎖 vague_sample 第 2 行的裸『可能』)."""
    import subprocess
    import json
    lint = [str(SKILL / "scripts" / ".venv" / "bin" / "python"),
            str(SKILL / "scripts" / "output_lint.py"),
            "--format", "json"]
    r = subprocess.run(lint + ["--text-file",
                               str(SKILL / "tests" / "fixtures" / "confident_sample.txt"),
                               "--strict"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout
    assert json.loads(r.stdout)["violations"] == []
    r2 = subprocess.run(lint + ["--text-file",
                                str(SKILL / "tests" / "fixtures" / "vague_sample.txt"),
                                "--strict"],
                        capture_output=True, text=True)
    assert r2.returncode != 0
    assert "可能" in {h["token"] for h in json.loads(r2.stdout)["violations"]}


def test_output_lint_strict_notes_marked_lines():
    """Phase 2 可觀測性: 被標記豁免的行進 notes (不計違規、不影響 exit code)."""
    import subprocess
    import json
    r = subprocess.run([str(SKILL / "scripts" / ".venv" / "bin" / "python"),
                        str(SKILL / "scripts" / "output_lint.py"),
                        "--text-file", str(SKILL / "tests" / "fixtures" / "confident_sample.txt"),
                        "--format", "json", "--strict"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout
    d = json.loads(r.stdout)
    assert "可能" in {n["token"] for n in d.get("notes", [])}, d


def test_yongshen_decision_tree():
    """問事用神決策樹: 三條 fallback＋禁編領域＋古籍依據須在檔."""
    s = (SKILL / "references" / "ask-event" / "yongshen.md").read_text(encoding="utf-8")
    for tok in ["決策樹", "世爻為用", "完全無焦點", "不許為填表編領域",
                "增刪卜易", "卜筮正宗", "世為己，應為人"]:
        assert tok in s, tok


def test_liuyao_checkpoints_and_explain():
    """六爻引導檢查點三道門＋推理自檢＋說過程邀核對."""
    s = (SKILL / "references" / "ask-event" / "liuyao.md").read_text(encoding="utf-8")
    for tok in ["引導檢查點", "用神選定句", "澄清兩問", "現實錨定料",
                "自檢五段", "怎麼看出", "我重看"]:
        assert tok in s, tok


def test_meihua_guide_and_explain():
    """梅花引導與推理節."""
    s = (SKILL / "references" / "ask-event" / "meihua.md").read_text(encoding="utf-8")
    for tok in ["體用定位檢查", "推理三段", "說過程"]:
        assert tok in s, tok


def test_verification_conflict_order():
    """打架裁決順序: 問句漂移→分工→純度加權→六爻為主."""
    s = (SKILL / "references" / "shared" / "verification.md").read_text(encoding="utf-8")
    for tok in ["打架裁決", "問句漂移", "成敗細節聽六爻", "純度加權", "以六爻為主"]:
        assert tok in s, tok


def test_check_env_passes_when_set_up():
    """環境檢查: 已就緒的機器須 exit 0 並顯示『環境就緒』."""
    import subprocess
    r = subprocess.run(["bash", str(SKILL / "scripts" / "check_env.sh")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "環境就緒" in r.stdout
    for tok in ("python3", "node", "lunar_python"):
        assert tok in r.stdout, tok


def test_vendor_lunar_python_present():
    """零安裝: scripts/vendor/lunar_python 存在, 且可被『未安裝』的系統 python3 匯入."""
    import shutil
    import subprocess
    vendor = SKILL / "scripts" / "vendor"
    assert (vendor / "lunar_python").is_dir()
    py = shutil.which("python3")
    assert py, "找不到系統 python3"
    code = f"import sys; sys.path.insert(0, {str(vendor)!r}); import lunar_python; print('ok')"
    r = subprocess.run([py, "-c", code], capture_output=True, text=True)
    assert r.returncode == 0 and "ok" in r.stdout, r.stderr


def test_bazi_runs_on_system_python3():
    """零安裝: 用系統 python3 (無 lunar_python 安裝) 跑八字應成功 (靠 vendor)."""
    import shutil
    import subprocess
    import json
    py = shutil.which("python3")
    r = subprocess.run([py, str(SKILL / "scripts" / "bazi_pai.py"),
                        "--date", "1990-08-18", "--time", "06:30", "--city", "台北",
                        "--gender", "male", "--format", "json"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    d = json.loads(r.stdout)
    assert [p["gan"] + p["zhi"] for p in d["pillars"]] == ["庚午", "甲申", "乙卯", "己卯"]


def test_ziwei_bundle_runs_with_plain_node():
    """零安裝: bundle 用純 node (無 NODE_PATH / node_modules) 應可跑."""
    import os
    import subprocess
    import json
    bundle = SKILL / "scripts" / "ziwei_full.bundle.mjs"
    assert bundle.exists(), "缺 ziwei_full.bundle.mjs"
    env = dict(os.environ)
    env.pop("NODE_PATH", None)
    r = subprocess.run(["node", str(bundle), "--date", "1990-08-18", "--hour", "卯",
                        "--gender", "male", "--format", "json"],
                       capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["hour"] == "卯"
