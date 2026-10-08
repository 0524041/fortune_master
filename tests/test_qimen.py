"""奇門遁甲測試. 驗證基準 = 拆補法+轉盤+陽盤 通例 (衍象坊案例)。"""
import json
import subprocess
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "skills" / "mingli-master"
YJ = SKILL / "scripts" / "yijing"
PY = "python3"

import sys
sys.path.insert(0, str(YJ))
sys.path.insert(0, str(SKILL / "scripts" / "vendor"))
import qimen_core as qm  # noqa: E402


def test_dipan_and_ju():
    """地盤三奇六儀: 陽遁1局自坎1順布; 陰遁7局自兌7逆布; 節氣局數表。"""
    assert qm.dipan('陽', 1) == {1: '戊', 2: '己', 3: '庚', 4: '辛', 5: '壬', 6: '癸', 7: '丁', 8: '丙', 9: '乙'}
    assert qm.dipan('陰', 7) == {7: '戊', 6: '己', 5: '庚', 4: '辛', 3: '壬', 2: '癸', 1: '丁', 9: '丙', 8: '乙'}
    assert qm.ju_number('秋分', '上元') == 7 and qm.ju_number('立秋', '中元') == 5
    assert qm.ju_number('冬至', '上元') == 1 and qm.ju_number('夏至', '上元') == 9


def test_yuan_of_day():
    """三元: 由日干支符頭定 (己酉→上元、甲寅→中元)。"""
    assert qm.yuan_of_day('癸丑') == ('上元', '己酉')
    assert qm.yuan_of_day('甲寅') == ('中元', '甲寅')
    assert qm.yuan_of_day('乙卯') == ('中元', '甲寅')


def test_known_case_yifanzi_like():
    """定點真值 (對照獨立排盤): 2026-10-05 23:19 → 陰遁7局 上元, 值符天冲3宮, 值使傷門4宮。"""
    from datetime import datetime
    c = qm.QiMenChart(datetime(2026, 10, 5, 23, 19))
    d = c.to_dict()
    assert d['yin_yang'] == '陰' and d['ju'] == 7 and d['yuan'] == '上元'
    assert d['zhifu_star'] == '天冲' and d['zhifu_gong'] == 3
    assert d['zhishi_gate'] == '傷' and d['zhishi_gong'] == 4
    assert d['hour_gan_gong'] == 3
    # 八神: 值符在3宮、九天在4宮、九地在9宮 (對照基準)
    assert d['gong'][3]['god'] == '值符'
    assert d['gong'][4]['god'] == '九天'
    assert d['gong'][9]['god'] == '九地'


def test_invariants():
    """不變式: 九宮各一儀/星; 八宮各一門/神; 中宮無門無神。"""
    from datetime import datetime
    for dt in (datetime(2026, 10, 7, 10, 30), datetime(1990, 8, 18, 6, 30),
               datetime(2024, 2, 4, 16, 30), datetime(2000, 6, 21, 12, 0)):
        d = qm.QiMenChart(dt).to_dict()
        assert len({d['gong'][g]['dipan_gan'] for g in range(1, 10)}) == 9
        assert len({d['gong'][g]['tianpan_gan'] for g in range(1, 10)}) == 9
        assert len({d['gong'][g]['star'] for g in range(1, 10)}) == 9
        assert sorted(d['gong'][g]['gate'] for g in qm.RING8) == sorted(qm.GATE_FIXED.values())
        assert sorted(d['gong'][g]['god'] for g in qm.RING8) == sorted(qm.GOD_ORDER)
        assert d['gong'][5]['gate'] == '（中宮無門）'


def test_lifetime_minggong():
    """終身盤: 命宮=年干落宮、大限一宮9年、六親宮齊備。"""
    from datetime import datetime
    c = qm.QiMenChart(datetime(1990, 8, 18, 6, 30), lifetime=True)
    d = c.to_dict()
    assert d['ming_gong'] in range(1, 10)
    assert len(d['daxian']) == 8
    assert d['daxian'][0]['age'] == '0-8歲'
    assert d['daxian'][1]['age'] == '9-17歲'
    # 六親宮 (雙胞胎用: 兄弟宮 vs 本人宮)
    assert set(d['qin_gong']) == {'父', '母', '兄弟', '本人', '子女'}
    assert all(1 <= v <= 9 for v in d['qin_gong'].values())


def test_geju_full():
    """格局: 十干克應表齊、格局可判定 (含伏吟/反吟/門迫/擊刑/五不遇/天網/入墓)。"""
    from datetime import datetime
    assert len(qm.KE_YING) >= 70   # 9×9 去同干
    seen = set()
    for dt in (datetime(1990, 8, 18, 6, 30), datetime(2026, 10, 7, 10, 30),
               datetime(2026, 10, 5, 23, 19), datetime(2000, 6, 21, 12, 0)):
        seen |= set(qm.QiMenChart(dt).to_dict()['geju'])
    # 至少出現這些類型之一以上
    assert any('伏吟' in x for x in seen)
    assert any('門迫' in x for x in seen)
    assert any('擊刑' in x for x in seen)
    assert any(x in ('大格', '小格', '刑格', '五不遇時', '天網四張') or '[' in x for x in seen)


def test_cli_schema():
    r = subprocess.run([PY, str(YJ / "qimen.py"), "--time", "2026-10-07 10:30", "--json"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    d = json.loads(r.stdout.split('===== JSON =====')[-1])
    assert {'sizhu', 'yin_yang', 'ju', 'zhifu_star', 'zhishi_gate', 'gong', 'geju'} <= set(d)
    assert len(d['gong']) == 9


def test_event_cast_four_plates():
    """四式合盤: 六爻+梅花+六壬+奇門 同刻，四盤日柱一致 (2026-10 起: 預設=六爻+梅花, --with 追加)。"""
    r = subprocess.run([PY, str(YJ / "event_cast.py"), "--time", "2026-10-07 10:30",
                        "--coins", "1", "2", "3", "1", "0", "2", "--numbers", "17", "23",
                        "--with", "liuren", "qimen", "--format", "json"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    d = json.loads(r.stdout.split('===== JSON =====')[-1])
    assert {'liuyao', 'meihua', 'liuren', 'qimen', 'cross'} <= set(d)
    assert d['cross']['day_pillar_match'] is True


def test_event_cast_default_summary():
    """預設 summary: 只出六爻+梅花一行結論, 不含六壬/奇門全文 (省 token 契約)。"""
    r = subprocess.run([PY, str(YJ / "event_cast.py"), "--time", "2026-10-07 10:30",
                        "--coins", "1", "2", "3", "1", "0", "2", "--numbers", "17", "23"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "問事摘要" in r.stdout
    assert "六爻：" in r.stdout and "本卦" in r.stdout
    assert "六壬：" not in r.stdout and "奇門：" not in r.stdout


def test_event_cast_with_liuren_qimen():
    """--with liuren qimen: summary + 追加兩式全文。"""
    r = subprocess.run([PY, str(YJ / "event_cast.py"), "--time", "2026-10-07 10:30",
                        "--coins", "1", "2", "3", "1", "0", "2", "--numbers", "17", "23",
                        "--with", "liuren", "qimen"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "六壬：" in r.stdout and "奇門：" in r.stdout
    assert "【三傳】" in r.stdout and "【奇門遁甲】" in r.stdout


def test_zhifu_zhonggong_no_crash():
    """旬首落中五宮 (值符天禽5宮) 不得 KeyError: 值使寄坤二 (1998-01-05 15:52 回歸)。"""
    from datetime import datetime
    for dt in (datetime(1998, 1, 5, 15, 52), datetime(1998, 1, 5, 15, 0)):
        for lt in (False, True):
            d = qm.QiMenChart(dt, lifetime=lt).to_dict()
            assert d['zhifu_gong'] == 5 and d['zhifu_star'] == '天禽'
            assert d['zhishi_gate'] == '死'  # 中宮寄坤二之固定門
            assert len(d['gong']) == 9
