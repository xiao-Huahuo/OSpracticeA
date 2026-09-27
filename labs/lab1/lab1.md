# Lab 1：启动与串口输出

本实验从学号 `2024302111239` 的空白内核骨架出发，沿着 QEMU 交出控制权后的执行顺序，建立一条可检查的路径：汇编入口准备运行环境，M 态代码配置 S 态权限，内核主函数通过 UART 打印 Banner 和格式化自检。代码留在同一棵个人内核中，下一轮实验可直接接入陷阱与输入路径。

## 计划与验收位置

1. `entry.S` 建立入口、栈和异常向量，`start.c` 完成特权级切换；用干净编译、ELF 入口地址和 QEMU 冷启动核对。
2. `console.c` 实现轮询 UART 与学号节流，`printf.c` 实现整数和字符串格式化；用真实串口输出检查边界值和长字符串。
3. `main.c` 输出个人 Banner 与自检，`expect_banner.txt` 固定预期首行；用课程评测脚本核对逐字节输出、第二次冷启动和异常日志。

这三步分别对应实验说明书中的启动、输出和验收交付。预置的 `kernel.ld`、`riscv.h`、`memlayout.h` 与 `course_sid.h` 保持原样。新增的 `defs.h` 集中声明跨文件调用的三个函数，Makefile 只补充这份头文件及汇编所用学号头文件的重编译依赖。设计和结果保存在本文件，项目现状同步到两个 README 与当天变更记录。

## 从复位地址到内核主函数

QEMU virt 机器从 `0x1000` 的引导 ROM 开始执行。`-bios none` 省去了外部固件，QEMU 提供的短引导代码仍会把执行流交到内核 ELF 的入口。RAM 起点是 `0x80000000`，因此预置链接脚本把内核放在该地址；链接到 `0x0` 会让代码落到 RAM 之外。当前 ELF 的 `_entry` 经 `readelf` 验证位于 `0x80000000`。

```text
QEMU ROM 0x1000
    ↓ 加载并跳转
_entry  M 态，关中断，选 hart 0，清 BSS，设置 sp 与 mtvec
    ↓ call start
start   M 态，准备 mepc、委托、satp、PMP 与 stvec
    ↓ mret，MPP=S
kernel_main  S 态，打印 Banner、自检，随后停在等待循环
```

`entry.S` 先用 `csrci mstatus, 8` 清除 MIE，再清 `mie`，这样初始化期间没有异步中断。`csrr t0, mhartid` 取得核号，`bnez` 让非零 hart 进入 `park`；本轮只有 hart 0 进入 C 路径。`la t0, mtrap` 与 `csrw mtvec, t0` 安装 M 态异常向量，标号前的 `.balign 4` 满足 `mtvec` 低两位的对齐要求。预期外的 M 态异常会停在 `mtrap`，并进入 QEMU 的异常日志。

清零循环用 `la` 取得 `bss_start` 和链接脚本提供的 `kernel_end`，`bgeu` 判断结束，`sb zero, 0(t0)` 清一个字节，`addi` 推进地址。这个过程包含 4 KB 栈和 `console.c` 的发送计数器。循环结束才以 `la sp, stack0_top` 设置栈，再用 `call start` 进入 C 语言；栈顶按 16 字节对齐。`start` 若返回，控制流落入 `park` 的 `wfi` 等待循环。S 态备用向量 `strap` 同样按 4 字节对齐，当前承担早期故障停留点，Lab 2 会接入完整的 trap 处理。

现场逐行解释 `entry.S` 时，可按源码顺序核对下表。栈放在 BSS 中，大小由 `LAB1_STACK_KB` 给出；当前值是 4 KB，供单核启动和格式化函数使用，栈内没有递归路径。

