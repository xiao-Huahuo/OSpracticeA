// stride_test.c — 步长调度公平性断言
//
// 断言:任意时刻,票数为 t_i 的进程累计"运行量"满足步长调度的有界公平性:
//     | runs_i - runs_j | 与 1/t_i : 1/t_j 的比例一致,且
//     各进程 pass 值之差有界(有界 = max_stride × 2)。
// 用户态无法直接读 pass,因此用间接形式断言:
//     cpu_i / cpu_j ≈ t_j / t_i(票多者多跑),容差 ±20%;
//     且任意两次采样窗口内,任何进程不会被连续冷落超过 K 个窗口
//     (K = 票数最小进程的相对步长上限,防"批量追赶"实现退化)。

#include "common.h"

int main(int argc, char *argv[]) {
  int t1 = PARAM_STRIDE_TICKETS_MIN;          // 票少(如 5)
  int t2 = PARAM_STRIDE_TICKETS_MIN * 3;      // 票多(3 倍)

  int p1 = fork();
  if (p1 == 0) { setickets(t1); burn_forever(); }
  int p2 = fork();
  if (p2 == 0) { setickets(t2); burn_forever(); }

  // 采样 8 个窗口,每窗口 100 tick
  int cpu1[8], cpu2[8];
  for (int w = 0; w < 8; w++) {
    sleep(100);
    cpu1[w] = delta_cpu(p1);        // 本窗口增量,框架经 schedstat 差分
    cpu2[w] = delta_cpu(p2);
  }
  kill(p1); kill(p2); wait(0); wait(0);

  int total1 = 0, total2 = 0;
  for (int w = 0; w < 8; w++) { total1 += cpu1[w]; total2 += cpu2[w]; }

  // 断言 1:总量比例 ≈ 1:3(容差 ±20%)
  double ratio = (double)total2 / (double)(total1 ? total1 : 1);
  ASSERT(ratio > 3 * 0.8 && ratio < 3 * 1.2, "CPU 分配比与票数反比关系不成立");

  // 断言 2:无冷落——每个窗口两个进程都应获得 CPU(步长调度轮转紧凑)
  for (int w = 0; w < 8; w++) {
    ASSERT(cpu1[w] > 0 && cpu2[w] > 0, "存在整窗口未被调度的进程(pass 有界性被破坏)");
  }

  PASS("stride");
  return 0;
}

// burn_forever / delta_cpu 由测试框架提供,同 lottery_test.c 的说明。
