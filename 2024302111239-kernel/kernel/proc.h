/* Process state and the exact trapframe layout used by course trampoline.S. */
#ifndef LAB2_PROC_H
#define LAB2_PROC_H

#include "param.h"

enum procstate { UNUSED, USED, RUNNABLE, RUNNING, SLEEPING, ZOMBIE };

struct trapframe {
  uint64 kernel_satp, kernel_sp, kernel_trap, epc, kernel_hartid;
  uint64 ra, sp, gp, tp, t0, t1, t2, s0, s1;
  uint64 a0, a1, a2, a3, a4, a5, a6, a7;
  uint64 s2, s3, s4, s5, s6, s7, s8, s9, s10, s11;
  uint64 t3, t4, t5, t6;
};

struct context {
  uint64 ra, sp;
  uint64 s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11;
};

struct proc {
  enum procstate state;
  int pid, xstatus, killed;
  struct proc *parent;
  void *chan;
  pagetable_t pagetable;
  struct trapframe *trapframe;
  void *kstack;
  uint64 sz;
  struct context context;
};

struct proc *myproc(void);
void procinit(void);
void scheduler(void) __attribute__((noreturn));
void proc_yield(void);
void proc_sleep(void *chan);
void proc_wakeup(void *chan);
int proc_fork(void);
int proc_wait(int *status);
int proc_exec(struct proc *p, const char *name);
void proc_exit(int status) __attribute__((noreturn));
void usertrapret(void) __attribute__((noreturn));
void swtch(struct context *old, struct context *new);

#endif
