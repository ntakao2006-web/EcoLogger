// Replay bench for the STM32 firmware on the PC (SP-7-9, 2026-11-17). logger_impl.h is built unchanged
// against the stand-ins in host_kernel.h and driven by the fake devices in host_devices.h, which play back
// a drive recorded on the SD card (prepared by test_replay.py). Built and run in WSL:
//   g++ -std=c++17 -O2 -Itests/host/include -Itests/host -o /tmp/replay tests/host/replay.cpp
//   /tmp/replay --events EVENTS --out DIR [--sd-busy-us N] [--stall FROM_MS:TO_MS:BUSY_MS]... [--rpc-port P [--speed X]]
// Without --rpc-port a simulated Linux side (like EcoCapture-Web server.py: logger.status every 0.1 s,
// logger.take every 0.05 s) runs inside the virtual time. With --rpc-port the Bridge RPC is served on
// 127.0.0.1:P (MessagePack-RPC like Arduino Router) and the virtual clock follows the wall clock (× speed).
// Outputs in DIR: card.img (the whole SD card), imu_served.bin (every BNO055 read, as SD records),
// linux.txt (what the Linux side got: "S ms json" status, "T ms json" take, "Q ms command" sent,
// "C ms command status" completed),
// summary.json (device counters, problems, threads, final status).
// logger_impl.h comes first, as in the sketch: it defines LOGGER_BRIDGE_SERIAL_INIT_HOOK before it
// includes the Bridge header (host_kernel.h). The warnings below come from the firmware as written for a
// 32-bit ARM (unsigned long is 64 bits here) and are not about the replay.
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Woverflow"
#pragma GCC diagnostic ignored "-Wunused-variable"
#pragma GCC diagnostic ignored "-Wunused-but-set-variable"
#pragma GCC diagnostic ignored "-Wmisleading-indentation"
// -DLOGGER_IMPL='"<dir>/logger_impl.h"' builds another copy of the firmware (test_replay.py --firmware).
#ifdef LOGGER_IMPL
#include LOGGER_IMPL
#else
#include "../../logger_impl.h"
#endif
#pragma GCC diagnostic pop
#undef min
#include "host_devices.h"
#include "../../rpc_frame.h"
#include <arpa/inet.h>
#include <chrono>
#include <fcntl.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <thread>
#include <unistd.h>

