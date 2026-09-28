/* Kernel-owned page allocation and Sv39 interfaces; include types and riscv first. */
#ifndef VMCORE_H
#define VMCORE_H

void kinit(uint64 start);
void *kalloc(void);
void kfree(void *page);
int vmmap(pagetable_t table, uint64 va, uint64 pa, uint64 size, int flags);
uint64 vmaddr(pagetable_t table, uint64 va, int write);
void vmfree(pagetable_t table);
pagetable_t vmkernel(void);
pagetable_t vmuser(uint64 trapframe);
uint64 vmsatp(pagetable_t table);
pagetable_t vmkernel_table(void);

#endif
