/*
 * Minimal freestanding formatter for the single-hart Lab 1 console.
 * Supported conversions: %c, %s, %d, %u, %x, %ld, %lu, %lx and %%.
 */
#include <stdarg.h>
#include "types.h"
#include "defs.h"

static void
print_unsigned(uint64 value, uint base)
{
  char digits[sizeof(uint64) * 8];
  const char *alphabet = "0123456789abcdef";
  int count = 0;

  do {
    digits[count++] = alphabet[value % base];
    value /= base;
  } while (value != 0);

  while (count > 0)
    consoleputc(digits[--count]);
}

static void
print_signed(long value)
{
  if (value < 0) {
    consoleputc('-');
    print_unsigned((uint64)(-(value + 1)) + 1, 10);
  } else {
    print_unsigned((uint64)value, 10);
  }
}

void
kprintf(const char *format, ...)
{
  va_list args;
  va_start(args, format);

  for (const char *p = format; *p; p++) {
    int wide;

    if (*p != '%') {
      consoleputc(*p);
      continue;
    }
    p++;
    wide = (*p == 'l');
    if (wide)
      p++;
    if (*p == 0) {
      consoleputc('%');
      if (wide)
        consoleputc('l');
      break;
    }

    switch (*p) {
    case 'c':
      consoleputc(va_arg(args, int));
      break;
    case 's': {
      const char *text = va_arg(args, const char *);
      if (text == 0)
        text = "(null)";
      while (*text)
        consoleputc(*text++);
      break;
    }
    case 'd':
      print_signed(wide ? va_arg(args, long) : va_arg(args, int));
      break;
    case 'u':
      print_unsigned(wide ? va_arg(args, unsigned long) : va_arg(args, uint), 10);
      break;
    case 'x':
      print_unsigned(wide ? va_arg(args, unsigned long) : va_arg(args, uint), 16);
      break;
    case '%':
      consoleputc('%');
      break;
    default:
      consoleputc('%');
      if (wide)
        consoleputc('l');
      consoleputc(*p);
      break;
    }
  }
  va_end(args);
}
