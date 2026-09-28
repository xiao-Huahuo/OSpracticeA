# Lab 2：陷入、中断与用户态

Lab 2 接在 Lab 1 的内核上。现在 QEMU 启动后仍先打印原来的 Banner 和两行自检，随后进入 `sh>`；输入 `hi` 可以运行用户程序，输入 `badecall` 可以检查非法系统调用。下面按一次命令从键盘进入内核、运行程序、返回 Shell 的顺序解释代码。

## 要求落在哪些文件

| 实验要求 | 实现位置 | 实际检查 |
|---|---|---|
| 用户态与内核态切换，保存寄存器 | 课程 `trampoline.S`、`trampoline_wrap.S`、`trap.c`、`proc.h` | `hi`、`spin` 在用户态运行；QEMU 日志只有预期陷入 |
| 系统调用号、参数与错误码 | 课程 `syscall.h`、新建 `syscall.c` | `badecall` 返回 PASS，`badptr` 拒绝内核地址 |
| UART 接收、输入缓冲与时钟中断 | `console.c`、`trap.c`、`start.c` | `bufstorm`、连续输入和 `spin` 时敲键盘 |
| `fork`、`exec`、`wait` 与内嵌程序 | `proc.c`、`swtch.S`、`vm.c`、`kalloc.c` | `sh` 执行 `hi` 后重新出现提示符，连续执行 40 次仍正常 |
| Lab 1 串口回归 | 保留 `main.c` 的 Banner 与自检 | `test_lab1.py` 核对开机前三行 |

课程赠送的跳板、用户库、用户程序和系统调用号表保持原样。`Makefile.upgrade` 负责编译用户程序，个人 `Makefile` 负责把生成的二进制表链接进内核。`badecall`、`bufstorm` 通过两个薄包装文件从课程测试目录编译；`inputcheck` 和 `badptr` 是本轮新增的边界测试。

## 为什么提前接入地址映射

课程跳板固定从高地址读取 trapframe，赠送的用户程序从地址 0 链接。QEMU 的实际 RAM 从 `0x80000000` 开始；若保持 `satp=0`，这两处地址都指不到可用 RAM。为了让课程赠送文件原样运行，本轮提前建立一张最小的 Sv39 页表：内核原有 RAM 仍用相同地址访问，UART 和 PLIC 设备也映射进去；每个进程把自己的程序放在用户虚拟地址 0，并把 trapframe 与跳板映射到赠送代码约定的高地址。

`trampoline_wrap.S` 只负责让赠送的 `trampoline.S` 进入可执行、页对齐的段，运行指令仍来自赠送文件。构建时核对 `trampoline` 的页对齐和长度，用户页表在高地址映射该页。trapframe 所在页留给 S 态，用户代码的页设置 `PTE_U`；`badptr` 用系统调用试读写 trapframe 地址，内核返回 `-1`。这张页表解决当前地址约定，完整的内存管理仍归后续实验。

## 一次命令怎样经过内核

```text
QEMU 启动 → 内核建立页表与中断 → sh 在 U 态打印 sh>
键盘字节 → UART 中断 → console.c 输入环形缓冲 → 等待 read 的 sh
sh 输入 hi → fork 复制用户页 → 子进程 exec 装入内嵌 hi
hi 执行 ecall → trampoline 保存寄存器 → usertrap 分发系统调用
hi exit → 父进程 wait 回收子进程 → sh 再次打印 sh>
```

RISC-V 执行 `ecall` 时把当前地址放入 `sepc`、记录原因并跳到 `stvec`。硬件保留特权级状态，但通用寄存器、内核栈和下一条指令地址都由软件处理。赠送的 `uservec` 先用 `sscratch` 暂存用户 `a0`，将 31 个通用寄存器保存到当前进程的 trapframe，再换到该进程的内核栈与内核页表。`proc.h` 中 `a0` 和 `t6` 的偏移由编译期检查分别固定在 112 与 280 字节。

`usertrap` 遇到用户 `ecall` 时把保存的 `epc` 加 4，随后从 `a7` 取调用号、从 `a0` 至 `a2` 取参数。`syscall.c` 对当前实现的调用使用 `switch` 分发，其他号码统一返回 `-1`。读写用户地址之前，`vmaddr` 核对页表和用户权限；`badptr` 覆盖了这条错误路径。返回用户态前，`usertrapret` 把 `stvec` 切回用户入口，设置 `sepc` 与 `sstatus`，课程 `userret` 恢复寄存器后执行 `sret`。内核执行期间的中断走独立的 `kernelvec`，从而保住被打断的内核寄存器。

每个进程拥有自己的内核栈、trapframe、页表和用户页。`fork` 分配新页并复制父进程的程序和栈，让子进程的返回值为 0；`exec` 先构造新映像，成功后替换旧页表。`wait` 找到退出的子进程后释放这些页。等待时，内核在关中断状态下完成“检查条件、登记睡眠、切换出去”，子进程退出后再唤醒父进程，避免错过通知。调度器只选择当前可运行的进程，Lab 2 先使用单核；`spin` 运行时由时钟中断打断并返回。

