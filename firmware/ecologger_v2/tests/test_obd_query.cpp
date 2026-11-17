// PC test of obd_query.h (SP-11, 2026-11-17): only the allowed OBD requests can leave, and a snapshot reads
// every PID the (fake) ECU says it supports, mode 03/07 and mode 09 without the VIN.
// Built with g++ in WSL:
//   g++ -std=c++17 -O1 -Wall -o /tmp/test_obd_query tests/test_obd_query.cpp && /tmp/test_obd_query
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>
#include <set>

struct Rec { uint8_t type; uint32_t ms; std::vector<uint8_t> b; };
static std::vector<Rec> sd;
static void sdRecord(uint8_t t, uint32_t ms, const uint8_t *p, int n) { sd.push_back({t, ms, std::vector<uint8_t>(p, p + n)}); }
struct Sent { uint32_t id; std::vector<uint8_t> d; };
static std::vector<Sent> wire;
static bool hwOk = true;
static bool obdHwSend(uint32_t id, const uint8_t *d) { if (!hwOk) return false; wire.push_back({id, std::vector<uint8_t>(d, d + 8)}); return true; }
#include "../obd_query.h"

typedef std::vector<uint8_t> Bytes;
static Bytes pad(Bytes b) { while (b.size() < 8) b.push_back(0x55); return b; }

// An independent statement of SPEC.md G-5 to check obdAllowed against.
static bool g5(uint32_t id, const Bytes &d) {
  bool fc = d[0] == 0x30 && d[1] == 0 && d[2] == 0 && id == 0x7e0;
  bool sf1 = d[0] == 1 && (d[1] == 3 || d[1] == 7) && (id == 0x7e0 || id == 0x7df);
  bool sf2 = d[0] == 2 && (d[1] == 1 || (d[1] == 9 && d[2] != 2)) && (id == 0x7e0 || id == 0x7df);
  unsigned used = fc || sf2 ? 3 : 2;
  if (!(fc || sf1 || sf2)) return false;
  for (unsigned i = used; i < 8; i++) if (d[i] != 0x55) return false;
  return true;
}

static void testAllowed() {
  // Every frame of the shape "len mode pid pad..." and every flow control, on the three ids.
  unsigned yes = 0, total = 0;
  for (uint32_t id : {0x7e0u, 0x7dfu, 0x7e8u, 0x000u, 0x7e1u}) {
    for (unsigned a = 0; a < 256; a++)
      for (unsigned b = 0; b < 256; b++)
        for (unsigned c : {0u, 1u, 2u, 0x0cu, 0x55u, 0xffu}) {
          Bytes d = pad({(uint8_t)a, (uint8_t)b, (uint8_t)c});
          bool want = g5(id, d), got = obdAllowed(id, d.data());
          assert(want == got);
          yes += got; total++;
        }
  }
  // Things that must never go out, whatever the scheduler does.
  const Bytes never[] = {
    pad({1, 4}),                    // clear DTCs
    pad({2, 9, 2}),                 // VIN
    pad({2, 0x10, 3}),              // diagnostic session
    pad({2, 0x11, 1}),              // ECU reset
    pad({3, 0x22, 0x09, 0x67}),     // read DID (not in G-5)
    pad({4, 0x2e, 0, 1, 0}),        // write DID
    pad({2, 0x27, 1}),              // security access
    pad({2, 0x3e, 0}),              // tester present
    pad({2, 1, 0x0c}),              // fine, but padded wrongly below
  };
  for (int i = 0; i < 8; i++) assert(!obdAllowed(0x7e0, never[i].data()) && !obdAllowed(0x7df, never[i].data()));
  Bytes bad = never[8]; bad[7] = 0; assert(!obdAllowed(0x7e0, bad.data()));
  assert(obdAllowed(0x7e0, never[8].data()) && !obdAllowed(0x7e8, never[8].data()));
  Bytes fc = pad({0x30, 0, 0}); assert(obdAllowed(0x7e0, fc.data()) && !obdAllowed(0x7df, fc.data()));
  printf("PASS: obdAllowed agrees with G-5 on %u frames (%u allowed); clear DTC, VIN, sessions, reset, DIDs refused\n", total, yes);
}

