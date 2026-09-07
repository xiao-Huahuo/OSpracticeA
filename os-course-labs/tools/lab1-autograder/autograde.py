#!/usr/bin/env python3
"""autograde.py — lab1 统一验收驱动(macOS/Linux 均可跑)

用法:
    python3 tools/lab1-autograder/autograde.py --tree <学生树> --sid 20230101

验收项:
  1. banner 逐字节比对: 以学生树内 expect_banner.txt 为准;
     先对其做协议形状校验(gen_expect.py), 再与实跑输出的前 N 字节全等比对
  2. `-d int` 清洁检查: 全程零异常行
  3. 断电幂等: 两次冷启动输出逐字节一致
  4. 节流源码检查: console 层有按 16+COURSE_SID%16 的计数逻辑
输出: PASS:/FAIL: 判定行
      末行 RESULT: x/y
"""
import argparse
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gen_expect import check_student_expect  # noqa: E402

QEMU = "qemu-system-riscv64"
QEMU_ARGS = ["-machine", "virt", "-bios", "none", "-kernel",
             "kernel/kernel", "-nographic"]


def build(tree):
    subprocess.run(["make", "clean"], cwd=tree, capture_output=True)
    r = subprocess.run(["make"], cwd=tree, capture_output=True, timeout=300)
    return r.returncode == 0


def capture(tree, extra=None, seconds=4.0):
    cmd = [QEMU] + QEMU_ARGS + (extra or [])
    p = subprocess.Popen(cmd, cwd=tree, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    time.sleep(seconds)
    p.kill()
    out = p.stdout.read()
    p.wait()
    return out


def verdict(line):
    print(line)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", required=True)
    ap.add_argument("--sid", type=int, required=True)
    args = ap.parse_args()
    tree = os.path.abspath(args.tree)

    score, total = 0, 3

    # 前置:构建
    if not build(tree):
        verdict("[FAIL:build] make 失败")
        print(f"RESULT: 0/{total}")
        sys.exit(1)

    # 1. expect 文件校验
    exp_path = os.path.join(tree, "expect_banner.txt")
    if not os.path.exists(exp_path):
        verdict("[FAIL:expect_file] 未找到 expect_banner.txt")
        print(f"RESULT: 0/{total}")
        sys.exit(1)
    exp = open(exp_path, "rb").read()
    errs = check_student_expect(args.sid, exp)
    if errs:
        verdict(f"[FAIL:expect_shape] 期望文件不符合协议: {'; '.join(errs)}")
        print(f"RESULT: 0/{total}")
        sys.exit(1)

    # 2. 实跑输出 capture
    out1 = capture(tree)
    if not out1.startswith(exp):
        verdict("[FAIL:banner_match] 实跑输出与 expect_banner.txt 不匹配")
        print(f"  期望前 60B: {exp[:60]!r}")
        print(f"  实跑前 60B: {out1[:60]!r}")
    else:
        verdict("[PASS:banner_match] banner 逐字节一致")
        score += 1

    # 3. 幂等性(第二次启动)
    out2 = capture(tree)
    if out1 != out2:
        verdict("[FAIL:idempotent] 两次启动输出不一致")
    else:
        verdict("[PASS:idempotent] 两次启动输出逐字节一致")
        score += 1

    # 4. `-d int` 清洁
    int_log = capture(tree, extra=["-d", "int"])
    bad = [ln for ln in int_log.decode("latin1", "ignore").splitlines()
           if re.search(r"\b(cause|fault|trap)\b", ln, re.I)]
    if bad:
        verdict(f"[FAIL:d_int] 发现异常输出 ({len(bad)} 行)")
    else:
        verdict("[PASS:d_int] 全程无内核异常/中断报错")
        score += 1

    # 源码检查(节流逻辑)
    src = ""
    for root, _, files in os.walk(os.path.join(tree, "kernel")):
        for f in files:
            if f.endswith((".c", ".h")):
                try:
                    src += open(os.path.join(root, f),
                                errors="ignore").read() + "\n"
                except Exception:
                    pass
    if "COURSE_SID" in src and ("nop" in src or "% 16" in src):
        verdict("[INFO:throttle] 源码包含 COURSE_SID 节流引用")
    else:
        verdict("[WARN:throttle] 未在 kernel/ 源码中检测到 COURSE_SID 节流逻辑")

    print(f"RESULT: {score}/{total}")
    sys.exit(0 if score == total else 1)


if __name__ == "__main__":
    main()
