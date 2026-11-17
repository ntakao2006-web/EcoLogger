"""Decode standalone ELxxxxxx.BIN logs: python sd_decode.py FILE.BIN [OUTPUT.csv] [--config config.json] [--mount imu_mount.json].

With the logger's vehicle configuration, each configured CAN signal becomes a CSV
column decoded exactly as the logger does live (hardware.HardwareDecoder): a value
is kept for 1 s after its frame, and sensor-hub oil temperature adds <name>State
(0 OK, 1 open, 2 short, 3 bad frame, 4 no frame). Raw frames still go to .can.jsonl.

Since SP-7-8 (2026-11-16) the logger also writes, once a second, which augmentation the
receiver used: record 5 (NAV-SAT counted by the STM32) and record 6 (the NAV-SLAS head).
They go to .gnss.jsonl (see gnss_aux); files without them get no .gnss.jsonl.

Since SP-11 (2026-11-17) the logger asks the car's ECU over OBD (SPEC.md G-5): record 7 is a frame it sent
(id u16, 8 data bytes), record 8 the start of a snapshot (1 = new SD file, 2 = the bus came alive). The answers
are ordinary CAN records (0x7E8 on channel 1); ObdAnswers puts their ISO-TP frames back together and they go,
with the sent frames and snapshot starts, to .obd.jsonl (see ObdAnswers); files without them get no .obd.jsonl.

LongAccel/LatAccel/VertAccel are the car's axes from the mounting calibration, run
over the file exactly as the logger runs it live (imu_mount.py). The SD card holds
only the raw IMU, so the calibration starts from --mount (GET /api/imu/mount, or the
first imu_mount cell of the eMMC log of the same drive); without it, it is taken
again at the first stop. The calibration in use is in the imu_mount column.
"""
import argparse
import csv
import struct
import zlib
from pathlib import Path

def records(stream):
    expected=0;file_id=None
    while block:=stream.read(512):
        if len(block)!=512:raise ValueError('Truncated SD block')
        if block[:4]!=b'ELB2':raise ValueError('Invalid SD block signature')
        ident,sequence,used=struct.unpack_from('<IIH',block,4)
        if file_id is None:file_id=ident
        if ident!=file_id or sequence!=expected:raise ValueError('Missing or reordered SD block')
        if zlib.crc32(block[:508])!=struct.unpack_from('<I',block,508)[0]:raise ValueError('SD block CRC mismatch')
        if not 16<=used<=508:raise ValueError('Invalid SD payload length')
        expected+=1;pos=16
        while pos<used:
            if pos+6>used:raise ValueError('Truncated record header')
            kind,size,stamp=struct.unpack_from('<BBI',block,pos);pos+=6
            if pos+size>used:raise ValueError('Truncated record')
            yield kind,stamp,block[pos:pos+size]
            pos+=size

def gnss_aux(kind,data):
    """SD record 5 or 6 as a dict (SP-7-8), None for any other kind. u-blox M10 SPG 5.10 3.15.13 / 3.15.16.
    5, NAV-SAT counted by the STM32: satellites in the message, used for navigation, used and with differential
    correction data, used with SBAS corrections, used with QZSS SLAS corrections.
    6, the 20-byte head of NAV-SLAS: the ground monitoring station and QZSS satellite whose corrections are used."""
    if kind==5:
        if len(data)!=9:raise ValueError('Invalid NAV-SAT summary record')
        itow,svs,used,diff,sbas,slas=struct.unpack('<I5B',data)
        return {'kind':'sat','itow_ms':itow,'svs':svs,'used':used,'diff':diff,'sbas':sbas,'slas':slas}
    if kind==6:
        if len(data)!=20:raise ValueError('Invalid NAV-SLAS record')
        itow,lon,lat,code,sv,flags,count=struct.unpack('<I4xii4B',data)
        return {'kind':'slas','itow_ms':itow,'gms_lon':lon/1000,'gms_lat':lat/1000,'gms_code':code,'qzss_sv':sv,
                'gms_available':bool(flags&1),'qzss_available':bool(flags&2),'test_mode':bool(flags&4),'corrections':count}
    return None

# SAE J1979 mode 01 values for the PIDs the logger keeps reading and a few more (others stay as hex).
OBD01={0x04:('load','%',lambda d:d[0]*100/255),0x05:('coolant','degC',lambda d:d[0]-40),
       0x06:('stft1','%',lambda d:d[0]/1.28-100),0x07:('ltft1','%',lambda d:d[0]/1.28-100),
       0x0B:('map','kPa',lambda d:d[0]),0x0C:('rpm','rpm',lambda d:(d[0]*256+d[1])/4),0x0D:('speed','km/h',lambda d:d[0]),
       0x0E:('timing','deg',lambda d:d[0]/2-64),0x0F:('iat','degC',lambda d:d[0]-40),0x10:('maf','g/s',lambda d:(d[0]*256+d[1])/100),
       0x11:('throttle','%',lambda d:d[0]*100/255),0x15:('o2_b1s2_v','V',lambda d:d[0]/200),0x1F:('run_time','s',lambda d:d[0]*256+d[1]),
       0x21:('mil_distance','km',lambda d:d[0]*256+d[1]),0x30:('warmups_since_clear','',lambda d:d[0]),
       0x31:('distance_since_clear','km',lambda d:d[0]*256+d[1]),0x33:('baro','kPa',lambda d:d[0]),
       0x42:('module_voltage','V',lambda d:(d[0]*256+d[1])/1000),0x43:('abs_load','%',lambda d:(d[0]*256+d[1])*100/255),
       0x44:('equiv_ratio','',lambda d:(d[0]*256+d[1])/32768),0x45:('rel_throttle','%',lambda d:d[0]*100/255)}
FUEL_SYSTEM={1:'open_loop_cold',2:'closed_loop',4:'open_loop_load',8:'open_loop_fault',16:'closed_loop_fault'}

def dtc(a,b):
    """Two bytes of a mode 03/07 answer as a trouble code such as P0101."""
    return 'PCBU'[a>>6]+f'{(a>>4)&3}{a&15:X}{b>>4:X}{b&15:X}'

class ObdAnswers:
    """Puts the ECU's 0x7E8 frames (ISO-TP) back together and describes each answer (SP-11)."""
    def __init__(self):self.lines=[];self.part=None
    def sent(self,stamp,data):
        if len(data)!=10:raise ValueError('Invalid OBD sent record')
        self.lines.append({'kind':'sent','mcu_ms':stamp,'id':data[0]|data[1]<<8,'data':data[2:].hex()})
    def snapshot(self,stamp,data):
        if len(data)!=1:raise ValueError('Invalid OBD snapshot record')
        self.lines.append({'kind':'snapshot','mcu_ms':stamp,'reason':{1:'new_file',2:'bus_alive'}.get(data[0],data[0])})
    def frame(self,stamp,d):
        pci=d[0]>>4 if d else 9
        if pci==0 and 1<=d[0]&15<=7:self.answer(stamp,d[1:1+(d[0]&15)])
        elif pci==1 and len(d)==8:self.part=[stamp,((d[0]&15)<<8)|d[1],bytearray(d[2:])]
        elif pci==2 and self.part:
            self.part[2]+=d[1:]
            if len(self.part[2])>=self.part[1]:stamp0,size,body=self.part;self.part=None;self.answer(stamp0,bytes(body[:size]))
    def answer(self,stamp,p):
        line={'kind':'answer','mcu_ms':stamp,'service':p[0],'raw':p.hex()}
        if p[0]==0x41 and len(p)>=2:
            pid,d=p[1],p[2:];line['pid']=pid
            if pid%32==0 and len(d)>=4:line['supported']=[pid+i+1 for i in range(32) if int.from_bytes(d[:4],'big')>>(31-i)&1]
            elif pid==3 and d:line['value']=FUEL_SYSTEM.get(d[0],d[0])
            elif pid==1 and len(d)>=4:line.update(mil=bool(d[0]&0x80),dtc_count=d[0]&0x7f)
            elif pid in OBD01:
                name,unit,f=OBD01[pid]
                try:line.update(name=name,unit=unit,value=round(f(d),3))
                except IndexError:pass
        elif p[0] in (0x43,0x47) and len(p)>=2:
            codes=p[2:2+2*p[1]];line['dtc']=[dtc(codes[i],codes[i+1]) for i in range(0,len(codes)-1,2) if codes[i] or codes[i+1]]
        elif p[0]==0x49 and len(p)>=2:
            line['pid']=p[1]
            if p[1]==4:line['calid']=p[3:].decode('ascii','replace').rstrip('\x00')
        self.lines.append(line)

FIELDS=['mcu_ms','AccelX','AccelY','AccelZ','GyroX','GyroY','GyroZ','Roll','Pitch','LongAccel','LatAccel','VertAccel','Lat','Lon','Altitude','GPSSpeed','GPSFix','GPSSats','gnss_itow_ms','imu_raw','imu_calibration','imu_mount']

def can_columns(config):
    from models import signal_columns
    names=signal_columns(config)
    if clash:=set(names)&set(FIELDS):raise ValueError(f'CAN signal name clashes with an SD column: {sorted(clash)}')
    return names

def new_decoder():
    from hardware import HardwareDecoder
    return HardwareDecoder()

