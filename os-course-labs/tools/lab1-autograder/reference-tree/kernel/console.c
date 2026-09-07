/*
 * console.c — 参考实现:串口驱动 + 协议层(课程教师冒烟专用,严禁下发学生)。
 * 学号 20230101:LAB1_BANNER_PROTOCOL=0(明文+换行),无点缀、无校验和;
 * 节流 = 每发 16 + COURSE_SID%16 = 27 字节注入 nop 空转。
 */
#include "types.h"
#include "riscv.h"
#include "memlayout.h"
#include "course_sid.h"

#define UART_THR  0
#define UART_LSR  5
#define UART_LSR_THRE 0x20

static uint32 byte_count;

#define REG(reg) (*(volatile unsigned char *)(UART0 + (reg)))

void
uart_init(void)
{
    REG(3) = 0x03;         // LCR: 8N1, 关 DLAB
}

static void
uartputc_sync(char c)
{
    while((REG(UART_LSR) & UART_LSR_THRE) == 0)
        ;
    REG(UART_THR) = c;
}

static void
throttle(void)
{
    for(int i = 0; i < COURSE_SID % 16 + 16; i++)
        asm volatile("nop");
}

void
consputc(char c)
{
    uartputc_sync(c);
    if(++byte_count >= COURSE_SID % 16 + 16){
        byte_count = 0;
        throttle();
    }
}
