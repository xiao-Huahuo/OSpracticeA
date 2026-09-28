# Lab 2 设计文档：陷入、中断与键盘输入

本笔记对应 `lab2-submit` 的实现，解释用户程序怎样进入内核并返回，以及 UART 接收中断怎样把键盘字节交给 Shell。复现运行结果时使用 [lab2验收.md](./lab2验收.md)。课程赠送的 `trampoline.S`、用户库、用户程序和调用号头文件保持原样；个人代码接入陷入分发、系统调用、输入缓冲与进程运行。

## 要求、实现位置与检查方式

| 说明书要求 | 对应代码 | 可观察检查 |
|---|---|---|
| 用户态陷入、现场保存和返回 | `trampoline.S`、`proc.h`、`trap.c`、`kernelvec.S` | `hi` 执行后回到 Shell；异常日志只含预期事件 |
| 系统调用参数与错误码 | `syscall.c`、`trap.c` | `badecall` 对未知号码返回 `-1`；`badptr` 拒绝无效用户地址 |
| UART 中断接收和输入缓冲 | `console.c`、`trap.c`、`proc.c` | `bufstorm` 完成四行读取；`inputcheck` 核对容量内连续输入 |
| 启动 Shell、加载用户程序 | `proc.c`、`vm.c`、`kalloc.c`、`swtch.S` | `hi`、`spin` 从 Shell 启动；`wait` 后提示符再次出现 |
| Lab 1 输出回归 | `main.c`、`printf.c`、`console.c` | 重启后首行仍是个人 Banner；`test_lab1.py` 核对前三行 |

实际验证按三个关口进行：干净构建后进入 `sh>`；在 QEMU 中执行课程命令并观察错误返回；退出再重启，核对 Lab 1 输出，最后运行两份自动测试。操作顺序写在验收文档中。

## 用户陷入时谁保存现场

从 U 态执行 `ecall` 时，硬件把当前指令地址记入 `sepc`，把原因写入 `scause`，并在 `sstatus` 中保存此前的特权级和中断状态，随后进入 S 态并跳到 `stvec`。通用寄存器、用户栈和内核栈的交接由 `trampoline.S` 完成。`sepc` 此时仍指向 `ecall`，`usertrap` 对系统调用把保存的 `epc` 加 4，返回时才会从下一条指令继续。

内核在返回用户态前把 `stvec` 指向高地址的 `uservec`。陷入发生后，CPU 仍使用该进程的用户页表，因此 `uservec` 和 trapframe 都映射在用户页表中，trapframe 仅供 S 态访问。`uservec` 先用 `sscratch` 暂存用户 `a0`，借出 `a0` 装入 trapframe 地址，再保存用户的 31 个非零通用寄存器，包括 `sp`；随后从 trapframe 取内核栈顶、内核页表和 `usertrap` 地址。`proc.h` 的字段顺序与赠送汇编中的固定偏移一致，编译期检查锁定 `a0` 和 `t6` 的偏移。

[陷入与返回图源码](./01-陷入与返回.puml)及[同名 PNG](./01-陷入与返回.png)画出一次系统调用的完整路径。用户态中断同样从 `uservec` 进入，进入 C 函数后由 `devintr` 区分时钟与 UART；在内核执行期间，`stvec` 改为 `kernelvec`，该入口保存内核寄存器并调用 `kerneltrap`。`usertrapret` 关闭中断，重新设置 `stvec=uservec`、`sepc` 和 `sstatus`，赠送的 `userret` 切回用户页表、恢复寄存器，最后由 `sret` 回到 U 态。两套入口的切换顺序保证中断发生时能找到与当前栈、页表相配的处理代码。

## 系统调用怎样分发

用户桩把调用号放在 `a7`，前三个参数放在 `a0` 至 `a2`。`usertrap` 识别 `scause=8` 后推进 `epc`，再调用 `syscall`；后者从 trapframe 提取参数，用调用号选择 `fork`、`exit`、`wait`、`read`、`exec`、`getpid` 或 `write`。未知号码保留初始结果 `-1`，最终结果写回 trapframe 的 `a0`。用户返回后从 `a0` 读到它。

