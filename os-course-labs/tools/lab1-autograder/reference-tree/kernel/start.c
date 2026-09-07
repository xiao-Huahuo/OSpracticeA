/*
 * start.c — M 态下的最后一站:完成 M→S 清单后 mret 进入 main()。
 * 清单顺序即设计:先关中断相关项,再委托,再 PMP,最后 mepc/mstatus,mret 收尾。
 */
#include "types.h"
#include "riscv.h"

void start(void);
void main(void);
void uart_init(void);

void
start(void)
{
    // 1. 委托:全部中断与异常交给 S 态处理(M 态不再接管)
    w_medeleg(0xffff);
    w_mideleg(0xffff);

    // 2. PMP 授权:S 态取指与访存必须落在 PMP 允许的物理区内。
    //    NAPOT 模式覆盖全部物理地址空间,R/W/X=1,L=0(锁定位不开,便于后续实验)
    w_pmpaddr0(0x3fffffffffffffull);
    w_pmpcfg0(0xf);

    // 3. mstatus.MPP = S:mret 后降入 S 态;关全局中断(MIE=0)
    unsigned long x = r_mstatus();
    x &= ~MSTATUS_MPP_MASK;
    x |= MSTATUS_MPP_S;
    w_mstatus(x);

    // 4. mepc = main(S 态入口),mret 一步到位
    w_mepc((uint64)main);

    // 5. satp = 0:Bare 模式直译物理地址。设计决策:启动阶段无页表,
    //    恒等映射徒增工作量,Bare 足够;页表留给 lab3
    w_satp(0);

    asm volatile("fence.i");
    asm volatile("mret");
}
