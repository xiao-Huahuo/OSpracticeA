/*
 * S-mode trap dispatch. User traps arrive through the unchanged trampoline;
 * kernel interrupts use kernelvec on the active process kernel stack.
 */
#include "types.h"
#include "riscv.h"
#include "memlayout.h"
#include "course_sid.h"
#include "defs.h"
#include "vmcore.h"
#include "proc.h"

extern char trampoline[], uservec[], userret[];
extern void kernelvec(void);
extern void syscall(void);

static int
devintr(void)
{
  uint64 cause = r_scause();

  if (cause == ((1ULL << 63) | 9)) {
    volatile uint32 *claim = (volatile uint32 *)PLIC_SCLAIM(0);
    int irq = *claim;
    if (irq == UART0_IRQ)
      uartintr();
    if (irq)
      *claim = irq;
    return 1;
  }
  if (cause == ((1ULL << 63) | 5)) {
    w_stimecmp(r_time() + 1000000ULL * LAB2_TICK);
    return 2;
  }
  return 0;
}

void
trapinit(void)
{
  volatile uint32 *priority = (volatile uint32 *)(PLIC + UART0_IRQ * 4);
  volatile uint32 *enable = (volatile uint32 *)PLIC_SENABLE(0);

  w_stvec((uint64)kernelvec);
  *priority = 1;
  *enable |= 1 << UART0_IRQ;
  w_sie(r_sie() | SIE_SEIE | SIE_STIE);
}

void
usertrap(void)
{
  struct proc *p = myproc();
  int interrupt;

  w_stvec((uint64)kernelvec);
  p->trapframe->epc = r_sepc();
  if (r_scause() == 8) {
    p->trapframe->epc += 4;
    intr_on();
    syscall();
  } else if ((interrupt = devintr()) == 0) {
    kprintf("lab2: user trap cause=%lx va=%lx\n", r_scause(), r_stval());
    p->killed = 1;
  } else if (interrupt == 2) {
    proc_yield();
  }
  if (p->killed)
    proc_exit(-1);
  usertrapret();
}

void
kerneltrap(void)
{
  uint64 epc = r_sepc();
  uint64 status = r_sstatus();

  if (devintr() == 0) {
    kprintf("lab2: kernel trap cause=%lx va=%lx\n", r_scause(), r_stval());
    for (;;)
      ;
  }
  w_sepc(epc);
  w_sstatus(status);
}

void
usertrapret(void)
{
  struct proc *p = myproc();
  uint64 status;
  uint64 entry = TRAMPOLINE + ((uint64)uservec - (uint64)trampoline);
  uint64 ret = TRAMPOLINE + ((uint64)userret - (uint64)trampoline);

  intr_off();
  w_stvec(entry);
  p->trapframe->kernel_satp = vmsatp(vmkernel_table());
  p->trapframe->kernel_sp = (uint64)p->kstack + PGSIZE;
  p->trapframe->kernel_trap = (uint64)usertrap;
  p->trapframe->kernel_hartid = 0;
  status = r_sstatus();
  status &= ~SSTATUS_SPP;
  status |= SSTATUS_SPIE;
  w_sstatus(status);
  w_sepc(p->trapframe->epc);
  ((void (*)(uint64))ret)(vmsatp(p->pagetable));
  for (;;)
    ;
}
