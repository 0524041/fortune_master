"""大六壬測試. 驗證基準 = 獨立六壬排盤工具之 720 課結構資料 (tests/fixtures/liuren_reference.json)。

- 天地盤 / 四課 / 十二天將: 須 100% 相符 (純規則, 無歧義)。
- 三傳 (九宗門): 賊克/比用/涉害 有流派歧義, 容許極少數邊界差異 (門檻 97%)。
"""
import json
import subprocess
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "skills" / "mingli-master"
YJ = SKILL / "scripts" / "yijing"
PY = "python3"

import sys
sys.path.insert(0, str(YJ))
sys.path.insert(0, str(SKILL / "scripts" / "vendor"))
import liuren_core as lr  # noqa: E402

REF = json.loads((Path(__file__).resolve().parent / "fixtures" / "liuren_reference.json").read_text(encoding="utf-8"))
PAN = ['巳', '午', '未', '申', '辰', '卯', '酉', '戌', '寅', '丑', '子', '亥']


def _shift(key):
    return (-(int(key.split('_')[1]) - 1)) % 12


def test_tianpan_sike_jiang_exact():
    """天地盤/四課/十二天將: 720 課全對 (純規則)。"""
    for key, ref in REF.items():
        dz = key.split('_')[0]; shift = _shift(key)
        tp = lr.tianpan(shift)
        assert ''.join(tp[d] for d in PAN) == ref[0], key
        sh, xi = lr.four_lessons(dz, shift)
        assert ''.join(sh) == ref[1], key
        assert ''.join(xi) == ref[2], key
        jd = lr.tianjiang(tp, dz, 'day')
        assert ''.join(jd[tp[d]] for d in PAN) == ref[3], key
        jn = lr.tianjiang(tp, dz, 'night')
        assert ''.join(jn[tp[d]] for d in PAN) == ref[4], key


def test_sanchuan_match_rate():
    """三傳: 與基準符合率 >= 97% (流派歧義邊界除外)。"""
    ok = 0
    for key, ref in REF.items():
        dz = key.split('_')[0]; shift = _shift(key)
        sc = lr.sanchuan(dz, shift)[0]
        exp = ref[5].split(',')
        got = [(lr.dungan(dz, c) or '') + c for c in sc]
        if got == exp:
            ok += 1
    assert ok / len(REF) >= 0.97, f"符合率 {ok}/{len(REF)}"


def test_sanchuan_known_cases():
    """定點真值: 甲子_2 (比用連茹) / 甲寅_2 (比用退茹, 秋分後辰將巳時)。"""
    def gz(dz, sc):
        return [(lr.dungan(dz, c) or '') + c for c in sc]
    assert gz('甲子', lr.sanchuan('甲子', (-(2 - 1)) % 12)[0]) == ['甲子', '亥', '戌']
    assert gz('甲寅', lr.sanchuan('甲寅', (-(2 - 1)) % 12)[0]) == ['子', '癸亥', '壬戌']


def test_kongwang_dungan_liuqin():
    """旬空/遁干/六親: 甲子旬 → 空戌亥; 甲日木, 亥水=父母。"""
    assert lr.kongwang('甲子') == ['戌', '亥']
    assert lr.dungan('甲子', '寅') == '丙'
    assert lr.dungan('甲子', '戌') is None
    assert lr.liuqin('甲子', '亥') == '父'


def test_yuejiang_zhongqi():
    """月將中氣換將: 2026-10-07 (秋分後) → 辰。"""
    from liuren_core import LiuRenChart
    from datetime import datetime
    c = LiuRenChart(datetime(2026, 10, 7, 10, 30))
    assert c.yuejiang == '辰'
    assert c.ju == 2  # 占時巳 - 月將辰 = 1 → 第2局


def test_daynight_boundary():
    """晝夜: 卯至申為晝、酉至寅為夜 (酉時起夜占)。"""
    from liuren_core import LiuRenChart
    from datetime import datetime
    assert LiuRenChart(datetime(2026, 10, 7, 10, 30)).daynight == 'day'    # 巳時
    assert LiuRenChart(datetime(2026, 10, 7, 17, 30)).daynight == 'night'  # 酉時
    assert LiuRenChart(datetime(2026, 10, 7, 2, 30)).daynight == 'night'   # 丑時


def test_keti_36_vocabulary():
    """三十六課體: 九宗門細分 + 格局標籤可判定 (自查全 720 課無例外)。"""
    seen = set()
    for key in REF:
        dz = key.split('_')[0]; shift = (-(int(key.split('_')[1]) - 1)) % 12
        sh, xi = lr.four_lessons(dz, shift)
        sc, kind = lr.sanchuan(dz, shift)
        seen |= set(lr.compute_keti(sc, sh, xi, dz, shift, kind))
    for t in ('元首', '重審', '比用', '涉害', '見機', '察微', '綴瑕', '蒿矢', '昴星',
              '別責', '八專', '伏吟', '自任', '自信', '返吟', '無依', '曲直', '炎上',
              '稼穡', '從革', '潤下', '三交', '連茹', '間傳', '元胎', '亂首', '勵德'):
        assert t in seen, f"課體 {t} 未出現"


def test_lifetime_cli():
    """終身課模式: 以出生時刻起課，含終身課框架與本命行年。"""
    r = subprocess.run([PY, str(YJ / "liuren.py"), "--time", "1990-08-18 06:30",
                        "--lifetime", "--gender", "男", "--at-year", "2026", "--json"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    d = json.loads(r.stdout.split('===== JSON =====')[-1])
    assert d['lifetime'] is True and d['at_year'] == 2026
    assert d['persons'][0]['benming'] == '庚午'
    assert d['persons'][0]['xingnian']  # 2026 行年


def test_twin_cike():
    """雙胞胎次客法: 二客換將不換時 (陰將前五/陽將後三)。"""
    assert lr.cike_yuejiang('午', 1) == '午'          # 正課
    assert lr.cike_yuejiang('午', 2) == '卯'          # 陽將(午) 二客 = 後三
    assert lr.cike_yuejiang('亥', 2) == '辰'          # 陰將(亥) 二客 = 前五
    from datetime import datetime
    c = lr.LiuRenChart(datetime(1990, 8, 18, 6, 30), twin=2)
    assert c.twin == 2


def test_cli_json_schema():
    r = subprocess.run([PY, str(YJ / "liuren.py"), "--time", "2026-10-07 10:30",
                        "--birth", "1990", "--gender", "女", "--json"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    d = json.loads(r.stdout.split('===== JSON =====')[-1])
    assert {'sizhu', 'yuejiang', 'sanchuan', 'sike', 'tianpan', 'keti', 'shensha',
            'wangxiang', 'suosheng'} <= set(d)
    assert len(d['sanchuan']) == 3 and len(d['sike']['shang']) == 4
    assert d['yuejiang']['zhi'] == '辰' and d['ju'] == 2
    assert d['persons'][0]['benming']
    assert d['wangxiang'] == {'旺': '金', '相': '水', '死': '木', '囚': '火', '休': '土'}


def test_wangxiang_month():
    """月令五氣: 春木旺火相土死金囚水休; 冬水旺木相火死土囚金休。"""
    assert lr.wangxiang('寅') == {'旺': '木', '相': '火', '死': '土', '囚': '金', '休': '水'}
    assert lr.wangxiang('子') == {'旺': '水', '相': '木', '死': '火', '囚': '土', '休': '金'}
    assert lr.wangxiang('酉') == {'旺': '金', '相': '水', '死': '木', '囚': '火', '休': '土'}


def test_cli_text_clean():
    """文字輸出不得外洩程式符號 (檔名/路徑; 規則見 output-quality.md 五)."""
    import re
    out = subprocess.run([PY, str(YJ / "liuren.py"), "--time", "2026-10-07 10:30"],
                         capture_output=True, text=True).stdout
    assert "【大六壬】" in out and "【三傳】" in out
    assert not re.search(r"[A-Za-z_][\w-]*\.(py|sh|ts|mjs|js|md|json|txt)", out), "英文檔名外洩"
    assert not re.search(r"/Users/|/tmp/", out), "本機路徑外洩"
