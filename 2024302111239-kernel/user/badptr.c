/* Check that syscall arguments cannot access a supervisor-only page. */
#include "kernel/types.h"
#include "kernel/riscv.h"
#include "kernel/memlayout.h"
#include "user/user.h"

int
main(void)
{
  void *supervisor_page = (void *)TRAPFRAME;

  if (write(1, supervisor_page, 1) == -1 &&
      read(0, supervisor_page, 1) == -1 &&
      exec((char *)supervisor_page, 0) == -1)
    printf("BADPTR PASS\n");
  else
    printf("BADPTR FAIL\n");
  exit(0);
}