namespace host {
static std::string outDir;
static std::vector<std::string> linuxLog;
static std::string filesResult = "null", fatalWhy;
static bool stopFlag = false, realtime = false;
static double speed = 1;
static int rpcPort = 0;
static uint64_t endUs = 0, rpcCalls = 0;
static bool wroteOutputs = false;

static std::string jsonString(const std::string &s) {
  std::string o = "\"";
  for (char c : s) {
    if (c == '"' || c == '\\') { o += '\\'; o += c; }
    else if ((unsigned char)c < 0x20) { char b[8]; snprintf(b, sizeof(b), "\\u%04x", c); o += b; }
    else o += c;
  }
  return o + "\"";
}
static const char *taskName(Task *t) {
  if (t->entry == (void (*)(void *, void *, void *))can1Capture) return "can1Capture";
  if (t->entry == (void (*)(void *, void *, void *))sdWorker) return "sdWorker";
  if (t->entry == (void (*)(void *, void *, void *))lteWorker) return "lteWorker";
  if (t->entry == (void (*)(void *, void *, void *))bridgeWorker) return "bridgeWorker";
  return t->name;
}
static void writeOutputs() {
  if (wroteOutputs) return;
  wroteOutputs = true;
  std::string dir = outDir + "/";
  if (FILE *f = fopen((dir + "card.img").c_str(), "wb")) {
    std::vector<uint32_t> lbas; for (auto &kv : sd.data) lbas.push_back(kv.first);
    std::sort(lbas.begin(), lbas.end());
    for (uint32_t lba : lbas) { fseeko(f, (off_t)lba * 512, SEEK_SET); fwrite(sd.data[lba].data(), 1, 512, f); }
    fflush(f); if (ftruncate(fileno(f), (off_t)sd.sectors * 512)) problem("card.img size");
    fclose(f);
  }
  if (FILE *f = fopen((dir + "imu_served.bin").c_str(), "wb")) { fwrite(bno.served.data(), 1, bno.served.size(), f); fclose(f); }
  if (FILE *f = fopen((dir + "linux.txt").c_str(), "wb")) { for (auto &l : linuxLog) fprintf(f, "%s\n", l.c_str()); fclose(f); }
  FILE *f = fopen((dir + "summary.json").c_str(), "wb");
  if (!f) return;
  fprintf(f, "{\"fatal\":%s,\"virtual_ms\":%llu,\"switches\":%llu,\"rpc_calls\":%llu,\n", fatalWhy.empty() ? "null" : jsonString(fatalWhy).c_str(),
          (unsigned long long)(nowUs / 1000), (unsigned long long)switches, (unsigned long long)rpcCalls);
  fprintf(f, "\"events\":{\"total\":%zu,\"applied\":%zu,\"imu\":%llu,\"imu_fail\":%llu,\"gnss\":%llu,\"can1\":%llu,\"can2\":%llu},\n", events.size(), nextEvent,
          (unsigned long long)eventsApplied[EV_IMU], (unsigned long long)eventsApplied[EV_IMU_FAIL], (unsigned long long)eventsApplied[EV_GNSS],
          (unsigned long long)eventsApplied[EV_CAN1], (unsigned long long)eventsApplied[EV_CAN2]);
  fprintf(f, "\"bno055\":{\"reads\":%llu,\"fails\":%llu,\"opr_mode\":%u},\n", (unsigned long long)bno.reads, (unsigned long long)bno.fails, bno.regs[0x3d]);
  fprintf(f, "\"gnss\":{\"bytes_in\":%llu,\"bytes_read\":%llu,\"left\":%zu,\"config_ok\":%llu,\"config_bad\":%llu},\n", (unsigned long long)gnss.bytesIn,
          (unsigned long long)gnss.bytesRead, gnss.out.size(), (unsigned long long)gnss.configOk, (unsigned long long)gnss.configBad);
  fprintf(f, "\"can1\":{\"delivered\":%llu,\"fifo_lost\":%llu,\"while_init\":%llu,\"not_listen_only\":%llu,\"bad_ack\":%llu,\"left\":%u},\n",
          (unsigned long long)can1.delivered, (unsigned long long)can1.lost, (unsigned long long)can1.whileInit, (unsigned long long)can1.notListenOnly,
          (unsigned long long)can1.badAck, can1.fill);
  fprintf(f, "\"can2\":{\"delivered\":%llu,\"overflow\":%llu,\"not_ready\":%llu,\"resets\":%llu,\"mode\":%u},\n", (unsigned long long)mcp.delivered,
          (unsigned long long)mcp.overflow, (unsigned long long)mcp.notReady, (unsigned long long)mcp.resets, mcp.mode());
  fprintf(f, "\"sd\":{\"reads\":%llu,\"writes\":%llu,\"max_busy_us\":%llu,\"sectors\":%u},\n", (unsigned long long)sd.reads, (unsigned long long)sd.writes,
          (unsigned long long)sd.maxBusyUs, sd.sectors);
  fprintf(f, "\"spi_bytes\":%llu,\"leds\":%u,\"led_latches\":%llu,\n", (unsigned long long)spi.bytes, ledLatched, (unsigned long long)ledLatches);
  fprintf(f, "\"problem_count\":%llu,\"problems\":[", (unsigned long long)problemCount);
  for (size_t i = 0; i < problems.size(); i++) fprintf(f, "%s%s", i ? "," : "", jsonString(problems[i]).c_str());
  fprintf(f, "],\n\"threads\":[");
  for (size_t i = 0; i < tasks.size(); i++) fprintf(f, "%s{\"name\":\"%s\",\"prio\":%d,\"done\":%d}", i ? "," : "", taskName(tasks[i]), tasks[i]->prio, tasks[i]->done);
  String st = state;  // the firmware's last status snapshot (no lock needed: nothing else runs now)
  fprintf(f, "],\n\"files\":%s,\n\"status\":%s}\n", filesResult.c_str(), st.length() ? st.c_str() : "null");
  fclose(f);
}
[[noreturn]] void fatal(const char *why) {
  fatalWhy = why;
  if (current) fatalWhy += std::string(" (thread ") + taskName(current) + ")";
  fprintf(stderr, "replay: %s\n", fatalWhy.c_str());
  writeOutputs();
  _exit(2);
}

// ---- the Linux side -------------------------------------------------------------------------------
static String call(const char *m) { rpcCalls++; return Bridge.noArgs.at(m)(); }
static int call(const char *m, const String &arg) { rpcCalls++; return Bridge.oneString.at(m)(arg); }
static long field(const String &json, const char *name) {
  std::string key = std::string("\"") + name + "\":";
  size_t i = json.str().find(key);
  return i == std::string::npos ? -1 : strtol(json.c_str() + i + key.size(), nullptr, 10);
}
static void logLine(char kind, const String &body) { linuxLog.push_back(std::string(1, kind) + " " + std::to_string(millis()) + " " + body.str()); }
// Like TelemetryBridge.command: submit, then read logger.status every 20 ms until "completed" moves.
static String command(const char *text) {
  long before = field(call("logger.status"), "completed");
  linuxLog.push_back(std::string("Q ") + std::to_string(millis()) + " " + text);
  if (call("logger.command", String(text)) != 0) fatal("logger.command was refused (queue busy)");
  for (int i = 0; i < 1000; i++) {
    k_msleep(20);
    String s = call("logger.status");
    if (field(s, "completed") != before) { linuxLog.push_back(std::string("C ") + std::to_string(millis()) + " " + text + " " + s.str()); return s; }
  }
  fatal("a command did not complete");
}
static void linuxSide(void *, void *, void *) {
  k_msleep(1000);  // the firmware has registered its handlers by now (bridgeWorker)
  command("C500000");
  uint32_t statusAt = 0;
  bool stopping = false;
  while (true) {
    uint32_t now = millis();
    if (!statusAt || now - statusAt >= 100) { logLine('S', call("logger.status")); statusAt = now; }
    logLine('T', call("logger.take"));
    if (!stopping && nextEvent == events.size() && nowUs >= endUs) {
      stopping = true;
      command("LOG0");
      String s = command("FILES0");
      std::string r = s.str(); size_t a = r.find("\"result\":\"");
      if (a != std::string::npos) {  // the result is a JSON array escaped inside the status JSON
        std::string v; for (size_t i = a + 10; i < r.size() && r[i] != '"'; i++) { if (r[i] == '\\' && i + 1 < r.size()) i++; v += r[i]; }
        filesResult = v;
      }
      logLine('S', call("logger.status")); logLine('T', call("logger.take"));
      stopFlag = true;
    }
    k_msleep(50);
  }
}

// ---- Bridge RPC over TCP --------------------------------------------------------------------------------
struct Mp { int type = 0; int64_t i = 0; std::string s; std::vector<Mp> a; };  // 0 nil, 1 int, 2 str, 3 array
static bool mpRead(const uint8_t *&p, const uint8_t *e, Mp &o) {
  if (p >= e) return false;
  uint8_t c = *p++;
  auto be = [&](int n) { uint64_t v = 0; for (int k = 0; k < n; k++) v = (v << 8) | *p++; return v; };
  auto str = [&](size_t n) { o.type = 2; o.s.assign((const char *)p, n); p += n; return true; };
  auto arr = [&](size_t n) { o.type = 3; o.a.resize(n); for (auto &x : o.a) if (!mpRead(p, e, x)) return false; return true; };
  if (c <= 0x7f) { o.type = 1; o.i = c; return true; }
  if (c >= 0xe0) { o.type = 1; o.i = (int8_t)c; return true; }
  if ((c & 0xe0) == 0xa0) return str(c & 31);
  if ((c & 0xf0) == 0x90) return arr(c & 15);
  switch (c) {
    case 0xc0: o.type = 0; return true;
    case 0xc2: case 0xc3: o.type = 1; o.i = c == 0xc3; return true;
    case 0xcc: o.type = 1; o.i = (int64_t)be(1); return true;
    case 0xcd: o.type = 1; o.i = (int64_t)be(2); return true;
    case 0xce: o.type = 1; o.i = (int64_t)be(4); return true;
    case 0xcf: o.type = 1; o.i = (int64_t)be(8); return true;
    case 0xd0: o.type = 1; o.i = (int8_t)be(1); return true;
    case 0xd1: o.type = 1; o.i = (int16_t)be(2); return true;
    case 0xd2: o.type = 1; o.i = (int32_t)be(4); return true;
    case 0xd3: o.type = 1; o.i = (int64_t)be(8); return true;
    case 0xd9: case 0xc4: return str(be(1));
    case 0xda: case 0xc5: return str(be(2));
    case 0xdb: case 0xc6: return str(be(4));
    case 0xdc: return arr(be(2));
    case 0xdd: return arr(be(4));
  }
  return false;
}
static void mpInt(std::string &o, int64_t v) {
  if (v >= 0 && v < 128) o += (char)v;
  else if (v < 0 && v >= -32) o += (char)(uint8_t)v;
  else if (v >= 0 && v <= 0xffffffffLL) { o += (char)0xce; for (int k = 3; k >= 0; k--) o += (char)(v >> (8 * k)); }
  else { o += (char)0xd3; for (int k = 7; k >= 0; k--) o += (char)(v >> (8 * k)); }
}
static void mpStr(std::string &o, const std::string &s) {
  size_t n = s.size();
  if (n < 32) o += (char)(0xa0 | n);
  else if (n < 256) { o += (char)0xd9; o += (char)n; }
  else if (n < 65536) { o += (char)0xda; o += (char)(n >> 8); o += (char)n; }
  else { o += (char)0xdb; for (int k = 3; k >= 0; k--) o += (char)(n >> (8 * k)); }
  o += s;
}
// The virtual clock starts once the client is connected (main), so no row is lost before its first take.
static int listenFd = -1, clientFd = -1;
static void rpcListen() {
  listenFd = socket(AF_INET, SOCK_STREAM, 0); int one = 1;
  setsockopt(listenFd, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one));
  sockaddr_in a{}; a.sin_family = AF_INET; a.sin_port = htons(rpcPort); a.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
  if (bind(listenFd, (sockaddr *)&a, sizeof(a)) || listen(listenFd, 1)) fatal("cannot listen on the RPC port");
  fprintf(stderr, "replay: RPC on 127.0.0.1:%d, waiting for the client\n", rpcPort);
  clientFd = accept(listenFd, nullptr, nullptr);
  if (clientFd < 0) fatal("accept failed");
  fcntl(clientFd, F_SETFL, O_NONBLOCK); fcntl(listenFd, F_SETFL, O_NONBLOCK);
}
static void rpcServer(void *, void *, void *) {
  int c = clientFd; std::vector<uint8_t> in;
  while (true) {
    if (c < 0) {  // the client went away: the replay ends once every event is played, else wait for it again
      c = accept(listenFd, nullptr, nullptr);
      if (c >= 0) { fcntl(c, F_SETFL, O_NONBLOCK); in.clear(); }
      else if (nextEvent == events.size()) stopFlag = true;
    }
    if (c >= 0) {
      uint8_t b[4096]; ssize_t n;
      while ((n = recv(c, b, sizeof(b), 0)) > 0) in.insert(in.end(), b, b + n);
      if (n == 0) { close(c); c = -1; continue; }
      int size;
      while ((size = loggerRpcFrame(in.data(), in.size())) > 0) {
        const uint8_t *p = in.data(); Mp req;
        bool ok = mpRead(p, in.data() + size, req) && req.type == 3 && req.a.size() == 4 && req.a[0].i == 0 && req.a[2].type == 2;
        in.erase(in.begin(), in.begin() + size);
        if (!ok) { problem("bad RPC request"); continue; }
        std::string m = req.a[2].s, reply = "\x94\x01";
        mpInt(reply, req.a[1].i);
        if (Bridge.noArgs.count(m)) { String r = call(m.c_str()); reply += (char)0xc0; mpStr(reply, r.str()); }
        else if (Bridge.oneString.count(m) && req.a[3].type == 3 && req.a[3].a.size() == 1 && req.a[3].a[0].type == 2) { int r = call(m.c_str(), String(req.a[3].a[0].s)); reply += (char)0xc0; mpInt(reply, r); }
        else { mpStr(reply, "method " + m + " not available"); reply += (char)0xc0; }
        for (size_t off = 0; off < reply.size();) {
          ssize_t w = send(c, reply.data() + off, reply.size() - off, MSG_NOSIGNAL);
          if (w > 0) off += w; else if (errno == EAGAIN) std::this_thread::sleep_for(std::chrono::microseconds(200)); else break;
        }
      }
      if (size < 0) { problem("unframeable RPC bytes"); in.clear(); }
    }
    k_msleep(1);
  }
}

