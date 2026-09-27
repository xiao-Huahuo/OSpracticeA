/*
 * S-mode Lab 1 entry. Print the student-specific banner, exercise the
 * formatter's boundary cases, then remain in the initialized kernel.
 */
#include "types.h"
#include "course_sid.h"
#include "defs.h"

#define LONG_BLOCK "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"

void
kernel_main(void)
{
  kprintf("OSLAB1 sid=%ld mod97=0x%x\n", (long)COURSE_SID,
          (uint)(COURSE_SID % 97));
  kprintf("SELFTEST zero=%d min=%d max=%d hex=0x%x empty=[%s]\n",
          0, (-2147483647 - 1), 2147483647, 0xffffffffU, "");
  kprintf("SELFTEST long=[%s]\n", LONG_BLOCK LONG_BLOCK LONG_BLOCK LONG_BLOCK
                               LONG_BLOCK LONG_BLOCK LONG_BLOCK LONG_BLOCK);

  for (;;)
    asm volatile("wfi");
}
