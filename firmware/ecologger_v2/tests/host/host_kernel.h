// Stand-ins for the Arduino / Zephyr / STM32 calls used by logger_impl.h, so the firmware builds with g++
// on the PC unchanged (SP-7-9, 2026-11-17). Only the logic runs: the clock is virtual, and the threads are
// ucontext coroutines run one at a time in the order of the virtual time (no real concurrency, no
// preemption). Code takes no time; time passes only in delay / k_msleep / k_usleep / k_busy_wait.
// The fake devices (host_devices.h) are reached through the hooks declared at the end.
#pragma once
#include <algorithm>
#include <array>
#include <cerrno>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <functional>
#include <map>
#include <string>
#include <ucontext.h>
#include <vector>

namespace host {
[[noreturn]] void fatal(const char *why);   // writes what is known and exits (replay.cpp)
inline void devicesAdvance(uint64_t us);           // devices catch up with the virtual clock
inline uint64_t devicesNextUs();                   // next input event, UINT64_MAX when none

const uint64_t NEVER = UINT64_MAX;
inline uint64_t nowUs = 0;
// Zephyr on the UNO Q (arduino:zephyr 0.52.0, variants/arduino_uno_q_stm32u585xx): 10 kHz tick,
// CONFIG_MAIN_THREAD_PRIORITY 5 (setup/loop), lower number = higher priority.
const int MAIN_PRIORITY = 5;
const uint64_t SPIN_LIMIT = 50000000;  // calls without a sleep before a thread is called stuck

struct Task {
  ucontext_t ctx;
  std::vector<char> stack;
  const char *name;
  int prio;
  uint64_t wake = 0, order = 0, spins = 0;
  bool done = false, blocked = false;
  void (*entry)(void *, void *, void *) = nullptr;
  void *p1 = nullptr, *p2 = nullptr, *p3 = nullptr;
};
inline std::vector<Task *> tasks;
inline Task *current = nullptr;
inline ucontext_t schedulerCtx;
inline uint64_t orderCounter = 0;
inline uint64_t switches = 0;

inline void spin() { if (current && ++current->spins > SPIN_LIMIT) fatal("a thread runs without ever sleeping"); }
inline void yieldToScheduler() {
  Task *t = current; t->spins = 0; t->order = ++orderCounter;
  swapcontext(&t->ctx, &schedulerCtx);
}
inline void sleepUs(uint64_t us) {
  if (!current) fatal("sleep outside a thread");
  current->wake = nowUs + us; yieldToScheduler();
}
inline void trampoline(unsigned hi, unsigned lo) {
  Task *t = (Task *)(((uintptr_t)hi << 32) | lo);
  t->entry(t->p1, t->p2, t->p3);
  t->done = true;
  swapcontext(&t->ctx, &schedulerCtx);
}
inline Task *spawn(const char *name, void (*entry)(void *, void *, void *), void *a, void *b, void *c, int prio, uint64_t delayUs) {
  Task *t = new Task();
  t->name = name; t->entry = entry; t->p1 = a; t->p2 = b; t->p3 = c; t->prio = prio;
  t->wake = nowUs + delayUs; t->order = ++orderCounter;
  t->stack.resize(1 << 20);
  getcontext(&t->ctx);
  t->ctx.uc_stack.ss_sp = t->stack.data(); t->ctx.uc_stack.ss_size = t->stack.size(); t->ctx.uc_link = &schedulerCtx;
  uintptr_t p = (uintptr_t)t;
  makecontext(&t->ctx, (void (*)())trampoline, 2, (unsigned)(p >> 32), (unsigned)(p & 0xffffffffu));
  tasks.push_back(t);
  return t;
}

}  // namespace host

// ---- Zephyr kernel -------------------------------------------------------------------------------------
struct k_timeout_t { int64_t us; };
#define K_FOREVER (k_timeout_t{-1})
#define K_NO_WAIT (k_timeout_t{0})
#define K_MSEC(ms) (k_timeout_t{(int64_t)(ms) * 1000})
#define K_SECONDS(s) (k_timeout_t{(int64_t)(s) * 1000000})

