import csv,io,struct,tempfile,unittest,zlib
from pathlib import Path
from sd_decode import FIELDS,convert,records
class SDDecodeTests(unittest.TestCase):
    def block(self):
        b=bytearray(512);b[:4]=b'ELB2';struct.pack_into('<IIH',b,4,1,0,68)
        struct.pack_into('<BBI',b,16,1,46,100);struct.pack_into('<I',b,508,zlib.crc32(b[:508]));return b
    def test_record_and_crc(self):
        b=self.block();self.assertEqual(list(records(io.BytesIO(b))),[(1,100,bytes(46))])
        b[30]^=1
        with self.assertRaisesRegex(ValueError,'CRC'):list(records(io.BytesIO(b)))
    def test_missing_block(self):
        b=self.block();struct.pack_into('<I',b,8,1);struct.pack_into('<I',b,508,zlib.crc32(b[:508]))
        with self.assertRaisesRegex(ValueError,'Missing'):list(records(io.BytesIO(b)))
    def test_partial_block(self):
        with self.assertRaisesRegex(ValueError,'Truncated'):list(records(io.BytesIO(self.block()[:200])))
    def log(self,items):
        """One SD block holding (kind,stamp,payload) records."""
        b=bytearray(512);b[:4]=b'ELB2';pos=16
        for kind,stamp,data in items:
            struct.pack_into('<BBI',b,pos,kind,len(data),stamp);b[pos+6:pos+6+len(data)]=data;pos+=6+len(data)
        struct.pack_into('<IIH',b,4,1,0,pos);struct.pack_into('<I',b,508,zlib.crc32(b[:508]));return bytes(b)
    def can(self,stamp,can_id,payload,channel=2):
        return (3,stamp,bytes([channel])+struct.pack('<I',can_id)+bytes([0,len(payload)])+payload)
    def imu(self,stamp):return (1,stamp,bytes(46))
    def decode(self,items,config=None):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'EL000001.BIN';source.write_bytes(self.log(items))
            convert(source,Path(tmp)/'out.csv',config)
            with open(Path(tmp)/'out.csv',encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
    def test_without_config_columns_are_unchanged(self):
        rows=self.decode([self.can(5,0x600,struct.pack('<hHI',2365,2065,10172)),self.imu(10)])
        self.assertEqual(list(rows[0]),FIELDS)
    def test_config_adds_oil_temperature_and_state_columns(self):
        from models import Configuration,Signal
        config=Configuration(signals=[Signal(name='OilTemp',unit='°C',channel=2,can_id=0x600,byte_offset=0,data_type='int16',scale=.01,conversion='sensorhub_oiltemp'),
                                      Signal(name='RPM',channel=1,can_id=0x201,byte_offset=0,data_type='uint16',endian='big',scale=.25)])
        opened=struct.pack('<hHI',-32768,4094,0xffffffff)
        rows=self.decode([self.imu(0),self.can(5,0x600,struct.pack('<hHI',6016,1700,13000)),self.can(6,0x201,(4000).to_bytes(2,'big')+bytes(6),channel=1),
                          self.can(7,0x201,bytes(8)),  # right ID on the wrong bus is not RPM
                          self.imu(10),self.can(20,0x600,opened),self.imu(30),self.imu(1100)],config)
        self.assertEqual(list(rows[0])[len(FIELDS):],['OilTemp','OilTempState','RPM'])
        self.assertEqual((rows[0]['OilTemp'],rows[0]['OilTempState'],rows[0]['RPM']),('','4',''))   # before any frame
        self.assertAlmostEqual(float(rows[1]['OilTemp']),60.16);self.assertEqual(rows[1]['OilTempState'],'0');self.assertEqual(rows[1]['RPM'],'1000.0')
        self.assertEqual((rows[2]['OilTemp'],rows[2]['OilTempState']),('','1'))                     # open sensor is not a temperature
        self.assertEqual((rows[3]['OilTempState'],rows[3]['RPM']),('4',''))                        # >1 s without a frame
    def test_augmentation_records_go_to_gnss_jsonl(self):
        """SP-7-8: records 5 (NAV-SAT counted) and 6 (NAV-SLAS head) do not stop the decoding and are kept apart."""
        import json
        sat=(5,50,struct.pack('<I5B',345600100,52,31,28,0,27))
        slas=(6,60,struct.pack('<IB3xiiBBBB',345600100,0,140873,38259,7,184,3,24))
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'EL000001.BIN';source.write_bytes(self.log([self.imu(10),sat,slas,self.imu(70)]))
            out=convert(source,Path(tmp)/'out.csv')
            self.assertEqual((out['rows'],out['gnss_aux']),(2,2))
            lines=[json.loads(x) for x in (Path(tmp)/'out.csv.gnss.jsonl').read_text(encoding='utf-8').splitlines()]
        self.assertEqual(lines[0],{'kind':'sat','itow_ms':345600100,'svs':52,'used':31,'diff':28,'sbas':0,'slas':27,'mcu_ms':50})
        self.assertEqual(lines[1],{'kind':'slas','itow_ms':345600100,'gms_lon':140.873,'gms_lat':38.259,'gms_code':7,'qzss_sv':184,
                                   'gms_available':True,'qzss_available':True,'test_mode':False,'corrections':24,'mcu_ms':60})
    def test_no_gnss_jsonl_without_augmentation_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'EL000001.BIN';source.write_bytes(self.log([self.imu(10)]))
            self.assertEqual(convert(source,Path(tmp)/'out.csv')['gnss_aux'],0)
            self.assertFalse((Path(tmp)/'out.csv.gnss.jsonl').exists())
    def test_obd_records_and_answers_go_to_obd_jsonl(self):
        """SP-11: records 7 (sent) and 8 (snapshot) are accepted; 0x7E8 frames on CAN1 are put back together and decoded."""
        import json
        pad=lambda b:bytes(b)+b'\x55'*(8-len(b))
        items=[(8,90,b'\x02'),(7,100,bytes([0xe0,7])+pad([2,1,0])),self.can(102,0x7E8,pad([6,0x41,0,0x98,0x3b,0x80,0x13]),channel=1),
               (7,110,bytes([0xe0,7])+pad([2,1,0x10])),self.can(112,0x7E8,pad([4,0x41,0x10,0x01,0x2c]),channel=1),
               self.can(113,0x7E8,pad([3,0x41,0x06,0x80]),channel=2),   # same id on the other bus is not the ECU
               self.can(114,0x7E8,pad([3,0x41,0x07,0x7a]),channel=1),
               self.can(120,0x7E8,bytes([0x10,0x08,0x43,0x03,0x01,0x01,0x01,0x02]),channel=1),(7,121,bytes([0xe0,7])+pad([0x30,0,0])),
               self.can(123,0x7E8,pad([0x21,0x01,0x03]),channel=1),
               self.can(130,0x7E8,bytes([0x10,0x13,0x49,0x04,0x01])+b'ABC',channel=1),self.can(132,0x7E8,b'\x21DEFGHIJ',channel=1),
               self.can(133,0x7E8,b'\x22KLMNOP\x00',channel=1),self.can(140,0x7E8,pad([3,0x7f,1,0x12]),channel=1),self.imu(150)]
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'EL000001.BIN';source.write_bytes(self.log(items))
            out=convert(source,Path(tmp)/'out.csv')
            lines=[json.loads(x) for x in (Path(tmp)/'out.csv.obd.jsonl').read_text(encoding='utf-8').splitlines()]
        self.assertEqual((out['rows'],out['can_frames'],out['obd']),(1,10,10))
        self.assertEqual(lines[0],{'kind':'snapshot','mcu_ms':90,'reason':'bus_alive'})
        self.assertEqual(lines[1],{'kind':'sent','mcu_ms':100,'id':0x7e0,'data':'0201005555555555'})
        self.assertEqual(lines[2]['supported'],[1,4,5,11,12,13,15,16,17,28,31,32])
        self.assertEqual((lines[4]['name'],lines[4]['unit'],lines[4]['value']),('maf','g/s',3.0))
        self.assertEqual((lines[5]['name'],lines[5]['value']),('ltft1',-4.688))
        self.assertEqual(lines[6]['data'],'3000005555555555')
        self.assertEqual((lines[7]['mcu_ms'],lines[7]['dtc']),(120,['P0101','P0102','P0103']))  # stamped with the first frame
        self.assertEqual(lines[8]['calid'],'ABCDEFGHIJKLMNOP')
        self.assertEqual((lines[9]['service'],lines[9]['raw']),(0x7f,'7f0112'))
    def test_no_obd_jsonl_without_obd_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'EL000001.BIN';source.write_bytes(self.log([self.imu(10),self.can(12,0x7E8,bytes(8),channel=2)]))
            self.assertEqual(convert(source,Path(tmp)/'out.csv')['obd'],0);self.assertFalse((Path(tmp)/'out.csv.obd.jsonl').exists())
    def test_bad_augmentation_record_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'EL000001.BIN';source.write_bytes(self.log([(5,1,bytes(8))]))
            with self.assertRaisesRegex(ValueError,'NAV-SAT'):convert(source,Path(tmp)/'out.csv')
    def test_mcu_restart_drops_previous_values(self):
        from models import Configuration,Signal
        config=Configuration(signals=[Signal(name='Boost',channel=2,can_id=0x500,byte_offset=0,data_type='uint8')])
        rows=self.decode([self.can(5000,0x500,bytes([7])),self.imu(5010),self.imu(20)],config)
        self.assertEqual([r['Boost'] for r in rows],['7',''])
    def test_shared_decoder_carries_values_across_files(self):
        from models import Configuration,Signal
        from sd_decode import new_decoder
        config=Configuration(signals=[Signal(name='OilTemp',unit='°C',channel=2,can_id=0x600,byte_offset=0,data_type='int16',scale=.01,conversion='sensorhub_oiltemp')])
        decoder=new_decoder()
        with tempfile.TemporaryDirectory() as tmp:
            for n,items in enumerate(([self.can(5,0x600,struct.pack('<hHI',6016,1700,13000)),self.imu(10)],[self.imu(110)])):
                source=Path(tmp)/f'EL{n:06}.BIN';source.write_bytes(self.log(items));convert(source,Path(tmp)/f'{n}.csv',config,decoder)
            with open(Path(tmp)/'1.csv',encoding='utf-8',newline='') as f:row=next(csv.DictReader(f))
        self.assertEqual((row['OilTemp'],row['OilTempState']),('60.16','0'))   # rounded, and still fresh in the next file
    def test_signal_name_must_not_hide_an_sd_column(self):
        from models import Configuration,Signal
        with self.assertRaisesRegex(ValueError,'clashes'):self.decode([self.imu(0)],Configuration(signals=[Signal(name='GPSSpeed',can_id=0x100,byte_offset=0)]))
if __name__=='__main__':unittest.main()
