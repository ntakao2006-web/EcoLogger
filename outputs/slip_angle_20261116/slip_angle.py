"""IMU（BNO055 の角速度）と測位（u-blox の NAV-PVT の速度の向き）から、車体の横すべり角 β を出してみる試し（2026-11-16）。

  python outputs/slip_angle_20261116/slip_angle.py [キャッシュのフォルダ]

β ＝ 進む向き（測位の速度の向き）－ 車の向き（角速度を足し合わせた向き）。左回りを＋とする（SAE と同じ向き）。
  左コーナーで β が－＝頭が進む向きより内（左）を向いている。下の図と表では「頭が内向き＝＋」に直した beta_in も出す。
角速度を足し合わせた向きは少しずつずれるので、まっすぐ走っている所（β≒0 とみなせる所）で毎回合わせ直し、
そのあいだは前後の合わせ直しの値を直線でつなぐ（デジスパイスのドリフトの「前後に1秒まっすぐ」と同じ考え）。

データ：SUGO 2026-11-08 決勝（本体のCSVの角速度・横G・周、100行/秒）と、シールドのSDに残った NAV-PVT（10Hz全部）。
読むのは写しだけ。
"""
import glob, json, os, struct, sys
import numpy as np, pandas as pd

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'EcoCapture-Web'))
from sd_decode import records  # noqa: E402

OUT = os.path.dirname(os.path.abspath(__file__))
CACHE = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('TEMP', '/tmp')
CFG = json.load(open(os.path.join(REPO, 'tools/race_analysis/sugo_20261108_sd.json'), encoding='utf-8'))
WB, B_REAR = 2.330, 1.165        # NC の軸距（m）と、重心から後軸まで（前後50:50とみた目安）
NORMAL = [n for n in range(CFG['race_laps'][0] + 1, CFG['race_laps'][1] + 1)
          if n not in {22, 23, 24, 25, 26, 35, 36, 37, 38, 39, 41}]   # 決勝の通常の周（ピット・減速・停止の周を除く）

# ---------- 1. 本体のCSV（角速度・横G・周） ----------
cols = ['mcu_ms', 'GyroX', 'GyroY', 'GyroZ', 'LatAccel', 'LongAccel', 'GPSSpeed', 'CurrentLap', 'Throttle',
        'WheelFrontA', 'WheelFrontB', 'WheelRearA', 'WheelRearB', 'imu_mount', 'gnss_itow_ms']
d = pd.read_csv(os.path.join(REPO, CFG['race_csv']), usecols=cols, low_memory=False)
d = d[d.GyroZ.notna()].reset_index(drop=True)
mount = json.loads(d.imu_mount.dropna().iloc[-1])
up = np.array(mount['up']); up /= np.linalg.norm(up)
d['r'] = d[['GyroX', 'GyroY', 'GyroZ']].values @ up          # 鉛直まわりの回る速さ（deg/s、左回りが＋）
d['t'] = d.mcu_ms / 1000.0
d['lap'] = d.CurrentLap.ffill()

# ---------- 2. SDの NAV-PVT（速度の向き・精度も） ----------
cache = os.path.join(CACHE, 'slip_nav_20261108.pkl')
if os.path.exists(cache):
    nav = pd.read_pickle(cache)
else:
    rows = []
    for fi, f in enumerate(sorted(glob.glob(os.path.join(REPO, CFG['sd_dir'], 'EL*.BIN')))):
        try:
            with open(f, 'rb') as s:
                for kind, stamp, data in records(s):
                    if kind == 2 and len(data) == 92: rows.append((stamp, data))
        except ValueError:
            pass
    raw = np.frombuffer(b''.join(r[1] for r in rows), dtype=np.uint8).reshape(len(rows), 92)
    u = lambda off, t: raw[:, off:off + np.dtype(t).itemsize].copy().view(t).ravel()
    nav = pd.DataFrame({'stamp': np.array([r[0] for r in rows], dtype=np.int64), 'itow': u(0, '<u4').astype(np.int64),
                        'fix': raw[:, 20], 'flags': raw[:, 21], 'lon': u(24, '<i4') * 1e-7, 'lat': u(28, '<i4') * 1e-7,
                        'velN': u(48, '<i4') / 1000, 'velE': u(52, '<i4') / 1000, 'gspeed': u(60, '<i4') / 1000,
                        'headMot': u(64, '<i4') * 1e-5, 'sAcc': u(68, '<u4') / 1000, 'headAcc': u(72, '<u4') * 1e-5})
    nav['boot'] = np.cumsum(np.r_[0, np.diff(nav.stamp.values) < -60000])
    nav.to_pickle(cache)
