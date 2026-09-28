/* Shared startup, console, and trap interfaces for the boot hart. */
#ifndef LAB1_DEFS_H
#define LAB1_DEFS_H

void kernel_main(void);
void consoleputc(int c);
void consoleinit(void);
int consolegetc(int block);
void kprintf(const char *format, ...);
void trapinit(void);
void uartintr(void);

#endif
