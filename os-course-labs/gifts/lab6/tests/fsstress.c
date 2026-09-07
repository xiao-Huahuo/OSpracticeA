// 官方测试 · lab6-test1:并发读写 + link/unlink 一致性
// 前置:fs 已挂载,open/read/write/link/unlink/close 可用(规范 §1.3)。
// 断言(与 sid 无关):
//   1. N 个子进程各写各的文件,读回逐字节一致(无交叉损坏);
//   2. link+unlink 全程计数正确,unlink 后 open 失败;
//   3. 内核存活,sh 可继续。
#include "kernel/types.h"
#include "kernel/fcntl.h"
#include "user/user.h"

#define N 3
#define PAYLOAD 512

static void
fill(char *b, char seed)
{
    for(int i = 0; i < PAYLOAD; i++)
        b[i] = seed + (i % 13);
}

int
main(void)
{
    char wbuf[PAYLOAD], rbuf[PAYLOAD];
    int pids[N];

    for(int w = 0; w < N; w++){
        pids[w] = fork();
        if(pids[w] == 0){
            char name[16], seed = 'A' + w;
            // 文件名:自描述(便于断链测试定位)
            name[0]='f'; name[1]='0'+w; name[2]=0;
            int fd = open(name, O_CREATE | O_RDWR);
            if(fd < 0){ printf("T1 FAIL: open %s\n", name); exit(1); }
            fill(wbuf, seed);
            for(int r = 0; r < 4; r++)
                if(write(fd, wbuf, PAYLOAD) != PAYLOAD){
                    printf("T1 FAIL: write %s\n", name); exit(1);
                }
            close(fd);
            // 读回校验
            fd = open(name, O_RDONLY);
            for(int r = 0; r < 4; r++){
                if(read(fd, rbuf, PAYLOAD) != PAYLOAD ||
                   memcmp(rbuf, wbuf, PAYLOAD) != 0){
                    printf("T1 FAIL: verify %s round %d\n", name, r);
                    exit(1);
                }
            }
            close(fd);
            exit(0);
        }
    }
    int bad = 0, st;
    for(int w = 0; w < N; w++){ wait(&st); if(st) bad++; }

    // link/unlink 一致性
    if(link("f0", "g0") < 0) bad++;
    if(unlink("f0") < 0) bad++;
    if(open("f0", O_RDONLY) >= 0){ printf("T1 FAIL: f0 should be gone\n"); bad++; }
    int fd = open("g0", O_RDONLY);
    if(fd < 0 || read(fd, rbuf, PAYLOAD) != PAYLOAD || rbuf[0] != 'A') bad++;
    close(fd);
    unlink("g0");

    if(bad == 0){
        printf("T1 PASS: concurrent rw + link/unlink consistent\n");
        exit(0);
    }
    printf("T1 FAIL: %d bad workers\n", bad);
    exit(1);
}
