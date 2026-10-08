#!/usr/bin/env python3
"""問人總盤入口 (zongpan)：分層子命令。

Layer 0 必讀摘要：
  zongpan.py summary --date 1998-01-05 --time 15:57 --city 台南 --gender male
Layer 1 按需細節：
  zongpan.py bazi  ... [--year 2029]                 # 原局＋大運；加年給流年＋12流月
  zongpan.py ziwei ... [--palaces 財帛,田宅,官祿,福德] [--patterns]
  zongpan.py yun year 2029 ... [--full]              # 單年塊（八字段＋紫微運限）
  zongpan.py yun decade --from 2026 --to 2031 ...    # 多年運總表（一年一行）
  zongpan.py aux liuren ... [--at-year 2029]         # 六壬終身課
  zongpan.py aux qimen ...                           # 奇門終身盤
本機快取（僅留存本機，LLM 需先向使用者說明）：
  zongpan.py summary ... --save 小王 --relation 朋友  # 存摘要＋基本資訊到 .cache/
  zongpan.py cache list                              # 列出已存
  zongpan.py cache show --name 小王                   # 讀回

輸出全為 txt/md；細節項目按需取，不必全跑。讀法見 references/ask-person/zongpan-spec.md。
"""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

DIR = Path(__file__).resolve().parent
PY = sys.executable
CACHE_DIR = Path.cwd() / '.cache'


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print(r.stderr.strip(), file=sys.stderr)
        sys.exit(r.returncode)
    return r.stdout


def cache_key(name: str) -> str:
    return hashlib.sha1(name.encode('utf-8')).hexdigest()[:16]


def cache_save(name: str, relation: str, input_info: dict, summary: str):
    """存本機快取 (.cache/<key>.json)：僅留存本機，不上傳。"""
    CACHE_DIR.mkdir(exist_ok=True)
    path = CACHE_DIR / f"{cache_key(name)}.json"
    data = {"name": name, "relation": relation, "input": input_info,
            "summary": summary, "saved_at": datetime.now().strftime('%Y-%m-%d %H:%M')}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    return path


def cache_load(name: str):
    path = CACHE_DIR / f"{cache_key(name)}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding='utf-8'))


def common(p):
    p.add_argument('--date', required=True)
    p.add_argument('--time', default='12:00')
    p.add_argument('--city', default='')
    p.add_argument('--lon', type=float, default=None)
    p.add_argument('--gender', required=True, choices=['male', 'female'])
    p.add_argument('--calendar', default='solar', choices=['solar', 'lunar'])
    p.add_argument('--leap', action='store_true')
    return p


def loc_args(a):
    out = []
    if a.city:
        out += ['--city', a.city]
    if a.lon is not None:
        out += ['--lon', str(a.lon)]
    if a.calendar != 'solar':
        out += ['--calendar', a.calendar]
    if a.leap:
        out += ['--leap']
    return out


