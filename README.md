# OSpracticeA

基于 xv6 RISC-V 的操作系统课程实验项目。`2024302111239-kernel` 是全学期持续开发的个人操作系统代码树，`labs` 保存各实验的图、笔记和报告，`xv6-riscv` 保存完整参考源码，`os-course-labs` 保存课程实验材料与工具。

## 当前状态

| 项目 | 当前进度 |
|---|---|
| Lab 0 | 三张图已按命令主线重画，中文说明与本地 PlantUML 渲染通过 |
| Lab 1 | 启动、串口输出、格式化自检和设计记录已完成；课程评测 `3/3` |
| Lab 2 | 用户态陷入、系统调用、串口接收和交互式 Shell 已接通；QEMU 交互测试通过 |
| 最近验证 | 干净构建、`hi`／`badecall`／输入缓冲测试、时钟与 UART 中断、Lab 1 输出回归通过 |
| 运行环境 | Apple Silicon macOS，QEMU 11.1.1，Homebrew RISC-V ELF 工具链 |
| 下一步 | 在通过验收的 Lab 2 内核上继续 Lab 3 内存管理 |

## 构建与启动

当前个人内核使用 Homebrew 的 `riscv64-elf-` 工具链。在项目根目录执行：

```bash
cd 2024302111239-kernel
make CC=riscv64-elf-gcc LD=riscv64-elf-ld OBJCOPY=riscv64-elf-objcopy
make CC=riscv64-elf-gcc LD=riscv64-elf-ld OBJCOPY=riscv64-elf-objcopy qemu
```

QEMU 启动后，按 `Control+A`，松开后再按小写 `x` 退出。异常日志、Banner 检查和 Lab 1 统一验收命令记录在 [个人内核 README](./2024302111239-kernel/README) 中。

## 目录结构

```text
OSpracticeA/
├── README.md                         # 项目说明
├── .gitignore                       # Git 忽略规则
├── .vscode/                         # 当前项目的 VS Code 设置
│   └── settings.json                # PlantUML 本地 Java 与实时预览配置
├── AGENTS.md                         # Agent 工作规则与规范入口
├── CLAUDE.md                         # Claude 工作规则与规范入口
├── 内核开发规范.md                    # 累积内核的编码、验证与维护规则
├── 写作规范.md                        # 项目文档写作规则
├── 去AI味写作规范.md                  # 中文文本复审规则
├── .agents/                          # 本地 Skills 集合，由 Git 忽略
├── docs/                             # 课程文档与原始资料包
│   ├── 01-开课指南-环境安装与基线生成.docx
│   ├── 05-学生须知.docx
│   ├── 06-学生环境安装指引.docx
│   ├── 07-学生无gdb调试手册.docx
│   ├── lab0-实验说明书-学生版.docx
│   ├── lab1-实验说明书-学生版.docx
│   ├── lab2-实验说明书-学生版.docx
│   ├── 实验导学授课大纲.docx
│   ├── 开学第一课-第0课与lab0.pptx
│   ├── change_history/               # 按日期维护的项目变更记录
│   │   ├── README.md                 # 变更日期索引
│   │   ├── 2026-09-14.md             # 工作区建立与 Lab 0 记录
│   │   ├── 2026-09-27.md             # Lab 1 验收与 Lab 2 增量包记录
│   │   └── 2026-09-28.md             # Lab 2 验收与 Lab 0 图纸重画
│   └── 原始包/                       # 原始代码和课程材料的压缩备份
│       ├── Archive.zip
│       ├── os-course-labs.zip
│       └── xv6-riscv.zip
├── 2024302111239-kernel/             # 我的操作系统代码树，从 Lab 1 起持续演进
│   ├── kernel/                       # 内核源码与个性化参数
│   ├── README                        # 当前内核目录树、稳定接口和运行方法
│   ├── Makefile                      # 构建和 QEMU 启动入口
│   ├── Makefile.upgrade              # Lab 2 用户程序内嵌规则，课程赠送件
│   ├── check_expect.py               # Banner 输出格式自检
│   ├── expect_banner.txt             # Lab 1 预期 Banner
│   ├── 我的参数.txt                   # 学号派生的各实验参数
│   ├── user/                          # Lab 2 赠送的用户程序与基础库
│   ├── tests/                         # Lab 2 官方用户态测试
│   └── support/                       # Lab 2 串口输入测试工具
├── labs/                             # 各实验的文档材料
│   ├── 基础知识.md                    # 操作系统基础知识笔记
│   ├── lab0/                         # Lab 0 流程图、分析和报告
│   ├── lab1/                         # Lab 1 设计、QEMU 测试与报告
│   └── lab2/                         # Lab 2 设计、交互测试与验收记录
├── xv6-riscv/                        # 完整的 xv6 RISC-V 参考源码
│   ├── kernel/                       # 内核源码
│   ├── user/                         # 用户程序与用户态库
│   ├── mkfs/                         # 文件系统镜像生成工具
│   ├── Makefile                      # xv6 构建和运行入口
│   └── README                        # xv6 官方说明
├── os-course-labs/                   # 课程实验生成与验收工具
│   ├── baselines/                    # 课程包附带的 Lab 1 示例基线
│   ├── gifts/                        # Lab 2 至 Lab 6 的预置支撑代码
│   ├── pack_manifests/               # 各实验包的内容清单与接口约定
│   ├── packs/                        # 已生成的 Lab 2 至 Lab 6 增量包
│   └── tools/                        # 基线生成、打包、评测和故障题库工具
├── preflight.py                      # RISC-V 工具链与 QEMU 环境预检
└── monpeek.py                        # 无 GDB 时查看 QEMU 寄存器状态
```

其中，日常完成实验时使用 `docs/` 查看实验说明，在 `2024302111239-kernel/` 中逐轮开发操作系统，并把每轮的设计图、笔记、测试记录和报告放进 `labs/labN/`。`xv6-riscv/` 用于阅读参考实现，`os-course-labs/` 用于生成和检查课程实验材料。
