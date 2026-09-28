/*
 * S-mode entry. Preserve the Lab 1 serial contract, then initialize traps
 * and the Lab 2 scheduler before running the first user shell.
 */
#include "types.h"
#include "riscv.h"
#include "course_sid.h"
#include "defs.h"
#include "vmcore.h"
#include "proc.h"

#define LONG_BLOCK "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"

void
kernel_main(void)
{
  extern char kernel_end[];
  pagetable_t table;

  kinit((uint64)kernel_end);
  table = vmkernel();
  if (table == 0) {
    kprintf("lab2: kernel mapping failed\n");
    for (;;)
      asm volatile("wfi");
  }
  w_satp(vmsatp(table));
  sfence_vma();

  kprintf("OSLAB1 sid=%ld mod97=0x%x\n", (long)COURSE_SID,
          (uint)(COURSE_SID % 97));
  kprintf("SELFTEST zero=%d min=%d max=%d hex=0x%x empty=[%s]\n",
          0, (-2147483647 - 1), 2147483647, 0xffffffffU, "");
  kprintf("SELFTEST long=[%s]\n", LONG_BLOCK LONG_BLOCK LONG_BLOCK LONG_BLOCK
                               LONG_BLOCK LONG_BLOCK LONG_BLOCK LONG_BLOCK);

  trapinit();
  consoleinit();
  procinit();
  scheduler();
}
