// OBD queries to the car's ECU on CAN1 (SP-11, SPEC.md G-5, 2026-11-17).
// Only read-only OBD requests ever leave this logger: mode 01 (current data), 03 (stored DTCs), 07 (pending
// DTCs) and 09 (vehicle information, never PID 02 = VIN: G-8) to 0x7E0 (0x7DF allowed), plus the ISO-TP flow
// control (30 00 00) that lets 0x7E8 send a multi-frame answer. obdAllowed() is the single check, made on every
// frame just before it is handed to the hardware; anything else is dropped and counted (obdRejected).
// A snapshot reads every PID the ECU says it supports (0100/0120/0140/0160, then each set bit), mode 03 and 07,
// and mode 09 (0900, then each set bit except 02). It runs when the bus comes alive and whenever a new SD file
// starts. Between snapshots 03 (fuel system status), 06/07 (fuel trims) and 10 (MAF) are read in turn, one
// every 250 ms, if supported. Answers are not decoded here: every 0x7E8 frame is already kept as a CAN record
// (type 3) and the PC decodes them (EcoCapture-Web/sd_decode.py). Sent frames go to SD as type 7, the start of
// a snapshot as type 8. No allocation, no library calls: tested on the PC in tests/test_obd_query.cpp.
static bool obdHwSend(uint32_t id,const uint8_t*d);
static bool obdAllowed(uint32_t id,const uint8_t*d){
 unsigned n;
 if(d[0]==0x30){if(id!=0x7e0||d[1]||d[2])return false;n=3;}
 else{if(id!=0x7e0&&id!=0x7df)return false;uint8_t m=d[1];
  if(d[0]==1&&(m==3||m==7))n=2;else if(d[0]==2&&(m==1||(m==9&&d[2]!=2)))n=3;else return false;}
 for(;n<8;n++)if(d[n]!=0x55)return false;
 return true;
}
static uint32_t obdSent=0,obdRejected=0,obdSnapshots=0;
static bool obdSend(uint32_t id,uint8_t len,uint8_t mode,uint8_t pid,uint32_t now){
 uint8_t r[10]={(uint8_t)id,(uint8_t)(id>>8),len,mode,pid,0x55,0x55,0x55,0x55,0x55};
 if(len==1)r[4]=0x55;
 if(!obdAllowed(id,r+2)){obdRejected++;return false;}
 if(!obdHwSend(id,r+2))return false;
 obdSent++;sdRecord(7,now,r,10);return true;
}
struct Obd {
 uint32_t mask[4]={0,0,0,0},mask9=0,at=0,file=0;
 uint16_t cur=0xffff;            // snapshot position: 0x000-0x07f mode 01 PID, 0x100/0x101 mode 03/07, 0x200-0x21f mode 09 PID; 0xffff none
 uint8_t wait=0,mode=0,pid=0,turn=0;  // wait: 0 free, 1 single frame expected, 2 multi-frame running
 static bool supp(uint32_t m,unsigned p){return p&&p<=32&&(m>>(32-p)&1);}   // bit for PID p (1..32) of a support mask
 bool has(unsigned p){return p&&p<=128&&supp(mask[(p-1)/32],(p-1)%32+1);}
 bool wanted(unsigned c){
  if(c<0x80)return c%32?has(c):(c==0||has(c));
  if(c==0x100||c==0x101)return true;
  unsigned p=c-0x200;return p==0||(p!=2&&supp(mask9,p));
 }
 void start(uint32_t now,uint32_t f,uint8_t why){file=f;cur=0;mask[0]=mask[1]=mask[2]=mask[3]=mask9=0;obdSnapshots++;sdRecord(8,now,&why,1);}
 // One step: call often (every loop). alive: the car's frames are being received and sending is allowed.
 void tick(uint32_t now,bool alive){
  if(wait==1&&now-at>60)wait=0;          // no answer: unsupported or the ECU is busy
  if(wait==2&&now-at>100)wait=0;         // the multi-frame answer has ended (or stalled)
  if(wait||!alive||now-at<10)return;
  if(cur!=0xffff){
   while(cur<0x220&&!wanted(cur))cur=cur==0x7f?0x100:cur==0x101?0x200:cur+1;
   if(cur>=0x220){cur=0xffff;return;}
   unsigned c=cur;cur=c==0x7f?0x100:c==0x101?0x200:c+1;
   if(c<0x80)ask(now,1,c);else if(c<0x200)ask(now,c==0x100?3:7,0);else ask(now,9,c-0x200);
   return;
  }
  static const uint8_t keep[4]={0x03,0x06,0x07,0x10};
  if(now-at<250)return;
  uint8_t p=keep[turn++&3];if(has(p))ask(now,1,p);else at=now;
 }
 void ask(uint32_t now,uint8_t m,uint8_t p){mode=m;pid=p;at=now;wait=obdSend(0x7e0,m==3||m==7?1:2,m,p,now)?1:0;}
 // A frame from 0x7E8 (standard id).
 void rx(const uint8_t*d,int n,uint32_t now){
  if(!wait||n<1)return;
  uint8_t pci=d[0]>>4;
  if(pci==1&&wait==1&&n>=3&&d[2]==(mode|0x40)){if(obdSend(0x7e0,0x30,0,0,now)){wait=2;at=now;}else wait=0;return;}
  if(pci==2&&wait==2){at=now;return;}
  if(pci||wait!=1||n<2)return;
  if(d[1]==0x7f){wait=0;return;}
  if(d[1]!=(mode|0x40))return;
  if(n>=7&&d[0]>=6&&d[2]==pid&&pid%32==0){uint32_t m=(uint32_t)d[3]<<24|(uint32_t)d[4]<<16|d[5]<<8|d[6];if(mode==1&&pid<128)mask[pid/32]=m;else if(mode==9&&!pid)mask9=m;}
  wait=0;
 }
};
