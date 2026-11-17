"""Health checks of the NCEC's parts from the CAN1 frames the logger already keeps (2026-11-17).

Reads what the car broadcasts (no OBD needed) and, when the file has them, the ECU's OBD answers (0x7E8).
The decodings are in docs/design/ncec_can_spec.md; the judgments on the car (WSM limits, what is new or old)
are in the ncec-roadster repository (maintenance/reliability-plan.md 2-3, 3-3b, 3-3c, 3-3d). Nothing here prints
positions, so the output can be pasted into the repositories; the inputs (drive_logs/) stay out of git.

    python tools/vehicle_health/vehicle_health.py idle     <files...>   # warm stationary idle: rpm, load, throttle, A/C; MAF if OBD
    python tools/vehicle_health/vehicle_health.py timing   <files...>   # ignition timing at full throttle by rpm, and its dips
    python tools/vehicle_health/vehicle_health.py wheels   <files...>   # the 4 wheel speed sensors: dropouts, jumps, ratios
    python tools/vehicle_health/vehicle_health.py throttle <files...>   # electronic throttle: steadiness, response, map at 2000-3500 rpm

Inputs: the logger's `<CSV>.can.jsonl` (rows `[ms, channel, id, ext, rtr, "hex"]`), sd_decode.py's `.can.jsonl`
(one object per frame) or the capture CSV of the 2026-09 survey (`host_iso,t_us,can_id,ext,rtr,dlc,data_hex`).
A folder is searched for `*.can.jsonl`. Only CAN1 (the car) is read.
"""
import argparse, bisect, collections, csv, json, statistics as st
from pathlib import Path

# MAF / (rpm/1000) / calculated load %, at warm idle with A/C off, from the 2026-09-06 survey (172 points,
# 0.124-0.133 for 10-90 %). Used to estimate the MAF reading when only the broadcast load is recorded.
MAF_PER_LOAD_RPM = 0.128


def frames(path):
    """(t_s, id, data) of CAN1 frames."""
    path = str(path)
    if path.endswith('.csv'):
        with open(path, newline='') as f:
            for r in csv.DictReader(f):
                yield int(r['t_us']) / 1e6, int(r['can_id'], 16), bytes.fromhex(r['data_hex'])
        return
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            if isinstance(r, dict):
                if r['channel'] == 1:
                    yield r['mcu_ms'] / 1000, r['id'], bytes.fromhex(r['data'])
            elif r[1] == 1:
                yield r[0] / 1000, r[2], bytes.fromhex(r[5])


class Car:
    """The latest broadcast values (ncec_can_spec.md)."""
    def __init__(self): self.v = {}
    def feed(self, i, b):
        v = self.v
        if i == 0x201: v['rpm'] = (b[0] << 8 | b[1]) / 4; v['speed'] = (b[4] << 8 | b[5]) / 100 - 100
        elif i == 0x200: v['pedal'] = b[7] * 0.2144 + 30.68; v['brake'] = b[6] & 1
        elif i == 0x215: v['ac'] = bool(b[7] & 0x40)
        elif i == 0x231: v['clutch'] = b[1]
        elif i == 0x240:
            v['load'] = b[0] * 100 / 255; v['coolant'] = b[1] - 40; v['timing'] = b[2] / 2 - 64
            v['throttle'] = b[3] * 0.3938 - 0.342; v['iat'] = b[4] - 40
        elif i == 0x4B0: v['wheels'] = [(b[k] << 8 | b[k + 1]) / 100 - 100 for k in (0, 2, 4, 6)]
        else: return False
        return True
    def ready(self, *keys): return all(k in self.v for k in keys)


def inputs(paths):
    out = []
    for p in map(Path, paths):
        out += sorted(p.rglob('*.can.jsonl')) if p.is_dir() else [p]
    return out


def med(xs): return st.median(xs) if xs else float('nan')


