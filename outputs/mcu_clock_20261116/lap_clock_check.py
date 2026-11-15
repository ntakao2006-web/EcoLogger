"""STM32の時計（mcu_ms）の進みと、記録のラップタイムがどの時計で測られているかの確かめ（2026-11-16）。

  python outputs/mcu_clock_20261116/lap_clock_check.py <キャッシュのフォルダ>

キャッシュの slip_nav_20261108.pkl は outputs/slip_angle_20261116/slip_angle.py が作る（SDの NAV-PVT）。
1) SDの起動ごとに、STM32の時計（届いた時刻）が受信機の時計（itow）に対してどれだけ遅れて進むか
2) 記録の LapTime と、SDの測位で線の中心をいちばん近く通った時刻の差から出したラップ
3) 同じ周を STM32 の時計（行の mcu_ms）で測った長さ
"""
import json, sys, numpy as np, pandas as pd
S=sys.argv[1]
CFG=json.load(open('tools/race_analysis/sugo_20261108_sd.json',encoding='utf-8'))
d=pd.read_csv(CFG['race_csv'],usecols=['mcu_ms','host_utc','gnss_itow_ms','gnss_utc','LapCount','LapTime','CurrentLap'],low_memory=False); d['LapTime']=d.LapTime*60  # RaceCapture の決まりで分
nav=pd.read_pickle(S+'/slip_nav_20261108.pkl')
probe=d[d.gnss_itow_ms.notna()].iloc[::500]
best=max(nav.boot.unique(),key=lambda b: np.isin(probe.gnss_itow_ms.astype(np.int64),nav.itow[nav.boot==b]).sum())
# 1) 起動ごとの STM32 の時計の進み（受信機の時計に対して）
print('boot  hours  ppm')
for b,g in nav.groupby('boot'):
    g=g[(g.fix>=3)&(g['flags']&1==1)].drop_duplicates('itow')
    if len(g)>10: g=g[np.abs((g.stamp-g.itow)-np.median(g.stamp-g.itow))<60000]
    if len(g)<3000: continue
    p=np.polyfit(g.itow.values,(g.stamp-g.itow).values.astype(float),1)
    print(b, round((g.itow.max()-g.itow.min())/3.6e6,2), round(p[0]*1e6), '(race)' if b==best else '')
# 2) 記録の LapTime（本体が走りながら出した値）と、SD の測位で線に一番近づいた時刻の差から出したラップ
g=nav[(nav.boot==best)&(nav.fix>=3)].drop_duplicates('itow').reset_index(drop=True)
lat0,lon0=CFG['line']
x=(g.lon-lon0)*np.cos(np.radians(lat0))*111320; y=(g.lat-lat0)*110540
dist=np.hypot(x,y).values; t=g.itow.values/1000
near=np.where((dist<25))[0]
# 通過ごとに、いちばん近い点の前後で放物線をあてて最も近い時刻を出す
passes=[]; grp=np.split(near,np.where(np.diff(near)>20)[0]+1)
for idx in grp:
    if len(idx)==0: continue
    i=idx[np.argmin(dist[idx])]
    if i<1 or i>=len(t)-1: continue
    # 速度ベクトルに沿った位置で線の中心を通る時刻（中心に一番近い時刻）
    vx=(x[i+1]-x[i-1])/(t[i+1]-t[i-1]); vy=(y[i+1]-y[i-1])/(t[i+1]-t[i-1])
    tc=t[i]-(x[i]*vx+y[i]*vy)/(vx*vx+vy*vy)
    passes.append(tc)
passes=np.array(passes); gl=np.diff(passes)
rec=d[d.LapCount.diff()==1][['LapCount','LapTime','mcu_ms']]
rec_mcu=np.diff(d[d.LapCount.diff()==1].mcu_ms.values)/1000
# 記録のラップと突き合わせ（近い長さのものを順に）
rows=[]
for _,r in rec.iterrows():
    if not (60<r.LapTime<200): continue
    j=np.argmin(np.abs(gl-r.LapTime)); rows.append((int(r.LapCount),r.LapTime,gl[j],r.LapTime-gl[j]))
R=pd.DataFrame(rows,columns=['lap','recorded','gnss_center','diff'])
print(R.describe().round(4)); print(R.head(8).round(3))
ok=R[R['diff'].abs()<0.5]
print('recorded - gnss: median %.4f s, mean %.4f s, n=%d; ratio median %.5f'%(ok['diff'].median(),ok['diff'].mean(),len(ok),(ok.recorded/ok.gnss_center).median()))
# 3) 同じ周を STM32 の時計（行の mcu_ms）で測ると
lc=d[d.LapCount.diff()==1]
m=pd.DataFrame({'lap':lc.LapCount.values[1:],'rec':lc.LapTime.values[1:],'mcu':np.diff(lc.mcu_ms.values)/1000})
m=m[(m.rec>100)&(m.rec<130)]
print('mcu clock lap / recorded LapTime: median %.5f, median diff %.3f s'%((m.mcu/m.rec).median(),(m.mcu-m.rec).median()))
