#!/usr/bin/env python3
"""
gen_baseline.py — V3 基线生成器(每生一棵,开学一次性)

基线 = 初始代码骨架 + 预置支撑代码 + 个性化参数头文件(course_sid.h)。
学生从零长出内核;后续每轮实验只发全班同份的增量包(见 gen_lab_pack.py)。

用法:
  # 全班批量
  python3 tools/gen_baseline.py --src ../xv6-riscv \
      --ids 20230101 20230102 --out baselines/
  # 完整性自检(开学前跑一次)
  python3 tools/gen_baseline.py --check --src ../xv6-riscv

course_sid.h 的参数公式与 v2 逐字相同(题库兼容的前提):
15 项参数宏 + COURSE_SID + 说明书派生公式(节流周期/自检序列等)。
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
V3_ROOT = os.path.dirname(HERE)
GIFTS = os.path.join(V3_ROOT, "gifts", "baseline")
STUDENT_CHECK = os.path.join(HERE, "student_check", "check_expect.py")

STUDENT_FILES = ["entry.S", "start.c", "console.c", "printf.c", "main.c"]

# Makefile 三固定项(ABI,--check 与 V3-01 §三核对)
MAKEFILE_MUSTS = ["make kernel", "kernel/kernel", "make qemu", "course_sid.h"]

# ------------------------------------------------------------ 参数表(= v2)
def sid_macros(sid: int) -> list:
    """course_sid.h 的派生参数(与各实验说明书公式一一对应)。"""
    return [
        ("LAB1_BANNER_PROTOCOL", sid % 3,
         "0=明文+换行 1=每字节后'.' 2=整段后回显校验和"),
        ("LAB1_STACK_KB", 4 * (1 + sid % 3), "内核栈大小(KB)"),
        ("LAB2_TICK", 1 + sid % 3, "时间片 tick"),
        ("LAB2_BUF_SEMANTICS", sid % 2, "0=行缓冲 1=字符流"),
        ("LAB2_BUF_SIZE", 32 * (1 + sid % 4), "输入缓冲区字节"),
        ("LAB3_ALLOC_ORDER", sid % 3, "0=升序 1=降序 2=中点"),
        ("LAB3_GUARD_PAGES", 1 + sid % 2, "每进程 guard 页数"),
        ("LAB3_MEMCAP_DELTA", sid % 16, "内存上限 = 总页数 − 本值"),
        ("LAB4_POLICY_ID", sid % 10,
         "分配表随 lab4 增量包发放(0=MLFQ 1=彩票 2=步长 3=优先级…)"),
        ("LAB5_REFCNT_SCHEME", sid % 3, "0=PTE保留位 1=全局数组 2=页表扫描"),
        ("LAB5_COW_BUDGET", 128 + sid % 128, "缺页复制预算(次)"),
        ("LAB5_KILL_SEMANTICS", sid % 2, "0=立即不复制 1=完成当前复制"),
        ("LAB6_REPLACE_POLICY", sid % 4, "0=LRU 1=FIFO 2=CLOCK 3=LFU"),
        ("LAB6_BUF_SLOTS", 8 + sid % 8, "缓存槽位数"),
        ("LAB6_LOG_BLOCKS", 24 + sid % 16, "日志块数"),
    ]

def write_sid_header(tree: str, sid: int):
    lines = ["/* 本文件自动生成,请勿修改;个性化参数唯一来源。 */",
             "#ifndef COURSE_SID_H", "#define COURSE_SID_H", "",
             f"#define COURSE_SID {sid}", ""]
    for name, val, desc in sid_macros(sid):
        lines.append(f"#define {name} {val}  /* {desc} */")
    lines += ["", "#endif", ""]
    p = os.path.join(tree, "kernel", "course_sid.h")
    os.makedirs(os.path.join(tree, "kernel"), exist_ok=True)
    with open(p, "w") as f:
        f.write("\n".join(lines))
    with open(os.path.join(tree, "我的参数.txt"), "w") as f:
        f.write(f"学号 {sid} 的个性化参数(与各实验说明书公式一致)\n" +
                "=" * 50 + "\n")
        for name, val, desc in sid_macros(sid):
            f.write(f"{name:26s} = {val:<6d} {desc}\n")

# ------------------------------------------------------------ 预置支撑代码
GIFT_HEADER = """/* ============ 预置支撑代码 · 请勿修改 ============
 * 说明: {reason}
 * 修改该支撑代码可能破坏统一接口规范；若遇到问题建议通过 git diff 核对本段代码。
 * ======================================== */