读写系统调用先检查地址范围，再由 `vmaddr` 查页表并核对用户权限。`badptr` 传入受保护的 trapframe 地址，访问检查返回失败，内核把错误传给用户程序。`fork` 复制用户页与现场，`exec` 从内嵌程序表装入新映像，`wait` 等待并回收子进程；因此 `sh` 执行 `hi` 后还能再次打印提示符。用户程序来自 `_uprog_table`，本轮没有磁盘文件系统。

## UART 输入缓冲区的状态转换

当前学号在 `course_sid.h` 中得到 `LAB2_BUF_SIZE=128`、`LAB2_BUF_SEMANTICS=1` 和 `LAB2_TICK=1`。语义 1 表示每收到一个字符就唤醒等待的读取进程。`console.c` 用 `input_write - input_read` 记录占用量，以取模方式定位 128 字节数组；下表用 `write`、`read` 简写这两个索引。UART 中断是生产者，执行 `read` 的进程是消费者。当前实现运行在单 hart 上，消费者操作索引时关闭本 hart 中断，UART 中断上下文也在中断关闭的状态下执行；这里没有额外的自旋锁。

| 到达前的状态 | 发生的动作 | 新状态与后续行为 |
|---|---|---|
| 空：`write == read` | `read` 需要首个字符 | 进程在 `input` 通道睡眠，调度器运行其他进程。 |
| 空或未满：`write - read < 128` | UART 收到一个字节 | 写入环形数组，`write` 加 1，回显该字节；语义 1 立即唤醒等待进程。回车先转换为换行。 |
| 有数据：`write > read` | `read` 取一个字节 | `read` 加 1；读到换行，或当前可取数据已经读完时，系统调用返回已读字节数。 |
| 满：`write - read == 128` | UART 再收到字节 | 丢弃新到的字节，索引保持原值；消费者读走数据后恢复可写空间。 |

`consolegetc` 在检查空缓冲、登记睡眠和切换出去时保持本 hart 中断关闭；生产者写入后调用 `proc_wakeup(input)`。这避免消费者在“检查为空”与“开始等待”之间错过唤醒。容量内的连续输入由 `inputcheck` 检查计数和校验和；输入总量超过缓冲容量时，满缓冲分支明确丢弃新字节，因此测试结论限定在容量内。

## 地址选择与运行边界

说明书允许在 Lab 2 暂时用物理地址运行 U 态程序，但课程赠送的 `trampoline.S` 固定访问高地址 trapframe，用户程序又从地址 0 链接。QEMU 的 RAM 从 `0x80000000` 开始，这两个地址按 `satp=0` 无法直接访问。当前代码在 `kernel_main` 中建立最小 Sv39 页表，内核 RAM 和 UART、PLIC 采用同地址映射；每个进程另外映射用户程序页、仅供 S 态访问的 trapframe 与可执行 trampoline 页。`vmaddr` 核对 `PTE_U`，系统调用通过它翻译用户指针。这个选择解决了赠送代码的实际地址要求，Lab 3 再扩展内存管理。

时钟中断由 `start.c` 设置首次比较值，`trap.c` 在每次中断后设置下一个比较值；UART 外部中断通过 PLIC 接收。`spin` 持续运行时，时钟中断仍能进入内核，键盘字节也能由 UART 中断接收。当前实验用单 hart，内嵌程序表加载用户程序，没有文件系统；课程的 `inject_uart.py` 固定等待 `$ ` 并要求 `fs.img`，与当前 `sh>` 和无磁盘配置不合。实际交互用仓库内的 `test_lab2.py` 检查。

## 三题问答

### 第一题：`ecall` 和 `sret` 怎样完成一次往返？

- 用户程序把调用号放入 `a7`，把参数放入 `a0` 至 `a2`，再执行 `ecall`。硬件完成三类动作：在 `sepc` 记录当前指令地址，在 `scause` 记录陷入原因，在 `sstatus` 记录原特权级和中断状态；随后切到 S 态，跳往 `stvec`。本轮用户态系统调用的 `scause` 值为 8。
- 硬件保留的 `sepc` 指向 `ecall` 本身。`kernel/trap.c` 的 `usertrap` 把这个地址保存到当前进程的 trapframe，并在系统调用分支加 4。若返回地址仍指向原处，用户程序会再次执行同一条 `ecall`；加 4 后，`sret` 才能从下一条指令继续。
- 陷入时的通用寄存器和内核栈由软件处理。赠送的 `trampoline.S` 先把用户 `a0` 放进 `sscratch`，借用 `a0` 指向 trapframe，保存 31 个非零通用寄存器；接着换到 trapframe 指定的内核栈和内核页表，再调用 `usertrap`。`sscratch` 解决了“需要一个寄存器找 trapframe，但所有用户寄存器都要保留”的起步问题。
- 返回时，`usertrapret` 设置用户入口、返回地址和 `sstatus`；赠送的 `userret` 换回用户页表并恢复寄存器。最后 `sret` 根据 `sepc` 和 `sstatus` 返回 U 态。`sret` 负责特权级与控制流的最后一步，寄存器恢复发生在它之前。

### 第二题：个人输入缓冲区在哪里，改成 8 字节会出现什么？

- 只读的 `kernel/course_sid.h` 给出 `LAB2_BUF_SIZE=128` 和 `LAB2_BUF_SEMANTICS=1`。前者是环形数组容量；后者选中字符流模式。`kernel/console.c` 的 `input` 数组保存字节，`input_write - input_read` 是当前已存数量。索引持续递增，读写数组时再对容量取模。
- UART 中断进入 `uartintr` 后，先读取接收寄存器，随后把回车转换为换行。缓冲未满时，函数写入一个字节、回显，并因语义值为 1 调用 `proc_wakeup(input)`。所以等待中的读取进程在每个成功接收的字符到达后就有机会运行；若语义值为 0，源码中的另一分支要等换行才唤醒。
- 消费者是执行 `read` 的进程。`consolegetc` 遇到空缓冲会在 `input` 通道睡眠，唤醒后继续检查索引并取走字符；`sys_read` 读到换行，或取完当时可用的数据，就把已读字节数交给用户程序。当前单 hart 实现用关闭本核中断保护读写索引与睡眠交接，满缓冲时生产者丢弃新到字节。
- 说明书提出的 8 字节是口头推演，当前参数仍为 128。容量缩到 8 后，只要读者尚未取走数据，连续到来的第 9 个字节就会落入满缓冲丢弃分支；回显和唤醒也只发生在成功入队的字符上。长命令或连续输入因此更容易缺字。仓库的 `inputcheck` 实测范围为现有容量的一半，即连续 64 字节；这个结果只覆盖容量内输入。

### 第三题：到哪里指出中断向量切换和系统调用分发？

- `kernel/trap.c` 第 44 行在 `trapinit` 中设置初始 `stvec=kernelvec`。进入 `usertrap` 后，第 56 行再次将 `stvec` 切到 `kernelvec`，让内核执行期间到来的中断使用内核入口。返回用户态前，第 96 行先关中断，第 97 行才把 `stvec` 切回高地址的 `uservec`；接着设置 trapframe 中的内核栈、内核页表，以及 `sepc` 和 `sstatus`。这几个步骤决定下一次陷入能否找到与当前页表相配的入口。
- `kernel/trap.c` 第 58 至 61 行识别用户 `ecall`、推进保存的返回地址并调用 `syscall()`。若为时钟或 UART 中断，`devintr` 走设备分支。这样在现场可以从同一个入口指出“系统调用”和“设备中断”各在哪里分流。
- `kernel/syscall.c` 的 `syscall` 函数从第 157 行开始。第 161 行先把结果设为 `-1`，第 163 行读取 trapframe 的 `a7` 并进入 `switch`，第 164 至 170 行处理已实现的调用，第 173 行把结果写回 `a0`。未知号码走默认分支，保留 `-1`，因此 `badecall` 收到错误码而内核继续运行。以上行号对应 `lab2-submit` 与当前未改动的相关源码。

## 既有验证记录

2026 年 9 月 28 日再次干净构建并依次运行 `test_lab2.py`、`test_lab1.py`；前者输出 `Lab 2 QEMU interaction: PASS`，后者输出 `Lab 1 serial output: PASS`。这两次测试分别启动 QEMU，第二次冷启动完成了 Lab 1 输出回归。交互测试检查 `hi`、`badecall`、`badptr`、`bufstorm`、容量内连续输入和 `spin` 时的键盘响应，并确认中断日志只出现预期的用户系统调用、S 态时钟与 UART 外部中断。此前另一次连续运行 40 条 `hi` 命令，均返回 Shell。当前操作步骤见 [lab2验收.md](./lab2验收.md)。
