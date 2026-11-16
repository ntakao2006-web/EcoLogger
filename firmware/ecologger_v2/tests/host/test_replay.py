"""再生の試験台（SP-7-9、2026-11-17）：STM32のファームに走行の記録を流し込み、SDに残った記録とLinuxが受け取った値を照らす。

    python firmware/ecologger_v2/tests/host/test_replay.py [--sd-dir DIR] [--first 100] [--files 4] [--seconds 0] [--no-stall] [--no-rpc]
        [--firmware DIR] [--keep DIR]

Windows の Python から動かす（試験台の組み立てと実行だけ WSL の g++）。WSL・Linux の中から動かしてもよい（そのときは msgpack が無ければ
TCP の段を飛ばす）。入力は SUGO 11/8 の SD（既定は drive_logs/20261111/run02_2049/v2_sd の EL000100 から4本、約170秒、140km/h前後）。
drive_logs はリポジトリに入れないので、このリポジトリかその上のフォルダーにある drive_logs を探す。位置を含む入力・SDの像は一時フォルダーに
作って最後に消す（--keep で残す）。

3つの段：
1. ふつうの再生：元の時刻どおりに IMU・受信機（NAV-PVT と作り物の NAV-SAT・NAV-SLAS）・CAN1・CAN2 を出し、SDの像を pyfatfs で読み、
   sd_decode.records() で全部のブロック（CRC・連番）を読み、入力と同じ数・同じ中身か、時刻の並びを照らす。Linux側（server.py と同じ間隔の
   logger.status・logger.take）が受け取った行も SD と照らし、hardware.HardwareDecoder で読めるかを見る。
2. SDの書き込みが止まる（--stall）：途中の10秒、1ブロックの書き込みごとに0.9秒待たせる。待ち行列があふれて捨てた数（sd_queue_dropped）と、
   SDから欠けた記録の数が一致し、残った記録は入力の並びのまま、取得（CAN・Linuxへの行）は止まらないかを見る。
3. TCP の RPC：試験台が logger.status・logger.take などを 127.0.0.1 の TCP で出し、EcoCapture-Web の telemetry_bridge.TelemetryBridge
   （本体ではUNIXソケット）で実時間に受け取る。最後に記録を止めて FILES0 と logger.sdread でSDのブロックを1つ読む。
"""
import argparse
import asyncio
import io
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import zlib
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
FW = HERE.parents[1]
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'EcoCapture-Web'))
sys.path.insert(0, str(REPO / 'EcoCapture-Web' / 'vendor'))
from sd_decode import records, gnss_aux  # noqa: E402

T0_US = 3_000_000           # the replay starts 3 s after the MCU boots (setup takes about 0.7 s)
OTHER_FILES = 30            # the card's root directory (32 entries a cluster) starts with the label and 30 other files:
                            # EL000001 takes the last entry and EL000002 makes the directory grow (fixed 2026-11-11)
DEFAULT_SD = Path('drive_logs/20261111/run02_2049/v2_sd')
IN_WSL = sys.platform.startswith('linux')


def find_sd_dir(given):
    if given:
        return Path(given)
    for root in [REPO, *REPO.parents]:
        if (root / DEFAULT_SD).is_dir():
            return root / DEFAULT_SD
    raise SystemExit(f'{DEFAULT_SD} が見つからない（--sd-dir で渡す）')


def ubx(cls, ident, payload):
    f = bytes([0xb5, 0x62, cls, ident]) + struct.pack('<H', len(payload)) + payload
    a = b = 0
    for v in f[2:]:
        a = (a + v) & 255
        b = (b + a) & 255
    return f + bytes([a, b])