## 键盘输入如何交给 Shell

当前学号使用 `LAB2_BUF_SIZE=128` 和 `LAB2_BUF_SEMANTICS=1`。UART 接收中断把字符写进 128 字节环形缓冲，每收到一个字符就唤醒等待读取的进程；`read` 取走当时可用的字符。生产者是中断处理函数，消费者是系统调用，双方更新读写位置时都屏蔽本核中断。缓冲区满时丢弃新到的字节，课程测试允许超长输入出现这类丢弃；容量内的连续 64 字节由 `inputcheck` 验证，计数和校验和均正确。

时钟比较器以 1,000,000 个 `time` 计数作为基本周期，再乘上 `LAB2_TICK`；当前学号参数为 1。PLIC 把 UART 中断交给 S 态，QEMU 的 `-d int` 日志在交互测试中同时记录到用户 `ecall`、S 态时钟中断和 UART 外部中断。日志中的其他异常会让自动测试失败。

## 验收过程

这次直接在当前项目操作，使用的就是已经完成 Lab 2 的代码。打开 VS Code 下方的终端，按下面顺序做。

1. 进入内核目录，清理上次编译的文件，再编译并启动：

   ```bash
   cd /Users/slumpyfufu/Desktop/Projects/OSpracticeA/2024302111239-kernel
   make clean
   make CC=riscv64-elf-gcc LD=riscv64-elf-ld OBJCOPY=riscv64-elf-objcopy qemu
   ```

   终端先显示编译命令，然后打印 Lab 1 的 Banner 和两行自检，接着出现 `sh>`。看到 `sh>`，就表示可以输入命令了。链接时的 `LOAD segment with RWX permissions` 提示来自课程链接脚本，后面的命令仍会正常运行。

2. 在 `sh>` 后输入 `hi`，按回车。应看到 `hi: user program running, pid=2`，随后再次出现 `sh>`。这里的进程号会随执行次数增加，重点是程序能打印、Shell 能回来。

3. 继续输入 `badecall`，应看到 `TEST-1 PASS: unknown syscalls all return -1`，随后回到 `sh>`。输入 `badptr`，应看到 `BADPTR PASS`。这两项分别检查错误的系统调用和错误的内存地址有没有得到安全处理。

4. 输入 `bufstorm` 后，依次输入 `one`、`two`、`three`、`four`，每输入一行都按回车。四行输入结束后应看到 `BUFSTORM lines=4 bytes=19`，然后回到 `sh>`。键盘输入和程序回显可能让同一行文字出现两次。

5. 输入 `spin`。屏幕会继续显示 `spin 0`、`spin 1` 等数字；这时输入 `abc` 并按回车，应能看到 `abc` 出现在终端，数字继续增加。`spin` 会一直运行，按 `Control+A`，松开后按小写 `x` 退出 QEMU。

6. 回到命令提示符后，运行自动测试。它会自己启动和关闭 QEMU，还会检查容量以内的连续 64 字节输入，以及 Lab 1 原来的输出：

   ```bash
   python3 ../labs/lab2/test_lab2.py
   python3 ../labs/lab1/test_lab1.py
   ```

   两条命令通过时，分别显示 `Lab 2 QEMU interaction: PASS` 和 `Lab 1 serial output: PASS`。检查结束后可运行 `make clean` 清掉编译文件，日常代码仍留在当前的 `master` 分支。

课程赠送的 `inject_uart.py` 会把本轮的 `sh>` 误认成启动失败，因此它的 `boot TIMEOUT` 属于提示符不匹配；最终以上面两条实跑测试检查启动、输入和程序运行。

## 实测结果与当前边界

2026 年 9 月 28 日，干净构建和两项 QEMU 测试通过。另一次连续执行 40 条 `hi` 命令，每次都返回 Shell，确认子进程页和状态可以重复回收。赠送文件与 Lab 2 压缩包逐字节一致，跳板入口在页边界且代码位于同一页。链接器仍对课程脚本的 RWX 加载段发出提示，启动和交互结果正常。

课程赠送的 `support/inject_uart.py` 固定等待 `$ ` 提示符并要求 `fs.img`，而赠送的 Shell 打印 `sh>`，本实验也尚无文件系统。用临时空镜像运行该脚本时，它报告 `boot TIMEOUT`，随后注入 `hi` 的 `EXPECT` 返回 PASS。随 Lab 文档提供的 `test_lab2.py` 直接使用 QEMU 串口完成可复现的交互验收，保留了赠送脚本的原始内容。

内嵌程序表只保存平铺二进制的起止地址，`proc_exec` 据此分配程序页和一页用户栈。课程提供的 `sh`、`hi`、`spin` 及本轮测试程序均在该布局下运行；后续若程序的 BSS 跨过镜像末页，需要在程序表中加入内存长度信息，再扩展加载器。本轮交付节点标记为 `lab2-submit`。
