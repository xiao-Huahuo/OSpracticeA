/*
 * entry.S — 上电后执行的第一段代码(M 态)。
 * 设计决策:只做"让 C 语言能安全运行"的最小准备,其余 M→S 清单放在 start.c,
 * 职责分层:entry.S=机器事实(栈/核间差异/mtvec),start.c=特权级政策(委托/PMP)。
 */
    .section .text
    .globl _entry
_entry:
    # 1. 关中断:trap 向量尚未就绪,任何中断都是灾难
    csrw    mie, zero

    # 2. 从核(mhartid != 0)自旋等待:启动阶段只有 hart0 干活
    csrr    t0, mhartid
    bnez    t0, park

    # 3. 初始内核栈:course_sid.h 的 LAB1_STACK_KB=12,即 .space 4096*3,
    #    静态分配在本文件的 .bss;sp 指向栈顶(高地址端)
    la      sp, boot_stack_top

    # 4. mtvec:指向极简 park 陷阱处理(任何意外 trap 就地 wfi,便于发现)
    #    标号已 .balign 4 —— mtvec 低 2 位是模式位,基址必须 4 字节对齐
    la      t0, early_trap
    csrw    mtvec, t0

    # 5. 进入 C:call start (M 态,栈已就绪)
    call    start

park:
    wfi
    j       park

    .balign 4
early_trap:
    csrw    mie, zero
    wfi
    j       early_trap

    .section .bss
    .align  16                  # 栈需 16 字节对齐(RISC-V ABI)
    .globl  boot_stack_bottom
boot_stack_bottom:
    .space  4096 * 1            # LAB1_STACK_KB = 4KB = 1 页
    .globl  boot_stack_top
boot_stack_top:
