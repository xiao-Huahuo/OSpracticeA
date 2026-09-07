// 官方测试 · lab5-test2:COW 配对写与计数对账
// 断言(与 sid 无关):
//   1. fork 后、写之前,共享页计数 > 0(pmc(1));
//   2. 父子各写同一页:各得独立副本且互不串数据;
//   3. 两次写触发恰好 2 次物理复制(pmc(0) 增量 == 2)。
#include "kernel/types.h"
#include "user/user.h"

static volatile int child_done;

int
main(void)
{
    // 在栈附近放一页可写页(sbrk)
    char *page = sbrk(4096);
    if(page == (char *)-1){ printf("T5-2 FAIL: sbrk\n"); exit(1); }
    for(int i = 0; i < 4096; i++) page[i] = 0x11;

    unsigned long long c0 = pmc(0);
    int pid = fork();
    if(pid == 0){
        unsigned long long s1 = pmc(1);
        if(s1 == 0) printf("T5-2 WARN: fork 后共享计数为 0(检查你的计数时机)\n");
        for(int i = 0; i < 4096; i++) page[i] = 0x22;   // 子写:触发复制
        for(int i = 0; i < 4096; i++)
            if(page[i] != 0x22){ printf("T5-2 FAIL: child read-back\n"); exit(1); }
        exit(0);
    }
    for(int i = 0; i < 4096; i++) page[i] = 0x33;       // 父写:触发复制
    for(int i = 0; i < 4096; i++)
        if(page[i] != 0x33){ printf("T5-2 FAIL: parent read-back\n"); exit(1); }
    int st; wait(&st);
    unsigned long long c1 = pmc(0);
    printf("T5-2 copies delta = %llu (expect 2)\n", c1 - c0);
    if(st == 0 && c1 - c0 == 2){
        printf("T5-2 PASS: pair-write exact 2 copies, data isolated\n");
        exit(0);
    }
    printf("T5-2 FAIL\n");
    exit(1);
}