| 指令或伪指令 | 此处的作用 |
|---|---|
| `csrci mstatus, 8` | 清 MIE，阻止准备栈和向量时进入 M 态中断。 |
| `csrw mie, zero` | 清各类 M 态中断使能。 |
| `csrr t0, mhartid` | 把当前 hart 编号读入 `t0`。 |
| `bnez t0, park` | 将非零 hart 留在等待路径，只让 hart 0 初始化共享状态。 |
| `la t0, mtrap` | 取得对齐后的 M 态向量地址。 |
| `csrw mtvec, t0` | 安装 M 态直接异常入口。 |
| `la t0, bss_start` | 设置 BSS 清零游标。 |
| `la t1, kernel_end` | 取得 BSS 清零的结束边界。 |
| `bgeu t0, t1, bss_done` | 游标到达边界时结束循环。 |
| `sb zero, 0(t0)` | 把当前 BSS 字节写为零。 |
| `addi t0, t0, 1` | 游标前进一个字节。 |
| `j clear_bss` | 返回边界检查，继续清零。 |
| `la sp, stack0_top` | 在清零完成后设置 16 字节对齐的初始栈顶。 |
| `call start` | 按 C 调用约定进入 M 态初始化函数。 |
| `wfi`、`j park` | 非启动 hart 或意外返回的启动 hart 留在等待循环。 |
| `j mtrap`、`j strap` | 早期异常停在对应向量，由 QEMU 异常日志辅助定位。 |

`.balign 4` 约束 `_entry` 与两个陷阱入口的指令地址；`.space LAB1_STACK_KB * 1024` 从学号头文件分配栈空间。这两条汇编指示符决定内存布局，没有运行时指令行为。

`start.c` 对 `mstatus` 做读、改、写：清 MIE、MPIE、SIE 和旧 MPP，设置 MPP 为 S。`mepc` 指向 `kernel_main`，`mret` 因而会以 S 态执行它。`medeleg` 与 `mideleg` 保留已有位并加入 S 态可处理的异常和中断委托，`stvec` 指向备用向量。Lab 1 使用物理地址，`satp=0` 选择 Bare 模式，写入后执行 `sfence.vma`；此时无需建立初始页表。PMP 条目 0 使用 NAPOT 覆盖物理地址空间，并给予 R、W、X 权限，使 S 态能够从 RAM 取指和访问 UART。若缺少这项配置，新版 QEMU 在 `mret` 后的首次 S 态取指会记录 instruction access fault。

内存关系如下，图中的段顺序来自预置 `kernel.ld`；QEMU 将 ELF 的加载段放在 `0x80000000` 起始的 RAM 中。

```text
0x00001000    QEMU 引导 ROM
0x10000000    UART0 寄存器
0x80000000    _entry、.text
              .rodata、.data
              bss_start、stack0（LAB1_STACK_KB × 1024）、sent_bytes
kernel_end    内核镜像末端，留给后续实验的内存分配器
```

## 一条字符怎样到达终端

`kernel_main` 调用 `kprintf`。格式化器把十进制或十六进制数字转为字符，把字符串逐字节展开，再统一调用 `consoleputc`。UART 基址取自预置 `memlayout.h` 的 `UART0`，MMIO 使用 `volatile uint8` 访问。发送前轮询偏移 5 的线路状态寄存器，直到 bit 5（THRE）为 1，再向偏移 0 的发送保持寄存器写入一个字节。启动阶段只有 hart 0 调用这条路径，状态 `sent_bytes` 归控制台模块维护。

每发送 `16 + COURSE_SID % 16` 个字节执行一次 32 次 `nop` 的短节流循环。当前学号的周期是 23 字节，周期始终由 `COURSE_SID` 计算。`LAB1_BANNER_PROTOCOL` 为 0，本人的输出采用明文加换行；编译时检查该参数，避免把其他学号协议误当作已实现。`kprintf` 支持 `%c`、`%s`、`%d`、`%u`、`%x`、对应的 `l` 长整数格式和 `%%`。有符号最小值通过先处理 `value + 1` 再转为无符号值，规避取负时溢出；十六进制数字只输出小写有效位，前缀由调用处明确写出。

`main.c` 的首行由学号宏和 `% 97` 计算得到，`expect_banner.txt` 保存完全相同的预期字节：

```text
OSLAB1 sid=2024302111239 mod97=0x1d
```

随后输出一行数字与空字符串测试，再通过一次 `%s` 输出 512 个连续字符。测试内容位于 Banner 后面，课程工具仍按第一行检查个人协议；独立测试会检查自检两行的完整内容和长度。内核完成输出后进入 `wfi` 循环，保持 QEMU 中的运行状态。

