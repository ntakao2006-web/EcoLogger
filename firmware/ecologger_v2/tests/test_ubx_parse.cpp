// PC test of ubx_parse.h (SP-7-8, 2026-11-16): NAV-PVT is read as before, and the longer NAV-SAT and
// NAV-SLAS frames are followed to their checksum (NAV-SAT counted on the way) instead of being dropped.
// Built with g++ in WSL:
//   g++ -std=c++17 -O1 -Wall -o /tmp/test_ubx_parse tests/test_ubx_parse.cpp && /tmp/test_ubx_parse
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>
#include "../ubx_parse.h"

typedef std::vector<uint8_t> Bytes;

static Bytes frame(uint8_t cls, uint8_t id, const Bytes &payload) {
  Bytes f = {0xb5, 0x62, cls, id, (uint8_t)payload.size(), (uint8_t)(payload.size() >> 8)};
  f.insert(f.end(), payload.begin(), payload.end());
  uint8_t a = 0, c = 0;
  for (size_t k = 2; k < f.size(); k++) { a += f[k]; c += a; }
  f.push_back(a); f.push_back(c);
  return f;
}

// Feeds bytes and returns the index of each byte at which feed() reported a complete frame.
static std::vector<size_t> feedAll(UbxParser &p, const Bytes &s, std::vector<Bytes> *heads = nullptr) {
  std::vector<size_t> ends;
  for (size_t i = 0; i < s.size(); i++)
    if (p.feed(s[i])) {
      ends.push_back(i);
      if (heads) heads->push_back(Bytes(p.f, p.f + (p.len < sizeof(p.f) ? p.len : sizeof(p.f))));
    }
  return ends;
}

static Bytes pvt(uint8_t seed) { Bytes b(92); for (int i = 0; i < 92; i++) b[i] = (uint8_t)(seed + i * 7); return b; }

struct Sv { bool used, diff, sbas, slas; };
static Bytes navSat(uint32_t itow, const std::vector<Sv> &svs) {
  Bytes b(8 + 12 * svs.size(), 0);
  memcpy(b.data(), &itow, 4); b[4] = 1; b[5] = (uint8_t)svs.size();
  for (size_t n = 0; n < svs.size(); n++) {
    uint8_t *s = b.data() + 8 + 12 * n;
    s[0] = (uint8_t)(n % 7); s[1] = (uint8_t)(n + 1); s[2] = 40; s[3] = 30;
    uint32_t flags = 4 | (svs[n].used << 3) | (1 << 4) | (svs[n].diff << 6) | (1 << 11) | (svs[n].sbas << 16) | (svs[n].slas << 18);
    flags |= 1u << 17;  // rtcmCorrUsed is not counted
    memcpy(s + 8, &flags, 4);
  }
  return b;
}

