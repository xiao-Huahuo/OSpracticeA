// 官方测试 · lab5-test1:fork 立即 exec 零复制断言
// 断言(与 sid 无关):子进程 fork 后立刻 exec(hi),全程不写父进程页
// —— 真实现的物理页复制增量应为 0(容忍 ≤2,给栈/guard 的边缘实现留裕度)。
#include "kernel/types.h"
#include "user/user.h"

int
main(void)
{
    unsigned long long c0 = pmc(0);
    int pid = fork();
    if(pid == 0){
        char *argv[2];
        argv[0] = "hi";
        argv[1] = 0;
        exec("hi", argv);          // 立即 exec,不碰任何父进程页
        printf("T5-1 FAIL: exec hi\n");
        exit(1);
    }
    wait(0);
    unsigned long long c1 = pmc(0);
    printf("T5-1 copies: %llu -> %llu (delta %llu)\n", c0, c1, c1 - c0);
    if(c1 - c0 <= 2){
        printf("T5-1 PASS: fork-immediately-exec ~zero copy\n");
        exit(0);
    }
    printf("T5-1 FAIL: 伪 COW(复制次数过多)\n");
    exit(1);
}
