# Lab 1 设计文档：启动与串口输出

本笔记对应仓库中的 `lab1-submit` 标签。该提交从课程给出的个人内核骨架出发，让 QEMU 启动后进入 S 态的 `kernel_main`，经串口打印学号 Banner 和两行自检。当前 `master` 已继续开发到 Lab 2，阅读 Lab 1 源码时以该标签为准；实际操作和屏幕结果单独保存在 [lab1验收.md](./lab1验收.md)。

## 实现范围与文件分工

说明书要求从上电入口走到第一行输出，并能解释沿途的特权级、地址和寄存器变化。实际修改集中在 `kernel/entry.S`、`kernel/start.c`、`kernel/console.c`、`kernel/printf.c`、`kernel/main.c`。`defs.h` 声明跨文件函数，`expect_banner.txt` 固定首行预期字节，Makefile 补充头文件依赖。课程预置的 `kernel.ld`、`riscv.h`、`types.h`、`memlayout.h` 和 `course_sid.h` 保持原样。

启动顺序见 [启动时序图源码](./01-启动时序.puml)或[同名 PNG](./01-启动时序.png)。图中标出 M 态汇编入口、M 态配置函数和 S 态主函数之间的交接。`satp=0` 是本实验的地址选择，后续 Lab 2 的运行方式另见其文档。

## 从上电地址到 C 函数

QEMU virt 从 `0x1000` 的引导 ROM 执行，`-bios none` 表示没有另行加载外部固件。QEMU 的引导代码仍把执行权交给 ELF 入口 `_entry`。课程预置链接脚本把内核基址设为 `0x80000000`，此处也是机器 RAM 的起点；地址 `0x0` 不在这块 RAM 内。`readelf` 对 Lab 1 ELF 的检查记录显示 `_entry=0x80000000`。

`entry.S` 在 M 态先关中断，再读取 `mhartid`。只有 hart 0 清零 BSS 并进入 C 函数，其余 hart 停在 `park` 的等待循环。清零范围从 `bss_start` 到链接器给出的 `kernel_end`，覆盖初始栈和未初始化的全局变量。栈由 `LAB1_STACK_KB=4` 指定，在 BSS 内占 4096 字节；清零完成后，`sp` 指向 16 字节对齐的 `stack0_top`。这样 `start` 和后续 C 函数进入时已有可用栈。

说明书要求逐条解释入口汇编。下表按源码顺序列出运行时指令；标签和 `.balign`、`.space` 在其后说明。

| 指令 | 作用 |
|---|---|
| `csrci mstatus, 8`；`csrw mie, zero` | 清 MIE 和 M 态中断使能，初始化期间先保持中断关闭。 |
| `csrr t0, mhartid`；`bnez t0, park` | 读取核号，让非零 hart 进入等待循环。 |
| `la t0, mtrap`；`csrw mtvec, t0` | 把 M 态早期异常入口写入 `mtvec`。 |
| `la t0, bss_start`；`la t1, kernel_end` | 取得 BSS 清零的起止地址。 |
| `bgeu t0, t1, bss_done` | 游标到达末尾时跳出循环。 |
| `sb zero, 0(t0)`；`addi t0, t0, 1`；`j clear_bss` | 清当前字节，向前移动，再检查边界。 |
| `la sp, stack0_top`；`call start` | 设置栈顶并调用 M 态 C 初始化函数。 |
| `wfi`；`j park` | 非零 hart 或意外返回的 hart 留在等待循环。 |
| `j mtrap`；`j strap` | 早期异常停在对应入口，方便查看 QEMU 异常日志。 |

`.balign 4` 让 `_entry`、`mtrap` 和 `strap` 按 4 字节对齐，满足向量入口地址的对齐要求；`.balign 16` 对齐栈边界。`.space LAB1_STACK_KB * 1024` 分配栈空间。这些是汇编期布局指示，并非 CPU 执行的指令。

## M 态交给 S 态前的配置

`start.c` 读取 `mstatus` 后清除旧 MPP、MIE、MPIE 和 SIE 位，再设置 `MPP=S`。`mepc` 指向 `kernel_main`。执行 `mret` 时，CPU 按 MPP 选择 S 态，并从 `mepc` 指定的地址继续执行。这个顺序使 Lab 1 的主函数在 S 态运行，同时保持早期中断关闭。

异常与中断委托分别写入 `medeleg`、`mideleg`，S 态向量 `stvec` 指向对齐的 `strap`。此时 `strap` 只让异常停住，方便定位；完整的陷阱处理属于后续实验。`satp=0` 选择 Bare 模式，接着执行 `sfence.vma`，因此本轮内核按物理地址取指和访问设备，无需建立页表。PMP 条目 0 设为覆盖物理地址空间的 NAPOT 区域，权限为读、写、执行。它允许 S 态从 RAM 取指，并访问 UART 的内存映射寄存器；缺少这项权限时，实测 QEMU 在 `mret` 后报告 instruction access fault。

[物理内存布局图源码](./02-物理内存布局.puml)及[同名 PNG](./02-物理内存布局.png)把引导 ROM、UART 和 RAM 分开标示。RAM 中的节顺序来自预置 `kernel.ld`，具体节大小由链接结果决定；图中不臆造每个节的固定末地址。`kernel_end` 是这次清 BSS 的边界，Lab 1 没有继续使用它分配页。

## 首行输出如何形成