## 如何启动

在仓库根目录进入个人内核，运行 Makefile 的 `qemu` 目标。该目标会先编译内核，再以 QEMU virt 机器启动；本机 Homebrew 工具链的编译器和链接器需要通过命令行指定。

```bash
cd 2024302111239-kernel
make CC=riscv64-elf-gcc LD=riscv64-elf-ld qemu
```

串口输出从 `OSLAB1 sid=2024302111239 mod97=0x1d` 开始，接着打印 `SELFTEST zero=0` 所在的数字边界行，以及 `SELFTEST long=[...]` 所在的长字符串行。输出结束后内核停在等待循环，QEMU 仍占用终端。按 `Control+A`，松开后按小写 `x` 退出。若要从干净构建开始，先在同一目录执行 `make clean`，再运行上面的启动命令。

链接阶段会提示单个加载段具有 RWX 权限，原因和本轮验收结果记录在下节。看到 Banner 和两行自检输出，说明本轮启动路径已运行到 S 态的 `kernel_main`。

## 如何验收

在 `OSpracticeA` 根目录运行下面两条命令。第一条是课程提供的验收脚本，会重新编译内核、启动 QEMU 并检查开机输出；这里由脚本负责关闭 QEMU。`MAKEFLAGS` 把本机的 RISC-V 编译器和链接器名称传给脚本。第二条检查 Banner 后面的两行自检内容，包括数字边界和 512 个连续字符。

```bash
MAKEFLAGS='CC=riscv64-elf-gcc LD=riscv64-elf-ld' \
  sh os-course-labs/tools/lab1-autograder/run.sh \
  2024302111239-kernel 2024302111239
python3 labs/lab1/test_lab1.py
```

课程脚本显示 `PASS:banner_match`，表示实际开机首行与 `expect_banner.txt` 对上了；`PASS:idempotent` 表示两次开机打印的内容相同；`PASS:d_int` 表示运行期间没有记录到异常。最后看到 `RESULT: 3/3`，这三项就全部通过。`INFO:throttle` 是对学号节流代码的提示，单独列在三项结果之外。第二条命令打印 `Lab 1 serial output: PASS`，说明后两行自检也符合预期。

若出现 `FAIL`，先看冒号后面的项目名。`banner_match` 对应首行文字与换行，`idempotent` 对应两次开机的输出差异，`d_int` 对应内核异常；`expect_file` 或 `expect_shape` 则指向预期输出文件。修好后重跑同一组命令，就能看到改动是否解决了问题。

## 验证记录

2026 年 9 月 27 日按上一节命令验收，课程脚本返回 `RESULT: 3/3`，串口自检返回 `Lab 1 serial output: PASS`。干净构建生成入口 `0x80000000`；`stack0_top` 与 `bss_start` 相差 `0x1000` 字节，等于参数指定的 4 KB；期望文件通过协议 0 形状检查。独立 QEMU 测试核对了 `0`、`-2147483648`、`2147483647`、`0xffffffff`、空字符串及 512 字符连续输出。课程脚本还验证了两次冷启动输出一致、异常日志清洁，并识别 `COURSE_SID` 节流引用。额外以 `-smp 2` 冷启动，串口输出仍为 636 字节，`-d int` 日志为空。内核相关的 Lab 0 回归属于图表审阅，三份图表源码与说明维持在 `labs/lab0/`，本次未改动。

链接器仍报告一个 `LOAD` 段具有 RWX 权限。预置且标明只读的 `kernel.ld` 把代码与数据连续放进同一加载段，`-z separate-code` 也保持该段布局。该提示不影响本轮 QEMU 启动及串口验收；后续若课程允许调整链接段权限，可在调整链接脚本时一并消除。

本轮没有遗留的功能验收项。后续 Lab 2 接入中断接收、系统调用和用户态时，需要把当前的备用陷阱向量替换为真正的处理入口，并保留这次实验验证过的启动 Banner。

Git 起点标记为 `lab1-start`，本轮提交节点标记为 `lab1-submit`。已有的 Lab 2 文档维持在工作区，本次提交只包含 Lab 1 相关改动。
