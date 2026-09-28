/*
 * Polling UART transmit and interrupt-driven receive on the boot hart.
 * Interrupt masking protects the ring indices shared with the trap handler.
 */
#include "types.h"
#include "riscv.h"
#include "memlayout.h"
#include "course_sid.h"
#include "defs.h"
#include "proc.h"

#if LAB1_BANNER_PROTOCOL != 0
#error This personal Lab 1 console requires the assigned plain-line protocol
#endif

#define UART_THR 0
#define UART_RHR 0
#define UART_IER 1
#define UART_FCR 2
#define UART_LSR 5
#define UART_LSR_THRE (1 << 5)
#define UART_LSR_DR 1
#define THROTTLE_BYTES (16 + COURSE_SID % 16)
#define THROTTLE_NOPS 32

static uint64 sent_bytes;
static char input[LAB2_BUF_SIZE];
static uint64 input_read, input_write;

void
consoleinit(void)
{
  volatile uint8 *uart = (volatile uint8 *)UART0;
  uart[UART_FCR] = 1;
  uart[UART_IER] = 1;
}

void
consoleputc(int c)
{
  volatile uint8 *uart = (volatile uint8 *)UART0;
  int enabled = intr_get();

  intr_off();

  while ((uart[UART_LSR] & UART_LSR_THRE) == 0)
    ;
  uart[UART_THR] = (uint8)c;

  sent_bytes++;
  if (sent_bytes % THROTTLE_BYTES == 0) {
    for (int i = 0; i < THROTTLE_NOPS; i++)
      asm volatile("nop");
  }
  if (enabled)
    intr_on();
}

void
uartintr(void)
{
  volatile uint8 *uart = (volatile uint8 *)UART0;

  while (uart[UART_LSR] & UART_LSR_DR) {
    int c = uart[UART_RHR];
    if (c == '\r')
      c = '\n';
    if (input_write - input_read == LAB2_BUF_SIZE)
      continue;
    input[input_write++ % LAB2_BUF_SIZE] = c;
    consoleputc(c);
    if (LAB2_BUF_SEMANTICS == 1 || c == '\n')
      proc_wakeup(input);
  }
}

int
consolegetc(int block)
{
  int c;

  intr_off();
  while (input_read == input_write) {
    if (!block) {
      intr_on();
      return -1;
    }
    proc_sleep(input);
  }
  c = input[input_read++ % LAB2_BUF_SIZE];
  intr_on();
  return c;
}
