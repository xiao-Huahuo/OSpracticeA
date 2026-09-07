#!/usr/bin/env python3
"""gen_expect.py — lab1 期望输出生成与协议结构校验

两个用途:
  1) TA 侧: python3 gen_expect.py --sid 20230101 [--print]
     生成"标准形状"的期望 banner(供与该生声明文件对照参考;
     前缀文案是该生规格的自由项, 数值/协议形状不是)。
  2) 验收侧: import 或 --check <file> 校验学生提交的 expect_banner.txt
     是否符合其学号协议的形状与数值。

协议形状(实验说明书 §3):
  0 = 明文 + 换行: 一行, 含学号十进制与 (学号%97) 的十六进制
  1 = 每个字节后跟一个 '.'
  2 = 整段输出后回显校验和(ASCII 数字, 算法由该生规格声明)
"""
import argparse
import sys


def mod97(sid: int) -> int:
    return sid % 97


def std_banner(sid: int) -> str:
    return f"OSLAB1 sid={sid} mod97=0x{mod97(sid):x}\n"


def apply_protocol(sid: int, line: str) -> bytes:
    p = sid % 3
    raw = line.encode()
    if p == 0:
        return raw
    if p == 1:
        return b"".join(bytes([b]) + b"." for b in raw)
    if p == 2:
        s = sum(raw) % 100000
        return raw + f"[chk={s}]".encode()
    raise ValueError(p)


def check_student_expect(sid: int, data: bytes) -> list:
    errs = []
    p = sid % 3
    text = data.decode("utf-8", "ignore")
    # 学号/mod97 检查应作用于协议解码后的文本:
    # 协议 1 在每字节后插 '.', 须先去点还原,否则 --print 自产的标准形状也无法通过;
    # 协议 0/2 不插入字符,原文即解码文本。
    probe = text.replace(".", "") if p == 1 else text
    if str(sid) not in probe:
        errs.append(f"未包含学号十进制 {sid}")
    if f"0x{mod97(sid):x}" not in probe:
        errs.append(f"未包含 mod97 十六进制 0x{mod97(sid):x}(注意小写无前导零)")
    if p == 0 and not text.endswith("\n"):
        errs.append("协议 0 应以换行结束")
    if p == 1 and not text.endswith("."):
        errs.append("协议 1 每字节后跟 '.', 末尾亦然")
    if p == 2 and not any(ch.isdigit() for ch in text.rstrip("\n").split("\n")[-1]):
        errs.append("协议 2 末段应含 ASCII 数字校验和")
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sid", type=int)
    ap.add_argument("--print", action="store_true", help="打印标准形状期望")
    ap.add_argument("--check", help="校验学生提交的 expect_banner.txt")
    args = ap.parse_args()
    if not args.sid:
        sys.exit("需要 --sid")
    if args.print:
        out = apply_protocol(args.sid, std_banner(args.sid))
        sys.stdout.buffer.write(out)
    if args.check:
        data = open(args.check, "rb").read()
        errs = check_student_expect(args.sid, data)
        for e in errs:
            print(f"! {e}")
        print(f"[{'ok' if not errs else 'FAIL'}] 协议形状校验"
              f"(sid={sid_protocol(args.sid)} 号协议)")
        sys.exit(1 if errs else 0)


def sid_protocol(sid: int) -> int:
    return sid % 3


if __name__ == "__main__":
    main()
