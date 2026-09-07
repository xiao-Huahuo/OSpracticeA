#!/usr/bin/env python3
"""
gen_lab_pack.py — V3 增量包生成器(每轮一个,全班同份)

包结构:
  能力目标与接口约定.md   ← pack_manifests/labN-contract.md
  gifts/<dst>             ← 预置支撑代码(src 三种来源,见下)
  support/                ← 测试与支撑组件
  合并说明                 ← 自动生成

src 记法:
  gifts:<v3 gifts 下路径>    课程自制支撑代码
  ref:<课程参考树内路径>      从参考 xv6 复制(仅允许 .S/.pl/.h/用户态)
  v2:<v2 包内路径>            复用 v2 支撑件

铁律(自检):ref: 来源不得出现 kernel/*.c —— 官方 C 实现一件不发。
lab7 无包;lab1 无包(基线即 lab1)。

用法:
  python3 tools/gen_lab_pack.py --lab 2 --src ../xv6-riscv [--out packs/]
  python3 tools/gen_lab_pack.py --check --src ../xv6-riscv   # 全包自检
"""
import argparse
import json
import os
import shutil
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
V3_ROOT = os.path.dirname(HERE)
V2_ROOT = os.path.abspath(os.path.join(V3_ROOT, "..", "os-course-labs-v2"))

MERGE_NOTE = """# 合并说明(lab{lab})

1. 在工程根目录下执行: unzip packs/lab{lab}.zip -d .
   (解压得到 gifts/、support/ 以及《能力目标与接口约定.md》)
2. gifts/ 目录内的文件为**预置支撑代码（请勿修改）**, 请复制到工程中对应的位置;
   若与工程中已有文件同名, 请以增量包内版本为准(建议先使用 git diff 核对差异后再覆盖)。
3. 动手编写代码前, 请务必先仔细阅读《能力目标与接口约定.md》; 测试程序位于 support/ 目录。
4. 合并完成后建议执行:
     git add -A && git commit -m "lab{lab} pack merged" && git tag lab{lab}-start
5. 实验交付前:
     git tag lab{lab}-submit
     git archive --format=zip -o 提交-lab{lab}-<学号>.zip lab{lab}-submit

课程参考实现(如 MIT xv6 原版代码仅作为公开阅读参考)不包含本课程个性化接口与参数——
系统接口规范与行为定义严格以本实验包为准。
"""

def resolve_src(spec, src_root):
    kind, _, path = spec.partition(":")
    if kind == "gifts":
        return os.path.join(V3_ROOT, "gifts", path)
    if kind == "ref":
        return os.path.join(src_root, path)
    if kind == "v2":
        return os.path.join(V2_ROOT, path)
    sys.exit(f"未知 src 记法: {spec}")

def check_no_official_c(items, src_root):
    """铁律:ref:kernel/*.c 默认一票否决,仅显式 whitelist 例外(打印理由留痕);
    ref 下其他 .c 同样需白名单。例外仅限"非教学目标的环境事实"类
    (V3-01 §二判据),每学期核对一次例外清单。"""
    bad = []
    for it in items:
        if not it["src"].startswith("ref:"):
            continue
        rel = it["src"][4:]
        if rel.startswith("kernel/") and rel.endswith(".c"):
            if it.get("whitelist"):
                print(f"[ ok ] 白名单例外 {rel}: {it.get('reason','')}")
            else:
                bad.append(f"官方内核 C 实现: {rel}")
        elif rel.endswith(".c") and not it.get("whitelist"):
            bad.append(f"ref 下的 .c 未加白名单: {rel}")
    return bad

def build_pack(lab, src_root, out_dir):
    mpath = os.path.join(V3_ROOT, "pack_manifests", f"lab{lab}.json")
    if not os.path.isfile(mpath):
        sys.exit(f"缺少 pack_manifests/lab{lab}.json")
    manifest = json.load(open(mpath))

    gifts = manifest.get("gifts", [])
    support = manifest.get("support", [])
    bad = check_no_official_c(gifts + support, src_root)
    if bad:
        for b in bad:
            print(f"[FAIL] {b}")
        sys.exit("自检未通过:增量包不得包含官方实现")

    stage = os.path.join(out_dir, f"_stage_lab{lab}")
    if os.path.exists(stage):
        shutil.rmtree(stage)
    os.makedirs(stage)

    # 接口约定文档
    contract = os.path.join(V3_ROOT, "pack_manifests",
                            f"lab{lab}-contract.md")
    shutil.copy(contract, os.path.join(stage, "能力目标与接口约定.md"))

    # 预置支撑代码与测试组件
    copied = []
    for it in gifts:
        s = resolve_src(it["src"], src_root)
        d = os.path.join(stage, "gifts", it["dst"])
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copy(s, d)
        copied.append(("gifts/" + it["dst"], it["src"], it.get("reason", "")))
    for it in support:
        s = resolve_src(it["src"], src_root)
        d = os.path.join(stage, "support", it.get("dst", os.path.basename(s)))
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copy(s, d)
        copied.append(("support/" + it.get("dst", os.path.basename(s)),
                       it["src"], it.get("reason", "")))

    with open(os.path.join(stage, "合并说明.md"), "w") as f:
        f.write(MERGE_NOTE.format(lab=lab))

    zpath = os.path.join(out_dir, f"lab{lab}.zip")
    if os.path.exists(zpath):
        os.remove(zpath)
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(stage):
            for fn in files:
                p = os.path.join(root, fn)
                z.write(p, os.path.relpath(p, stage))
    shutil.rmtree(stage)

    print(f"打包 {zpath}")
    for dst, src, reason in copied:
        print(f"  {dst:40s} <- {src:45s} {reason}")
    todo = manifest.get("todo", [])
    if todo:
        print("  待课程组补齐(已列入接口约定规范 TODO 节):")
        for t in todo:
            print(f"    - {t}")
    return zpath, len(todo)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lab", type=int, choices=range(2, 7))
    ap.add_argument("--src", required=True, help="课程参考 xv6 目录")
    ap.add_argument("--out", default=os.path.join(V3_ROOT, "packs"))
    ap.add_argument("--check", action="store_true", help="全部包自检")
    ap.add_argument("--strict", action="store_true",
                    help="任一包存在'待课程组补齐'TODO 时以非零码退出"
                         "(用于开学前验收:绿灯必须等于内容齐备)")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    if args.check:
        ok = True
        total_todo = 0
        for lab in range(2, 7):
            try:
                _, n = build_pack(lab, args.src, args.out)
                total_todo += n
            except SystemExit as e:
                print(f"[FAIL] lab{lab}: {e}")
                ok = False
        if args.strict and total_todo:
            print(f"[strict] 共 {total_todo} 项待课程组补齐——增量包内容不齐,禁止发布")
            ok = False
        elif total_todo:
            print(f"[提示] 共 {total_todo} 项待课程组补齐(加 --strict 可使其阻断发布)")
        sys.exit(0 if ok else 1)
    build_pack(args.lab, args.src, args.out)

if __name__ == "__main__":
    main()
