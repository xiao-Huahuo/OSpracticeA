# Lab 0 阅读与剖析

Lab 0 的目标是建立一张能解释 xv6 系统行为的全景地图。本目录的三份 PlantUML 源文件分别对应实验要求的三份核心材料。阅读时应持续回答三个问题：当前是谁在运行、CPU 处于什么特权级、代码使用哪一个栈。

## 一 echo hi 命令的完整生命周期

文件：[01-echo命令生命周期.puml](./01-echo命令生命周期.puml)

这张时序图从 Shell 调用 `read` 等待命令开始，一直画到 echo 退出、Shell 回收子进程并打印下一个提示符。图中包含以下四段。

### Shell 等待输入

Shell 在用户态执行 `getcmd -> gets -> read`。`read` 的用户态桩把系统调用号放入 `a7`，再执行 `ecall`。CPU 进入 S 态后先执行 `trampoline.S` 中的 `uservec`，保存用户寄存器、切换页表和栈，然后进入 `usertrap -> syscall -> sys_read -> fileread -> consoleread`。

控制台正在积累一行输入时，Shell 登记等待通道 `&cons.r`，释放 `cons.lock`，通过 `sleep -> sched` 把 CPU 交还给调度器。Shell 此时处于 `SLEEPING` 状态。

### 键盘中断唤醒 Shell

键盘字符先到达 QEMU 模拟的 UART。UART 触发外部中断；Shell 已经睡眠且 CPU 正在内核或调度器中等待时，路径是 `kerneltrap -> devintr -> uartintr -> consoleintr`。如果中断恰好打断另一个用户进程，则先经过 `uservec -> usertrap`，再由 `devintr` 进入相同的 UART 处理路径。`consoleintr` 持有 `cons.lock`，把字符回显到终端并写入 `cons.buf`。收到换行后，它公布这一整行并调用 `wakeup(&cons.r)`，Shell 变回 `RUNNABLE`。

调度器重新选择 Shell 后，先恢复 Shell 的内核调用现场。`consoleread` 把缓冲区字符复制到用户空间，系统调用通过 `prepare_return -> userret -> sret` 返回 U 态。用户库里的 `gets` 会反复调用单字节 `read`，直到读到换行。

### fork 和 exec

Shell 解析 `echo hi` 后调用 `fork`。内核的 `kfork` 创建子进程，复制用户地址空间、trapframe 和文件描述符。父 Shell 得到子 PID，随后进入 `wait`；子进程得到返回值 0，进入 `runcmd` 并调用 `exec("echo", argv)`。

`exec` 沿用当前子进程，在其中装入 echo 的 ELF 映像并建立新的用户栈。子进程 PID、父子关系以及打开的控制台文件描述符全部保持原有关系。成功返回用户态时，执行位置已经是 `echo.main`。

### write 和 exit

echo 通过 `write(1, "hi", 2)` 和 `write(1, "\n", 1)` 输出结果。内核路径是 `sys_write -> filewrite -> consolewrite -> uartwrite`。`uartwrite` 使用 `tx_lock` 串行化输出，再通过 UART 的 THR 寄存器把字符交给 QEMU 终端。

echo 最后调用 `exit`。`kexit` 关闭文件、保存退出码、把进程设为 `ZOMBIE`，然后唤醒等待它的 Shell。Shell 的 `kwait` 回收子进程资源并返回，随后开始读取下一条命令。

## 二 exec 后的核心数据结构快照

文件：[02-exec后核心数据结构快照.puml](./02-exec后核心数据结构快照.puml)

这张对象图选择的截面是：echo 子进程已经完成 `kexec`，下一步将执行 `echo.main` 的第一条用户指令。图分成三个互相关联的部分。

### 进程表

图中保留 `init`、父 Shell 和 echo 子进程。父 Shell 通常睡眠在 `wait` 中；echo 仍在内核里准备返回用户态，因此处于 `RUNNING`。每个进程都有独立的 `pagetable`、`trapframe`、内核栈和用户地址空间。echo 的 `parent` 仍然指向 Shell。

PID 使用 `P_init`、`P_sh` 和 `P_echo` 表示，以突出各进程之间稳定的结构关系；一次具体运行可以再填入现场观察到的数字。