// ---- main -------------------------------------------------------------------------------------------
static void mainThread(void *, void *, void *) { setup(); for (;;) loop(); }

static void loadEvents(const char *path) {
  FILE *f = fopen(path, "rb");
  if (!f) fatal("cannot open the events file");
  char magic[8];
  if (fread(magic, 1, 8, f) != 8 || memcmp(magic, "ELRPLAY1", 8)) fatal("not an events file");
  uint8_t h[12];
  while (fread(h, 1, 12, f) == 12) {
    Event e; e.kind = h[0]; uint16_t n = h[2] | (h[3] << 8); e.us = 0;
    for (int i = 0; i < 8; i++) e.us |= (uint64_t)h[4 + i] << (8 * i);
    e.data.resize(n);
    if (n && fread(e.data.data(), 1, n, f) != n) fatal("truncated events file");
    if (!events.empty() && e.us < events.back().us) fatal("events out of time order");
    events.push_back(std::move(e));
  }
  fclose(f);
}

static void run() {
  auto wallStart = std::chrono::steady_clock::now();
  uint64_t limit = endUs + 120000000ULL;
  while (!stopFlag) {
    Task *pick = nullptr; uint64_t next = NEVER;
    for (Task *t : tasks) {
      if (t->done || t->blocked) continue;
      if (t->wake <= nowUs && (!pick || t->prio < pick->prio || (t->prio == pick->prio && (t->wake < pick->wake || (t->wake == pick->wake && t->order < pick->order))))) pick = t;
      next = std::min(next, t->wake);
    }
    if (pick) { current = pick; switches++; swapcontext(&schedulerCtx, &pick->ctx); current = nullptr; continue; }
    for (k_timer *t : ktimers) next = std::min(next, t->next);
    next = std::min(next, devicesNextUs());
    if (next == NEVER) fatal("every thread is blocked");
    if (next > limit) fatal("the replay did not finish in time");
    if (realtime) {
      auto target = wallStart + std::chrono::microseconds((uint64_t)(next / speed));
      if (target - std::chrono::steady_clock::now() > std::chrono::milliseconds(1)) std::this_thread::sleep_until(target);
      if (std::chrono::steady_clock::now() - wallStart > std::chrono::minutes(30)) fatal("the RPC client never finished");
    }
    nowUs = next; devicesAdvance(nowUs);
    for (k_timer *t : ktimers) if (t->next <= nowUs) { t->next = t->period ? t->next + t->period : NEVER; t->fn(t); }
  }
}
}  // namespace host

