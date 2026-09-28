/* Shell-only gets hook: edit characters already delivered by stream read.
 * Makefile.upgrade links this optional object; only sh wraps gets.
 */
#include "kernel/types.h"
#include "user/user.h"

char *
__wrap_gets(char *buf, int max)
{
  int i = 0;
  char c;

  while (i + 1 < max && read(0, &c, 1) == 1) {
    if (c == '\b' || c == '\x7f') {
      if (i > 0)
        i--;
      continue;
    }
    buf[i++] = c;
    if (c == '\n' || c == '\r')
      break;
  }
  buf[i] = 0;
  return buf;
}