// A fake ECU at 0x7E8: answers what it supports, multi-frame for 0902/0904 and for mode 03 with 3 DTCs.
struct Ecu {
  std::set<unsigned> pids = {0x01, 0x03, 0x04, 0x05, 0x06, 0x07, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x10, 0x11, 0x13, 0x15, 0x1c, 0x1f,
                             0x21, 0x2c, 0x2e, 0x30, 0x31, 0x33, 0x34, 0x41, 0x42, 0x43, 0x44, 0x45, 0x47, 0x49, 0x4a, 0x4c};  // NCEC, 2-0-4
  std::set<unsigned> mode9 = {0x02, 0x04};
  bool silent = false;
  std::vector<Bytes> answer(const Sent &s) {
    const Bytes &d = s.d; std::vector<Bytes> out;
    if (silent || d[0] == 0x30) return out;
    // Bit for each PID in (base, base+32]; the last bit also says "the next range is supported".
    auto mask = [](const std::set<unsigned> &set, unsigned base) {
      uint32_t m = 0; for (unsigned p : set) { if (p > base && p <= base + 32) m |= 1u << (32 - (p - base)); if (p > base + 32) m |= 1; } return m;
    };
    if (d[1] == 1) {
      unsigned p = d[2];
      if (p % 32 == 0) {
        bool any = false; for (unsigned q : pids) any |= q > p;
        if (p && !any) return out;
        uint32_t m = mask(pids, p);
        out.push_back(pad({6, 0x41, (uint8_t)p, (uint8_t)(m >> 24), (uint8_t)(m >> 16), (uint8_t)(m >> 8), (uint8_t)m}));
      } else if (pids.count(p)) out.push_back(pad({4, 0x41, (uint8_t)p, 0x12, 0x34}));
      else out.push_back(pad({3, 0x7f, 1, 0x12}));
    } else if (d[1] == 3) {
      out.push_back({0x10, 0x08, 0x43, 0x03, 0x01, 0x01, 0x01, 0x02});  // 3 DTCs, 8 bytes: first frame
      out.push_back({0x21, 0x01, 0x03, 0x55, 0x55, 0x55, 0x55, 0x55});
    } else if (d[1] == 7) out.push_back(pad({2, 0x47, 0}));
    else if (d[1] == 9) {
      if (d[2] == 0) { uint32_t m = mask(mode9, 0); out.push_back(pad({6, 0x49, 0, (uint8_t)(m >> 24), (uint8_t)(m >> 16), (uint8_t)(m >> 8), (uint8_t)m})); }
      else if (d[2] == 4) { out.push_back({0x10, 0x13, 0x49, 0x04, 0x01, 'L', 'F', 'X'}); out.push_back({0x21, 'X', 'X', 'X', 'X', 'X', 'X', 'X'}); out.push_back({0x22, 'X', 'X', 'X', 'X', 'X', 'X', 'X'}); }
    }
    return out;
  }
};

static void run(Obd &o, Ecu &e, uint32_t &now, uint32_t until, bool alive = true) {
  size_t seen = wire.size();
  for (; now < until; now++) {
    o.tick(now, alive);
    while (seen < wire.size()) {
      Sent s = wire[seen++];
      // A first frame makes rx() send the flow control at once (it lands on the wire before the rest is read).
      for (const Bytes &f : e.answer(s)) o.rx(f.data(), 8, now + 2);
    }
  }
}