int main(int argc, char **argv) {
  using namespace host;
  const char *eventsPath = nullptr;
  uint32_t cardMiB = 128, clusterSectors = 2;
  for (int i = 1; i < argc; i++) {
    std::string a = argv[i];
    auto next = [&]() { if (i + 1 >= argc) { fprintf(stderr, "missing value for %s\n", a.c_str()); exit(1); } return argv[++i]; };
    if (a == "--events") eventsPath = next();
    else if (a == "--out") outDir = next();
    else if (a == "--sd-busy-us") sd.busyUs = strtoull(next(), nullptr, 10);
    else if (a == "--stall") { unsigned long long f, t, b; if (sscanf(next(), "%llu:%llu:%llu", &f, &t, &b) != 3) exit(1); sd.stalls.push_back({f * 1000, t * 1000, b * 1000}); }
    else if (a == "--rpc-port") rpcPort = atoi(next());
    else if (a == "--speed") speed = atof(next());
    else if (a == "--card-mib") cardMiB = (uint32_t)atoi(next());
    else if (a == "--cluster-sectors") clusterSectors = (uint32_t)atoi(next());
    else { fprintf(stderr, "unknown argument %s\n", a.c_str()); return 1; }
  }
  if (!eventsPath || outDir.empty()) { fprintf(stderr, "usage: replay --events FILE --out DIR [...]\n"); return 1; }
  loadEvents(eventsPath);
  endUs = events.empty() ? 0 : events.back().us + 1500000;
  formatCard(cardMiB * 2048, (uint8_t)clusterSectors);
  hookRegisters();
  spawn("main", mainThread, nullptr, nullptr, nullptr, MAIN_PRIORITY, 0);
  if (rpcPort) { realtime = true; rpcListen(); spawn("rpcServer", rpcServer, nullptr, nullptr, nullptr, MAIN_PRIORITY, 0); }
  else spawn("linuxSide", linuxSide, nullptr, nullptr, nullptr, MAIN_PRIORITY, 0);
  run();
  writeOutputs();
  printf("replay: %.1f s virtual, %llu switches, %zu events, problems %llu\n", nowUs / 1e6, (unsigned long long)switches, events.size(), (unsigned long long)problemCount);
  return problemCount ? 3 : 0;
}
