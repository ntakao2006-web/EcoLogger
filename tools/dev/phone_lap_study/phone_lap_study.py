"""スマホ（測位1Hz）の周のタイムが、どれだけ正しいかを測る（SP-7-7、2026-11-15）。結果は docs/research/phone_lap_accuracy_20261115.md。

    1. noise：スマホの記録（サーバーが受けた行から tools/dev/race_replay/race_csv.py fixes で作るCSV）で、
       位置の誤差の性質を測る。1秒ごとの「位置の進み（2点の間の距離）」と「速度（ドップラー）×時間」の差を積み上げ、
       K秒離れた2点で誤差がどれだけ変わるか（D(K)）と、位置が速度より何秒遅れているかを出す。
    2. sim：10Hzの記録（Ver.2 のSDの解）を正解にして、1Hzのスマホの記録を作り（拍の位置はでたらめ）、
       1で測った誤差を足して、線を越えた時刻の出し方3つ（いまの2点・前後数秒の点に直線を当てる・速度の積分に合わせる）を比べる。

    python -I tools/dev/phone_lap_study/phone_lap_study.py noise <fixes.csv> [...]
    python -I tools/dev/phone_lap_study/phone_lap_study.py sim <10Hzのcsv> <線のjson> [--runs 200] [--slow 1.5] [--tau 60] [--white 0.15]

10Hzのcsv は drive_logs/20261025/majesta_race/majesta_20261025_本番.csv の形（列 gnss_itow_ms・Lat・Lon・GPSSpeed）。
線のjson は drive_logs/lap_backup_20261025/lap_restore_motegi.json の形（本体の lap.json）。
出すのは数だけで、位置は出さない（drive_logs/ の外へ位置を持ち出さない）。
"""
import argparse
import csv
import json
import math
import random
import statistics as st

M_PER_DEG = 111320.0


# ---- 1. スマホの誤差 ---------------------------------------------------------------

def load_fixes(path):
    out = []
    for r in csv.DictReader(open(path, encoding='utf-8')):
        out.append((int(r['utc_ms']) / 1000.0, float(r['lat']), float(r['lon']),
                    float(r['acc_m']) if r['acc_m'] else None, float(r['speed_kmh']) / 3.6))
    return out


def moving_runs(fixes, min_kmh=10.0, min_len=12):
    """1秒おきに続き、10km/h以上で動いている区間ごとに、各1秒の (位置の進み, 速度×時間) を返す"""
    k = M_PER_DEG * math.cos(math.radians(fixes[0][1]))
    runs, run = [], []
    for a, b in zip(fixes, fixes[1:]):
        dt = b[0] - a[0]
        if 0.9 <= dt <= 1.1 and a[4] * 3.6 > min_kmh and b[4] * 3.6 > min_kmh:
            chord = math.hypot((b[2] - a[2]) * k, (b[1] - a[1]) * M_PER_DEG)
            run.append((chord, (a[4] + b[4]) / 2 * dt, a[4], b[4]))
        else:
            if len(run) >= min_len:
                runs.append(run)
            run = []
    if len(run) >= min_len:
        runs.append(run)
    return runs


def noise(paths):
    for p in paths:
        runs = moving_runs(load_fixes(p))
        n = sum(len(r) for r in runs)
        print(f'{p}: 動いている1秒の数 {n}（区間 {len(runs)}）')
        if not n:
            continue
        # 位置の遅れ：位置の進みと、ずらした速度を比べ、いちばん合うずらし
        for lag in (-1, 0, 1, 2):
            res = []
            for r in runs:
                for i in range(2, len(r) - 2):
                    j = i - lag
                    if 0 <= j < len(r):
                        res.append(r[i][0] - (r[j][2] + r[j][3]) / 2)
            print(f'  速度を {lag:+d}秒ずらすと 位置の進みとの差 rms {math.sqrt(st.mean(x * x for x in res)):.3f} m')
        for K in (1, 2, 5, 10, 30, 60, 120, 300):
            vals = []
            for r in runs:
                c = [0.0]
                for chord, dop, _, _ in r:
                    c.append(c[-1] + chord - dop)
                vals += [c[i + K] - c[i] for i in range(len(c) - K)]
            if len(vals) >= 20:
                print(f'  D({K:3d}秒)：ばらつき {st.pstdev(vals):.2f} m（数 {len(vals)}、平均のずれ {st.mean(vals):+.2f} m は曲がりと速度の倍率で、周のタイムには効かない）')