# 決勝の起動：本体の行の itow がいちばん多く見つかる起動（sd_gnss.py と同じ選び方）
probe = d[d.gnss_itow_ms.notna()].iloc[::500]
best = max(nav.boot.unique(), key=lambda b: np.isin(probe.gnss_itow_ms.astype(np.int64), nav.itow[nav.boot == b]).sum())
g = nav[(nav.boot == best) & (nav.fix >= 3) & (nav['flags'] & 1 == 1)].copy()
g = g[(g.stamp >= d.mcu_ms.min()) & (g.stamp <= d.mcu_ms.max())].drop_duplicates('itow').reset_index(drop=True)
g['chi'] = np.degrees(np.unwrap(np.radians(-np.degrees(np.arctan2(g.velE, g.velN)))))   # 進む向き（左回りが＋）
g['v'] = g.gspeed
g['lap'] = d.lap.values[np.clip(np.searchsorted(d.mcu_ms.values, g.stamp.values), 0, len(d) - 1)]

# ---------- 3. 時刻のずれ：NAV-PVT が届くのは測った瞬間より遅い。進む向きの変わる速さが角速度に合うずれを探す ----------
run = (g.v > 15).values
chidot = np.gradient(g.chi.values, g.itow.values / 1000.0)
r_cum = np.cumsum(d.r.values * np.r_[0, np.clip(np.diff(d.t.values), 0, 0.05)])    # 角速度を足し合わせた向き（倍率は後で）
def r_at(t): return np.interp(t, d.t.values, d.r.values)
# 届いた時刻（stamp）は1つずつ十数 ms 揺れるので、受信機が測った時刻（itow）を STM32 の時計へ直線で写した時刻を使う。
# STM32 の時計は受信機の時計より少し遅れて進む（この日は −0.26 %）ので、傾きも合わせる。
dl = (g.stamp - g.itow).values.astype(float)
cp = np.polyfit(g.itow.values, dl, 1)
cp[1] += np.median(dl - np.polyval(cp, g.itow.values))
g['t_arr'] = (g.itow + np.polyval(cp, g.itow.values)) / 1000.0     # 揺れを除いた「ふつうに届く時刻」
CLOCK_PPM = cp[0] * 1e6
ARR_JIT = np.percentile(dl - np.polyval(cp, g.itow.values), [5, 95])
lags = np.arange(0, 0.301, 0.005)
fit = []
for L in lags:
    x = r_at(g.t_arr.values - L)[run]; y = chidot[run]
    fit.append(np.mean((y - x * (x @ y) / (x @ x)) ** 2))
LAG_GYRO = float(lags[int(np.argmin(fit))])
# 上の合わせ方は「進む向きの変わる速さ＝回る速さ」とみているので、コーナーの入りで β が育つ分（β の変わる速さ）まで
# 遅れとして吸い込み、遅れを多めに出す。β は横Gにつれて育つとみて、横Gの変わる速さの項を足して合わせ直す。
latd = np.gradient(d.LatAccel.interpolate(limit=5).values, d.t.values)
latd = pd.Series(latd).rolling(9, center=True, min_periods=1).mean().values
fit2 = []
for L in lags:
    X_ = np.c_[r_at(g.t_arr.values - L), np.interp(g.t_arr.values - L, d.t.values, latd)][run]; y_ = chidot[run]
    c_ = np.linalg.lstsq(X_, y_, rcond=None)[0]; fit2.append(np.mean((y_ - X_ @ c_) ** 2))