def convert(source,target,config=None,decoder=None,mount=None):
    """Pass the same decoder for consecutive files so a value (and the mounting calibration) is not lost at each
    file boundary. mount: a saved calibration (imu_mount.py state) to start from when no decoder is passed.
    Without config and decoder this needs only imu_mount.py next to it (the Web screen's download)."""
    nav=None;gnss_at=None;count=0;can_count=0;last_ms=None;aux=[];obd=ObdAnswers()
    can_path=Path(str(target)+'.can.jsonl')
    import json
    extra=can_columns(config) if config is not None else []
    if config is not None:
        from models import log_value
        if decoder is None:decoder=new_decoder()
    if decoder is not None and decoder.last_ms is not None:last_ms=decoder.last_ms
    if decoder is not None:imu=decoder.mount
    else:
        from imu_mount import ImuMount
        imu=ImuMount()
    if mount and (decoder is None or decoder.last_ms is None):imu.load(mount)
    last_mount=None
    with Path(source).open('rb') as stream,Path(target).open('w',encoding='utf-8',newline='') as output,can_path.open('w',encoding='utf-8') as can:
        writer=csv.DictWriter(output,fieldnames=FIELDS+extra);writer.writeheader()
        for kind,stamp,data in records(stream):
            if last_ms is not None and stamp<last_ms:
                imu.restart()  # MCU restarted: the calibration stays, its short-term sums do not
                if decoder is not None:decoder.can_values.clear();decoder.can_states.clear()  # earlier frames are not current
            last_ms=stamp
            if decoder is not None:decoder.last_ms=stamp
            if kind==2:
                if len(data)!=92:raise ValueError('Invalid GNSS record')
                nav=data;gnss_at=stamp;imu.on_pvt(nav)
                continue
            if kind==3:
                if len(data)<7 or data[6]>8 or len(data)!=7+data[6]:raise ValueError('Invalid CAN record')
                frame={'mcu_ms':stamp,'channel':data[0],'id':struct.unpack_from('<I',data,1)[0],'extended':bool(data[5]&1),'rtr':bool(data[5]&2),'data':data[7:].hex()}
                can.write(json.dumps(frame)+'\n');can_count+=1
                if config is not None:decoder.feed_can([list(frame.values())],config)
                if data[0]==1 and frame['id']==0x7E8 and not data[5]:obd.frame(stamp,data[7:])
                continue
            if kind in (5,6):
                a=gnss_aux(kind,data);a['mcu_ms']=stamp;aux.append(json.dumps(a))
                continue
            if kind==7:obd.sent(stamp,data);continue
            if kind==8:obd.snapshot(stamp,data);continue
            if kind not in (1,4):raise ValueError('Unknown record type')
            row={'mcu_ms':stamp}
            if nav is not None and (stamp-gnss_at)%2**32<1000:
                row.update(GPSFix=nav[20],GPSSats=nav[23],gnss_itow_ms=struct.unpack_from('<I',nav)[0])
                if nav[20]>=3 and nav[21]&1:
                    row.update(Lon=struct.unpack_from('<i',nav,24)[0]*1e-7,Lat=struct.unpack_from('<i',nav,28)[0]*1e-7,Altitude=struct.unpack_from('<i',nav,36)[0]/1000,GPSSpeed=struct.unpack_from('<i',nav,60)[0]*.0036)
            decoded=decoder.can_snapshot(stamp,config)[0] if config is not None else {}
            if extra:row.update((name,log_value(decoded.get(name))) for name in extra)
            if kind==1:
                if len(data)!=46:raise ValueError('Invalid IMU record')
                x=struct.unpack('<22h',data[:44])
                row.update(zip(['AccelX','AccelY','AccelZ'],(v/100 for v in x[:3])))
                row.update(zip(['GyroX','GyroY','GyroZ'],(v/16 for v in x[6:9])))
                row.update(Roll=x[10]/16,Pitch=x[11]/16,imu_raw=data.hex(),imu_calibration=data[45])
                speed=decoded.get('Speed') if isinstance(decoded.get('Speed'),(int,float)) else row.get('GPSSpeed')
                car=imu.add([x[0]/100,x[1]/100,x[2]/100],[x[6]/16,x[7]/16,x[8]/16],speed,stamp)
                if car:row.update(LongAccel=car[0],LatAccel=car[1],VertAccel=car[2])
                state=imu.state()
                if state is not last_mount:row['imu_mount']=json.dumps(state,separators=(',',':'));last_mount=state
            writer.writerow(row);count+=1
    if aux:Path(str(target)+'.gnss.jsonl').write_text('\n'.join(aux)+'\n',encoding='utf-8')
    if obd.lines:Path(str(target)+'.obd.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in obd.lines),encoding='utf-8')
    return {'rows':count,'can_frames':can_count,'gnss_aux':len(aux),'obd':len(obd.lines),'csv':str(target)}

def load_config(path):
    from models import Configuration
    return Configuration.model_validate_json(Path(path).read_text(encoding='utf-8'))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Decode an ELxxxxxx.BIN from the V2 shield SD card')
    parser.add_argument('source',type=Path);parser.add_argument('target',type=Path,nargs='?')
    parser.add_argument('--config',type=Path,help="the logger's config.json (GET /api/config); adds a column per CAN signal")
    parser.add_argument('--mount',type=Path,help="the logger's mounting calibration (GET /api/imu/mount) to start from")
    args=parser.parse_args()
    target=args.target or args.source.with_suffix('.csv')
    if target.exists():raise SystemExit('Output already exists; choose a new filename')
    import json
    mount=json.loads(args.mount.read_text(encoding='utf-8')) if args.mount else None
    print(convert(args.source,target,load_config(args.config) if args.config else None,mount=mount))
