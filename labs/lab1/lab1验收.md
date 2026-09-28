# Lab 1 验收

## 在最新内核直接检查 Lab 1 输出

当前 `master` 已包含 Lab 2，开机时仍先打印 Lab 1 的 Banner 和两行自检。检查这项回归直接在当前代码上操作，无需切换分支。打开 VS Code 终端，执行：

```bash
cd /Users/slumpyfufu/Desktop/Projects/OSpracticeA/2024302111239-kernel
make clean
make CC=riscv64-elf-gcc LD=riscv64-elf-ld OBJCOPY=riscv64-elf-objcopy
python3 ../labs/lab1/test_lab1.py
make clean
```

测试会自动启动并关闭 QEMU，逐行核对 Banner、数字自检和 512 字符长串。通过时显示 `Lab 1 serial output: PASS`。手动执行 `make CC=riscv64-elf-gcc LD=riscv64-elf-ld OBJCOPY=riscv64-elf-objcopy qemu`，屏幕会先显示同样三行，随后出现 Lab 2 的 `sh>`；按 `Control+A`，松开后按小写 `x` 退出。

若要复现 Lab 1 提交时课程脚本的 `RESULT: 3/3`，按下一节从标签取出一份临时代码。当前 `master` 保持不动，本文也会一直留在目录里。课程脚本要求整段运行日志没有陷入事件；当前 Lab 2 的系统调用和中断属于正常行为，所以两种检查的范围不同。

## 复现当时的 Lab 1 课程评分

1. 在 VS Code 终端回到仓库根目录，把 `lab1-submit` 的内核文件取到系统临时目录。以下命令在同一个终端连续执行：

   ```bash
   cd /Users/slumpyfufu/Desktop/Projects/OSpracticeA
   lab1_check_dir=$(mktemp -d)
   git archive lab1-submit:2024302111239-kernel | tar -xf - -C "$lab1_check_dir"
   ```

   `lab1_check_dir` 保存临时目录的位置。仓库仍在 `master`，`lab1验收.md` 仍可打开。

2. 启动这份临时内核，观察 Lab 1 的三行输出：

   ```bash
   cd "$lab1_check_dir"
   make CC=riscv64-elf-gcc LD=riscv64-elf-ld qemu
   ```

   第一行是 `OSLAB1 sid=2024302111239 mod97=0x1d`，后面两行以 `SELFTEST` 开头。这里运行的是当时的 Lab 1，打印后停住，没有 `sh>`。按 `Control+A`，松开后按小写 `x` 退出 QEMU。

3. 回到仓库根目录，运行课程评分并清理临时文件：

   ```bash
   cd /Users/slumpyfufu/Desktop/Projects/OSpracticeA
   MAKEFLAGS='CC=riscv64-elf-gcc LD=riscv64-elf-ld' \
     sh os-course-labs/tools/lab1-autograder/run.sh \
     "$lab1_check_dir" 2024302111239
   rm -r "$lab1_check_dir"
   ```

   评分通过时显示三项 `PASS` 和 `RESULT: 3/3`。清理的只有刚才生成的临时目录，当前仓库与分支不变。

## 旧步骤留档

下面的“验收过程”按此前要求原文保留。其中的 `git switch --detach lab1-submit` 会让较晚加入的 `lab1验收.md` 暂时从当前目录消失。实际操作请使用上面的两种无需切换的方式。

## 验收过程

1. 打开 VS Code 下方的终端。当前仓库已是 Lab 2，先暂时切到 Lab 1 提交时的版本：

   ```bash
   cd /Users/slumpyfufu/Desktop/Projects/OSpracticeA
   git switch --detach lab1-submit
   ```

2. 编译并开机：

   ```bash
   cd 2024302111239-kernel
   make clean
   make CC=riscv64-elf-gcc LD=riscv64-elf-ld qemu
   ```

   终端会先刷出编译命令，然后显示：

   ```text
   OSLAB1 sid=2024302111239 mod97=0x1d
   SELFTEST zero=0 min=-2147483648 max=2147483647 hex=0xffffffff empty=[]
   SELFTEST long=[很长的一串 0123456789abcdef]
   ```

   第三行实际是 `0123456789abcdef` **重复 32 次**。此后画面停住是正常的。按 `Control+A`，松开后按 `x` 退出 QEMU。编译时出现 `LOAD segment with RWX permissions` 提示是已记录的链接脚本提示；不应再出现“找不到 `_entry`”。

3. 在同一个内核目录检查第一行的预期文件：

   ```bash
   python3 check_expect.py 2024302111239
   ```

   应看到 `[ok] 形状校验通过`。

4. 回到仓库根目录，运行课程评分：

   ```bash
   cd ..
   MAKEFLAGS='CC=riscv64-elf-gcc LD=riscv64-elf-ld' \
     sh os-course-labs/tools/lab1-autograder/run.sh \
     2024302111239-kernel 2024302111239
   ```

   脚本会自动开机和关闭 QEMU。通过时显示三行 `PASS`，最后是 **`RESULT: 3/3`**。它检查：第一行一字不差、两次开机输出相同、运行期间没有异常。另有 `INFO:throttle` 提示，检查学号节流代码。

5. 检查结束，清理编译文件并回到现在的 Lab 2 版本：

   ```bash
   cd 2024302111239-kernel
   make clean
   cd ..
   git switch master
   ```

现场验收还会让你解释启动代码、4 KB 栈、为什么要给内核访问内存的权限，以及抽查一张 Lab 0 图。**`git switch master` 是最后一步，执行后你的日常代码就回到 Lab 2。**

