/*
 * Cooperative single-hart process lifecycle for Lab 2. Each process owns
 * its user pages, page table, trapframe and kernel stack until wait reaps it.
 */
#include "types.h"
#include "riscv.h"
#include "memlayout.h"
#include "defs.h"
#include "vmcore.h"
#include "proc.h"

static struct proc procs[NPROC];
static struct proc *current;
static struct context scheduler_context;
static int nextpid = 1;

typedef char trapframe_a0_offset[__builtin_offsetof(struct trapframe, a0) == 112 ? 1 : -1];
typedef char trapframe_t6_offset[__builtin_offsetof(struct trapframe, t6) == 280 ? 1 : -1];

extern uint64 _uprog_table[];

static int
same_name(const char *name, const char *program)
{
  while (*name && *name != '\n' && *name != '\r' && *program) {
    if (*name++ != *program++)
      return 0;
  }
  return (*name == 0 || *name == '\n' || *name == '\r') && *program == 0;
}

static void
free_user_pages(pagetable_t table, uint64 sz)
{
  if (table == 0)
    return;
  for (uint64 va = 0; va < sz; va += PGSIZE) {
    uint64 pa = vmaddr(table, va, 0);
    if (pa)
      kfree((void *)pa);
  }
  vmfree(table);
}

static void
freeproc(struct proc *p)
{
  free_user_pages(p->pagetable, p->sz);
  if (p->trapframe)
    kfree(p->trapframe);
  if (p->kstack)
    kfree(p->kstack);
  p->pagetable = 0;
  p->trapframe = 0;
  p->kstack = 0;
  p->sz = 0;
  p->parent = 0;
  p->chan = 0;
  p->state = UNUSED;
}

static void
forkret(void)
{
  usertrapret();
}

static struct proc *
allocproc(void)
{
  struct proc *p = 0;

  for (int i = 0; i < NPROC; i++)
    if (procs[i].state == UNUSED) {
      p = &procs[i];
      break;
    }
  if (p == 0)
    return 0;

  for (uint64 i = 0; i < sizeof(*p); i++)
    ((char *)p)[i] = 0;
  p->state = USED;
  p->pid = nextpid++;
  p->kstack = kalloc();
  p->trapframe = (struct trapframe *)kalloc();
  if (p->kstack == 0 || p->trapframe == 0)
    goto fail;
  p->pagetable = vmuser((uint64)p->trapframe);
  if (p->pagetable == 0)
    goto fail;
  p->context.ra = (uint64)forkret;
  p->context.sp = (uint64)p->kstack + PGSIZE;
  return p;

fail:
  freeproc(p);
  return 0;
}

int
proc_exec(struct proc *p, const char *name)
{
  uint64 *entry = _uprog_table;
  uint64 start = 0, end = 0;
  pagetable_t next;
  uint64 size, sz;

  while (entry[0] != 0) {
    if (same_name(name, (char *)(entry + 2))) {
      start = entry[0];
      end = entry[1];
      break;
    }
    entry = (uint64 *)((entry[1] + 7) & ~7L);
  }
  if (start == 0 || end <= start)
    return -1;
  size = end - start;
  sz = PGROUNDUP(size) + PGSIZE;
  next = vmuser((uint64)p->trapframe);
  if (next == 0)
    return -1;
  for (uint64 va = 0; va < sz; va += PGSIZE) {
    void *page = kalloc();
    if (page == 0)
      goto fail;
    if (vmmap(next, va, (uint64)page, PGSIZE,
              PTE_R | PTE_W | PTE_X | PTE_U) < 0) {
      kfree(page);
      goto fail;
    }
  }
  for (uint64 i = 0; i < size; i++)
    *(char *)vmaddr(next, i, 1) = *(char *)(start + i);

  free_user_pages(p->pagetable, p->sz);
  p->pagetable = next;
  p->sz = sz;
  for (uint64 i = 0; i < sizeof(*p->trapframe); i++)
    ((char *)p->trapframe)[i] = 0;
  p->trapframe->epc = 0;
  p->trapframe->sp = sz;
  return 0;

fail:
  free_user_pages(next, sz);
  return -1;
}

void
procinit(void)
{
  struct proc *init = allocproc();
  if (init == 0 || proc_exec(init, "sh") < 0) {
    kprintf("lab2: shell init failed\n");
    for (;;)
      ;
  }
  init->state = RUNNABLE;
}

struct proc *
myproc(void)
{
  return current;
}

void
scheduler(void)
{
  for (;;) {
    intr_on();
    for (int i = 0; i < NPROC; i++) {
      struct proc *p = &procs[i];
      intr_off();
      if (p->state == RUNNABLE) {
        current = p;
        p->state = RUNNING;
        swtch(&scheduler_context, &p->context);
        current = 0;
      }
      intr_on();
    }
    asm volatile("wfi");
  }
}

void
proc_yield(void)
{
  struct proc *p = current;
  intr_off();
  p->state = RUNNABLE;
  swtch(&p->context, &scheduler_context);
}

void
proc_sleep(void *chan)
{
  struct proc *p = current;
  p->chan = chan;
  p->state = SLEEPING;
  swtch(&p->context, &scheduler_context);
  p->chan = 0;
}

void
proc_wakeup(void *chan)
{
  for (int i = 0; i < NPROC; i++) {
    struct proc *p = &procs[i];
    if (p->state == SLEEPING && p->chan == chan)
      p->state = RUNNABLE;
  }
}

int
proc_fork(void)
{
  struct proc *parent = current;
  struct proc *child = allocproc();

  if (child == 0)
    return -1;
  child->sz = parent->sz;
  for (uint64 va = 0; va < parent->sz; va += PGSIZE) {
    void *page = kalloc();
    uint64 source = vmaddr(parent->pagetable, va, 0);
    if (page == 0 || source == 0) {
      if (page)
        kfree(page);
      goto fail;
    }
    for (uint64 i = 0; i < PGSIZE; i++)
      ((char *)page)[i] = ((char *)source)[i];
    if (vmmap(child->pagetable, va, (uint64)page, PGSIZE,
              PTE_R | PTE_W | PTE_X | PTE_U) < 0) {
      kfree(page);
      goto fail;
    }
  }
  *child->trapframe = *parent->trapframe;
  child->trapframe->a0 = 0;
  child->parent = parent;
  child->state = RUNNABLE;
  return child->pid;

fail:
  freeproc(child);
  return -1;
}

int
proc_wait(int *status)
{
  struct proc *parent = current;

  for (;;) {
    int found = 0;
    intr_off();
    for (int i = 0; i < NPROC; i++) {
      struct proc *child = &procs[i];
      if (child->parent != parent)
        continue;
      found = 1;
      if (child->state == ZOMBIE) {
        int pid = child->pid;
        if (status)
          *status = child->xstatus;
        freeproc(child);
        intr_on();
        return pid;
      }
    }
    if (!found) {
      intr_on();
      return -1;
    }
    proc_sleep(parent);
    intr_on();
  }
}

void
proc_exit(int status)
{
  struct proc *p = current;
  intr_off();
  p->xstatus = status;
  p->state = ZOMBIE;
  if (p->parent)
    proc_wakeup(p->parent);
  swtch(&p->context, &scheduler_context);
  for (;;)
    ;
}
