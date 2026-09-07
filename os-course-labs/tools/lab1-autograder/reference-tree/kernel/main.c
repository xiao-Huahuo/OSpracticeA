/*
 * main.c — 参考实现(学号 20230101,协议 0:明文+换行,无校验和)。
 */
#include "types.h"
#include "riscv.h"
#include "course_sid.h"

void uart_init(void);
void printf(const char *fmt, ...);

static volatile int keep_alive;

void
main(void)
{
    uart_init();

    printf("OSLAB1 sid=%d mod97=0x%x\n", COURSE_SID, COURSE_SID % 97);

    // printf 边界测试(设计规范:0/负数/最大/INT_MIN/空串/超长串)
    printf("t0 zero=%d neg=%d max=%d min=%d empty=[%s]\n",
           0, -7, 2147483647, -2147483647 - 1, "");
    printf("t1 hex=%x esc=100%%\n", 0x48);
    printf("t2 ");
    for(int i = 0; i < 3; i++)
        printf("0123456789abcdefghijklmnopqrstuvwxyz0123456789");
    printf("\n");

    for(;;)
        keep_alive++;
}
