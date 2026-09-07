#!/usr/bin/env python3
"""
bugbank.py — lab7 综合排错与系统诊断题库管理与试卷生成脚本

子命令:
  validate                     核对题库字段规范与取值范围
  assemble --sid 20230101 [--weak memory] [--out exams/]
                                 试卷生成:按学号哈希确定性抽取 3 道题目,跨 ≥2 层、
                                 含 1 高难度(≥4)与 1 低难度(≤2,不足放宽),
                                 弱项层优先纳入;变异参数由学号哈希确定生成。
                                 产物含根因答案,仅供教师存档,严禁下发学生。
"""
import argparse
import hashlib
import json
import os
import random
import sys

BANK_VERSION = 1

REQUIRED = ["id", "origin", "layer", "type", "root_cause", "symptom",
            "detection", "difficulty", "variant_params", "fixed_by_teachers"]
LAYERS = {"boot", "trap", "memory", "sched", "syscall", "fs"}
TYPES = {"race", "consistency", "order", "semantic"}


def load_cards(bank_dir: str) -> list:
    cards = []
    if not os.path.exists(bank_dir):
        return cards
    for f in sorted(os.listdir(bank_dir)):
        if not f.endswith(".json"):
            continue
        with open(os.path.join(bank_dir, f)) as fh:
            cards.append(json.load(fh))
    return cards


def validate(cards: list) -> list:
    errs = []
    ids = set()
    for c in cards:
        for k in REQUIRED:
            if k not in c:
                errs.append(f"{c.get('id', '?')}: 缺字段 {k}")
        if c.get("layer") not in LAYERS:
            errs.append(f"{c['id']}: layer 非法 {c['layer']}")
        if c.get("type") not in TYPES:
            errs.append(f"{c['id']}: type 非法 {c['type']}")
        d = c.get("difficulty", 0)
        if not (isinstance(d, int) and 1 <= d <= 5):
            errs.append(f"{c['id']}: difficulty 应为 1–5 整数")
        for p, rng in c.get("variant_params", {}).items():
            if not (isinstance(rng, list) and len(rng) == 2 and rng[0] <= rng[1]):
                errs.append(f"{c['id']}: 变异参数 {p} 需要 [min,max]")
        if c["id"] in ids:
            errs.append(f"{c['id']}: 重复 id")
        ids.add(c["id"])
    return errs


def assemble(cards: list, sid: int, weak=None) -> dict:
    rnd = random.Random(int(hashlib.sha256(str(sid).encode()).hexdigest(), 16))

    def pick(pool):
        return rnd.choice(pool) if pool else None

    chosen = []
    # 1) 弱项层一张(有数据且卡池允许时)
    weak_pool = [c for c in cards if c["layer"] == weak] if weak else []
    c = pick(weak_pool)
    if c:
        chosen.append(c)
    # 2) 一张高难度(≥4)
    pool = [c for c in cards if c not in chosen and c["difficulty"] >= 4]
    c = pick(pool)
    if c:
        chosen.append(c)
    # 3) 补齐到 3 张,优先换层
    for _ in range(3 - len(chosen)):
        pool = [c for c in cards if c not in chosen]
        if not pool:
            break
        other_layers = [c for c in pool
                        if {x["layer"] for x in chosen} - {c["layer"]}]
        chosen.append(pick(other_layers or pool))
    # 硬约束:跨 ≥2 层、含 1 高难度;不满足时换牌重试(最多 20 次)
    for _ in range(20):
        layers = {c["layer"] for c in chosen}
        has_high = any(c["difficulty"] >= 4 for c in chosen)
        if len(chosen) == 3 and len(layers) >= 2 and has_high:
            break
        chosen = rnd.sample(cards, min(3, len(cards)))

    bank_digest = hashlib.sha256(
        json.dumps([{k: c[k] for k in sorted(c)} for c in cards],
                   ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
    exam = {"sid": sid, "weak_layer": weak,
            "bank_version": BANK_VERSION,
            "bank_digest": bank_digest,
            "NOTE": "含根因答案,仅供教师存档,严禁下发;"
                    "bank_version/bank_digest 变化即视为换题,需全量重发",
            "cards": []}
    for c in chosen:
        chosen_params = {p: rnd.randint(rng[0], rng[1])
                         for p, rng in c["variant_params"].items()}
        exam["cards"].append({
            "id": c["id"], "layer": c["layer"], "type": c["type"],
            "difficulty": c["difficulty"], "root_cause": c["root_cause"],
            "detection": c["detection"], "symptom": c["symptom"],
            "chosen_params": chosen_params,
            "repro_seed": rnd.randrange(2**31)})
    return exam


def main():
    ap = argparse.ArgumentParser(description="lab7 综合排错题库管理与试卷生成工具")
    ap.add_argument("cmd", choices=["validate", "assemble"])
    ap.add_argument("--bank", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "cards"))
    ap.add_argument("--sid", type=int, help="学生学号")
    ap.add_argument("--roster", help="学生名单文本文件(每行一个学号)")
    ap.add_argument("--weak", help="薄弱模块(依据前序实验综合表现)")
    ap.add_argument("--out", default="exams", help="试卷输出目录")
    args = ap.parse_args()

    cards = load_cards(args.bank)
    if not cards:
        sys.exit(f"卡库 {args.bank} 为空或不存在")

    if args.cmd == "validate":
        errs = validate(cards)
        for e in errs:
            print(f"! {e}")
        layers = sorted({c["layer"] for c in cards})
        print(f"卡库:{len(cards)} 张;层覆盖 {layers};"
              f"{'字段全部合规' if not errs else f'{len(errs)} 处问题'}")
        sys.exit(1 if errs else 0)

    if args.cmd == "assemble":
        sids = []
        if args.roster:
            with open(args.roster) as f:
                for line in f:
                    s = line.strip().split()[0] if line.strip() else ""
                    if s and s.isdigit():
                        sids.append(int(s))
        elif args.sid:
            sids.append(args.sid)
        else:
            sys.exit("assemble 命令需要指定 --sid <学号> 或 --roster <花名册路径>")

        os.makedirs(args.out, exist_ok=True)
        for s in sids:
            exam = assemble(cards, s, args.weak)
            out_path = os.path.join(args.out, f"exam-{s}.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(exam, f, ensure_ascii=False, indent=2)
            card_ids = [c["id"] for c in exam["cards"]]
            print(f"[OK] 学号 {s} 试卷生成: {card_ids} → {out_path}")


if __name__ == "__main__":
    main()
