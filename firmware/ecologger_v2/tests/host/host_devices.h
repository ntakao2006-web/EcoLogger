// Fake devices for the replay (SP-7-9): BNO055 and MAX-M10M on I2C, FDCAN1 registers and message RAM,
// MCP25625 and the SD card on the bit-banged SPI (GPIOB), and the LED shift register. Input events
// (replay.cpp) reach them at their own virtual time. Each device counts what went wrong on its side.
#pragma once
#include <unordered_map>

namespace host {
struct Event { uint8_t kind; uint64_t us; std::vector<uint8_t> data; };
enum { EV_IMU = 1, EV_IMU_FAIL = 4, EV_GNSS = 20, EV_NAV_SAT = 21, EV_NAV_SLAS = 22, EV_CAN1 = 31, EV_CAN2 = 32 };
inline std::vector<Event> events;
inline size_t nextEvent = 0;
inline std::vector<std::string> problems;  // device-side protocol errors, the first few kept
inline uint64_t problemCount = 0;
inline void problem(const std::string &what) {
  problemCount++;
  if (problems.size() < 20) problems.push_back(what + " at " + std::to_string(nowUs) + " us");
}

// ---- BNO055 (0x28) -----------------------------------------------------------------------------------
// A burst read of the 46 data registers returns the latest replayed sample. A replayed "read failed"
// (SD record 4) makes the next burst read fail once. Every burst read is logged, as SD records, so the
// test can compare what the firmware was given with what it stored; bit 7 of the kind marks a read made
// while the firmware was not recording (logger_impl.h `recording`, after LOG0), which is not stored.
struct Bno055 {
  uint8_t regs[128] = {};
  uint8_t sample[46] = {};
  unsigned pendingFails = 0;
  uint64_t reads = 0, fails = 0;
  std::vector<uint8_t> served;  // kind, length, ms (LE), data: the SD record format
  Bno055() { regs[0] = 0xa0; }
  void log(uint8_t kind, const uint8_t *b, int n) {
    uint32_t ms = (uint32_t)(nowUs / 1000);
    served.push_back((uint8_t)(kind | (recording ? 0 : 0x80))); served.push_back((uint8_t)n);
    for (int i = 0; i < 4; i++) served.push_back((uint8_t)(ms >> (8 * i)));
    served.insert(served.end(), b, b + n);
  }
  int read(uint8_t reg, uint8_t *b, uint32_t n) {
    if (reg == 8 && n == 46) {
      reads++;
      if (pendingFails) { pendingFails--; fails++; log(4, nullptr, 0); return -EIO; }
      memcpy(b, sample, 46); log(1, sample, 46); return 0;
    }
    if (reg + n > sizeof(regs)) { problem("BNO055 read past the register map"); return -EIO; }
    memcpy(b, regs + reg, n); return 0;
  }
  int write(uint8_t reg, uint8_t v) { if (reg >= sizeof(regs)) return -EIO; if (reg) regs[reg] = v; return 0; }
};
inline Bno055 bno;

// ---- MAX-M10M (0x42, DDC) ---------------------------------------------------------------------------
// 0xfd/0xfe: bytes waiting (big endian); 0xff: the stream (0xff when empty). Writes are UBX CFG frames.
// Like the receiver, NAV-SAT and NAV-SLAS come out only once the firmware asks for them on I2C
// (CFG-VALSET CFG-MSGOUT-UBX_NAV_SAT_I2C 0x20910015, ..._NAV_SLAS_I2C 0x20910336): older firmware does not.
struct Gnss {
  std::deque<uint8_t> out;
  uint64_t bytesIn = 0, bytesRead = 0, configOk = 0, configBad = 0, auxSkipped = 0;
  bool satOn = false, slasOn = false;
  void valset(const uint8_t *p, uint32_t n) {
    for (uint32_t i = 4; i + 4 <= n;) {
      uint32_t key = p[i] | p[i + 1] << 8 | p[i + 2] << 16 | (uint32_t)p[i + 3] << 24; i += 4;
      static const uint32_t sizes[8] = {0, 1, 1, 2, 4, 8, 0, 0};
      uint32_t size = sizes[(key >> 28) & 7], v = 0;
      if (!size || i + size > n) { problem("GNSS CFG-VALSET item that cannot be read"); return; }
      for (uint32_t k = 0; k < size && k < 4; k++) v |= (uint32_t)p[i + k] << (8 * k);
      i += size;
      if (key == 0x20910015) satOn = v != 0;
      if (key == 0x20910336) slasOn = v != 0;
    }
  }
  int read(uint8_t reg, uint8_t *b, uint32_t n) {
    if (reg == 0xfd && n == 2) { size_t a = std::min<size_t>(out.size(), 0xffff); b[0] = (uint8_t)(a >> 8); b[1] = (uint8_t)a; return 0; }
    if (reg == 0xff) {
      for (uint32_t i = 0; i < n; i++) { if (out.empty()) b[i] = 0xff; else { b[i] = out.front(); out.pop_front(); bytesRead++; } }
      return 0;
    }
    problem("GNSS read of register " + std::to_string(reg)); return -EIO;
  }
  int write(const uint8_t *b, uint32_t n) {
    bool ok = n >= 8 && b[0] == 0xb5 && b[1] == 0x62 && 8u + (b[4] | (b[5] << 8)) == n;
    if (ok) { uint8_t x = 0, y = 0; for (uint32_t i = 2; i < n - 2; i++) { x += b[i]; y += x; } ok = x == b[n - 2] && y == b[n - 1]; }
    if (ok) { configOk++; if (b[2] == 6 && b[3] == 0x8a) valset(b + 6, n - 8); }
    else { configBad++; problem("GNSS config frame with a bad length or checksum"); }
    return 0;
  }
};
inline Gnss gnss;

inline int i2cBurstRead(uint16_t addr, uint8_t reg, uint8_t *b, uint32_t n) {
  if (addr == 0x28) return bno.read(reg, b, n);
  if (addr == 0x42) return gnss.read(reg, b, n);
  return -EIO;  // nothing at 0x29
}
inline int i2cRegWrite(uint16_t addr, uint8_t reg, uint8_t v) { return addr == 0x28 ? bno.write(reg, v) : -EIO; }
inline int i2cWrite(uint16_t addr, const uint8_t *b, uint32_t n) { return addr == 0x42 ? gnss.write(b, n) : -EIO; }

// ---- FDCAN1 RX FIFO 0: three elements of 72 bytes at message RAM offset 176 ---------------------------
struct Fdcan {
  unsigned get = 0, put = 0, fill = 0;
  uint64_t delivered = 0, lost = 0, whileInit = 0, notListenOnly = 0, badAck = 0;
  void deliver(const std::vector<uint8_t> &d) {  // id u32, flags (ext | rtr << 1), n, data
    uint32_t id; memcpy(&id, d.data(), 4); bool ext = d[4] & 1, rtr = d[4] & 2; unsigned n = d[5];
    if (fdcan1.CCCR.v & FDCAN_CCCR_INIT) { whileInit++; return; }
    if (!(fdcan1.CCCR.v & FDCAN_CCCR_MON)) notListenOnly++;
    if (fill == 3) { fdcan1.IR.v |= FDCAN_IR_RF0L; lost++; return; }
    uint32_t w[4] = {0, 0, 0, 0};
    w[0] = (ext ? (id & 0x1fffffff) | (1UL << 30) : (id & 0x7ff) << 18) | (rtr ? 1UL << 29 : 0);
    w[1] = (uint32_t)n << 16;
    for (unsigned i = 0; i < n && i < 8; i++) w[2 + i / 4] |= (uint32_t)d[6 + i] << (8 * (i % 4));
    memcpy(sramCan + 176 + put * 72, w, sizeof(w));
    put = (put + 1) % 3; fill++; delivered++;
  }
};
inline Fdcan can1;
inline uint32_t rxf0sRead(HostReg &) { return can1.fill | (can1.get << 8) | (can1.put << 16) | (can1.fill == 3 ? 1UL << 24 : 0); }
inline void rxf0aWrite(HostReg &r, uint32_t v) {
  r.v = v;
  if (!can1.fill || v != can1.get) { can1.badAck++; problem("FDCAN RXF0A acknowledges an element that is not the oldest"); return; }
  can1.get = (can1.get + 1) % 3; can1.fill--;
}
inline void irWrite(HostReg &r, uint32_t v) { r.v &= ~v; }  // write 1 to clear

// ---- SPI devices -----------------------------------------------------------------------------------
struct SpiDevice {
  virtual uint8_t nextOut() = 0;          // the byte this device drives on MISO for the next exchange
  virtual void receive(uint8_t b) = 0;    // the byte the MCU sent in that exchange
  virtual void select() {}
  virtual void deselect() {}
  virtual ~SpiDevice() {}
};

// MCP25625 (CAN2): RESET, READ, WRITE, BIT MODIFY and READ RX BUFFER; two receive buffers with rollover.
struct Mcp25625 : SpiDevice {
  uint8_t regs[128] = {};
  enum { IDLE, W_ADDR, W_DATA, R_ADDR, READ, B_ADDR, B_MASK, B_DATA, DONE } state = IDLE;
  uint8_t addr = 0, mask = 0; int clearOnDeselect = -1;
  uint64_t delivered = 0, overflow = 0, notReady = 0, resets = 0;
  Mcp25625() { reset(); }
  void reset() { memset(regs, 0, sizeof(regs)); regs[0x0e] = 0x80; regs[0x0f] = 0x87; resets++; }
  unsigned mode() const { return regs[0x0e] >> 5; }
  void writeReg(uint8_t a, uint8_t v) {
    a &= 0x7f; regs[a] = v;
    if (a == 0x0f) regs[0x0e] = (uint8_t)((regs[0x0e] & 0x1f) | (v & 0xe0));  // mode change takes effect at once
  }
  uint8_t nextOut() override { return state == READ ? regs[addr & 0x7f] : 0xff; }
  void receive(uint8_t b) override {
    switch (state) {
      case IDLE:
        if (b == 0xc0) { reset(); state = DONE; }
        else if (b == 0x02) state = W_ADDR;
        else if (b == 0x03) state = R_ADDR;
        else if (b == 0x05) state = B_ADDR;
        else if ((b & 0xf9) == 0x90) { unsigned n = (b >> 2) & 1; addr = (uint8_t)((n ? 0x71 : 0x61) + ((b & 2) ? 5 : 0)); clearOnDeselect = (int)n; state = READ; }
        else { problem("MCP25625 command " + std::to_string(b)); state = DONE; }
        break;
      case W_ADDR: addr = b; state = W_DATA; break;
      case W_DATA: writeReg(addr++, b); break;
      case R_ADDR: addr = b; state = READ; break;
      case READ: addr++; break;
      case B_ADDR: addr = b; state = B_MASK; break;
      case B_MASK: mask = b; state = B_DATA; break;
      case B_DATA: writeReg(addr, (uint8_t)((regs[addr & 0x7f] & ~mask) | (b & mask))); state = DONE; break;
      case DONE: break;
    }
  }
  void deselect() override {
    if (clearOnDeselect >= 0) regs[0x2c] &= (uint8_t)~(1 << clearOnDeselect);
    clearOnDeselect = -1; state = IDLE;
  }
  void deliver(const std::vector<uint8_t> &d) {
    uint32_t id; memcpy(&id, d.data(), 4); bool ext = d[4] & 1, rtr = d[4] & 2; unsigned n = d[5];
    if (mode() != 0) { notReady++; return; }  // normal mode only (CAN2 ACKs the sensor hub)
    int buf;
    if (!(regs[0x2c] & 1)) buf = 0;
    else if ((regs[0x60] & 0x04) && !(regs[0x2c] & 2)) buf = 1;
    else { regs[0x2d] |= (regs[0x60] & 0x04) ? 0x80 : 0x40; overflow++; return; }
    uint8_t *r = regs + (buf ? 0x61 + 0x10 : 0x61);
    if (ext) { uint32_t sid = id >> 18; r[0] = (uint8_t)(sid >> 3); r[1] = (uint8_t)(((sid & 7) << 5) | 0x08 | ((id >> 16) & 3)); r[2] = (uint8_t)(id >> 8); r[3] = (uint8_t)id; }
    else { r[0] = (uint8_t)(id >> 3); r[1] = (uint8_t)(((id & 7) << 5) | (rtr ? 0x10 : 0)); r[2] = r[3] = 0; }
    r[4] = (uint8_t)(n | (ext && rtr ? 0x40 : 0));  // DLC; the RTR bit here is valid for extended frames only
    for (unsigned i = 0; i < 8; i++) r[5 + i] = i < n ? d[6 + i] : 0;
    regs[0x2c] |= (uint8_t)(1 << buf); delivered++;
  }
};
inline Mcp25625 mcp;

// SD card in SPI mode (SDHC: block addresses). The card keeps sectors in a sparse map. After a block
// write it stays busy (MISO low) for busyUs, or for the stall time while the replay asks for one.
struct SdCard : SpiDevice {
  uint32_t sectors = 0;
  std::unordered_map<uint32_t, std::array<uint8_t, 512>> data;
  enum { IDLE, CMD, WAIT_TOKEN, DATA } state = IDLE;
  std::vector<uint8_t> cmd, block;
  std::deque<uint8_t> out;
  bool idle = true, appCmd = false; int initTries = 0;
  uint32_t writeLba = 0;
  uint64_t busyUntil = 0, busyUs = 200, reads = 0, writes = 0, maxBusyUs = 0;
  struct Stall { uint64_t from, to, us; };
  std::vector<Stall> stalls;
  const uint8_t *sector(uint32_t lba) { static const uint8_t zero[512] = {}; auto i = data.find(lba); return i == data.end() ? zero : i->second.data(); }
  void put(uint32_t lba, const uint8_t *b) { auto &s = data[lba]; memcpy(s.data(), b, 512); }
  bool busy() const { return nowUs < busyUntil; }
  uint8_t nextOut() override {
    if (!out.empty()) { uint8_t v = out.front(); out.pop_front(); return v; }
    return busy() ? 0x00 : 0xff;
  }
  void respond(std::initializer_list<uint8_t> r) { out.push_back(0xff); out.insert(out.end(), r); }
  void execute() {
    uint8_t c = cmd[0] & 0x3f; uint32_t arg = (uint32_t)cmd[1] << 24 | cmd[2] << 16 | cmd[3] << 8 | cmd[4];
    if (busy()) { problem("SD command " + std::to_string(c) + " while the card is busy"); return; }
    out.clear();
    bool app = appCmd; appCmd = false;
    if (c == 0) { if (cmd[5] != 0x95) problem("SD CMD0 CRC"); idle = true; initTries = 0; respond({0x01}); return; }
    if (c == 8) { if (cmd[5] != 0x87) problem("SD CMD8 CRC"); respond({(uint8_t)(idle ? 1 : 0), 0, 0, (uint8_t)((arg >> 8) & 15), (uint8_t)arg}); return; }
    if (c == 55) { appCmd = true; respond({(uint8_t)(idle ? 1 : 0)}); return; }
    if (c == 41 && app) { if (++initTries >= 2 && (arg & 0x40000000)) idle = false; respond({(uint8_t)(idle ? 1 : 0)}); return; }
    if (c == 58) { respond({(uint8_t)(idle ? 1 : 0), 0xc0, 0xff, 0x80, 0x00}); return; }
    if (idle) { problem("SD command " + std::to_string(c) + " before initialisation"); respond({0x05}); return; }
    if (c == 17) {
      if (arg >= sectors) { respond({0x40}); return; }
      reads++; respond({0x00}); out.push_back(0xff); out.push_back(0xfe);
      const uint8_t *s = sector(arg); out.insert(out.end(), s, s + 512); out.push_back(0xff); out.push_back(0xff);
      return;
    }
    if (c == 24) { if (arg >= sectors) { respond({0x40}); return; } writeLba = arg; respond({0x00}); state = WAIT_TOKEN; return; }
    problem("SD unsupported command " + std::to_string(c)); respond({0x04});
  }
  void receive(uint8_t b) override {
    if (state == WAIT_TOKEN) {
      if (b == 0xfe) { state = DATA; block.clear(); }
      else if (b != 0xff) { problem("SD bad data token"); state = IDLE; }
      return;
    }
    if (state == DATA) {
      block.push_back(b);
      if (block.size() < 514) return;
      put(writeLba, block.data()); writes++; state = IDLE;
      uint64_t us = busyUs;
      for (auto &s : stalls) if (nowUs >= s.from && nowUs < s.to) us = std::max(us, s.us);
      maxBusyUs = std::max(maxBusyUs, us);
      out.clear(); out.push_back(0x05); busyUntil = nowUs + us;
      return;
    }
    if (state == CMD) { cmd.push_back(b); if (cmd.size() == 6) { state = IDLE; execute(); } return; }
    if ((b & 0xc0) == 0x40) { cmd.assign(1, b); state = CMD; }
  }
  void deselect() override {
    if (state == CMD || state == DATA) problem("SD chip select raised in the middle of a transfer");
    state = IDLE; out.clear(); cmd.clear();
  }
};
inline SdCard sd;

// 74HC595 behind the SPI: bytes clocked with no chip select, latched on D7.
inline uint8_t ledShift = 0, ledLatched = 0;
inline uint64_t ledLatches = 0;
struct LedShift : SpiDevice {
  uint8_t nextOut() override { return 0xff; }
  void receive(uint8_t b) override { ledShift = b; }
};
inline LedShift leds595;

// Bit-banged SPI on GPIOB: PB13 SCK, PB14 MISO (read), PB15 MOSI. The device is picked at each byte's
// first rising edge from the chip selects (D10 MCP25625, A4 SD card, neither: the LED shift register).
struct Spi { int bit = 0; uint8_t in = 0, outByte = 0xff; bool sck = false, mosi = false; SpiDevice *dev = nullptr; uint64_t bytes = 0; };
inline Spi spi;
inline void bsrrWrite(HostReg &, uint32_t v) {
  if (v & (1UL << 15)) spi.mosi = true;
  if (v & (1UL << 31)) spi.mosi = false;
  if ((v & (1UL << 13)) && !spi.sck) {  // rising edge: the MCU samples MISO after this, then reads IDR
    spi.sck = true;
    if (spi.bit == 0) {
      bool mcpSel = !pins[D10], sdSel = !pins[A4];
      if (mcpSel && sdSel) problem("two SPI chip selects low");
      spi.dev = mcpSel ? (SpiDevice *)&mcp : sdSel ? (SpiDevice *)&sd : (SpiDevice *)&leds595;
      spi.outByte = spi.dev->nextOut(); spi.in = 0;
    }
    spi.in = (uint8_t)((spi.in << 1) | (spi.mosi ? 1 : 0));
  }
  if ((v & (1UL << 29)) && spi.sck) {
    spi.sck = false;
    if (++spi.bit == 8) { spi.bit = 0; spi.bytes++; spi.dev->receive(spi.in); }
  }
}
inline uint32_t idrRead(HostReg &) { return ((spi.outByte >> (7 - spi.bit)) & 1) ? 1UL << 14 : 0; }

inline void pinChanged(int pin, int, int now) {
  if (spi.bit) problem("chip select changed in the middle of an SPI byte");
  if (pin == D10) { if (now) mcp.deselect(); else mcp.select(); }
  if (pin == A4) { if (now) sd.deselect(); else sd.select(); }
  if (pin == D7 && now) { ledLatched = ledShift; ledLatches++; }
}

// ---- events and the clock ----------------------------------------------------------------------------
inline uint64_t devicesNextUs() { return nextEvent < events.size() ? events[nextEvent].us : NEVER; }
inline uint64_t eventsApplied[64];
inline void devicesAdvance(uint64_t us) {
  while (nextEvent < events.size() && events[nextEvent].us <= us) {
    Event &e = events[nextEvent++];
    eventsApplied[e.kind & 63]++;
    switch (e.kind) {
      case EV_IMU: memcpy(bno.sample, e.data.data(), 46); break;
      case EV_IMU_FAIL: bno.pendingFails++; break;
      case EV_NAV_SAT: case EV_NAV_SLAS:
        if (!(e.kind == EV_NAV_SAT ? gnss.satOn : gnss.slasOn)) { gnss.auxSkipped++; break; }
        [[fallthrough]];
      case EV_GNSS: gnss.out.insert(gnss.out.end(), e.data.begin(), e.data.end()); gnss.bytesIn += e.data.size(); break;
      case EV_CAN1: can1.deliver(e.data); break;
      case EV_CAN2: mcp.deliver(e.data); break;
      default: problem("unknown replay event " + std::to_string(e.kind));
    }
  }
}

inline void hookRegisters() {
  pins[D10] = pins[A4] = 1;
  gpioB.BSRR.wr = bsrrWrite; gpioB.IDR.rd = idrRead;
  fdcan1.RXF0S.rd = rxf0sRead; fdcan1.RXF0A.wr = rxf0aWrite; fdcan1.IR.wr = irWrite;
}

// A blank FAT32 card: MBR with one partition at 8192, a volume label in the root directory, and
// otherFiles empty files after it (OTHERnnn.TXT, no clusters), so the root directory's one cluster can be
// nearly full and has to grow while the firmware makes its files (the 2026-11-11 fix in sd_logger.h).
inline void formatCard(uint32_t totalSectors, uint8_t clusterSectors, unsigned otherFiles = 0) {
  sd.sectors = totalSectors; sd.data.clear();
  const uint32_t part = 8192, size = totalSectors - part, reserved = 32;
  uint32_t clusters = (size - reserved) / clusterSectors, fat = 0;
  for (int i = 0; i < 4; i++) { fat = ((clusters + 2) * 4 + 511) / 512; clusters = (size - reserved - 2 * fat) / clusterSectors; }
  uint8_t b[512] = {};
  auto p32 = [](uint8_t *p, uint32_t v) { for (int i = 0; i < 4; i++) p[i] = (uint8_t)(v >> (8 * i)); };
  b[446 + 4] = 0x0c; p32(b + 446 + 8, part); p32(b + 446 + 12, size); b[510] = 0x55; b[511] = 0xaa; sd.put(0, b);
  memset(b, 0, 512);
  b[0] = 0xeb; b[1] = 0x58; b[2] = 0x90; memcpy(b + 3, "MSWIN4.1", 8);
  b[12] = 2; b[13] = clusterSectors; b[14] = reserved; b[16] = 2; b[21] = 0xf8; b[24] = 63; b[26] = 255;
  p32(b + 28, part); p32(b + 32, size); p32(b + 36, fat); p32(b + 44, 2); b[48] = 1; b[50] = 6;
  b[64] = 0x80; b[66] = 0x29; p32(b + 67, 0x20261117); memcpy(b + 71, "ECOLOGGER  ", 11); memcpy(b + 82, "FAT32   ", 8);
  b[510] = 0x55; b[511] = 0xaa; sd.put(part, b); sd.put(part + 6, b);
  uint8_t fs[512] = {}; p32(fs, 0x41615252); p32(fs + 484, 0x61417272); p32(fs + 488, clusters - 1); p32(fs + 492, 3); fs[510] = 0x55; fs[511] = 0xaa;
  sd.put(part + 1, fs); sd.put(part + 7, fs);
  uint8_t f[512] = {}; p32(f, 0x0ffffff8); p32(f + 4, 0x0fffffff); p32(f + 8, 0x0fffffff);
  sd.put(part + reserved, f); sd.put(part + reserved + fat, f);
  if (otherFiles + 1 > clusterSectors * 16u) fatal("more other files than the root directory cluster holds");
  for (unsigned s = 0; s < clusterSectors; s++) {
    uint8_t root[512] = {};
    for (unsigned e = 0; e < 16; e++) {
      unsigned slot = s * 16 + e; uint8_t *p = root + e * 32;
      if (slot == 0) memcpy(p, "ECOLOGGER  \x08", 12);
      else if (slot <= otherFiles) { char n[12]; snprintf(n, sizeof(n), "OTHER%03uTXT", slot); memcpy(p, n, 11); p[11] = 0x20; }
    }
    sd.put(part + reserved + 2 * fat + s, root);
  }
}
}  // namespace host
