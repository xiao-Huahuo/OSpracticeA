# lab1-autograder · 自动化评分工具

> 用于 lab1 验收时自动化检验学生基线启动、个性化 Banner 格式规范匹配、`-d int` 异常日志清洁度与冷启动幂等性。

## 组成文件

| 文件 | 作用说明 |
|---|---|
| `autograde.py` | 主驱动：编译构建 $\to$ 双次冷启动 $\to$ Banner 逐字节比对 $\to$ `-d int` 异常检查 $\to$ 节流源码检查 |
| `gen_expect.py` | 期望输出文件格式规范校验（0/1/2 号格式）＋ 标准参考输出生成（`--print`） |
| `run.sh` | 快速验收入口：`sh tools/lab1-autograder/run.sh <学生代码树路径> <学号>` |

## 学生端前置要求
1. 工程根目录包含 `expect_banner.txt`：由学生在设计笔记中预先确立的期望输出内容；
2. 节流计数在 `kernel/console.c` 中引用 `COURSE_SID` 宏。

## 教师用法

```bash
# 单人快速验收
sh tools/lab1-autograder/run.sh /path/to/<学号>-kernel <学号>

# 查看指定学号的标准格式参考
python3 tools/lab1-autograder/gen_expect.py --sid 20230101 --print

# 单独校验学生期望输出文件的格式规范
python3 tools/lab1-autograder/gen_expect.py --sid 20230101 --check <文件路径>
```