// Zephyr mutexes are recursive and owned; unlocking hands the mutex to the highest-priority waiter.
struct k_mutex { host::Task *owner = nullptr; int count = 0; std::deque<host::Task *> waiters; };
#define K_MUTEX_DEFINE(name) static k_mutex name
inline int k_mutex_lock(k_mutex *m, k_timeout_t timeout) {
  host::spin();
  host::Task *me = host::current;
  if (!me) host::fatal("k_mutex_lock outside a thread");
  if (!m->owner) { m->owner = me; m->count = 1; return 0; }
  if (m->owner == me) { m->count++; return 0; }
  if (timeout.us == 0) return -EBUSY;
  if (timeout.us > 0) host::fatal("timed k_mutex_lock is not used by the firmware");
  m->waiters.push_back(me); me->blocked = true; me->wake = host::NEVER;
  host::yieldToScheduler();
  if (m->owner != me) host::fatal("mutex wake without ownership");
  return 0;
}
inline int k_mutex_unlock(k_mutex *m) {
  if (m->owner != host::current) host::fatal("k_mutex_unlock by a thread that does not own it");
  if (--m->count) return 0;
  m->owner = nullptr;
  if (m->waiters.empty()) return 0;
  auto best = m->waiters.begin();
  for (auto i = m->waiters.begin(); i != m->waiters.end(); ++i) if ((*i)->prio < (*best)->prio) best = i;
  host::Task *w = *best; m->waiters.erase(best);
  m->owner = w; m->count = 1; w->blocked = false; w->wake = host::nowUs;
  return 0;
}

#define K_THREAD_STACK_DEFINE(name, size) static char name[size]
#define K_THREAD_STACK_SIZEOF(name) sizeof(name)
struct k_thread { host::Task *task = nullptr; };
typedef k_thread *k_tid_t;
inline k_tid_t k_thread_create(k_thread *t, char *, size_t, void (*entry)(void *, void *, void *), void *a, void *b, void *c, int prio, uint32_t, k_timeout_t delay) {
  t->task = host::spawn("thread", entry, a, b, c, prio, delay.us > 0 ? delay.us : 0);
  return t;
}
inline int32_t k_msleep(int32_t ms) { host::sleepUs(ms > 0 ? (uint64_t)ms * 1000 : 0); return 0; }
inline int32_t k_usleep(int32_t us) { host::sleepUs(us > 0 ? (uint64_t)us : 0); return 0; }
inline int32_t k_sleep(k_timeout_t t) { host::sleepUs(t.us > 0 ? (uint64_t)t.us : 0); return 0; }
// A busy wait takes time without letting other threads run.
inline void k_busy_wait(uint32_t us) { host::nowUs += us; host::devicesAdvance(host::nowUs); }

struct k_timer { void (*fn)(k_timer *) = nullptr; uint64_t next = host::NEVER, period = 0; };
namespace host { inline std::vector<k_timer *> ktimers; }
inline void k_timer_init(k_timer *t, void (*fn)(k_timer *), void (*)(k_timer *)) { t->fn = fn; host::ktimers.push_back(t); }
inline void k_timer_start(k_timer *t, k_timeout_t first, k_timeout_t period) { t->next = host::nowUs + first.us; t->period = period.us; }

inline unsigned irq_lock() { return 0; }
inline void irq_unlock(unsigned) {}
namespace host { inline bool resetRequested = false; }
[[noreturn]] inline void NVIC_SystemReset() { host::resetRequested = true; host::fatal("NVIC_SystemReset (the loop watchdog fired)"); }
#define SYS_REBOOT_COLD 1  // the 2026-10-04 firmware reset with sys_reboot (zephyr/sys/reboot.h)
[[noreturn]] inline void sys_reboot(int) { host::resetRequested = true; host::fatal("sys_reboot (the loop watchdog fired)"); }

