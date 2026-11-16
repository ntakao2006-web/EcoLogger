// UBX frames from the receiver, fed one byte at a time (SP-7-8). Keeps the first 100 bytes of a frame
// (NAV-PVT is exactly 100); longer frames such as NAV-SAT and NAV-SLAS are followed to their checksum
// without being stored. For NAV-SAT the satellites are counted on the way (u-blox M10 SPG 5.10, 3.15.13):
// sat[0] used for navigation, sat[1] used and with differential correction data, sat[2] used with SBAS
// corrections, sat[3] used with QZSS SLAS corrections. No allocation, no library calls: tested on the PC
// in tests/test_ubx_parse.cpp.
struct UbxParser {
 uint8_t f[100],sat[4],a=0,c=0,ka=0,used=0;unsigned pos=0,len=0;
 // true when a frame ends with a good checksum: f[2] class, f[3] id, f+6 the stored payload, len the frame length
 bool feed(uint8_t v){
  if(pos==0&&v!=0xb5)return false;
  if(pos==1&&v!=0x62){pos=v==0xb5;return false;}
  if(pos<sizeof(f))f[pos]=v;
  if(pos==2){a=c=0;sat[0]=sat[1]=sat[2]=sat[3]=0;}
  if(pos>=2&&(pos<6||pos+2<len)){a+=v;c+=a;}
  if(pos==5){len=6+f[4]+(f[5]<<8)+2;if(len>1032){pos=0;return false;}}
  if(pos>=14&&pos+2<len&&f[2]==1&&f[3]==0x35){unsigned r=(pos-14)%12;
   if(r==8){used=v>>3&1;sat[0]+=used;sat[1]+=used&(v>>6);}else if(r==10&&used){sat[2]+=v&1;sat[3]+=v>>2&1;}}
  if(pos>=6&&pos+2==len)ka=v;
  if(++pos<7||pos<len)return false;
  pos=0;return a==ka&&c==v;
 }
};
