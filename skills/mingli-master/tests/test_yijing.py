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


def run_text(script, *args):
    r = subprocess.run([VENV_PY, str(YJ / script), *args], capture_output=True, text=True)
    assert r.returncode == 0, f"{script} failed: {r.stderr[-500:]}"
    return r.stdout


def test_yaoci_data_integrity():
    """爻辭資料庫: 64卦各6爻, 乾坤附用九/用六, 抽查通行底本."""
    import json
    d = json.load(open(SKILL / "data" / "yaoci_64.json", encoding="utf-8"))
    assert len(d) == 64
    assert {e["number"] for e in d} == set(range(1, 65))
    assert all(len(e["yao"]) == 6 for e in d)
    assert {e["number"] for e in d if e.get("yong")} == {1, 2}
    qian = next(e for e in d if e["number"] == 1)
    assert qian["yao"][0]["text"].startswith("潛龍勿用")
    assert "見龍在田" in qian["yao"][1]["text"]
    assert qian["yong"]["pos"] == "用九"


def test_liuyao_dongyao_yaoci():
    """六爻盤面: 有動爻時附《周易正義》動爻爻辭 (0=老陽 3=老陰)."""
    out = run_text("divine.py", "--coins", "0", "1", "2", "1", "3", "1",
                   "--time", "2026-10-02 21:42")
    assert "【動爻爻辭】" in out
    assert "初九" in out and "悔亡。喪馬" in out      # 火澤睽初九
    assert "六五" in out and "厥宗噬膚" in out        # 火澤睽六五


def test_liuyao_static_gua_note():
    """六爻靜卦: 無動爻須提示依月日旺衰/世應推斷, 不當作無訊號."""
    out = run_text("divine.py", "--coins", "1", "1", "1", "1", "1", "1",
                   "--time", "2026-10-02 21:42")
    assert "無動爻" in out


def test_meihua_includes_guaci_and_wuxing():
    """梅花盤面: 附本/互/變卦辭象傳 + 互變五行疊加."""
    out = run_text("meihua.py", "--numbers", "17", "23")
    assert "卦辭：" in out and "象傳：" in out
    assert "互卦疊加" in out and "變卦疊加" in out


def test_meihua_json_ti_relations():
    """梅花 JSON: 互卦/變卦對體的生剋已算好 (17 23 動4爻→用在上卦)."""
    d = run("meihua.py", "--numbers", "17", "23", "--json")
    assert d["biangua"]["ti_relation"] and d["hugua"]["ti_relation"]
    assert d["biangua"]["side_gua"] == d["biangua"]["upper"]


def test_meihua_time_lunar_conversion():
    """梅花時間起卦須走農曆: 2026-10-02 21:42 → 農曆8月22日, 年支7/月8/日22/時支12."""
    d = run("meihua.py", "--time", "2026-10-02 21:42", "--json")
    assert d["inputs"]["lunar"] == "二〇二六年8月22日"
    assert d["inputs"]["zhi"] == {"年支數": 7, "月": 8, "日": 22, "時支數": 12}
    assert d["bengua"]["name"] == "風天小畜" and d["dong_yao"] == 1


def test_liuyao_time_includes_hour_pillar():
    """六爻起卦時間含時柱 (Solar.fromDate 不可丟時間); 同搖卦不同時辰→四柱不同、卦相同."""
    a = run("divine.py", "--coins", "1", "1", "1", "1", "1", "1",
            "--time", "2026-10-02 09:00", "--json")
    b = run("divine.py", "--coins", "1", "1", "1", "1", "1", "1",
            "--time", "2026-10-02 21:00", "--json")
    assert a["bazi"] != b["bazi"]
    assert a["benguaming"] == b["benguaming"]