`kernel_main` 调用 `kprintf`，后者把格式中的数字和字符串逐字节交给 `consoleputc`。控制台把 UART0 基址 `0x10000000` 作为 `volatile uint8` 指针：先轮询偏移 5 的线路状态寄存器，等 bit 5（THRE）为 1，再写偏移 0 的发送保持寄存器。Lab 1 只有启动 hart 输出，发送过程采用轮询。

格式化器支持 `%c`、`%s`、`%d`、`%u`、`%x`、对应的 `l` 长整数格式及 `%%`。有符号最小值先处理 `value + 1` 再转为无符号数，避免直接取负溢出。十六进制使用小写数字，`0x` 前缀由调用者写入格式串。首行的学号来自 `COURSE_SID=2024302111239`，余数由代码计算，输出为 `OSLAB1 sid=2024302111239 mod97=0x1d`，行末还有一个换行字节。`LAB1_BANNER_PROTOCOL=0` 选用明文行协议，`expect_banner.txt` 保存对应的完整首行。

串口每发送 `16 + COURSE_SID % 16` 个字节，就执行 32 次 `nop`。当前参数对应每 23 字节节流一次。Banner 之后，主函数输出包含零、两个 32 位有符号边界、`0xffffffff` 和空字符串的自检行，再输出 `0123456789abcdef` 重复 32 次的长字符串。输出结束后停在 `wfi` 循环，QEMU 画面保持开启。

## 三题问答

### 第一题：上电从哪里执行，内核为何放在 `0x80000000`？

- QEMU virt 的启动代码先从 `0x1000` 的引导 ROM 运行。启动参数 `-bios none` 表示没有加载另一个外部固件；QEMU 提供的引导代码仍负责把控制权交给 `-kernel` 指定的内核。内核开始执行的位置由 ELF 入口 `_entry` 决定。
- `kernel/kernel.ld` 把链接基址设为 `0x80000000`，课程配置的 RAM 也从该地址开始，延伸到 `0x88000000`。链接地址决定汇编标号、C 函数和全局变量在 ELF 中使用什么地址；QEMU 把镜像装入 RAM 后，这些地址才能指到实际代码与数据。Lab 1 的 `readelf` 检查记录中，`_entry` 正好位于 `0x80000000`。
- 若把内核链接到 `0x0`，入口和后续访问的地址就落在这台课程机器的 RAM 范围之外。启动 ROM 的 `0x1000`、UART 寄存器的 `0x10000000` 和内核 RAM 的 `0x80000000` 各有不同用途，现场解释时要分别指出它们的作用。

### 第二题：个人首行怎样从学号变成终端上的字？

- 个性化参数来自只读的 `kernel/course_sid.h`：`COURSE_SID=2024302111239`，`LAB1_BANNER_PROTOCOL=0`。协议 0 规定一行明文，以换行结束；本人的首行没有逐字节加点或校验和后缀。`kernel/main.c` 用学号计算 `% 97`，因此首行中的余数是 `0x1d`，并非手写在输出字符串里的固定答案。
- `kernel/main.c` 调用 `kprintf("OSLAB1 sid=%ld mod97=0x%x\n", ...)`。`kernel/printf.c` 将 `%ld` 变成十进制学号，将 `%x` 变成小写十六进制余数；格式串中的 `0x` 是前缀，末尾的 `\n` 产生换行字节。屏幕上应看到 `OSLAB1 sid=2024302111239 mod97=0x1d`，下一行才开始自检。
- 格式化后的每个字符都进入 `kernel/console.c` 的 `consoleputc`。它先等 UART 线路状态寄存器的 THRE 位为 1，再把字节写到发送寄存器；每发送 `16 + COURSE_SID % 16` 个字节执行一次短节流，本学号对应 23 字节。现场定位时可沿 `main.c → printf.c → console.c` 讲清数值来源、字符转换和实际发送。

### 第三题：初始栈在哪里，为什么进入 S 态前配置 PMP？

- `kernel/entry.S` 在 BSS 内标出 `stack0`，用 `.space LAB1_STACK_KB * 1024` 留出栈空间。`LAB1_STACK_KB` 来自只读 `kernel/course_sid.h`，当前值为 4，所以栈占 4096 字节。`kernel.ld` 决定 BSS 在内核镜像中的位置；`stack0_top` 经 16 字节对齐，是启动 hart 的初始栈顶。
- `_entry` 先把 `bss_start` 到 `kernel_end` 清零，再执行 `la sp, stack0_top`，最后 `call start`。这个顺序让 C 函数一开始就有干净、对齐的栈。启动前的核号检查还让非零 hart 留在 `park`，本轮只有 hart 0 使用这块栈。
- `kernel/start.c` 设置 `mstatus.MPP=S` 和 `mepc=kernel_main`，`mret` 随后从 S 态的主函数地址取指。PMP 条目 0 在此之前授予物理地址的读、写、执行权限，供 S 态取内核指令、访问 RAM 和 UART。若撤掉这项配置，既有 QEMU 排查记录显示 `mret` 后首次 S 态取指触发 `instruction access fault`；异常发生在打印 Banner 之前。

## 验证依据与边界

Lab 1 的历史验收记录为课程脚本 `RESULT: 3/3`、串口自检 `Lab 1 serial output: PASS`。当时检查了两次冷启动输出一致、无意外异常、4 KB 栈地址差，以及格式化边界和 512 字符长串；另以 `-smp 2` 检查只有启动 hart 输出。课程预置链接脚本仍使链接器提示单个加载段有 RWX 权限，既有验收运行未受影响。要复现这些结果，按 [lab1验收.md](./lab1验收.md) 的原始步骤操作；该文件保留了原文的终端命令与预期画面。