LAG_GYRO_B = float(lags[int(np.argmin(fit2))])
LAG = LAG_GYRO_B
if os.environ.get('SLIP_LAG_MS'): LAG = float(os.environ['SLIP_LAG_MS']) / 1000
g['t'] = g.t_arr - LAG                  # 測った瞬間（STM32の時計で）

# ---------- 4. 角速度の倍率 K：コーナーの前後の向きの変化を測位に合わせる ----------
psi_at = lambda t: np.interp(t, d.t.values, r_cum)
gl = g[g.lap.isin(NORMAL) & (g.v > 15)]
x = np.diff(psi_at(gl.t.values)[::20]); y = np.diff(gl.chi.values[::20])
ok = np.abs(np.diff(gl.t.values[::20]) - 2.0) < 0.05
K = float(x[ok] @ y[ok] / (x[ok] @ x[ok]))
g['psi'] = psi_at(g.t.values) * K

# ---------- 5. まっすぐの所で合わせ直す ----------
lat_g = np.interp(g.t.values, d.t.values, d.LatAccel.values)
g['latg'] = lat_g
g['rr'] = r_at(g.t.values) * K
g['off'] = g.psi - g.chi
straight = (g.v > 60 / 3.6) & (np.abs(g.latg) < 0.08) & (np.abs(g.rr) < 1.5)
grp = (straight != straight.shift()).cumsum()
anchors = []
for _, s in g[straight].groupby(grp[straight]):
    if s.t.iloc[-1] - s.t.iloc[0] >= 1.0:
        anchors.append((float(s.t.mean()), float(s.off.median()), float(s.off.std()), len(s)))
A = pd.DataFrame(anchors, columns=['t', 'off', 'sd', 'n'])
g['beta'] = -(g.off - np.interp(g.t, A.t, A.off))                 # β（°、左回りが＋）
turn = np.sign(g.rr.rolling(5, center=True, min_periods=1).mean())
g['beta_in'] = -g.beta * turn                                      # 頭が進む向きより内を向くと＋
g['alpha_r'] = g.beta - np.degrees(B_REAR * np.radians(g.rr) / g.v.clip(lower=5))   # 後輪の滑り角（目安）
g['alpha_r_in'] = -g.alpha_r * turn
# 合わせ直しの1つを抜いて、前後の2つだけでそこを当てたときの外れ＝合わせ直しのあいだの誤差の目安
hold = []
for i in range(1, len(A) - 1):
    pred = A.off[i - 1] + (A.off[i + 1] - A.off[i - 1]) * (A.t[i] - A.t[i - 1]) / (A.t[i + 1] - A.t[i - 1])
    hold.append((A.t[i + 1] - A.t[i - 1], A.off[i] - pred))
H = pd.DataFrame(hold, columns=['span', 'err'])
H = H[H.span < 60]                                   # ピットの停止などで長くあいた所は除く
drift = np.diff(A.off) / np.diff(A.t)                # 合わせ直しの値の変わる速さ（°/s）＝ジャイロのずれ

# ---------- 6. 周ごとの同じ所をそろえる（31周目の線に投影） ----------
from scipy.spatial import cKDTree
lat0, lon0 = CFG['line']
X = (g.lon - lon0) * np.cos(np.radians(lat0)) * 111320; Y = (g.lat - lat0) * 110540
g['x'], g['y'] = X, Y
ref = g[g.lap == 31]
sref = np.r_[0, np.cumsum(np.hypot(np.diff(ref.x), np.diff(ref.y)))]
_, ii = cKDTree(np.c_[ref.x, ref.y]).query(np.c_[g.x, g.y])
g['s'] = sref[ii]