def nav_sat(itow):
    """A made-up NAV-SAT (the SUGO card predates SP-7-8) and the record 5 the firmware should make of it."""
    n = 16 + (itow // 1000) % 25
    body = bytearray(struct.pack('<IBB2x', itow, 1, n))
    used = diff = sbas = slas = 0
    for k in range(n):
        u = k % 4 != 3
        flags = 4 | u << 3 | 1 << 4 | (u and k % 3 == 0) << 6 | (k % 2) << 7 | (u and k % 5 == 0) << 16 | (k % 6 == 1) << 17 | (u and (itow // 1000 + k) % 7 == 0) << 18
        body += struct.pack('<BBbbhhI', k % 7, k + 1, 30 + k, 20, 90 + k, 0, flags)
        used += u
        diff += u and k % 3 == 0
        sbas += u and k % 5 == 0
        slas += u and (itow // 1000 + k) % 7 == 0
    return ubx(1, 0x35, bytes(body)), struct.pack('<I5B', itow, n, used, diff, sbas, slas)


def nav_slas(itow):
    cnt = (itow // 1000) % 6
    head = struct.pack('<IB3xii4B', itow, 0, 139000, 36000, 3, 189, 3, cnt)
    body = head + b''.join(struct.pack('<BB2xhh', 0, 2 + k, 10 * k, -k) for k in range(cnt))
    return ubx(1, 0x42, body), head


def build_events(sd_dir, first, count, seconds):
    """The drive as events at virtual microseconds, and what the firmware should make of them."""
    recs = []
    for i in range(first, first + count):
        with open(sd_dir / f'EL{i:06d}.BIN', 'rb') as f:
            recs.extend(records(f))
    base = recs[0][1]
    if seconds:
        recs = [r for r in recs if r[1] - base < seconds * 1000]
    us = lambda ms: (ms - base) * 1000 + T0_US  # noqa: E731
    events, can = [], {1: [], 2: []}
    exp = SimpleNamespace(can=can, nav=[], sat=[], slas=[], imu_in=0, imu_samples=set(), imu_fail_in=0, base_ms=base, offset_ms=T0_US // 1000 - base)
    same_ms = {}
    for i, (kind, ms, data) in enumerate(recs):
        if kind == 3:
            same_ms.setdefault((data[0], ms), []).append(i)
    spread = {}
    for (ch, ms), idx in same_ms.items():  # a CAN frame takes ~0.25 ms on the wire: spread those stamped in the same ms
        for k, i in enumerate(idx):
            spread[i] = k * 1000 // len(idx)
    for i, (kind, ms, data) in enumerate(recs):
        t = us(ms)
        if kind == 1:
            events.append((t, i, 1, data)); exp.imu_in += 1; exp.imu_samples.add(data)
        elif kind == 4:
            events.append((t, i, 4, b'')); exp.imu_fail_in += 1
        elif kind == 2:
            itow = struct.unpack_from('<I', data)[0]
            exp.nav.append((t, data))
            events.append((t, i, 20, ubx(1, 7, data)))
            if itow % 1000 == 0:  # the receiver sends these only when the firmware asked for them (host_devices.h)
                sat, rec5 = nav_sat(itow)
                slas, rec6 = nav_slas(itow)
                events.append((t, i, 21, sat)); events.append((t, i, 22, slas))
                exp.sat.append((t, rec5)); exp.slas.append((t, rec6))
        elif kind == 3:
            ch, ident, flags, n = data[0], struct.unpack_from('<I', data, 1)[0], data[5], data[6]
            t += spread[i]
            events.append((t, i, 30 + ch, struct.pack('<IBB', ident, flags, n) + data[7:7 + n]))
            can[ch].append((t, ident, flags, data[7:7 + n], ms))
    events.sort()
    return events, exp, (recs[-1][1] - base) / 1000


def write_events(path, events):
    with open(path, 'wb') as f:
        f.write(b'ELRPLAY1')
        for t, _, kind, data in events:
            f.write(struct.pack('<BBHQ', kind, 0, len(data), t) + data)


def to_wsl(p):
    p = str(Path(p).resolve())
    if IN_WSL:
        return p
    return '/mnt/' + p[0].lower() + p[2:].replace('\\', '/')


def build(work, firmware=None):
    exe = Path(work) / 'replay'
    other = f"-DLOGGER_IMPL='\"{to_wsl(Path(firmware) / 'logger_impl.h')}\"' " if firmware else ''
    cmd = f'g++ -std=c++17 -O2 -Wall {other}-Itests/host/include -Itests/host -o {to_wsl(exe)} tests/host/replay.cpp'
    shell(cmd, cwd=FW)
    return exe


def shell(cmd, cwd, background=False):
    full = f'cd {to_wsl(cwd)} && {cmd}'
    argv = ['bash', '-c', full] if IN_WSL else ['wsl', '-e', 'bash', '-c', full]
    if background:
        return subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
    r = subprocess.run(argv, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        print(r.stdout, r.stderr)
        raise SystemExit(f'失敗（{r.returncode}）：{cmd}')
    return r.stdout + r.stderr


def run_replay(exe, events_path, out, extra='', background=False):
    out.mkdir(parents=True, exist_ok=True)
    return shell(f'{to_wsl(exe)} --events {to_wsl(events_path)} --out {to_wsl(out)} --other-files {OTHER_FILES} {extra}', cwd=FW, background=background)


def read_card(out):
    """Every EL file on the card image, read with pyfatfs (a standard FAT reader), in index order."""
    try:
        import pkg_resources  # noqa: F401  (the vendored fs package declares its namespace with it)
    except ImportError:  # Python without setuptools: the namespace declaration is not needed here
        sys.modules['pkg_resources'] = SimpleNamespace(declare_namespace=lambda name: None)
    from pyfatfs.PyFatFS import PyFatFS
    data = (out / 'card.img').read_bytes()
    part = struct.unpack_from('<I', data, 446 + 8)[0]
    reserved = struct.unpack_from('<H', data, part * 512 + 14)[0]
    root = struct.unpack_from('<I', data, part * 512 + 44)[0]
    fat = (part + reserved) * 512
    chain = [root]
    while (nxt := struct.unpack_from('<I', data, fat + chain[-1] * 4)[0] & 0x0fffffff) < 0x0ffffff8:
        chain.append(nxt)
        assert len(chain) <= 2, (f'目次（ルートディレクトリ）の区画の鎖が {chain[:3]}… と伸び続ける：目次が新しいファイルの区画とつながった'
                                 '（2026-11-11 に直した不具合の形）')
    part_image = out / 'card.part'
    part_image.write_bytes(data[part * 512:])
    fs = PyFatFS(str(part_image), read_only=True)
    try:
        listed = fs.listdir('/')
        names = sorted(n for n in listed if n.upper().startswith('EL'))
        others = sorted(n for n in listed if n.upper().startswith('OTHER'))
        assert others == [f'OTHER{i:03d}.TXT' for i in range(1, OTHER_FILES + 1)], others  # nothing overwrote them
        assert all(fs.getsize('/' + n) == 0 for n in others)
        files = [(n, fs.readbytes('/' + n)) for n in names]
    finally:
        fs.close()
        part_image.unlink()
    if len(names) >= 2:
        assert len(chain) == 2, f'目次の区画 {chain}'  # 32 entries: the label, 30 others and EL000001, then a new cluster
    return files


def sd_records(files):
    out = []
    for name, body in files:
        assert len(body) % 512 == 0 and body, (name, len(body))
        first = struct.unpack_from('<I', body, 4)[0]
        assert first == int(name[2:8]), (name, first)  # every block names its own file
        out.extend(records(io.BytesIO(body)))  # raises on a bad CRC, a missing or reordered block, a bad length
    return out


def served_imu(out):
    return list(records_raw((out / 'imu_served.bin').read_bytes()))


def records_raw(b):
    pos = 0
    while pos < len(b):
        kind, n, ms = struct.unpack_from('<BBI', b, pos)
        yield kind, ms, b[pos + 6:pos + 6 + n]
        pos += 6 + n


def is_subsequence(part, whole):
    it = iter(whole)
    return all(any(x == y for y in it) for x in part)


def linux_view(lines):
    """Status snapshots and take batches in the order the Linux side got them."""
    seq = []
    for line in lines:
        kind, ms, body = line.split(' ', 2)
        seq.append((kind, int(ms), body if kind in 'CQ' else json.loads(body)))
    return seq


def decode_all(view):
    """Runs hardware.HardwareDecoder (EcoCapture-Web) over what the Linux side got, like server.py does."""
    from hardware import HardwareDecoder
    decoder = HardwareDecoder()
    config = SimpleNamespace(signals=[])
    status, samples, sensors = None, [], None
    for kind, _, body in view:
        if kind == 'S':
            status = body
        elif kind == 'T' and status is not None:
            got, sensors = decoder.decode(status, body, config)
            samples.extend(got)
    return samples, sensors


def rows_from_sd(sd, with_nav=True):
    rows, can = [], []
    for kind, ms, data in sd:
        if kind in ((1, 2, 4) if with_nav else (1, 4)):
            rows.append((ms, data.hex()))
        elif kind == 3:
            ident = struct.unpack_from('<I', data, 1)[0]
            can.append((ms, data[0], ident, data[5] & 1, data[5] >> 1 & 1, data[7:7 + data[6]].hex()))
    return rows, can


def check_linux(view, sd, label, sd_complete=True):
    """What the Linux side got against the card. With sd_complete the card holds every record (Linux also gets
    the ones after LOG0); otherwise the card misses records and holds a part of Linux's, in the same order."""
    rows = [r for kind, _, b in view if kind == 'T' for r in b['rows']]
    can = [c for kind, _, b in view if kind == 'T' for c in b['can']]
    # Firmware before 2026-11-09 puts only the IMU in the rows and the latest NAV-PVT in the status ("nav").
    legacy = any('nav' in b for kind, _, b in view if kind == 'S')
    want_rows, want_can = rows_from_sd(sd, with_nav=not legacy)
    got_rows = [(r[1], r[2]) for r in rows]
    got_can = [(c[0], c[1], c[2], c[3], c[4], c[5]) for c in can]
    if sd_complete:
        assert got_rows[:len(want_rows)] == want_rows, f'{label}: Linuxへの行がSDと違う'
        assert got_can[:len(want_can)] == want_can, f'{label}: LinuxへのCANがSDと違う'
    else:
        assert is_subsequence(want_rows, got_rows), f'{label}: SDの行がLinuxへの行の並びにない'
        assert is_subsequence(want_can, got_can), f'{label}: SDのCANがLinuxへのCANの並びにない'
    imu_seq = [r[0] for r in rows if len(r[2]) != 184]
    assert all(b == a + 1 for a, b in zip(imu_seq, imu_seq[1:])), f'{label}: IMUの行の連番が飛ぶ'
    samples, sensors = decode_all(view)
    imu_rows = sum(1 for r in rows if len(r[2]) != 184)
    assert len(samples) == imu_rows, (len(samples), imu_rows)
    with_speed = sum(1 for s in samples if s['values'].get('GPSSpeed') is not None)
    print(f'  {label}: Linuxへ IMUの行 {imu_rows}・NAV-PVTの行 {len(rows) - imu_rows}{"（この版はNAV-PVTを状態で渡す）" if legacy else ""}・CAN {len(can)}（SDに残った分と同じ並び・中身）、'
          f'HardwareDecoder のサンプル {len(samples)}（GPSの速さが入ったもの {with_speed}）、表示 {sensors}')
    return samples


def check_normal(out, exp, summary, view):
    files = read_card(out)
    sd = sd_records(files)
    by = {k: [(ms, d) for kk, ms, d in sd if kk == k] for k in range(1, 7)}
    assert not [k for k, _, _ in sd if k not in by], 'SDに知らない種類の記録'
    status = summary['status']
    st = {k: status.get(k) for k in ('seq', 'imu_errors', 'gnss_errors', 'dropped', 'can_counts', 'can_overflow', 'sd_errors', 'sd_queue_dropped',
                                 'sd_queue_max', 'sd_blocks', 'sd_logging', 'sd_alloc_ms')}
    print(f'  SD: {len(files)}本 {", ".join(f"{n}={len(b) // 1024}KiB" for n, b in files)}、記録 {len(sd)}件、ブロック {sum(len(b) for _, b in files) // 512}'
          f'（全部 CRC・連番・ファイル番号が合う。目次は2区画に伸び、ほかのファイル {OTHER_FILES}個もそのまま）')
    print(f'  状態: {st}')
    assert summary['problem_count'] == 0, summary['problems']
    assert summary['fatal'] is None, summary['fatal']
    assert status['sd_errors'] == 0 and status['sd_queue_dropped'] == 0 and not status['sd_logging']
    assert status['can_overflow'] == [0, 0] and status['gnss_errors'] == 0 and status['dropped'] == 0
    assert summary['can1']['fifo_lost'] == 0 and summary['can2']['overflow'] == 0 and summary['can2']['mode'] == 0
    assert summary['gnss']['config_ok'] == 3 and summary['gnss']['left'] == 0 and summary['bno055']['opr_mode'] == 12
    assert status['sd_blocks'] == sum(len(b) for _, b in files) // 512
    listed = json.loads(summary['files']) if isinstance(summary['files'], str) else summary['files']
    assert [(f['index'], f['size']) for f in listed] == [(int(n[2:8]), len(b)) for n, b in files], listed

    # CAN: the same frames in the same order on each channel; CAN1 keeps the drive's own time stamps.
    for ch in (1, 2):
        want = exp.can[ch]
        got = [(struct.unpack_from('<I', d, 1)[0], d[5], d[7:7 + d[6]], ms) for ms, d in by[3] if d[0] == ch]
        assert len(got) == len(want), (ch, len(got), len(want))
        assert [g[:3] for g in got] == [w[1:4] for w in want], f'CAN{ch} の中身・並びが違う'
        lag = [g[3] - w[0] // 1000 for g, w in zip(got, want)]
        assert min(lag) >= 0 and max(lag) <= (1 if ch == 1 else 3), (ch, min(lag), max(lag))
        same = sum(g[3] - exp.offset_ms == w[4] for g, w in zip(got, want))
        print(f'  CAN{ch}: {len(got)}件、入力と同じ並び・中身。SDの時刻＝届いた時刻＋{min(lag)}〜{max(lag)}ms、元の記録の時刻と同じ {same}件')
    assert status['can_counts'] == [len(exp.can[1]), len(exp.can[2])]

    # GNSS: every NAV-PVT, and one NAV-SAT summary and NAV-SLAS head a second.
    for kind, want, name in ((2, exp.nav, 'NAV-PVT'), (5, exp.sat, 'NAV-SAT の要約（種類5）'), (6, exp.slas, 'NAV-SLAS の頭（種類6）')):
        got = by[kind]
        if kind != 2 and not summary['gnss']['nav_sat_on' if kind == 5 else 'nav_slas_on']:
            assert not got, name
            print(f'  {name}: このファームは受信機に頼まない（受信機も出さない）')
            continue
        assert [d for _, d in got] == [d for _, d in want], f'{name} の中身・並びが違う（SD {len(got)}件・入力 {len(want)}件）'
        lag = [ms - t // 1000 for (ms, _), (t, _) in zip(got, want)]
        assert min(lag) >= 0 and max(lag) <= 50, (name, min(lag), max(lag))
        print(f'  {name}: {len(got)}件、入力と同じ。届いてから {min(lag)}〜{max(lag)}ms で読んだ')
    for _, d in by[5] + by[6]:
        gnss_aux(5 if len(d) == 9 else 6, d)

    # IMU: everything the BNO055 handed over is on the card, with the time it was read.
    served = served_imu(out)
    stored = [(k, ms, d) for k, ms, d in sd if k in (1, 4)]
    # Reads after LOG0 (recording stopped) are not stored: the card holds every read made while recording.
    recorded = [r for r in served if r[0] < 0x80]
    assert stored == recorded, f'IMU: SD {len(stored)}件と記録中に読んだ {len(recorded)}件が違う'
    fails = sum(1 for k, _, _ in served if k & 0x7f == 4)
    assert fails == exp.imu_fail_in and status['imu_errors'] == fails and len(served) - 5 <= status['seq'] <= len(served)
    covered = len({d for k, _, d in stored if k == 1} & exp.imu_samples)
    print(f'  IMU: BNO055 を読んだ {len(served)}回（うち失敗 {fails}、入力の失敗 {exp.imu_fail_in}）のうち、記録を止めるまでの {len(stored)}回が'
          f'全部、読んだ時刻のままSDにある。入力のサンプル {exp.imu_in} のうち {covered} が読まれた（ファームは自分の10msの刻みで読む）')

    # Time order: each kind never goes back; across kinds a record is at most a few ms older than the one before.
    for k, recs in by.items():
        assert all(b[0] >= a[0] for a, b in zip(recs, recs[1:])), f'種類{k} の時刻が戻る'
    back = max([a[1] - b[1] for a, b in zip(sd, sd[1:])] + [0])
    assert back <= 5, back
    print(f'  時刻の並び: 種類ごとに戻らない。種類をまたぐと最大 {back}ms 前の記録が後に来る（CAN1 は捕まえた時刻のまま後から書くため）')
    check_linux(view, sd, 'ふつうの再生')
    return sd


def check_stall(out, exp, summary, view, stall):
    files = read_card(out)
    sd = sd_records(files)
    status = summary['status']
    assert summary['problem_count'] == 0 and summary['fatal'] is None, (summary['problems'], summary['fatal'])
    served = served_imu(out)
    want = {k: [r for r in served if r[0] == k] for k in (1, 4)}  # reads made while recording
    got = {k: [(kk, ms, d) for kk, ms, d in sd if kk == k] for k in (1, 2, 3, 4, 5, 6)}
    missing = 0
    for k in (1, 4):
        assert is_subsequence(got[k], want[k]), f'種類{k}: 残った記録が入力の並びにない'
        missing += len(want[k]) - len(got[k])
    for k, w in ((2, exp.nav), (5, exp.sat), (6, exp.slas)):
        wd = [d for _, d in w] if k == 2 or summary['gnss']['nav_sat_on' if k == 5 else 'nav_slas_on'] else []
        gd = [d for _, _, d in got[k]]
        assert is_subsequence(gd, wd), f'種類{k}: 残った記録が入力の並びにない'
        missing += len(wd) - len(gd)
    for ch in (1, 2):
        wd = [(i, f, d) for _, i, f, d, _ in exp.can[ch]]
        gd = [(struct.unpack_from('<I', d, 1)[0], d[5], d[7:7 + d[6]]) for _, _, d in got[3] if d[0] == ch]
        assert is_subsequence(gd, wd), f'CAN{ch}: 残った記録が入力の並びにない'
        missing += len(wd) - len(gd)
    print(f'  SDが止まった間（{stall}）: 待ち行列の一番深い量 {status.get("sd_queue_max")}B、捨てた数 sd_queue_dropped={status["sd_queue_dropped"]}、'
          f'SDから欠けた記録 {missing}件、SDの書き込みの最長の待ち {summary["sd"]["max_busy_us"] // 1000}ms、sd_errors={status["sd_errors"]}')
    assert status['sd_queue_dropped'] > 0, 'この止まり方では待ち行列があふれるはず'
    assert missing == status['sd_queue_dropped'], '捨てた数と欠けた記録の数が違う'
    assert status['sd_errors'] == 0 and status['can_overflow'] == [0, 0] and status['dropped'] == 0
    assert summary['can1']['fifo_lost'] == 0 and summary['can2']['overflow'] == 0
    assert status['can_counts'] == [len(exp.can[1]), len(exp.can[2])]
    samples = check_linux(view, sd, 'SDが止まった間も', sd_complete=False)
    assert len(samples) == len(served), 'SDが止まっても、Linuxへは読んだIMUが全部届くはず'
    can_rows = sum(len(b['can']) for kind, _, b in view if kind == 'T')
    assert can_rows == len(exp.can[1]) + len(exp.can[2]), 'SDが止まっても、LinuxへはCANが全部届くはず'


async def rpc_client(port, end_ms):
    """EcoCapture-Web's TelemetryBridge, connected over TCP instead of the Router's UNIX socket."""
    import msgpack  # noqa: F401  (TelemetryBridge needs it)
    from unittest import mock
    import telemetry_bridge
    from telemetry_bridge import TelemetryBridge

    async def tcp(_path):
        for _ in range(200):
            try:
                return await asyncio.open_connection('127.0.0.1', port)
            except OSError:
                await asyncio.sleep(.1)
        raise ConnectionError('the replay RPC port did not open')

    lines = []
    with mock.patch.object(telemetry_bridge.asyncio, 'open_unix_connection', tcp, create=True):
        bridge = TelemetryBridge('tcp')
        t0 = time.monotonic()
        refused = 0
        while True:  # right after boot the handlers are not registered yet; server.py retries after 0.5 s
            try:
                lines.append(f'C 0 C500000 {json.dumps({"result": await bridge.command("C500000")})}')
                break
            except ValueError as e:
                assert 'not available' in str(e), e
                refused += 1
                await asyncio.sleep(.5)
        status_at = 0
        while True:
            tick = time.monotonic()
            if tick - status_at >= .1:
                status = json.loads(await bridge.call('logger.status'))
                status_at = tick
                lines.append(f'S {status["mcu_ms"]} {json.dumps(status)}')
            batch = await bridge.call('logger.take')
            lines.append(f'T {status["mcu_ms"]} {batch}')
            if status['mcu_ms'] >= end_ms:
                break
            await asyncio.sleep(max(0, .05 - (time.monotonic() - tick)))
        wall = time.monotonic() - t0
        assert await bridge.command('LOG0') == 'stopped'
        files = json.loads(await bridge.command('FILES0'))
        lines.append(f'S 0 {await bridge.call("logger.status")}')
        lines.append(f'T 0 {await bridge.call("logger.take")}')
        mbr = bytes.fromhex((await bridge.sector(0))[5:])
        part = struct.unpack_from('<I', mbr, 446 + 8)[0]
        bpb = bytes.fromhex((await bridge.sector(part))[5:])
        spc, reserved, fats, fat = bpb[13], struct.unpack_from('<H', bpb, 14)[0], bpb[16], struct.unpack_from('<I', bpb, 36)[0]
        lba = part + reserved + fats * fat + (files[0]['cluster'] - 2) * spc
        block = bytes.fromhex((await bridge.sector(lba))[5:])
        await bridge.close()
    assert block[:4] == b'ELB2' and zlib.crc32(block[:508]) == struct.unpack_from('<I', block, 508)[0]
    assert struct.unpack_from('<II', block, 4) == (files[0]['index'], 0)
    return lines, files, wall, refused


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--sd-dir')
    ap.add_argument('--first', type=int, default=100)
    ap.add_argument('--files', type=int, default=4)
    ap.add_argument('--seconds', type=float, default=0, help='0: the whole of the files')
    ap.add_argument('--no-stall', action='store_true')
    ap.add_argument('--no-rpc', action='store_true')
    ap.add_argument('--rpc-seconds', type=float, default=20)
    ap.add_argument('--rpc-port', type=int, default=47911)
    ap.add_argument('--firmware', help='another copy of firmware/ecologger_v2 (e.g. the one on the board) instead of this one')
    ap.add_argument('--keep', help='keep the inputs and outputs (they hold positions: not in the repository)')
    a = ap.parse_args()
    sd_dir = find_sd_dir(a.sd_dir)
    work = Path(a.keep) if a.keep else Path(tempfile.mkdtemp(prefix='ecologger_replay_'))
    work.mkdir(parents=True, exist_ok=True)
    try:
        print(f'入力: {sd_dir} の EL{a.first:06d} から {a.files}本')
        exe = build(work, a.firmware)
        events, exp, length = build_events(sd_dir, a.first, a.files, a.seconds)
        write_events(work / 'events.bin', events)
        print(f'  {length:.1f}秒ぶん: IMU {exp.imu_in}（失敗 {exp.imu_fail_in}）・NAV-PVT {len(exp.nav)}（NAV-SAT・NAV-SLAS 各 {len(exp.sat)} は作り物）'
              f'・CAN1 {len(exp.can[1])}・CAN2 {len(exp.can[2])}')

        print('1. ふつうの再生')
        started = time.monotonic()
        print('  ' + run_replay(exe, work / 'events.bin', work / 'normal').strip().replace('\n', '\n  '))
        summary = json.loads((work / 'normal' / 'summary.json').read_text())
        view = linux_view((work / 'normal' / 'linux.txt').read_text().splitlines())
        print(f'  （PCで {time.monotonic() - started:.0f}秒）')
        check_normal(work / 'normal', exp, summary, view)

        if not a.no_stall:
            print('2. SDの書き込みが止まる')
            stall = '20000:30000:900'
            short, exp_short, _ = build_events(sd_dir, a.first, a.files, 60)
            write_events(work / 'stall.bin', short)
            run_replay(exe, work / 'stall.bin', work / 'stall', f'--stall {stall}')
            summary = json.loads((work / 'stall' / 'summary.json').read_text())
            view = linux_view((work / 'stall' / 'linux.txt').read_text().splitlines())
            check_stall(work / 'stall', exp_short, summary, view, f'起動から20〜30秒、1ブロックごとに0.9秒')

        if not a.no_rpc:
            try:
                import msgpack  # noqa: F401
            except ImportError:
                print('3. TCP の RPC：msgpack が無いので飛ばす')
                return
            print(f'3. TCP の RPC（実時間で {a.rpc_seconds:.0f}秒ぶん）')
            short, _, _ = build_events(sd_dir, a.first, a.files, a.rpc_seconds)
            write_events(work / 'rpc.bin', short)
            proc = run_replay(exe, work / 'rpc.bin', work / 'rpc', f'--rpc-port {a.rpc_port}', background=True)
            end_ms = short[-1][0] // 1000 + 1500
            lines, files, wall, refused = asyncio.run(rpc_client(a.rpc_port, end_ms))
            out, _ = proc.communicate(timeout=120)
            print('  ' + out.strip().replace('\n', '\n  '))
            summary = json.loads((work / 'rpc' / 'summary.json').read_text())
            assert proc.returncode == 0 and summary['problem_count'] == 0 and summary['fatal'] is None, (proc.returncode, summary['problems'])
            sd = sd_records(read_card(work / 'rpc'))
            print(f'  起動直後の「method ... not available」{refused}回のあと、TelemetryBridge で {len(lines)}回 受け取った（実時間 {wall:.1f}秒）。FILES0 → {files}、logger.sdread でSDの1ブロック目を読めた（ELB2・CRC）')
            view = linux_view(lines)
            last = [b for kind, _, b in view if kind == 'S'][-1]
            assert last['dropped'] == 0 and last['sd_queue_dropped'] == 0 and last['sd_errors'] == 0 and last['can_overflow'] == [0, 0], last
            check_linux(view, sd, 'TCPで')
        print('PASS: 再生の試験台（SDの記録・待ち行列の数え方・Linuxへの行・状態のJSON）')
    finally:
        if not a.keep:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == '__main__':
    main()