"""

def copy_gift(dst_path: str, src_path: str, reason: str, prepend=True):
    with open(src_path) as f:
        body = f.read()
    if prepend and not body.lstrip().startswith("/* 预置支撑代码") and not body.lstrip().startswith("/* 赠送件"):
        body = GIFT_HEADER.format(reason=reason) + body
    with open(dst_path, "w") as f:
        f.write(body)

# ------------------------------------------------------------ 主流程
def gen_one(src, out, sid):
    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(os.path.join(out, "kernel"))

    # 1) 初始基线预置支撑文件(gifts/baseline)
    copy_gift(os.path.join(out, "kernel", "kernel.ld"),
              os.path.join(GIFTS, "kernel.ld"),
              "加载地址与段排布规则(环境事实,注释讲清了为什么)")
    copy_gift(os.path.join(out, "Makefile"),
              os.path.join(GIFTS, "Makefile"),
              "构建规范:make kernel / make qemu / course_sid.h 依赖",
              prepend=False)  # Makefile 里已带说明注释
    copy_gift(os.path.join(out, "README"),
              os.path.join(GIFTS, "README.template"),
              "骨架说明 + git 工作流", prepend=False)

    # 2) 体系结构与环境支撑文件(从课程参考树复制,保持与快照同步)
    for rel, reason in [
        ("kernel/riscv.h", "RISC-V CSR 名与读写指令(环境事实)"),
        ("kernel/memlayout.h", "QEMU virt 机器地址地图(环境事实)"),
        ("kernel/types.h", "完整类型集(用户库/内核共用的 ABI 事实)"),
    ]:
        copy_gift(os.path.join(out, rel), os.path.join(src, rel), reason)

    # 3) 学生从零实现的五个空文件(带骨架注释)
    with open(os.path.join(GIFTS, "skeleton_note.txt")) as f:
        note = f.read()
    for name in STUDENT_FILES:
        with open(os.path.join(out, "kernel", name), "w") as f:
            f.write(note)

    # 4) 个性化参数
    write_sid_header(out, sid)

    # 5) 学生版 expect 形状自检器(验收前学生可自行校验,不泄题)
    shutil.copy(STUDENT_CHECK, os.path.join(out, "check_expect.py"))
    return out

def check(src):
    ok = True
    need = ["kernel.ld", "Makefile", "README.template",
            "skeleton_note.txt"]
    for n in need:
        p = os.path.join(GIFTS, n)
        mark = "[ ok ]" if os.path.isfile(p) else "[FAIL]"
        ok &= os.path.isfile(p)
        print(f"{mark} gifts/baseline/{n}")
    mk = open(os.path.join(GIFTS, "Makefile")).read()
    for m in MAKEFILE_MUSTS:
        hit = (m in mk) or m.replace("make ", "").replace("kernel/", "") in mk
        mark = "[ ok ]" if hit else "[FAIL]"
        ok &= hit
        print(f"{mark} Makefile 固定项含: {m}")
    for rel in ("kernel/riscv.h", "kernel/memlayout.h"):
        p = os.path.join(src, rel)
        mark = "[ ok ]" if os.path.isfile(p) else "[FAIL]"
        ok &= os.path.isfile(p)
        print(f"{mark} 参考树存在 {rel}")

    # 冒烟:临时生成一棵空基线并 make,预期编译通过、仅在链接处报
    # cannot find entry symbol _entry(说明书 §4 预告的唯一"设计信号")。
    # 若出现 missing separator / syntax error 等模板级错误,说明预置支撑文件损坏。
    try:
        with tempfile.TemporaryDirectory() as td:
            tree = gen_one(src, os.path.join(td, "smoke"), 20230000)
            r = subprocess.run(["make"], cwd=tree, capture_output=True,
                               text=True, timeout=120)
            out = r.stdout + r.stderr
            if r.returncode == 0 and "cannot find entry symbol _entry" in out:
                print("[ ok ] 空基线冒烟:make 通过,仅预告的 _entry 链接警告")
            else:
                ok = False
                print("[FAIL] 空基线冒烟异常(预置支撑代码模板可能损坏):")
                for ln in out.splitlines():
                    if any(k in ln for k in ("Error", "error", "missing",
                                             "separator", "syntax")):
                        print("       " + ln.strip())
    except Exception as e:  # make 不存在等环境问题不阻断自检结论
        print(f"[warn] 空基线冒烟跳过({e})——请人工执行一次 make 验证")

    print("结论:基线自检" + ("通过" if ok else "未通过(修好再生成)"))
    return ok

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="课程参考 xv6 目录")
    ap.add_argument("--sid", type=int)
    ap.add_argument("--ids", nargs="*", type=int)
    ap.add_argument("--out", default=os.path.join(V3_ROOT, "baselines"))
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    if args.check:
        sys.exit(0 if check(args.src) else 1)

    ids = [args.sid] if args.sid else (args.ids or [])
    if not ids:
        sys.exit("需要 --sid 或 --ids")
    for sid in ids:
        out = gen_one(args.src, os.path.join(args.out, f"{sid}-kernel"), sid)
        print(f"生成 {out}")
    print(f"共 {len(ids)} 棵基线。发布:压缩后按学号挂课程平台(唯一个性化分发物)。")

if __name__ == "__main__":
    main()