N = g[g.lap.isin(NORMAL)].copy()
cor = N[(np.abs(N.latg) > 0.6) & (N.v > 50 / 3.6)]
summary = {
    'nav_points_race': len(g), 'lag_ms': round(LAG * 1000), 'K': round(K, 4),
    'mcu_clock_ppm': round(CLOCK_PPM), 'arrival_jitter_p5_p95_ms': [round(float(x_), 1) for x_ in ARR_JIT], 'up_tilt_deg': round(float(np.degrees(np.arccos(up[2]))), 1),
    'headAcc_med_cornering': round(float(cor.headAcc.median()), 2), 'headAcc_p95_cornering': round(float(cor.headAcc.quantile(.95)), 2),
    'anchors': len(A), 'anchor_gap_med_s': round(float(np.median(np.diff(A.t))), 1),
    'anchor_inner_sd_med': round(float(A.sd.median()), 2),
    'gyro_drift_med_deg_s': round(float(np.median(np.abs(drift))), 3),
    'holdout_err_med_abs': round(float(H.err.abs().median()), 2), 'holdout_err_p90_abs': round(float(H.err.abs().quantile(.9)), 2),
    'beta_in_med_cornering': round(float(cor.beta_in.median()), 2), 'beta_in_p95_cornering': round(float(cor.beta_in.quantile(.95)), 2),
    'alpha_r_in_med_cornering': round(float(cor.alpha_r_in.median()), 2),
}
# 周どうしで同じ所の β がどれだけそろうか（コーナーの中、5 m ごと）
N['sbin'] = (N.s // 5).astype(int)
c2 = N[(np.abs(N.latg) > 0.6) & (N.v > 50 / 3.6)]
rep = c2.groupby('sbin').beta_in.agg(['median', 'std', 'count'])
rep = rep[rep['count'] >= 15]
summary['repeat_sd_med_deg'] = round(float(rep['std'].median()), 2)
# 横Gに対する β（定常の旋回だけ：横Gの変わる速さが小さい所）
N['dlat'] = np.gradient(N.latg.values, N.t.values)
st = N[(np.abs(N.latg) > 0.3) & (np.abs(N.dlat) < 0.3) & (N.v > 50 / 3.6)]
p = np.polyfit(np.abs(st.latg), st.beta_in, 1)
summary['beta_in_per_G'] = round(float(p[0]), 2); summary['beta_in_at_0G'] = round(float(p[1]), 2)
pr = np.polyfit(np.abs(st.latg), st.alpha_r_in, 1)
summary['alpha_r_in_per_G'] = round(float(pr[0]), 2)
# 幾何の確かめ：定常の旋回で β_in = −b·r/v（低い速さで頭が外を向く分）＋ タイヤの分（横Gに比例）＋ 時刻のずれの分（ΔL·r）
st2 = N[(np.abs(N.latg) > 0.3) & (np.abs(N.dlat) < 0.3) & (N.v > 40 / 3.6)]
rr_ = np.radians(np.abs(st2.rr.values)); vv = st2.v.values; ay = np.abs(st2.latg.values); yb = np.radians(st2.beta_in.values)
cf = np.linalg.lstsq(np.c_[rr_ / vv, ay, rr_], yb, rcond=None)[0]
cb = np.linalg.lstsq(np.c_[ay, rr_], yb + B_REAR * rr_ / vv, rcond=None)[0]
summary.update({'lag_used_ms': round(LAG * 1000), 'lag_gyro_ms': round(LAG_GYRO * 1000), 'lag_gyro_with_beta_ms': round(LAG_GYRO_B * 1000),
                'geo_free_b_m': round(float(-cf[0]), 2), 'geo_free_residual_lag_ms': round(float(cf[2] * 1000)),
                'geo_bfixed_residual_lag_ms': round(float(cb[1] * 1000)), 'geo_bfixed_tire_deg_per_G': round(float(np.degrees(cb[0])), 2)})
print(json.dumps(summary, ensure_ascii=False, indent=1))
json.dump(summary, open(os.path.join(OUT, 'summary.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
H.to_csv(os.path.join(OUT, 'holdout.csv'), index=False)

# ---------- 7. 図 ----------
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = ['Yu Gothic', 'MS Gothic', 'sans-serif']
fig, ax = plt.subplots(3, 1, figsize=(13, 9), sharex=True)
for n, c in ((31, 'C3'), (30, 'C0'), (32, 'C2')):
    L_ = g[g.lap == n]
    ax[0].plot(L_.s, L_.beta_in, c, lw=1, label=f'{n}周目')
    ax[1].plot(L_.s, L_.alpha_r_in, c, lw=1)
    ax[2].plot(L_.s, np.abs(L_.latg), c, lw=1)
ax[0].set_ylabel('横すべり角 β（°）\n頭が内向き＋'); ax[0].legend(loc='upper right'); ax[0].axhline(0, c='k', lw=.5)
ax[1].set_ylabel('後輪の滑り角（°）\n目安'); ax[1].axhline(0, c='k', lw=.5)
ax[2].set_ylabel('|横G|（G）'); ax[2].set_xlabel('31周目の線に沿った距離（m）')
ax[0].set_ylim(-6, 26); ax[1].set_ylim(-6, 26)
fig.suptitle('SUGO 2026-11-08 決勝：IMU＋測位から出した横すべり角（30・31・32周目、32周目にC4の大きな滑り）')
fig.tight_layout(); fig.savefig(os.path.join(OUT, 'beta_laps.png'), dpi=110); plt.close(fig)

fig, ax = plt.subplots(1, 2, figsize=(13, 5))
rep = rep.reindex(range(rep.index.min(), rep.index.max() + 1))      # 直線など横G0.6以下の所は空けて描く
ax[0].plot(rep.index * 5, rep['median'], 'k', lw=1, label='中央値')
ax[0].fill_between(rep.index * 5, rep['median'] - rep['std'], rep['median'] + rep['std'], color='C0', alpha=.3, label='±標準偏差（周どうし）')
ax[0].set_xlabel('距離（m）'); ax[0].set_ylabel('β（°、頭が内向き＋）'); ax[0].legend(); ax[0].set_title(f'{len(NORMAL)}周の同じ所の β（横G0.6超の所だけ）')
h = ax[1].hexbin(np.abs(st.latg), st.beta_in, gridsize=60, bins='log', cmap='viridis', extent=(0.3, 1.3, -4, 10))
xx = np.linspace(.3, 1.3, 10); ax[1].plot(xx, np.polyval(p, xx), 'r', lw=1.5, label=f'直線 {p[0]:.1f}°/G')
ax[1].set_xlabel('|横G|（G）'); ax[1].set_ylabel('β（°、頭が内向き＋）'); ax[1].legend(); ax[1].set_title('定常の旋回での横Gと β')
fig.tight_layout(); fig.savefig(os.path.join(OUT, 'beta_repeat_and_gradient.png'), dpi=110); plt.close(fig)

fig, ax = plt.subplots(1, 2, figsize=(13, 4.5))
ax[0].plot(lags * 1000, np.array(fit) / min(fit), 'k'); ax[0].axvline(LAG * 1000, c='r')
ax[0].set_xlabel('NAV-PVT が届くまでの遅れとみた値（ms）'); ax[0].set_ylabel('合わないぐあい（いちばん小さい所を1）'); ax[0].set_title(f'時刻のずれ：{LAG * 1000:.0f} ms')
ax[1].scatter(H.span, H.err, s=6); ax[1].axhline(0, c='k', lw=.5)
ax[1].set_xlabel('合わせ直しの間隔（前後の2つのあいだ、秒）'); ax[1].set_ylabel('抜いた所の外れ（°）'); ax[1].set_title('合わせ直しを1つ抜いて当てたときの外れ')
fig.tight_layout(); fig.savefig(os.path.join(OUT, 'checks.png'), dpi=110); plt.close(fig)
