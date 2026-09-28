# Lab 2 验收过程

本次验收使用当前 `master` 上的 Lab 2 内核。打开 VS Code 下方的终端，按顺序操作。`hi`、`badecall` 等用户程序名在 QEMU 出现 `sh>` 后输入。

1. 进入个人内核目录，清理、编译并启动 QEMU：

   ```bash
   cd /Users/slumpyfufu/Desktop/Projects/OSpracticeA/2024302111239-kernel
   make clean
   make CC=riscv64-elf-gcc LD=riscv64-elf-ld OBJCOPY=riscv64-elf-objcopy qemu
   ```

   编译命令结束后，屏幕先显示 `OSLAB1 sid=2024302111239 mod97=0x1d`，接着是两行 `SELFTEST`，最后出现 `sh>`。看到提示符就可以输入命令。课程链接脚本可能显示 `LOAD segment with RWX permissions` 提示，不影响下面的操作。

2. 在 `sh>` 后输入 `hix`，按一次退格键，看到末尾的 `x` 消失后按回车。应运行 `hi`，显示 `hi: user program running, pid=2` 和新的 `sh>`。再输入一次 `hi`，仍应打印程序消息并回到 `sh>`；第二次的 PID 会增加。输入 `badecall`，应看到 `TEST-1 PASS: unknown syscalls all return -1`；输入 `badptr`，应看到 `BADPTR PASS`。

3. 输入 `bufstorm`。第一行先慢慢输入 `onx`，按退格删掉 `x`，再输入 `e` 和回车；后面依次输入 `two`、`three`、`four`，每行都按回车。输入时字母逐个显示一次，回车后程序把完整的一行再显示在下一行；字母不再交错成 `oonnee`。四行结束后应看到 `BUFSTORM lines=4 bytes=19`，随后回到 `sh>`。再输入 `spin`，屏幕会持续打印 `spin 0`、`spin 1` 等行；这时输入 `abc` 并按回车，应看到 `abc`，后续 `spin` 数字继续增加。按 `Control+A`，松开后按小写 `x` 退出 QEMU。

4. **必查回归：重启，检查 Lab 1 输出。** 在同一个内核目录再次执行：

   ```bash
   make CC=riscv64-elf-gcc LD=riscv64-elf-ld OBJCOPY=riscv64-elf-objcopy qemu
   ```

   重启后的第一行仍须是 `OSLAB1 sid=2024302111239 mod97=0x1d`，后面仍有两行 `SELFTEST`，最后出现 `sh>`。这一步核对的是 Lab 2 加入陷入、中断和键盘输入后，Lab 1 的启动输出仍能完整走通。看完后按 `Control+A`，松开再按小写 `x` 退出。

5. 在内核目录运行自动测试，核对手动操作不方便检查的连续输入、完整首行和异常日志：

   ```bash
   python3 ../labs/lab2/test_lab2.py
   python3 ../labs/lab1/test_lab1.py
   make clean
   ```

   前两条命令通过时分别显示 `Lab 2 QEMU interaction: PASS` 和 `Lab 1 serial output: PASS`。其中 `test_lab2.py` 还会逐字慢速输入、用退格改字，检查四行输入、容量内连续输入及时钟和 UART 中断；`test_lab1.py` 逐行核对 Banner 与两行自检。`make clean` 清理构建文件。

6. 回到仓库根目录，核对本轮提交标签并导出课程要求的内核归档：

   ```bash
   cd ..
   git rev-parse --verify refs/tags/lab2-submit
   git archive --format=zip -o 提交-lab2-2024302111239.zip lab2-submit:2024302111239-kernel
   ```

   第一条 Git 命令显示提交哈希，第二条生成 `提交-lab2-2024302111239.zip`。`lab2-submit` 是退格修复前的原验收节点，这份归档保留该历史版本；要归档当前修复，需先把本轮改动提交，再从新提交导出。

现场问答还需解释 `ecall` 与 `sret`、个人缓冲区参数，以及在源码中指出中断向量切换和系统调用分发的位置。对应答案写在 [Lab 2 设计文档](./lab2设计文档.md) 的“三题问答”章节。