int main() {
  // 1. NAV-PVT (100 bytes), with garbage and a false sync byte in front, ends exactly on its last byte.
  {
    UbxParser p;
    Bytes s = {0x00, 0xb5, 0x00, 0xb5, 0xb5};
    Bytes f = frame(1, 7, pvt(3));
    s.insert(s.end(), f.begin() + 1, f.end());  // the last 0xb5 above starts the frame
    std::vector<Bytes> heads;
    auto ends = feedAll(p, s, &heads);
    assert(ends.size() == 1 && ends[0] == s.size() - 1);
    assert(p.len == 100 && heads[0][2] == 1 && heads[0][3] == 7);
    assert(memcmp(heads[0].data() + 6, pvt(3).data(), 92) == 0);
  }
  // 2. NAV-SAT with 40 satellites (496 bytes, longer than the stored part): counted on the way.
  {
    std::vector<Sv> svs;
    int used = 0, diff = 0, sbas = 0, slas = 0;
    for (int n = 0; n < 40; n++) {
      Sv v = {n % 3 != 0, n % 2 == 0, n % 5 == 0, n % 4 == 0};
      svs.push_back(v);
      if (v.used) { used++; diff += v.diff; sbas += v.sbas; slas += v.slas; }
    }
    UbxParser p;
    Bytes f = frame(1, 0x35, navSat(123456789, svs));
    assert(f.size() == 496);
    auto ends = feedAll(p, f);
    assert(ends.size() == 1 && ends[0] == f.size() - 1);
    assert(p.f[2] == 1 && p.f[3] == 0x35 && p.len == 496 && p.f[11] == 40);
    uint32_t itow; memcpy(&itow, p.f + 6, 4); assert(itow == 123456789);
    assert(p.sat[0] == used && p.sat[1] == diff && p.sat[2] == sbas && p.sat[3] == slas);
    assert(used == 26 && slas > 0 && sbas > 0);
  }
  // 3. NAV-SLAS with 15 corrections (148 bytes): the 20-byte head is kept.
  {
    Bytes b(20 + 15 * 8, 0x5a);
    for (int i = 0; i < 20; i++) b[i] = (uint8_t)(0x10 + i);
    UbxParser p;
    Bytes f = frame(1, 0x42, b);
    auto ends = feedAll(p, f);
    assert(ends.size() == 1 && p.len == 148 && p.f[3] == 0x42);
    assert(memcmp(p.f + 6, b.data(), 20) == 0);
  }
  // 4. A bad checksum is not reported, and the next frame still is. Counts restart for each NAV-SAT.
  {
    UbxParser p;
    Bytes bad = frame(1, 0x35, navSat(1, std::vector<Sv>(30, Sv{true, true, true, true})));
    bad[200] ^= 0x40;
    Bytes good = frame(1, 0x35, navSat(2, std::vector<Sv>(3, Sv{true, false, false, true})));
    Bytes s = bad; s.insert(s.end(), good.begin(), good.end());
    auto ends = feedAll(p, s);
    // the corrupted frame is followed to its end and rejected; the parser is then in step for the next one
    assert(ends.size() == 1 && ends[0] == s.size() - 1);
    assert(p.sat[0] == 3 && p.sat[1] == 0 && p.sat[2] == 0 && p.sat[3] == 3);
  }
  // 5. A length too long to be a frame (> 1032) is dropped at once and the parser resyncs.
  {
    UbxParser p;
    Bytes s = {0xb5, 0x62, 1, 0x35, 0x00, 0x08};
    Bytes f = frame(1, 7, pvt(9));
    s.insert(s.end(), f.begin(), f.end());
    auto ends = feedAll(p, s);
    assert(ends.size() == 1 && p.f[3] == 7 && memcmp(p.f + 6, pvt(9).data(), 92) == 0);
  }
  // 6. Back to back, as the receiver sends them in one second: PVT, SAT, SLAS, PVT, an ACK (no payload).
  {
    UbxParser p;
    std::vector<Bytes> parts = {frame(1, 7, pvt(1)), frame(1, 0x35, navSat(5, std::vector<Sv>(57, Sv{true, true, false, true}))),
                                frame(1, 0x42, Bytes(20 + 8 * 20, 1)), frame(1, 7, pvt(2)), frame(5, 1, Bytes{6, 0x8a})};
    Bytes s, empty = frame(0x0a, 4, Bytes());
    for (auto &x : parts) s.insert(s.end(), x.begin(), x.end());
    s.insert(s.end(), empty.begin(), empty.end());
    std::vector<Bytes> heads;
    auto ends = feedAll(p, s, &heads);
    assert(ends.size() == 6);
    uint8_t ids[6][2] = {{1, 7}, {1, 0x35}, {1, 0x42}, {1, 7}, {5, 1}, {0x0a, 4}};
    for (int i = 0; i < 6; i++) assert(heads[i][2] == ids[i][0] && heads[i][3] == ids[i][1]);
    assert(memcmp(heads[3].data() + 6, pvt(2).data(), 92) == 0);
  }
  // 7. Split into the 64-byte reads gnssPoll makes, with the parser kept between reads (it has no per-read state).
  {
    UbxParser p;
    Bytes s;
    for (int k = 0; k < 10; k++) { Bytes f = frame(1, 7, pvt(k)); s.insert(s.end(), f.begin(), f.end()); }
    Bytes sat = frame(1, 0x35, navSat(9, std::vector<Sv>(44, Sv{true, true, true, false})));
    s.insert(s.end(), sat.begin(), sat.end());
    int got = 0;
    for (size_t at = 0; at < s.size(); at += 64)
      for (size_t i = at; i < at + 64 && i < s.size(); i++) got += p.feed(s[i]);
    assert(got == 11 && p.sat[0] == 44 && p.sat[2] == 44 && p.sat[3] == 0);
  }
  puts("PASS: NAV-PVT as before; NAV-SAT counted and NAV-SLAS head kept past 100 bytes; bad checksum, too long, back to back, split reads");
}
