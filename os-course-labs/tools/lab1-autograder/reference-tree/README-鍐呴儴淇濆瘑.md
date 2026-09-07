# 参考基线（教师内部教学资产 · 严禁下发学生）

## 用途说明
仅用于 **lab1 自动化评分工具（Autograder）健康自检**（验证评测工具链正常，预期 3/3 PASS）：
```bash
# 在资料包根目录执行
sh tools/lab1-autograder/run.sh tools/lab1-autograder/reference-tree 20230101
```

## 说明
- 学号 20230101（`LAB1_BANNER_PROTOCOL=0`：明文+换行；栈大小 4KB；控制台节流 27 字节）。
- 本代码树完整实现了 lab1 的个性化 Banner 输出规范，属于"课程参考实现"，**与上游纯净源码树 `xv6-riscv/` 有所不同**——后者是生成学生实验初始基线的原料源码（pre-lab1），未包含个性化参数规范，无法直接通过自动化评分脚本。
- 若需更换学号进行冒烟自检：运行 `gen_baseline.py --sid <新学号>` 生成空白基线后，将本代码树中的 `kernel/entry.S、start.c、console.c、printf.c、main.c` 实现迁移至新工程，并按照新学号参数重新生成 `expect_banner.txt`（可使用基线包内的 `check_expect.py` 校验输出格式）。
- 教学管理纪律同《04-题库》：严格限于教师内部存档测试，严禁直接下发学生或上传至公开网络平台。
