/* Put the unchanged course trampoline into an executable, aligned page. */
  .section trampsec, "ax"
  .balign 4096
#include "trampoline.S"
  .globl trampoline_end
trampoline_end:
