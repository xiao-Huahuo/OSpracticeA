/*
 * Polling UART transmitter for early, single-hart output. No interrupt
 * handler or lock exists yet; only kernel_main calls this path in Lab 1.
 */
#include "types.h"
#include "memlayout.h"
#include "course_sid.h"
#include "defs.h"

#if LAB1_BANNER_PROTOCOL != 0
#error This personal Lab 1 console requires the assigned plain-line protocol
#endif

#define UART_THR 0
#define UART_LSR 5
#define UART_LSR_THRE (1 << 5)
#define THROTTLE_BYTES (16 + COURSE_SID % 16)
#define THROTTLE_NOPS 32

static uint64 sent_bytes;

void
consoleputc(int c)
{
  volatile uint8 *uart = (volatile uint8 *)UART0;

  while ((uart[UART_LSR] & UART_LSR_THRE) == 0)
    ;
  uart[UART_THR] = (uint8)c;

  sent_bytes++;
  if (sent_bytes % THROTTLE_BYTES == 0) {
    for (int i = 0; i < THROTTLE_NOPS; i++)
      asm volatile("nop");
  }
}
