// bench.c — 上下文切换延迟测量(性能验收统一程序)
//
// 方法:父进程与子进程经共享的管道做"乒乓"——每次 ping-pong 强制两次
// 上下文切换(唤醒对方 + 自己睡眠)。用 rdtime 采样墙钟时间,
// 单次切换延迟 = 总耗时 / (2 × 轮数)。
//
// 验收阈值 T:在课程机器上以默认轮转调度的参考实现实测值 × 1.5 公布。
// 学生提交的优化对话记录中应体现"读了 bench 输出→定位→给 AI 指令"的迭代。

#include "common.h"

#define ROUNDS 200

int main(void) {
  int pfd[2];              // 父→子
  int cfd[2];              // 子→父
  pipe(pfd); pipe(cfd);
  char byte = 'x';

  int pid = fork();
  if (pid == 0) {
    close(pfd[1]); close(cfd[0]);
    for (int i = 0; i < ROUNDS; i++) {
      if (read(pfd[0], &byte, 1) != 1) exit(1);
      if (write(cfd[1], &byte, 1) != 1) exit(1);
    }
    exit(0);
  }
  close(pfd[0]); close(cfd[1]);

  unsigned long start = time_rdtime();
  for (int i = 0; i < ROUNDS; i++) {
    write(pfd[1], &byte, 1);
    read(cfd[0], &byte, 1);
  }
  unsigned long end = time_rdtime();
  wait(0);

  unsigned long per_switch = (end - start) / (2UL * ROUNDS);
  printf("RESULT avg_ctx_switch = %lu\n", per_switch);   // autograder 抓取此行
  PASS("bench");
  return 0;
}

// time_rdtime:从用户态读 time。需内核在 usertrap 设置
// sstatus 的 SUM/或提供 rdtime 系统调用——这也是 spec 的一部分:
// 学生的设计文档需声明如何向用户态提供时间戳(系统调用或 mmode 转发),
// 两种方案在验收时等价。
