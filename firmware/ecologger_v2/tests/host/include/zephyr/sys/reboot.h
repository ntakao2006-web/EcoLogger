// Stand-in for the board header on the PC: everything is in host_kernel.h (SP-7-9). Only the 2026-10-04
// firmware includes it (sys_reboot); later versions reset through NVIC_SystemReset.
#include "host_kernel.h"