# ---- 2. 数え方の比べ ---------------------------------------------------------------

def load_truth(path):
    pts, last = [], None
    for r in csv.DictReader(open(path, encoding='utf-8')):
        it = r['gnss_itow_ms']
        if it != last and r['Lat']:
            pts.append((int(it) / 1000.0, float(r['Lat']), float(r['Lon']), float(r['GPSSpeed']) / 3.6))
            last = it
    return pts


def load_lines(path):
    j = json.load(open(path, encoding='utf-8'))
    out = {'control': (j['lat'], j['lon'], j['bearing'], j.get('width_m', 30.0))}
    for name in ('start', 'goal'):
        if j.get(name):
            g = j[name]
            out[name] = (g['lat'], g['lon'], g['bearing'], g.get('width_m', 30.0))
    return out


class Plane:
    def __init__(self, lat0, lon0):
        self.lat0, self.lon0, self.k = lat0, lon0, M_PER_DEG * math.cos(math.radians(lat0))

    def xy(self, lat, lon):
        return (lon - self.lon0) * self.k, (lat - self.lat0) * M_PER_DEG


def side(plane, g, x, y):
    """線からの (進む向きの距離, 横の距離)"""
    gx, gy = plane.xy(g[0], g[1])
    b = math.radians(g[2])
    px, py = x - gx, y - gy
    return px * math.sin(b) + py * math.cos(b), abs(px * math.cos(b) - py * math.sin(b))


def crossings(plane, track, g, method):
    """track = [(t, x, y, 速度m/s)]。線を前へ越えた時刻の一覧"""
    d = [side(plane, g, x, y) for _, x, y, _ in track]
    out = []
    for i in range(1, len(track)):
        if not (d[i - 1][0] < 0 <= d[i][0] and d[i][1] < g[3] / 2 + 5):
            continue
        t0, t1 = track[i - 1][0], track[i][0]
        if method == 'two':      # いまの数え方（本体の lap.py・スマホの LapTimer.kt と同じ）
            out.append(t0 + (t1 - t0) * (-d[i - 1][0] / (d[i][0] - d[i - 1][0])))
            continue
        js = list(range(max(0, i - 3), min(len(track), i + 3)))
        if method == 'fit':      # 前後3点ずつに直線を当てる
            ts = [track[j][0] - t0 for j in js]
            ds = [d[j][0] for j in js]
            mt, md = st.mean(ts), st.mean(ds)
            slope = sum((a - mt) * (c - md) for a, c in zip(ts, ds)) / sum((a - mt) ** 2 for a in ts)
            out.append(t0 + mt - md / slope)
            continue
        # 'doppler'：速度を積分した道のりの形に、前後3点ずつの位置で高さだけ合わせる
        S = [0.0]
        for a, b in zip(js, js[1:]):
            S.append(S[-1] + (track[a][3] + track[b][3]) / 2 * (track[b][0] - track[a][0]))
        step = math.hypot(track[i][1] - track[i - 1][1], track[i][2] - track[i - 1][2])
        cos_in = (d[i][0] - d[i - 1][0]) / max(1e-6, step)
        c = st.mean(d[j][0] - cos_in * S[n] for n, j in enumerate(js))
        at = float('nan')
        for n in range(len(js) - 1):
            a0, a1 = c + cos_in * S[n], c + cos_in * S[n + 1]
            if a0 < 0 <= a1:
                ta, tb = track[js[n]][0], track[js[n + 1]][0]
                at = ta + (tb - ta) * (-a0 / (a1 - a0))
                break
        out.append(at)
    return out


