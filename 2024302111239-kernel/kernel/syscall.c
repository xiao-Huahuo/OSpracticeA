/*
 * Lab 2 system-call ABI. User addresses are translated and checked before
 * kernel access; unknown and unsupported calls return -1 to the caller.
 */
#include "types.h"
#include "riscv.h"
#include "memlayout.h"
#include "syscall.h"
#include "defs.h"
#include "vmcore.h"
#include "proc.h"

static uint64
argraw(int index)
{
  struct trapframe *tf = myproc()->trapframe;
  switch (index) {
  case 0: return tf->a0;
  case 1: return tf->a1;
  case 2: return tf->a2;
  default: return 0;
  }
}

static int
argint(int index)
{
  return (int)argraw(index);
}

static uint64
argaddr(int index)
{
  return argraw(index);
}

static int
copyinstr(char *dst, uint64 va, uint64 max)
{
  pagetable_t table = myproc()->pagetable;
  for (uint64 i = 0; i < max; i++) {
    uint64 pa;
    if (va + i < va)
      return -1;
    pa = vmaddr(table, va + i, 0);
    if (pa == 0)
      return -1;
    dst[i] = *(char *)pa;
    if (dst[i] == 0)
      return 0;
  }
  return -1;
}

static int
argstr(int index, char *dst, uint64 max)
{
  return copyinstr(dst, argaddr(index), max);
}

static int
copyout(uint64 va, const char *src, uint64 count)
{
  pagetable_t table = myproc()->pagetable;
  for (uint64 i = 0; i < count; i++) {
    uint64 pa;
    if (va + i < va)
      return -1;
    pa = vmaddr(table, va + i, 1);
    if (pa == 0)
      return -1;
    *(char *)pa = src[i];
  }
  return 0;
}

static int
sys_read(void)
{
  uint64 addr = argaddr(1);
  int count = argint(2);
  struct proc *p = myproc();
  int used = 0;

  if (argint(0) != 0 || count < 0)
    return -1;
  if (count == 0)
    return 0;
  if (addr >= p->sz || (uint64)count > p->sz - addr)
    return -1;
  for (int i = 0; i < count; i++)
    if (vmaddr(p->pagetable, addr + i, 1) == 0)
      return -1;

  /* Single-byte readers keep stream delivery; bulk reads finish a line. */
  while (used < count) {
    int c = consolegetc(1);
    char ch;
    if (c < 0)
      break;
    if (count > 1 && (c == '\b' || c == '\x7f')) {
      if (used > 0)
        used--;
      continue;
    }
    ch = (char)c;
    if (copyout(addr + used, &ch, 1) < 0)
      return -1;
    used++;
    if (ch == '\n')
      break;
  }
  return used;
}

static int
sys_write(void)
{
  uint64 addr = argaddr(1);
  int count = argint(2);
  struct proc *p = myproc();

  if ((argint(0) != 1 && argint(0) != 2) || count < 0)
    return -1;
  if (count == 0)
    return 0;
  if (addr >= p->sz || (uint64)count > p->sz - addr)
    return -1;
  for (int i = 0; i < count; i++) {
    uint64 pa = vmaddr(p->pagetable, addr + i, 0);
    if (pa == 0)
      return i ? i : -1;
    consoleputc(*(char *)pa);
  }
  return count;
}

static int
sys_exec(void)
{
  char name[MAXPATH];
  if (argstr(0, name, sizeof(name)) < 0)
    return -1;
  return proc_exec(myproc(), name);
}

static int
sys_wait(void)
{
  uint64 va = argaddr(0);
  int status, pid;

  if (va && (va + sizeof(status) - 1 < va ||
             vmaddr(myproc()->pagetable, va, 1) == 0 ||
             vmaddr(myproc()->pagetable, va + sizeof(status) - 1, 1) == 0))
    return -1;
  pid = proc_wait(va ? &status : 0);
  if (pid > 0 && va && copyout(va, (char *)&status, sizeof(status)) < 0)
    return -1;
  return pid;
}

void
syscall(void)
{
  struct proc *p = myproc();
  int result = -1;

  switch (p->trapframe->a7) {
  case SYS_fork: result = proc_fork(); break;
  case SYS_exit: proc_exit(argint(0));
  case SYS_wait: result = sys_wait(); break;
  case SYS_read: result = sys_read(); break;
  case SYS_exec: result = sys_exec(); break;
  case SYS_getpid: result = p->pid; break;
  case SYS_write: result = sys_write(); break;
  default: break;
  }
  p->trapframe->a0 = result;
}
