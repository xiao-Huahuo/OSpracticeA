/*
 * lab1 骨架(自动生成):启动与串口输出。
 * 到这里之前发生了一切 —— 而这一切现在归你铺。
 * 你需要:entry.S(start 前的 M 态准备可另置 start.c)、串口轮询输出、
 * 最小 printf。链接脚本 kernel.ld 带注释保留;底层宏 riscv.h 完整保留。
 * 阅读路线与规格引导问题见《实验说明书(lab1)》。
 *
 * 两个环境要点(说明书 §2"环境前置条件"与附录 C,动手前必读):
 *  1. start() 的 M→S 清单必须包含 PMP 配置(最简两行):
 *       w_pmpaddr0(0x3fffffffffffffull); w_pmpcfg0(0xf);
 *     否则在新版 QEMU 上 mret 进 S 态的第一条取指即 fault(全程零输出)。
 *  2. entry.S 里的陷阱向量标号前加 .balign 4(mtvec 要求 4 字节对齐,
 *     不满足时写入会被静默丢弃)。
 */
