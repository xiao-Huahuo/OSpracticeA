// common.c — lab4 策略测试采样簿记框架(课程组出品,随包交付)
// 全部经 schedstat(pid,...) 观测,不进入内核数据结构;非教学目标。
#include "common.h"

static struct { int pid; int last; int prev; int init; } T[16];

int
cpu_of(int pid)
{
    int cpu, slice;
    if(schedstat(pid, &cpu, &slice) != 0)
        return -1;
    return cpu;
}

int
delta_cpu(int pid)
{
    int cpu, slice;
    if(schedstat(pid, &cpu, &slice) != 0)
        return -1;
    for(int i = 0; i < 16; i++){
        if(!T[i].init){
            T[i].pid = pid; T[i].last = cpu;
            T[i].prev = cpu; T[i].init = 1;
            return 0;                       // 首个窗口无前值,增量记 0
        }
        if(T[i].pid == pid){
            int d = cpu - T[i].prev;
            T[i].prev = cpu;
            return d;
        }
    }
    return -1;
}

void
child_loop(int out_fd)
{
    int i = 0;
    for(;;){
        pause(1);
        if(out_fd >= 0 && ++i % 16 == 0)
            write(out_fd, ".", 1);          // 心跳:证明子进程存活与推进
    }
}

int
burn_forever(void)
{
    for(;;)
        pause(1);
    return 0;
}