def phone_track(truth, seed, slow, tau, white, speed_noise):
    """正解の線を1Hzで拾い、ゆっくり動く誤差（ばらつき slow m、時定数 tau 秒）と1秒ごとの揺れ（white m）を足す"""
    rnd = random.Random(seed)
    a = math.exp(-1 / tau)
    q = slow * math.sqrt(1 - a * a)
    e_along, e_cross = rnd.gauss(0, slow), rnd.gauss(0, slow)
    t, j, out = truth[0][0] + rnd.random(), 0, []
    while t < truth[-1][0]:
        while truth[j + 1][0] < t:
            j += 1
        p, n = truth[j], truth[j + 1]
        f = (t - p[0]) / (n[0] - p[0])
        x, y, v = (p[1] + (n[1] - p[1]) * f, p[2] + (n[2] - p[2]) * f, p[3] + (n[3] - p[3]) * f)
        h = math.hypot(n[1] - p[1], n[2] - p[2]) or 1.0
        ux, uy = (n[1] - p[1]) / h, (n[2] - p[2]) / h
        e_along, e_cross = a * e_along + rnd.gauss(0, q), a * e_cross + rnd.gauss(0, q)
        ea, ec = e_along + rnd.gauss(0, white), e_cross + rnd.gauss(0, white)
        out.append((t, x + ux * ea - uy * ec, y + uy * ea + ux * ec, max(0.0, v + rnd.gauss(0, speed_noise))))
        t += 1.0
    return out


def rms(xs):
    xs = [x for x in xs if x == x]
    return math.sqrt(st.mean(x * x for x in xs)), max(abs(x) for x in xs)


def sim(truth_csv, lines_json, runs, slow, tau, white):
    pts = load_truth(truth_csv)
    lines = load_lines(lines_json)
    plane = Plane(pts[0][1], pts[0][2])
    truth = [(t, *plane.xy(la, lo), v) for t, la, lo, v in pts]
    ref = {n: crossings(plane, truth, g, 'two') for n, g in lines.items()}
    speeds = []
    for t_c in ref['control']:
        i = min(range(len(truth)), key=lambda k: abs(truth[k][0] - t_c))
        speeds.append(truth[i][3] * 3.6)
    print(f'正解（10Hz）：{len(pts)}点、線を越えた回数 ' + '・'.join(f'{n} {len(v)}' for n, v in ref.items())
          + f'、コントロールラインを越えた速さ {min(speeds):.0f}〜{max(speeds):.0f} km/h')
    cases = [('雑音なし（1Hzに間引いただけ）', (1e-3, tau, 0.0, 0.0)),
             (f'1秒ごとの揺れだけ（{white} m）', (1e-3, tau, white, 0.1)),
             (f'測った誤差（ゆっくり {slow} m・時定数 {tau:.0f}秒 ＋ 揺れ {white} m）', (slow, tau, white, 0.1))]
    names = {'two': 'いまの2点', 'fit': '前後3点に直線', 'doppler': '速度の積分に合わせる'}
    for label, par in cases:
        cross = {m: [] for m in names}
        lap = {m: [] for m in names}
        for seed in range(runs):
            tr = phone_track(truth, seed, *par)
            for m in names:
                for n, g in lines.items():
                    c = crossings(plane, tr, g, m)
                    if len(c) == len(ref[n]):
                        cross[m] += [a - b for a, b in zip(c, ref[n])]
                c, r = crossings(plane, tr, lines['control'], m), ref['control']
                if len(c) == len(r):
                    lap[m] += [(c[i + 1] - c[i]) - (r[i + 1] - r[i]) for i in range(len(r) - 1)]
        print(label)
        for m, name in names.items():
            (cr, cm), (lr, lm) = rms(cross[m]), rms(lap[m])
            print(f'  {name:12s} 線を越えた時刻 rms {cr:.3f}秒（最大 {cm:.2f}）／周のタイム rms {lr:.3f}秒（最大 {lm:.2f}）')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='mode', required=True)
    a = sub.add_parser('noise')
    a.add_argument('fixes', nargs='+')
    b = sub.add_parser('sim')
    b.add_argument('truth_csv')
    b.add_argument('lines_json')
    b.add_argument('--runs', type=int, default=200)
    b.add_argument('--slow', type=float, default=1.5)
    b.add_argument('--tau', type=float, default=60.0)
    b.add_argument('--white', type=float, default=0.15)
    args = ap.parse_args()
    if args.mode == 'noise':
        noise(args.fixes)
    else:
        sim(args.truth_csv, args.lines_json, args.runs, args.slow, args.tau, args.white)


if __name__ == '__main__':
    main()