### echo 页表

SV39 使用三级页表。图中从 L2 根页表经过 L1、L0 叶子页表连接到 echo 的代码、数据、guard page、用户栈和将来可扩展的堆。

最高地址处有两个固定映射：`TRAMPOLINE = MAXVA - PGSIZE`，权限为 S 态可读和可执行；其下一页是 `TRAPFRAME`，权限为 S 态可读写。两页都设置 `PTE_U = 0`，将访问权限限定在 S 态。guard page 同样设置 `PTE_U = 0`，用于捕获用户栈越界。

### 标准输出引用链

fork 会增加父进程文件对象的引用计数，所以 Shell 和 echo 的 `ofile[1]` 共同指向控制台 `struct file`。该对象类型为 `FD_DEVICE`，其 `major` 为 `CONSOLE`，再通过 `devsw[CONSOLE].write` 找到 `consolewrite`，最终连接到 UART 驱动。

exec 保留文件描述符，因此 echo 直接沿用 fd 1 并调用 `write(1, ...)` 输出。echo 退出时减少引用计数，Shell 持有的引用让控制台文件对象继续存活。

## 三 一次时钟中断的微观旅程

文件：[03-时钟中断旅程.puml](./03-时钟中断旅程.puml)

这张时序图描述一个用户进程运行时收到 supervisor timer interrupt 的全过程，对应 `scause = 0x8000000000000005`。

### 进入内核

中断到达后，CPU 自动把用户 PC 保存到 `sepc`，写入 `scause` 和 `sstatus`，关闭当前中断并跳转到 `stvec`。此刻 CPU 已进入 S 态，但仍使用用户页表和用户栈，因此必须先执行同时映射在两套页表中的 trampoline。

`uservec` 把用户寄存器保存到固定地址的 trapframe，从 trapframe 取得内核栈、内核页表和 `usertrap` 地址，然后完成切换。

### 处理中断并让出 CPU

`usertrap` 调用 `devintr` 识别时钟中断。CPU 0 在 `tickslock` 保护下增加全局 `ticks` 并唤醒等待时间的进程；每个 CPU 都重新设置自己的 `stimecmp`，预约下一次时钟中断。

返回值 `which_dev == 2` 表明这是时钟中断，于是当前进程执行 `yield`：持有自己的 `p->lock`，把状态从 `RUNNING` 改成 `RUNNABLE`，再通过 `sched -> swtch` 切换到调度器栈。调度器可能选择另一个进程，也可能再次选择原进程。

### 返回用户态

原进程再次得到 CPU 后，执行从 `yield` 后面继续。`prepare_return` 设置下一次用户陷阱入口、内核栈和 `sepc`，并把 `sstatus.SPP` 清零，表明 `sret` 应返回 U 态。

最后，`userret` 切换回用户页表，从 trapframe 恢复所有用户寄存器。`sret` 把 PC 恢复为 `sepc`，用户程序从被中断的位置继续运行。

## 对照源码

- Shell 命令循环和命令执行：`xv6-riscv/user/sh.c`
- echo 用户程序：`xv6-riscv/user/echo.c`
- 用户系统调用桩：`xv6-riscv/user/usys.pl`
- 用户态和内核态切换：`xv6-riscv/kernel/trampoline.S`
- 陷阱与时钟中断：`xv6-riscv/kernel/trap.c`
- 系统调用分派：`xv6-riscv/kernel/syscall.c`
- 文件系统调用：`xv6-riscv/kernel/sysfile.c`
- 进程创建、退出、等待和调度：`xv6-riscv/kernel/proc.c`
- 控制台缓冲区：`xv6-riscv/kernel/console.c`
- UART 驱动：`xv6-riscv/kernel/uart.c`
- exec 加载过程：`xv6-riscv/kernel/exec.c`
- 页表和地址空间：`xv6-riscv/kernel/vm.c`、`kernel/memlayout.h`

## 渲染方法

安装 PlantUML 后，可以在项目根目录执行：

```bash
plantuml labs/lab0/*.puml
```

也可以在支持 PlantUML 的编辑器插件中直接预览。每次修改图后，应重新核对函数调用顺序、特权级、栈和锁是否一致。
