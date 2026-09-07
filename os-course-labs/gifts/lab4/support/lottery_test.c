// lottery_test.c — 彩票调度份额断言
//
// 断言:彩票数为 tickets_i 的进程,其 CPU 占比 ≈ tickets_i / TOTAL
// (TOTAL = PARAM_LOTTERY_TOTAL),容差 ±15%。
// 变体(5:转让 / 8:通胀)共用本测试:autograder 按变体在运行前通过
// 命令行注入额外参数,本文件的份额守恒断言对两种变体同样成立——
// 转让只是重新分配票数,通胀只是改变票数但比例语义不变。

#include "common.h"

int main(int argc, char *argv[]) {
  // autograder 注入:两个进程的票数,默认占总票的比例约 2:1
  int t1 = argc > 1 ? atoi(argv[1]) : 60;
  int t2 = argc > 2 ? atoi(argv[2]) : 30;

  int fd[2];
  pipe(fd);

  int p1 = fork();
  if (p1 == 0) { setickets(t1); close(fd[0]); child_loop(fd[1]); exit(0); }
  int p2 = fork();
  if (p2 == 0) { setickets(t2); close(fd[0]); child_loop(fd[1]); exit(0); }

  close(fd[1]);
  int RUN_TICKS = 300;              // 观测总时长
  sleep(RUN_TICKS);
  // 采样必须在子进程存活期完成(schedstat 对已退出进程返回 -1)
  int c1 = cpu_of(p1), c2 = cpu_of(p2);
  kill(p1); kill(p2); wait(0); wait(0);
  ASSERT(c1 + c2 > RUN_TICKS / 2, "总 CPU 采样过少,调度疑似未运行");

  double share1 = (double)c1 / (c1 + c2);
  double expect = (double)t1 / (t1 + t2);
  ASSERT(share1 > expect - 0.15 && share1 < expect + 0.15,
         "CPU 份额与彩票比例偏差超过 ±15%");

  PASS("lottery");
  return 0;
}

// child_loop / cpu_of 由测试框架提供(读取各子进程 schedstat 累计值并
// 经管道/父进程采样汇总),此处省略——统一测试运行器负责采样簿记。
