/*
 * printf.c — 最小格式化打印:支持 %d %x %c %s %%。
 * 边界规范(设计笔记预先确立):0 直接印;负数带 '-' 号印绝对值;
 * INT_MIN 用无符号取模避免溢出;空串印空;超长串逐字符发射不做截断。
 */
#include "types.h"
#include "riscv.h"
#include <stdarg.h>

void consputc(char c);

static void
printint(long long xx, int base, int sign)
{
    char buf[20];
    int i = 0;
    unsigned long long x;
    if(sign && xx < 0){
        consputc('-');
        x = (unsigned long long)(-(xx + 1)) + 1;  // INT_MIN 安全取正
    } else {
        x = (unsigned long long)xx;
    }
    do {
        buf[i++] = "0123456789abcdef"[x % base];
        x /= base;
    } while(x != 0);
    while(--i >= 0)
        consputc(buf[i]);
}

void
printf(const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    for(int i = 0; fmt[i]; i++){
        char c = fmt[i];
        if(c != '%'){
            consputc(c);
            continue;
        }
        c = fmt[++i];
        if(c == 'd'){
            printint(va_arg(ap, int), 10, 1);
        } else if(c == 'x'){
            printint((long long)va_arg(ap, unsigned int), 16, 0);
        } else if(c == 'c'){
            consputc((char)va_arg(ap, int));
        } else if(c == 's'){
            char *s = va_arg(ap, char *);
            if(s == 0) s = "(null)";
            while(*s)
                consputc(*s++);
        } else if(c == '%'){
            consputc('%');
        } else {
            // 未知转换符:原样吐出,便于发现格式笔误
            consputc('%');
            consputc(c);
        }
    }
    va_end(ap);
}
