/*
 * Boot hart entry in M mode. Clear BSS before using the configured stack;
 * other harts wait because Lab 1 has no per-hart execution path yet.
 */
#include "course_sid.h"

  .section .text
  .globl _entry
  .balign 4
_entry:
  /* Keep M-mode interrupts disabled throughout early initialization. */
  csrci mstatus, 8
  csrw mie, zero
  csrr t0, mhartid
  bnez t0, park

  la t0, mtrap
  csrw mtvec, t0

  /* The linker places all BSS, including the stack, before kernel_end. */
  la t0, bss_start
  la t1, kernel_end
clear_bss:
  bgeu t0, t1, bss_done
  sb zero, 0(t0)
  addi t0, t0, 1
  j clear_bss
bss_done:
  la sp, stack0_top
  call start

park:
  wfi
  j park

  .balign 4
  .globl mtrap
mtrap:
  j mtrap

  .balign 4
  .globl strap
strap:
  j strap

  .section .bss
  .balign 16
  .globl bss_start
bss_start:
stack0:
  .space LAB1_STACK_KB * 1024
  .balign 16
stack0_top:
