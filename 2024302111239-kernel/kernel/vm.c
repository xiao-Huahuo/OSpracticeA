/*
 * Sv39 mappings needed by the course trampoline and user programs.
 * Kernel RAM remains identity mapped; user pages are owned by proc.c.
 */
#include "types.h"
#include "riscv.h"
#include "memlayout.h"
#include "vmcore.h"

static pagetable_t kernel_pagetable;

static pte_t *
walk(pagetable_t table, uint64 va, int allocate)
{
  if (va >= MAXVA)
    return 0;
  for (int level = 2; level > 0; level--) {
    pte_t *pte = &table[PX(level, va)];
    if (*pte & PTE_V) {
      if (*pte & (PTE_R | PTE_W | PTE_X))
        return 0;
      table = (pagetable_t)PTE2PA(*pte);
    } else {
      if (!allocate || (table = (pagetable_t)kalloc()) == 0)
        return 0;
      *pte = PA2PTE(table) | PTE_V;
    }
  }
  return &table[PX(0, va)];
}

int
vmmap(pagetable_t table, uint64 va, uint64 pa, uint64 size, int flags)
{
  if ((va | pa | size) & (PGSIZE - 1))
    return -1;
  if (size == 0 || va >= MAXVA || size > MAXVA - va)
    return -1;
  for (uint64 offset = 0; offset < size; offset += PGSIZE) {
    pte_t *pte = walk(table, va + offset, 1);
    if (pte == 0 || (*pte & PTE_V))
      return -1;
    *pte = PA2PTE(pa + offset) | flags | PTE_V;
  }
  return 0;
}

uint64
vmaddr(pagetable_t table, uint64 va, int write)
{
  pte_t *pte = walk(table, va, 0);
  if (pte == 0 || !(*pte & PTE_V) || !(*pte & PTE_U))
    return 0;
  if (!(*pte & (write ? PTE_W : PTE_R)))
    return 0;
  return PTE2PA(*pte) + (va & (PGSIZE - 1));
}

static void
freewalk(pagetable_t table)
{
  for (int i = 0; i < 512; i++) {
    pte_t entry = table[i];
    if ((entry & PTE_V) && !(entry & (PTE_R | PTE_W | PTE_X)))
      freewalk((pagetable_t)PTE2PA(entry));
  }
  kfree(table);
}

void
vmfree(pagetable_t table)
{
  if (table)
    freewalk(table);
}

pagetable_t
vmkernel(void)
{
  extern char trampoline[], trampoline_end[];
  pagetable_t table;
  uint64 tramp_pa = PGROUNDDOWN((uint64)trampoline);

  if ((uint64)trampoline != tramp_pa ||
      (uint64)trampoline_end <= tramp_pa ||
      (uint64)trampoline_end - tramp_pa > PGSIZE)
    return 0;
  table = (pagetable_t)kalloc();
  if (table == 0)
    return 0;
  for (uint64 pa = KERNBASE; pa < PHYSTOP; pa += PGSIZE)
    if (vmmap(table, pa, pa, PGSIZE, PTE_R | PTE_W | PTE_X) < 0)
      goto fail;
  if (vmmap(table, UART0, UART0, PGSIZE, PTE_R | PTE_W) < 0 ||
      vmmap(table, PLIC, PLIC, 0x400000, PTE_R | PTE_W) < 0 ||
      vmmap(table, TRAMPOLINE, tramp_pa, PGSIZE, PTE_R | PTE_X) < 0)
    goto fail;
  kernel_pagetable = table;
  return table;

fail:
  vmfree(table);
  return 0;
}

pagetable_t
vmuser(uint64 trapframe)
{
  extern char trampoline[];
  pagetable_t table = (pagetable_t)kalloc();

  if (table == 0)
    return 0;
  if (vmmap(table, TRAMPOLINE, PGROUNDDOWN((uint64)trampoline),
            PGSIZE, PTE_R | PTE_X) < 0 ||
      vmmap(table, TRAPFRAME, trapframe, PGSIZE, PTE_R | PTE_W) < 0) {
    vmfree(table);
    return 0;
  }
  return table;
}

uint64
vmsatp(pagetable_t table)
{
  return MAKE_SATP(table);
}

pagetable_t
vmkernel_table(void)
{
  return kernel_pagetable;
}
