/*
 * M-mode setup for the boot hart. Establish S-mode access, timer support,
 * and a Bare boot address space before mret enters kernel_main.
 */
#include "types.h"
#include "riscv.h"
#include "defs.h"
#include "course_sid.h"

#define MSTATUS_MIE  (1L << 3)
#define MSTATUS_MPIE (1L << 7)
#define MEDELEG_SUPERVISOR 0xffffL
#define MIDELEG_SUPERVISOR ((1L << 1) | SIE_STIE | SIE_SEIE)

extern void strap(void);

void
start(void)
{
  uint64 status = r_mstatus();

  /* MPP=S chooses the target mode; MIE/MPIE/SIE stay disabled. */
  status &= ~(MSTATUS_MPP_MASK | MSTATUS_MIE | MSTATUS_MPIE | SSTATUS_SIE);
  status |= MSTATUS_MPP_S;
  w_mstatus(status);
  w_mepc((uint64)kernel_main);

  /* Future S-mode traps are delegated, with an aligned holding vector. */
  w_medeleg(r_medeleg() | MEDELEG_SUPERVISOR);
  w_mideleg(r_mideleg() | MIDELEG_SUPERVISOR);
  w_stvec((uint64)strap);

  /* Physical addresses remain directly usable until Lab 3 adds paging. */
  w_satp(0);
  sfence_vma();

  /* NAPOT permits S-mode instruction fetch and MMIO across physical RAM. */
  w_pmpaddr0(0x3fffffffffffffull);
  w_pmpcfg0(0xf);

  /* Expose time and the S-mode timer comparator for Lab 2 ticks. */
  w_menvcfg(r_menvcfg() | MENVCFG_STCE);
  w_mcounteren(r_mcounteren() | 2);
  w_stimecmp(r_time() + 1000000ULL * LAB2_TICK);

  asm volatile("mret");
  for (;;)
    ;
}
