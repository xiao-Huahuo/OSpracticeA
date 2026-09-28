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