// ---- Arduino ---------------------------------------------------------------------------------------------
class String {
  std::string s;
 public:
  String() {}
  String(const char *c) : s(c ? c : "") {}
  String(const std::string &x) : s(x) {}
  unsigned int length() const { return (unsigned)s.size(); }
  const char *c_str() const { return s.c_str(); }
  char operator[](unsigned i) const { return i < s.size() ? s[i] : 0; }
  String &operator+=(const String &o) { s += o.s; return *this; }
  String &operator+=(const char *c) { s += c; return *this; }
  String &operator+=(char c) { s += c; return *this; }
  bool operator==(const char *c) const { return s == c; }
  bool operator==(const String &o) const { return s == o.s; }
  bool startsWith(const char *p) const { return s.compare(0, strlen(p), p) == 0; }
  int indexOf(char c) const { size_t i = s.find(c); return i == std::string::npos ? -1 : (int)i; }
  String substring(unsigned from) const { return from >= s.size() ? String() : String(s.substr(from)); }
  String substring(unsigned from, unsigned to) const {
    if (from > to) std::swap(from, to);
    if (from >= s.size()) return String();
    return String(s.substr(from, std::min<size_t>(to, s.size()) - from));
  }
  void replace(const char *a, const char *b) {
    size_t n = strlen(a), m = strlen(b);
    if (!n) return;
    for (size_t i = s.find(a); i != std::string::npos; i = s.find(a, i + m)) s.replace(i, n, b);
  }
  const std::string &str() const { return s; }
};
inline String operator+(const String &a, const String &b) { String r = a; r += b; return r; }
inline String operator+(const String &a, const char *b) { String r = a; r += b; return r; }
inline String operator+(const char *a, const String &b) { String r = a; r += b; return r; }

enum { D0, D1, D2, D3, D4, D5, D6, D7, D8, D9, D10, D11, D12, D13, A0, A1, A2, A3, A4, A5, HOST_PINS };
#define LOW 0
#define HIGH 1
#define INPUT 0
#define OUTPUT 1
#define RISING 3
namespace host {
inline int pins[HOST_PINS];
inline void pinChanged(int pin, int was, int now);  // chip selects, LED latch (host_devices.h)
inline std::map<int, void (*)()> interrupts;
}
inline void digitalWrite(int p, int v) { host::spin(); int was = host::pins[p]; host::pins[p] = v ? 1 : 0; if (was != host::pins[p]) host::pinChanged(p, was, host::pins[p]); }
inline int digitalRead(int p) { host::spin(); return host::pins[p]; }
inline void pinMode(int, int) {}
inline void attachInterrupt(int p, void (*fn)(), int) { host::interrupts[p] = fn; }
inline uint32_t millis() { host::spin(); return (uint32_t)(host::nowUs / 1000); }
inline void delay(uint32_t ms) { k_msleep((int32_t)ms); }

// ---- Zephyr devices ---------------------------------------------------------------------------------------
struct device { const char *name; };
namespace host { inline device dev_i2c2{"i2c2"}, dev_lte_uart{"lte_uart"}; }
#define HOST_DEVICE_(x) (&host::dev_##x)
#define DEVICE_DT_GET(x) HOST_DEVICE_(x)
#define DT_NODELABEL(x) x
#define DT_PATH(x) x
#define DT_PHANDLE_BY_IDX(node, prop, idx) lte_uart

namespace host {
inline int i2cBurstRead(uint16_t addr, uint8_t reg, uint8_t *b, uint32_t n);
inline int i2cRegWrite(uint16_t addr, uint8_t reg, uint8_t v);
inline int i2cWrite(uint16_t addr, const uint8_t *b, uint32_t n);
}
#define I2C_MODE_CONTROLLER (1u << 4)
#define I2C_SPEED_FAST 2u
#define I2C_SPEED_SET(s) ((s) << 1)
inline int i2c_configure(const device *, uint32_t) { return 0; }
inline int i2c_burst_read(const device *, uint16_t a, uint8_t r, uint8_t *b, uint32_t n) { host::spin(); return host::i2cBurstRead(a, r, b, n); }
inline int i2c_reg_read_byte(const device *d, uint16_t a, uint8_t r, uint8_t *v) { return i2c_burst_read(d, a, r, v, 1); }
inline int i2c_reg_write_byte(const device *, uint16_t a, uint8_t r, uint8_t v) { host::spin(); return host::i2cRegWrite(a, r, v); }
inline int i2c_write(const device *, const uint8_t *b, uint32_t n, uint16_t a) { host::spin(); return host::i2cWrite(a, b, n); }

// LTE UART: no modem is attached; the interrupt never fires and nothing is read.
enum { UART_CFG_PARITY_NONE, UART_CFG_STOP_BITS_1 = 1, UART_CFG_DATA_BITS_8 = 3, UART_CFG_FLOW_CTRL_NONE = 0 };
struct uart_config { uint32_t baudrate; uint8_t parity, stop_bits, data_bits, flow_ctrl; };
typedef void (*uart_irq_callback_user_data_t)(const device *, void *);
inline int uart_configure(const device *, const uart_config *) { return 0; }
inline int uart_irq_callback_user_data_set(const device *, uart_irq_callback_user_data_t, void *) { return 0; }
inline int uart_irq_update(const device *) { return 0; }
inline int uart_irq_is_pending(const device *) { return 0; }
inline int uart_irq_rx_ready(const device *) { return 0; }
inline int uart_irq_tx_ready(const device *) { return 0; }
inline int uart_fifo_read(const device *, uint8_t *, int) { return 0; }
inline int uart_fifo_fill(const device *, const uint8_t *, int) { return 0; }
inline void uart_irq_tx_enable(const device *) {}
inline void uart_irq_tx_disable(const device *) {}
inline void uart_irq_rx_enable(const device *) {}

