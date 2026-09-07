// common.h — 策略断言测试公共设施
// 仅依赖 schedstat 系统调用的规格语义(见 kernel_patch/schedstat.patch 头注释)

#ifndef _LAB4_COMMON_H
#define _LAB4_COMMON_H

#include "kernel/types.h"
#include "user/user.h"

// 由 autograder 按 -DSID=<学号> 注入,断言阈值据此计算
#ifndef SID
#define SID 0
#endif

#define PARAM_MLFQ_QUEUES  (3 + SID % 3)
#define PARAM_MLFQ_MULT    (1 + SID % 2)      // 片长 (1,2,4)×MULT
#define PARAM_LOTTERY_TOTAL (100 + SID % 50)
#define PARAM_STRIDE_TICKETS_MIN (5 + SID % 15)

int schedstat(int pid, int *cpu_ticks, int *last_slice_ticks);

// 测试程序用 sleep(...) 命名;课程调用号表为 pause(见 syscall.h)
#define sleep(t) pause(t)

// 采样簿记框架(common.c 提供,统一实现"经 schedstat 差分/汇总"):
int   cpu_of(int pid);        // 目标进程累计 CPU tick(存活期查询)
int   delta_cpu(int pid);     // 距上次本函数调用的窗口增量(每窗口每 pid 恰调一次)
void  child_loop(int out_fd); // 子进程体:周期性让出(如需保活可向 fd 写心跳)
int   burn_forever(void);     // 子进程体:周期性让出的纯 CPU 负载

#define ASSERT(cond, msg) do { \
  if (!(cond)) { \
    printf("FAIL: %s (at %s:%d)\n", msg, __FILE__, __LINE__); \
    exit(1); \
  } \
} while (0)

#define PASS(msg) do { printf("PASS: %s\n", msg); exit(0); } while (0)

// 等待并收集一个子进程经管道传来的采样值
static inline int sample_child(int read_fd, int *out) {
  return read(read_fd, out, sizeof(int)) == sizeof(int) ? 0 : -1;
}

#endif