def main():
    ap = argparse.ArgumentParser(description='問人總盤入口 (summary 必讀 + 子命令按需)')
    sub = ap.add_subparsers(dest='cmd', required=True)

    p_sum = sub.add_parser('summary', help='Layer 0 必讀摘要 (md)')
    common(p_sum)
    p_sum.add_argument('--year', type=int, default=None)
    p_sum.add_argument('--at', default=None)
    p_sum.add_argument('--save', default=None, metavar='NAME', help='存本機快取 (使用者姓名/代稱)')
    p_sum.add_argument('--relation', default='', help='與問事者關係 (本人/朋友/家人...)')

    p_cache = sub.add_parser('cache', help='本機快取：list 列出 / show 讀回')
    csub = p_cache.add_subparsers(dest='cache_cmd', required=True)
    csub.add_parser('list', help='列出已存快取')
    p_cshow = csub.add_parser('show', help='讀回指定快取')
    p_cshow.add_argument('--name', required=True)

    p_bz = sub.add_parser('bazi', help='八字原局＋大運；--year 加流年＋12流月')
    common(p_bz)
    p_bz.add_argument('--year', type=int, default=None)

    p_zw = sub.add_parser('ziwei', help='紫微十二宮；--palaces 過濾；--patterns 格局')
    common(p_zw)
    p_zw.add_argument('--palaces', default=None, help='逗號分隔宮名, 如 財帛,田宅,官祿,福德')
    p_zw.add_argument('--patterns', action='store_true', help='只出格局段')
    p_zw.add_argument('--at', default=None, help='運限日期 YYYY-MM-DD')
    p_zw.add_argument('--year', type=int, default=None)

    p_yun = sub.add_parser('yun', help='運限：year 單年 / decade 多年')
    ysub = p_yun.add_subparsers(dest='yun_cmd', required=True)
    p_yy = ysub.add_parser('year', help='單年塊')
    common(p_yy)
    p_yy.add_argument('year', type=int, nargs='?', default=None, help='目標年 (預設今年)')
    p_yy.add_argument('--full', action='store_true', help='加流月')
    p_yd = ysub.add_parser('decade', help='多年運總表')
    common(p_yd)
    p_yd.add_argument('--from', dest='yfrom', type=int, required=True)
    p_yd.add_argument('--to', dest='yto', type=int, required=True)

    p_aux = sub.add_parser('aux', help='輔助盤：liuren 終身課 / qimen 終身盤')
    asub = p_aux.add_subparsers(dest='aux_cmd', required=True)
    p_lr = asub.add_parser('liuren', help='六壬終身課')
    common(p_lr)
    p_lr.add_argument('--at-year', type=int, default=None)
    p_qm = asub.add_parser('qimen', help='奇門終身盤')
    common(p_qm)

    a = ap.parse_args()

    if a.cmd == 'summary':
        cmd = [PY, str(DIR / 'person_cast.py'), '--date', a.date, '--time', a.time,
               '--gender', a.gender, *loc_args(a), '--format', 'md']
        if a.year:
            cmd += ['--year', str(a.year)]
        if a.at:
            cmd += ['--at', a.at]
        text = run(cmd)
        print(text, end='')
        if a.save:
            input_info = {'date': a.date, 'time': a.time, 'city': a.city or '',
                          'gender': a.gender, 'calendar': a.calendar, 'leap': a.leap}
            path = cache_save(a.save, a.relation, input_info, text)
            print(f"\n（已存本機快取：{a.save}／{a.relation or '未填關係'}；僅留存本機）", file=sys.stderr)

    elif a.cmd == 'cache':
        if a.cache_cmd == 'list':
            if not CACHE_DIR.exists():
                print('（快取空）')
            else:
                for f in sorted(CACHE_DIR.glob('*.json')):
                    try:
                        d = json.loads(f.read_text(encoding='utf-8'))
                        print(f"{d.get('name', '?')}\t{d.get('relation', '')}\t{d.get('input', {}).get('date', '')}\t{d.get('saved_at', '')}")
                    except (json.JSONDecodeError, OSError):
                        continue
        else:  # show
            d = cache_load(a.name)
            if not d:
                print(f'（查無快取：{a.name}）', file=sys.stderr)
                sys.exit(1)
            print(d['summary'])

    elif a.cmd == 'bazi':
        cmd = [PY, str(DIR / 'bazi_pai.py'), '--date', a.date, '--time', a.time,
               '--gender', a.gender, *loc_args(a), '--format', 'text']
        if a.year:
            cmd += ['--year', str(a.year)]
        print(run(cmd), end='')

    elif a.cmd == 'ziwei':
        cmd = [str(DIR / 'ziwei_full.sh'), '--date', a.date, '--time', a.time,
               '--gender', a.gender, *loc_args(a), '--format', 'text']
        if a.at:
            cmd += ['--at', a.at]
        elif a.year:
            cmd += ['--liunian', str(a.year)]
        text = run(cmd)
        if a.patterns:
            # 只出格局段
            grab = False
            for line in text.splitlines():
                if line.startswith('【格局】'):
                    grab = True
                elif line.startswith('【') and grab:
                    break
                if grab:
                    print(line)
        elif a.palaces:
            want = {p.strip() for p in a.palaces.split(',')}
            for line in text.splitlines():
                if any(line.startswith(w + '(') for w in want):
                    print(line)
        else:
            print(text, end='')

    elif a.cmd == 'yun':
        if a.yun_cmd == 'decade':
            cmd = [PY, str(DIR / 'decade.py'), '--date', a.date, '--time', a.time,
                   '--gender', a.gender, *loc_args(a),
                   '--from', str(a.yfrom), '--to', str(a.yto), '--format', 'text']
            print(run(cmd), end='')
        else:  # year
            y = a.year or __import__('datetime').datetime.now().year
            # 八字側：該年干支＋12流月（--full 才展開流月）
            bz = run([PY, str(DIR / 'bazi_pai.py'), '--date', a.date, '--time', a.time,
                      '--gender', a.gender, *loc_args(a), '--year', str(y), '--format', 'text'])
            print(f"## {y} 年")
            for ln in bz.splitlines():
                if ln.startswith('流年'):
                    if a.full:
                        print(f"- 八字歲運：{ln}")
                    else:
                        head = ln.split('):')[0] + ')'
                        print(f"- 八字歲運：{head}")
            # 紫微側：該年運限（取年中）；--full 才含小限以下與流耀
            zw = run([str(DIR / 'ziwei_full.sh'), '--date', a.date, '--time', a.time,
                      '--gender', a.gender, *loc_args(a), '--at', f'{y}-06-01', '--format', 'text'])
            grab = False
            for line in zw.splitlines():
                if line.startswith('【運限】'):
                    grab = True
                    print(f"- 紫微運限：{line.strip()}")
                    continue
                elif line.startswith('【') and grab:
                    break
                if not grab or not line.strip():
                    continue
                if '流耀' in line and not a.full:
                    continue
                if line.strip().startswith(('小限', '流月', '流日', '流時', '流年將前')) and not a.full:
                    continue
                print(f"- 紫微運限：{line.strip()}")

    elif a.cmd == 'aux':
        if a.aux_cmd == 'liuren':
            cmd = [PY, str(DIR / 'yijing' / 'liuren.py'), '--time',
                   f"{a.date} {a.time}", '--lifetime', '--gender', '男' if a.gender == 'male' else '女',
                   '--text']
            if a.at_year:
                cmd += ['--at-year', str(a.at_year)]
            print(run(cmd), end='')
        else:  # qimen
            cmd = [PY, str(DIR / 'yijing' / 'qimen.py'), '--time',
                   f"{a.date} {a.time}", '--lifetime', '--gender',
                   '男' if a.gender == 'male' else '女', '--text']
            if a.city:
                cmd += ['--city', a.city]
            elif a.lon is not None:
                cmd += ['--lon', str(a.lon)]
            print(run(cmd), end='')


if __name__ == '__main__':
    main()