def idle(path, args):
    """Stationary idle stretches of 20 s or more, warm (coolant >= args.warm). MAF from OBD answers if present."""
    car = Car(); segs = []; cur = None; obd = collections.defaultdict(list)
    for t, i, b in frames(path):
        if i == 0x7E8 and len(b) >= 4 and b[1] == 0x41 and cur:
            if b[2] == 0x10: obd[car.v['ac']].append(((b[3] << 8 | b[4]) / 100, car.v['rpm'], car.v['load']))
            continue
        if not car.feed(i, b) or i != 0x201 or not car.ready('rpm', 'speed', 'pedal', 'ac', 'load'): continue
        v = car.v
        if v['speed'] == 0 and 400 < v['rpm'] < 1300 and v['pedal'] < 33:
            if cur is None: cur = {'t0': t, 'rows': []}
            cur['t1'] = t; cur['ac'] = v['ac']; cur['rows'].append(dict(v))
        elif cur: segs.append(cur); cur = None
    if cur: segs.append(cur)
    print(f'== {path}')
    for s in segs:
        if s['t1'] - s['t0'] < 20: continue
        rows = s['rows'][len(s['rows']) // 5:]          # the first 20 % settles after stopping
        warm = [r for r in rows if r.get('coolant', -99) >= args.warm and not r['ac']]
        ac = sum(r['ac'] for r in rows) / len(rows)
        line = (f"  t={s['t0']:7.0f}s {s['t1'] - s['t0']:5.0f}s rpm {med([r['rpm'] for r in rows]):5.0f} "
                f"coolant {med([r.get('coolant', float('nan')) for r in rows]):3.0f} iat {med([r.get('iat', float('nan')) for r in rows]):3.0f} "
                f"throttle {med([r.get('throttle', float('nan')) for r in rows]):4.1f}% load {med([r['load'] for r in rows]):4.1f}% A/C {ac:.0%}")
        if warm:
            est = MAF_PER_LOAD_RPM * med([r['rpm'] for r in warm]) / 1000 * med([r['load'] for r in warm])
            line += f"  MAF reading estimated from load {est:.2f} g/s (warm, A/C off)"
        print(line)
    for ac, xs in sorted(obd.items()):
        ratio = [m / (r / 1000) / l for m, r, l in xs if l > 0]
        print(f"  OBD MAF at idle, A/C {'on' if ac else 'off'}: n={len(xs)} median {med([x[0] for x in xs]):.2f} g/s at "
              f"{med([x[1] for x in xs]):.0f} rpm, load {med([x[2] for x in xs]):.1f}%; MAF/(rpm/1000)/load {med(ratio):.4f}")


def timing(path, args):
    """Timing at throttle >= 75 % (the running engine opens to 80 % at most) and >= 3000 rpm."""
    car = Car(); rows = []; ctx = collections.deque(maxlen=16)
    for t, i, b in frames(path):
        if not car.feed(i, b) or i != 0x240 or not car.ready('rpm'): continue
        v = car.v; ctx.append((t, v['rpm'], v.get('clutch'), v['throttle'], v['timing']))
        if v['throttle'] >= 75 and v['rpm'] >= 3000:
            rows.append((t, v['rpm'], v['timing'], v['load'], v['coolant'], v['iat'], v.get('clutch'), list(ctx)))
    print(f'== {path}  full-throttle samples {len(rows)}')
    if not rows: return
    bins = collections.defaultdict(list)
    for r in rows: bins[int(r[1] // 500 * 500)].append(r)
    print('   rpm     n  timing median  p5   min   load  coolant iat')
    for k in sorted(bins):
        a = sorted(x[2] for x in bins[k])
        print(f"  {k:5d} {len(a):5d} {med(a):8.1f} {a[len(a) // 20]:6.1f} {a[0]:5.1f} {med([x[3] for x in bins[k]]):6.1f} "
              f"{med([x[4] for x in bins[k]]):6.0f} {med([x[5] for x in bins[k]]):4.0f}")
    m = {k: med([x[2] for x in v]) for k, v in bins.items()}
    dips = [r for r in rows if r[2] <= m[int(r[1] // 500 * 500)] - args.dip]
    print(f"  {args.dip} deg or more under the median of its rpm: {len(dips)}"
          " (look at the clutch: a dip just as it re-engages after a shift, or a downshift blip, is not knock)")
    for r in dips[:args.show]:
        print(f"   t={r[0]:.1f}s {r[1]:.0f} rpm timing {r[2]}  before: " +
              ' '.join(f"{c[0] - r[0]:+.1f}s:{c[1]:.0f}rpm/cl{c[2]}/thr{c[3]:.0f}/{c[4]}" for c in r[7][-6:]))


def wheels(path, args):
    """FL FR RL RR. Dropout: one wheel under half of the others (> 20 km/h). Jump: one wheel moves > 5 km/h in one frame."""
    names = ['FL', 'FR', 'RL', 'RR']; car = Car(); last = None; lt = None
    ratios = collections.defaultdict(list); drops = []; jumps = collections.Counter(); jump_list = []; gaps = 0; n = 0
    for t, i, b in frames(path):
        if not car.feed(i, b) or i != 0x4B0: continue
        w = car.v['wheels']; n += 1; brake = car.v.get('brake', 0)
        if lt is not None and t - lt > 0.5: gaps += 1
        m = st.median(w)
        if m > 20:
            for k in range(4):
                if w[k] < 0.5 * min(w[j] for j in range(4) if j != k): drops.append((t, names[k], w[k], m, brake))
            if last and t - lt < 0.03:
                turn = 'left' if w[1] - w[0] > 0.5 else 'right' if w[0] - w[1] > 0.5 else 'straight'
                for k in range(4):
                    if abs(w[k] - last[k]) > 5 and max(abs(w[j] - last[j]) for j in range(4) if j != k) < 1:
                        inside = (k in (0, 2) and turn == 'left') or (k in (1, 3) and turn == 'right')
                        jumps[(names[k], turn, 'inside' if inside else 'outside/straight', 'brake' if brake else 'no brake')] += 1
                        jump_list.append((t, names[k], turn, round(w[k] - last[k], 1), round(m)))
            if (m > 40 and not brake and abs(w[0] - w[1]) < 0.01 * m and abs(w[2] - w[3]) < 0.01 * m
                    and last and abs(m - st.median(last)) < 0.05):
                mean = sum(w) / 4
                for k in range(4): ratios[names[k]].append(w[k] / mean)
        last = w; lt = t
    print(f'== {path}  frames {n}, gaps > 0.5 s {gaps}')
    print('  straight steady cruise, ratio to the mean of 4:', {k: round(med(v), 4) for k, v in ratios.items() if v},
          f"(n={len(ratios['FL'])})")
    print(f'  dropouts {len(drops)}', [(round(d[0], 2), d[1], round(d[2], 1), round(d[3], 1), 'brake' if d[4] else 'no brake') for d in drops[:6]])
    print(f'  single-wheel jumps {sum(jumps.values())}: {dict(jumps)}')
    for j in jump_list[:args.show]: print('   ', j)


def throttle(path, args):
    """Throttle (10 Hz) against pedal (100 Hz)."""
    ped = []; thr = []; car = Car()
    for t, i, b in frames(path):
        if not car.feed(i, b): continue
        if i == 0x200: ped.append((t, car.v['pedal']))
        elif i == 0x240 and car.ready('rpm'): thr.append((t, car.v['throttle'], car.v['rpm']))
    pt = [p[0] for p in ped]; tt = [x[0] for x in thr]
    win = lambda arr, keys, a, b: arr[bisect.bisect_left(keys, a):bisect.bisect_right(keys, b)]
    bins = collections.defaultdict(list); spread = []
    for t, th, r in thr:
        w = [p[1] for p in win(ped, pt, t - 1.5, t)]
        if len(w) < 100 or max(w) - min(w) >= 0.5: continue
        if 2000 <= r < 3500: bins[round(med(w) / 2) * 2].append(th)
        if min(w) >= 33:          # pedal held, not released
            tw = [x[1] for x in win(thr, tt, t - 1.0, t)]; spread.append(max(tw) - min(tw))
    steps = slow = 0; delays = []; lastev = -9
    for t, p in ped:
        if t - lastev < 1: continue
        a = bisect.bisect_left(pt, t - 0.2)
        if p - ped[a][1] < 10: continue
        t0 = ped[a][0]; lastev = t; i0 = bisect.bisect_left(tt, t0 - 0.15)
        if i0 >= len(thr) or thr[i0][1] > 60: continue
        steps += 1; base = thr[i0][1]
        d = next((x[0] - t0 for x in thr[i0:i0 + 20] if x[1] - base >= 5), None)
        if d is None or d > 1: slow += 1
        else: delays.append(d)
    print(f'== {path}')
    print('  map at 2000-3500 rpm, steady pedal %: throttle % (n):',
          ' '.join(f"{k}:{med(v):.1f}({len(v)})" for k, v in sorted(bins.items()) if len(v) >= 10))
    sp = sorted(spread)
    if sp: print(f'  throttle spread in 1 s with the pedal held still: n={len(sp)} median {med(sp):.2f} max {sp[-1]:.2f} pt, over 2 pt: {sum(x > 2 for x in sp)}')
    print(f'  pedal steps (+10 pt in 0.2 s): {steps}, throttle +5 pt within 1 s: {len(delays)} (median {med(delays):.2f} s), slower or none: {slow}')
    # With the engine stopped (IG ON) the valve opens to about 90 %; running, it stops at about 80 %.
    full = [x[1] for x in thr if x[1] >= 75 and x[2] > 500]
    if full: print(f'  full throttle samples with the engine running {len(full)}, highest {max(full):.1f}%')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('check', choices=['idle', 'timing', 'wheels', 'throttle'])
    ap.add_argument('files', nargs='+')
    ap.add_argument('--warm', type=float, default=84, help='idle: coolant (deg C) counted as warm, default 84')
    ap.add_argument('--dip', type=float, default=4, help='timing: degrees under the rpm median counted as a dip, default 4')
    ap.add_argument('--show', type=int, default=10, help='how many dips/jumps to list')
    args = ap.parse_args()
    for f in inputs(args.files): globals()[args.check](f, args)


if __name__ == '__main__':
    main()