// ---- STM32U585 registers ----------------------------------------------------------------------------------
// A register is plain memory unless a fake device hooks its read or write.
struct HostReg {
  uint32_t v = 0;
  uint32_t (*rd)(HostReg &) = nullptr;
  void (*wr)(HostReg &, uint32_t) = nullptr;
  operator uint32_t() { host::spin(); return rd ? rd(*this) : v; }
  HostReg &operator=(uint32_t x) { host::spin(); if (wr) wr(*this, x); else v = x; return *this; }
  HostReg &operator|=(uint32_t x) { return *this = (uint32_t)*this | x; }
  HostReg &operator&=(uint32_t x) { return *this = (uint32_t)*this & x; }
  HostReg &operator=(const HostReg &) = delete;
};
struct HostGpio { HostReg MODER, OTYPER, OSPEEDR, PUPDR, IDR, ODR, BSRR, LCKR, AFR[2], BRR; };
struct HostUsart { HostReg CR1, CR2, CR3, BRR, ISR, ICR, RDR, TDR; };
struct HostRcc { HostReg APB1ENR2, CCIPR1; };
struct HostFdcan { HostReg CCCR, NBTP, RXGFC, IR, RXF0S, RXF0A; };
struct HostFdcanConfig { HostReg CKDIV; };
namespace host {
inline HostGpio gpioA, gpioB;
inline HostUsart lpuart1;
inline HostRcc rcc;
inline HostFdcan fdcan1;
inline HostFdcanConfig fdcanConfig;
alignas(8) inline uint8_t sramCan[1024];
}
#define GPIOA (&host::gpioA)
#define GPIOB (&host::gpioB)
#define LPUART1 (&host::lpuart1)
#define RCC (&host::rcc)
#define FDCAN1 (&host::fdcan1)
#define FDCAN_CONFIG (&host::fdcanConfig)
#define SRAMCAN_BASE ((uintptr_t)host::sramCan)
#define USART_CR1_UE (1UL << 0)
#define USART_CR1_FIFOEN (1UL << 29)
#define USART_CR3_RTSE (1UL << 8)
#define USART_CR3_CTSE (1UL << 9)
#define RCC_APB1ENR2_FDCAN1EN (1UL << 9)
#define RCC_CCIPR1_FDCANSEL (3UL << 26)
#define FDCAN_CCCR_INIT (1UL << 0)
#define FDCAN_CCCR_CCE (1UL << 1)
#define FDCAN_CCCR_CSA (1UL << 3)
#define FDCAN_CCCR_CSR (1UL << 4)
#define FDCAN_CCCR_MON (1UL << 5)
#define FDCAN_CCCR_FDOE (1UL << 8)
#define FDCAN_CCCR_BRSE (1UL << 9)
#define FDCAN_IR_RF0L (1UL << 2)

// ---- Arduino_RouterBridge ------------------------------------------------------------------------------
// The firmware registers its RPC handlers; the replay's Linux side (or the TCP server) calls them.
struct HostBridge {
  std::map<std::string, String (*)()> noArgs;
  std::map<std::string, int (*)(String)> oneString;
  uint32_t baud = 0;
  void begin(uint32_t b) {
    baud = b;
#ifdef LOGGER_BRIDGE_SERIAL_INIT_HOOK
    LOGGER_BRIDGE_SERIAL_INIT_HOOK();
#endif
  }
  void provide(const char *name, String (*f)()) { noArgs[name] = f; }
  void provide(const char *name, int (*f)(String)) { oneString[name] = f; }
};
inline HostBridge Bridge;

// Arduino's min() takes mixed types (uint32_t with unsigned long here). Defined last so the standard
// headers above are not affected; replay.cpp undefines it after logger_impl.h.
#define min(a, b) ((a) < (b) ? (a) : (b))
