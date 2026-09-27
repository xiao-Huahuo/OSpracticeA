/* Lab 1 module interfaces; UART output is single-hart and synchronous. */
#ifndef LAB1_DEFS_H
#define LAB1_DEFS_H

void kernel_main(void);
void consoleputc(int c);
void kprintf(const char *format, ...);

#endif
