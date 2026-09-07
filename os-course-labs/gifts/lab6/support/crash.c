// crash.c — lab6 受控断电驱动(课程提供,完整保留,排雷/验收环境组件)
//
// 原理:QEMU virt 机器带有 SiFive test device(MMIO @ 0x100000),
// 向它写入 0x7777 = 整机复位(system_reset 语义),0x5555 = 关机。
// 复位后 QEMU 重新加载 kernel/fs.img 并走文件系统恢复路径 —— 这就是
// "受控断电"的全部机制,无需 QEMU monitor 交互。
//
// 集成(教师/TA 操作,或学生按 spec 自行接线):
//   1. 本文件放入 kernel/;Makefile 的 KEROBJ 追加 crash.o
//   2. syscall.h/syscall.c/usys.pl 注册系统调用 crash_at(建议编号 55,
//      避开 lab5 的个性化系统调用号区间 22+sid%37 起)
//   3. 崩溃断点的实际插入位置在学生自己的 log.c 中:
//      在 begin_op/日志写/签名/install 各阶段调用 crash_at(stage) —
//      断点位置属于学生 spec 的一部分(阶段命名须在提交中声明),
//      本文件只提供复位原语与课程约定的参考阶段编号。

#include "types.h"
#include "riscv.h"
#include "defs.h"

#define TEST_DEVICE_PA 0x100000
#define RESET_CODE     0x7777

// 课程约定的参考阶段(与《实验说明书 lab6》§4 的崩溃表对应;
// 学生可按自己的 spec 细分,但编号 1–5 的语义必须保持):
#define CRASH_BEGIN_AFTER   1   // begin_op 之后、首个 log_write 之前
#define CRASH_LOG_HALF      2   // 日志块写了一半
#define CRASH_HEADER_DONE   3   // 签名块(n)写完、install 之前
#define CRASH_INSTALL_HALF  4   // install 进行到一半
#define CRASH_DONE          5   // end_op 全部完成后(验证正常路径可复位)

void
crash_at(int stage)
{
  // 打印阶段号:重启前的最后一行输出,供崩溃表断言脚本定位
  printf("crash: stage %d\n", stage);
  *(volatile uint64 *)TEST_DEVICE_PA = RESET_CODE;
  // 不会到达这里;到达说明复位原语失效(环境问题,报告 TA)
  panic("crash_at: reset failed");
}

// 用户态接口:int crash_at(int stage);
uint64
sys_crash_at(void)
{
  int stage;
  if(argint(0, &stage) < 0 || stage < 1 || stage > 5)
    return -1;
  crash_at(stage);
  return 0;
}