static void testSnapshot() {
  Obd o; Ecu e; uint32_t now = 1000; wire.clear(); sd.clear();
  o.start(now, 7, 2);
  assert(sd.size() == 1 && sd[0].type == 8 && sd[0].b[0] == 2 && o.file == 7);
  run(o, e, now, 4000);
  assert(o.cur == 0xffff);
  std::set<unsigned> got01; bool m3 = false, m7 = false, vin = false, calid = false; unsigned fc = 0;
  size_t snapEnd = 0;
  for (size_t i = 0; i < wire.size(); i++) {
    const Sent &s = wire[i]; assert(s.id == 0x7e0 && obdAllowed(s.id, s.d.data()));
    if (s.d[0] == 0x30) { fc++; continue; }
    if (s.d[1] == 1 && !snapEnd) got01.insert(s.d[2]);
    if (s.d[1] == 3) m3 = true;
    if (s.d[1] == 7) m7 = true;
    if (s.d[1] == 9 && s.d[2] == 2) vin = true;
    if (s.d[1] == 9 && s.d[2] == 4) { calid = true; snapEnd = i + 1; }
  }
  std::set<unsigned> want = e.pids; want.insert(0x00); want.insert(0x20); want.insert(0x40);  // 0x60 is not supported by this ECU
  assert(got01 == want);
  assert(m3 && m7 && calid && !vin && fc == 2);
  // Every request went to SD as type 7, in order, and matches the wire.
  std::vector<Rec> sent; for (auto &r : sd) if (r.type == 7) sent.push_back(r);
  assert(sent.size() == wire.size());
  for (size_t i = 0; i < wire.size(); i++) assert(sent[i].b[0] == 0xe0 && sent[i].b[1] == 7 && Bytes(sent[i].b.begin() + 2, sent[i].b.end()) == wire[i].d);
  // After the snapshot: 03, 06, 07, 10 in turn, one every 250 ms.
  std::vector<unsigned> after; for (size_t i = snapEnd; i < wire.size(); i++) if (wire[i].d[0] == 2 && wire[i].d[1] == 1) after.push_back(wire[i].d[2]);
  assert(after.size() >= 8);
  const unsigned order[4] = {0x03, 0x06, 0x07, 0x10};
  for (size_t i = 1; i < after.size(); i++) {
    unsigned k = 0; while (order[k] != after[i - 1]) k++;
    assert(after[i] == order[(k + 1) % 4]);
  }
  std::vector<uint32_t> at;
  for (auto &r : sd) if (r.type == 7 && r.b[2] == 2 && r.b[3] == 1 && r.ms > sd.back().ms - 2000) at.push_back(r.ms);
  for (size_t i = 1; i < at.size(); i++) assert(at[i] - at[i - 1] == 250);
  printf("PASS: snapshot asked %zu mode 01 PIDs (all the ECU supports, plus the support masks), 03, 07, 09 00/04 without 02 (VIN); %u flow controls; then 03/06/07/10 in turn\n", got01.size(), fc);
}

static void testSilentAndStops() {
  Obd o; Ecu e; e.silent = true; uint32_t now = 0; wire.clear(); sd.clear();
  o.start(now, 1, 2); run(o, e, now, 2000);
  // Nothing answers: 0100, 03, 07, 0900 once each and nothing more (no support masks, so no keep-up PIDs).
  assert(wire.size() == 4 && o.cur == 0xffff);
  assert(wire[0].d[1] == 1 && wire[0].d[2] == 0 && wire[1].d[1] == 3 && wire[2].d[1] == 7 && wire[3].d[1] == 9 && wire[3].d[2] == 0);
  // Not alive: nothing at all.
  Obd q; wire.clear(); q.start(0, 1, 2); uint32_t t = 0; run(q, e, t, 2000, false); assert(wire.empty());
  // The hardware refuses (TX FIFO full / not in normal mode): no type 7 record, the step is not stuck.
  Obd r; Ecu ok; wire.clear(); sd.clear(); hwOk = false; t = 0; r.start(0, 1, 2); run(r, ok, t, 500); hwOk = true;
  for (auto &x : sd) assert(x.type != 7);
  assert(obdRejected == 0);
  printf("PASS: a silent ECU gets 4 requests per snapshot; nothing is sent while the bus is not alive; a refused send leaves no record\n");
}

int main() { testAllowed(); testSnapshot(); testSilentAndStops(); return 0; }
