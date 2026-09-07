#!/usr/bin/env python3
"""gen_intro_slides.py — 生成《教师版-导学板书幻灯片.pptx》
浅色投影风格(面向学生讲授): 米白底、深墨字、深蓝强调, 大字号
保证后排可读; 无任何内部版本字样。9 讲(学期第一课 + lab0–7)。
用法: python3 tools/gen_intro_slides.py  → 输出到 导学材料/ 目录。
"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

BG      = RGBColor(0xFD, 0xFC, 0xF8)   # 米白纸底
INK     = RGBColor(0x23, 0x2A, 0x31)   # 深墨(正文)
ACCENT  = RGBColor(0x1B, 0x3F, 0x8A)   # 深蓝(标题/强调,投影高对比)
BOXBG   = RGBColor(0xEE, 0xF2, 0xF8)   # 浅蓝灰板书框底
BOXLINE = RGBColor(0x3A, 0x55, 0x7A)   # 板书框边
GRAY    = RGBColor(0x55, 0x60, 0x6C)   # 次要说明
LINE    = RGBColor(0xB9, 0xC2, 0xCE)   # 分隔线
W, H = 13.333, 7.5
FONT = "Kaiti SC"

def set_run(r, text, size, color=INK, bold=False):
    r.text = text
    f = r.font
    f.size, f.bold, f.name = Pt(size), bold, FONT
    f.color.rgb = color
    rPr = r._r.get_or_add_rPr()
    ea = rPr.makeelement(qn('a:ea'), {'typeface': FONT})
    rPr.append(ea)

def txbox(slide, x, y, w, h, lines, size=24, color=INK, bold=False,
          align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.3):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment, p.line_spacing = align, spacing
        set_run(p.add_run(), line, size, color, bold)
    return tb

def box(slide, x, y, w, h, fill=BOXBG, line=BOXLINE, lw=2.0,
        shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    sp = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    sp.fill.solid(); sp.fill.fore_color.rgb = fill
    sp.line.color.rgb = line; sp.line.width = Pt(lw)
    sp.shadow.inherit = False
    tf = sp.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.1)
    tf.margin_top = tf.margin_bottom = Inches(0.04)
    return sp

def box_text(sp, lines, size=20, title_size=None):
    """首行为小标题(深蓝加粗),其余为正文;单行时统一字号。"""
    tf = sp.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tsize = title_size or size
    multi = len(lines) > 1
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.CENTER
        p.line_spacing = 1.28
        if multi and i == 0:
            set_run(p.add_run(), line, tsize, ACCENT, True)
        else:
            set_run(p.add_run(), line, size, INK)

def title_of(slide, text):
    txbox(slide, 0.6, 0.22, W - 1.2, 1.05, [text], 44, ACCENT, True)
    box(slide, 0.65, 1.18, W - 1.35, 0.04, fill=LINE, line=LINE, lw=1.0,
        shape=MSO_SHAPE.RECTANGLE)

def caption(slide, text, y=6.7):
    txbox(slide, 0.8, y, W - 1.6, 0.8, ["✎ " + text], 24, GRAY)

def new_slide(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = BG
    return s

def h_arrow(s, x, y, w):
    ar = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y),
                            Inches(w), Inches(0.34))
    ar.fill.solid(); ar.fill.fore_color.rgb = ACCENT
    ar.line.fill.background()
    ar.shadow.inherit = False
    return ar

def v_arrow(s, x, y):
    ar = s.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(x), Inches(y),
                            Inches(0.5), Inches(0.55))
    ar.fill.solid(); ar.fill.fore_color.rgb = ACCENT
    ar.line.fill.background()
    ar.shadow.inherit = False
    return ar

# ---------------------------------------------------------------- 渲染器

def render_section(prs, payload):
    s = new_slide(prs)
    txbox(s, 0.9, 2.05, W - 1.8, 1.6, [payload["big"]], 56, ACCENT, True,
          align=PP_ALIGN.CENTER)
    box(s, 3.6, 3.9, W - 7.2, 0.04, fill=LINE, line=LINE, lw=1.0,
        shape=MSO_SHAPE.RECTANGLE)
    txbox(s, 0.9, 4.15, W - 1.8, 0.95, [payload["sub"]], 32, INK,
          align=PP_ALIGN.CENTER)

def render_bullets(prs, payload):
    s = new_slide(prs)
    title_of(s, payload["title"])
    items = payload["items"]
    size = 36 if len(items) <= 4 else 30
    y0 = 1.45 if len(items) <= 4 else 1.35
    step = 1.5 if len(items) <= 4 else 1.15
    for i, it in enumerate(items):
        txbox(s, 0.9, y0 + i * step, W - 1.8, 1.6,
              ["• " + it], size, ACCENT if i == 0 else INK, i == 0)
    if "cap" in payload:
        caption(s, payload["cap"])

def render_flow(prs, payload):
    s = new_slide(prs)
    title_of(s, payload["title"])
    labels = payload["items"]
    n = len(labels)
    gap = 0.42 if n >= 5 else 0.5
    if n <= 5:                       # 单行
        bw = min(2.7, (W - 1.6 - gap * (n - 1)) / n)
        bh, fsize = 1.9, (30 if n <= 4 else 28)
        x = (W - (n * bw + (n - 1) * gap)) / 2
        y = 2.45
        for i, lab in enumerate(labels):
            sp = box(s, x, y, bw, bh)
            box_text(sp, lab.split("|"), size=fsize)
            if i < n - 1:
                h_arrow(s, x + bw + 0.05, y + bh / 2 - 0.2, gap - 0.1)
            x += bw + gap
    else:                            # 双行
        r1 = (n + 1) // 2
        rows = [labels[:r1], labels[r1:]]
        bw = min(2.8, (W - 1.6 - gap * (r1 - 1)) / r1)
        bh, fsize = 1.8, 28
        for ri, row in enumerate(rows):
            x = (W - (len(row) * bw + (len(row) - 1) * gap)) / 2
            y = 1.6 if ri == 0 else 4.3
            for i, lab in enumerate(row):
                sp = box(s, x, y, bw, bh)
                box_text(sp, lab.split("|"), size=fsize)
                if i < len(row) - 1:
                    h_arrow(s, x + bw + 0.05, y + bh / 2 - 0.2, gap - 0.1)
                x += bw + gap
            if ri == 0 and len(rows) > 1:
                end_cx = x - gap + bw / 2 - 0.25
                v_arrow(s, end_cx, y + bh + 0.25)
    if "cap" in payload:
        caption(s, payload["cap"])

def render_stack(prs, payload):
    s = new_slide(prs)
    title_of(s, payload["title"])
    segs = payload["items"]
    bh, gap = 0.95, 0.1
    x, w = 1.6, 10.1
    y = 1.35
    for i, seg in enumerate(segs):
        sp = box(s, x, y, w, bh, line=ACCENT if i == len(segs) - 1 else BOXLINE,
                 lw=2.5 if i == len(segs) - 1 else 2.0)
        box_text(sp, [seg], size=28)
        y += bh + gap
    if "cap" in payload:
        caption(s, payload["cap"])

def render_cards(prs, payload):
    s = new_slide(prs)
    title_of(s, payload["title"])
    cards = payload["items"]
    n = len(cards)
    gap = 0.45
    cw = (W - 1.4 - gap * (n - 1)) / n
    ch = 4.35
    y = 1.5
    x = 0.7
    for c in cards:
        sp = box(s, x, y, cw, ch)
        box_text(sp, c.split("|"), size=26, title_size=30)
        x += cw + gap
    if "cap" in payload:
        caption(s, payload["cap"])

RENDER = {"section": render_section, "bullets": render_bullets,
          "flow": render_flow, "stack": render_stack, "cards": render_cards}

# ---------------------------------------------------------------- 幻灯片数据

SECTIONS = [
{"name": "第〇课 学期第一课", "slides": [
  {"kind": "section", "big": "操作系统实践", "sub": "第〇课 · 学期第一课(20 分钟)"},
  {"kind": "bullets", "title": "原理课 vs 实践课", "items": [
    "原理课: 操作系统『是什么』",
    "实践课: 它『怎么造出来』",
    "你的角色: 架构师 —— AI 是程序员",
    "思考 · 测试 · 诊断 · 验收: 你负责"]},
  {"kind": "flow", "title": "从零累积构建 (两周一轮)", "items": [
    "思考题", "自写测试", "指挥 AI 实现", "验收问答"],
    "cap": "官方测试随增量包发放判功能; 自写测试先于实现定规格, 是你的设计保险 —— 验收分占总评 70%, 档位由现场问答决定"},
  {"kind": "cards", "title": "两条游戏规则", "items": [
    "AI 政策|任何环节允许用|验收问的是你自己的参数与代码",
    "个性化参数|策略 / 方案 / 协议按学号生成|通用答案过不了测试"]},
  {"kind": "bullets", "title": "两条红线 & Git 刚需", "items": [
    "验收问答没有替身 —— 参数每人不同, 通用答案无效",
    "Git 是刚需: init 建仓 · tag 存盘 · archive 提交 · bisect 排障",
    "验收缺席/E 档: 一周内补验一次, 通过最高记 60",
    "评分口径全文对你公开"]},
  {"kind": "bullets", "title": "期末时的你", "items": [
    "『我指挥 AI 造过一个操作系统』",
    "『我能诊断它的故障』",
    "『十五周后它是属于你自己的操作系统』"]},
]},
{"name": "lab0 先学看地图", "slides": [
  {"kind": "section", "big": "lab0 · 阅读与剖析", "sub": "一条命令的生命周期 —— 不写一行代码(25 分钟)"},
  {"kind": "bullets", "title": "任务: 交付三张图", "items": [
    "控制流图: read → fork → exec → write 全链",
    "三张快照: 进程表 / 页表 / 文件表",
    "一次时钟中断的旅程",
    "走查课: 随机点名, 按图讲解"]},
  {"kind": "flow", "title": "两个世界与一扇门", "items": [
    "用户世界|shell · echo", "ecall 敲门", "内核世界|syscall · 调度 · uart"],
    "cap": "过边界只有这一扇门 —— 两侧的栈、权限、地址都不同"},
  {"kind": "cards", "title": "三本账(系统的账本)", "items": [
    "进程表|谁在运行|前台登记册",
    "页表|谁住哪个地址|房间登记册",
    "文件表|谁打开了什么|借阅登记册"],
    "cap": "操作系统的全部工作 = 维护三本账的一致性 —— 每个实验都在改其中一本"},
  {"kind": "bullets", "title": "中断驱动", "items": [
    "你敲键盘时, CPU 正在干别的",
    "是设备『打电话』过来",
    "CPU 挂起手头工作去接",
    "→ 一次回车引发一串内核活动"]},
  {"kind": "bullets", "title": "AI 怎么用", "items": [
    "可以让 AI 逐行解释汇编(它擅长)",
    "图必须自己画",
    "走查课随机点名 —— 讲不出来当场现形"]},
]},
{"name": "lab1 从电源到 main", "slides": [
  {"kind": "section", "big": "lab1 · 启动与串口输出", "sub": "从按下电源到第一行 C 代码(35 分钟)"},
  {"kind": "bullets", "title": "被跳过的问题", "items": [
    "『程序跑起来了』好像理所当然",
    "按下电源之后、main 之前, 发生了什么?",
    "一段在没有操作系统的荒野上的旅程",
    "两周内, 你亲手铺完这条路"]},
  {"kind": "stack", "title": "地址空间地图(virt 机器)", "items": [
    "0x0  ROM(出生点, 上电 PC=0x1000)",
    "MMIO 设备区(UART / CLINT 时钟 / PLIC)",
    "……(空洞)……",
    "0x80000000  RAM 起点 ← 内核的家"],
    "cap": "设备不在内存里, 却占用内存地址 —— 写它 = 触发动作, 不是存储"},
  {"kind": "flow", "title": "启动时序", "items": [
    "上电|PC=0x1000", "跳|0x80000000", "entry.S|关中断·立栈",
    "M 态准备|mepc 等", "mret|降 S 态", "main"],
    "cap": "像老板换工装下工地: 降级前把该交代的都交代好"},
  {"kind": "cards", "title": "链接地址 vs 加载地址", "items": [
    "课表(链接地址)|链接脚本说了算|『我以为我在哪』",
    "教室(加载地址)|加载器说了算|『实际被放在哪』"],
    "cap": "两者必须一致 —— 弄拧了就是黑屏, 一行输出都没有"},
  {"kind": "cards", "title": "特权级 与 MMIO", "items": [
    "M / S / U 态|总钥匙 · 管理层 · 访客|内核『自愿降级』到 S 态",
    "MMIO|设备冒充内存|同一门牌: 有的是仓库, 有的是对讲机"]},
  {"kind": "bullets", "title": "衔接 & 自检", "items": [
    "现在会『说』了, 还不会『听』、不会被打断 → lab2",
    "Git 首检: 下课前必须完成 baseline 初始提交",
    "上电第一条指令在哪执行? 为什么非 0 号核要睡觉?"]},
]},
{"name": "lab2 被打断后完美复原", "slides": [
  {"kind": "section", "big": "lab2 · 陷入与中断", "sub": "系统调用机制 与 中断驱动控制台(35 分钟)"},
  {"kind": "bullets", "title": "操作系统最重要的能力", "items": [
    "不是『做事』",
    "是『被打断后毫发无损地继续』",
    "时钟每几毫秒打断你一次, 键盘随时打断你",
    "而用户程序毫无察觉"]},
  {"kind": "flow", "title": "trap 路径(本章灵魂图)", "items": [
    "用户态", "打断", "trampoline|中转站", "trapframe|存档 ★",
    "内核办事", "读档", "sret 返回"],
    "cap": "谁保存、存在哪、何时恢复 —— 这个实验的全部内容"},
  {"kind": "cards", "title": "trapframe = 游戏存档", "items": [
    "存档|32 个寄存器 + PC, 一个不少|读档少一个道具, 游戏就废了",
    "伏笔|lab4 的 swtch 只存 14 个|为什么?——『编译器约定』, lab4 见"]},
  {"kind": "cards", "title": "ecall / sret = 一对旋转门", "items": [
    "ecall 进|硬件只做三件事: 记下来处 · 切模式 · 跳 stvec|门不帮你看包(寄存器)",
    "sret 出|从存档恢复现场|『回来时从下一条继续』 → epc 要 +4"]},
  {"kind": "cards", "title": "轮询 vs 中断", "items": [
    "轮询|每 30 秒问一次: 饭好了吗|CPU 空转(lab1 的做法)",
    "中断|饭好了, 锅自己响|代价: 并发! 锅响时你正端着油锅"]},
  {"kind": "bullets", "title": "衔接与伏笔", "items": [
    "门造好了, 但进程的『房间』还没分配 → lab3",
    "设计留债: 用户指针直接解引用(lab3还)、假调度(lab4还)"]},
]},
{"name": "lab3 门牌号与登记册", "slides": [
  {"kind": "section", "big": "lab3 · 内存管理", "sub": "三级页表 与 物理页分配(35 分钟)"},
  {"kind": "bullets", "title": "最古老的魔术", "items": [
    "每个程序都以为自己独占一台内存",
    "它用 0x1000, 我也用 0x1000, 互不打扰",
    "这个实验: 亲手变魔术",
    "造登记册 · 分房间 · 失败时体面收场(回滚)"]},
  {"kind": "flow", "title": "翻译 = 快递三级分拣", "items": [
    "va|三段索引", "L2 分拣", "L1 分拣", "L0 分拣", "pa|页号+偏移"],
    "cap": "每级 PTE =『下一站地址 + 通行权限』"},
  {"kind": "stack", "title": "进程地址空间(自高向低)", "items": [
    "trampoline(最高页: 两国交界的站台)",
    "trapframe",
    "代码 / 只读数据",
    "guard page: 谁也进不去的陷阱房 ← 栈溢出 = 报警",
    "栈 … 堆 …"]},
  {"kind": "cards", "title": "权限位 = 钥匙规格", "items": [
    "V / R / W / X / U|房间存在 · 能读 · 能写 · 能执行 · 访客可进|内核页无 U → 用户『看不见』内核",
    "guard page|存在, 但无权进入|栈溢出的报警地砖"]},
  {"kind": "cards", "title": "失败回滚 = 退房手续", "items": [
    "正确顺序|先销登记(PTE) → 再退房(free)|先到前台消名, 再交钥匙",
    "顺序反了|房间退了, 登记还在|下一个住户和『幽灵』同住(double free)"],
    "cap": "这个顺序是本实验所有排障的共同原型"},
  {"kind": "bullets", "title": "衔接 & 还债第一课", "items": [
    "还债第一课: 重构 lab2 用户指针, 走安全页表拷贝",
    "fork 要整套复印房子 → 太贵 (lab5 解决)",
    "在那之前, lab4: 这么多住户怎么轮流用 CPU"]},
]},
{"name": "lab4 一台 CPU 万户轮住", "slides": [
  {"kind": "section", "big": "lab4 · 进程与调度", "sub": "上下文切换 · 睡眠唤醒 · 你的专属策略(40 分钟)"},
  {"kind": "bullets", "title": "变的是人, 不变的是台", "items": [
    "单核同一时刻只跑一个进程",
    "每几毫秒『冻结一个、解冻一个』, 快到人眼无感",
    "本实验还要面对真敌人: 并发",
    "偿还 lab2 之债: 假调度在此替换为真调度"]},
  {"kind": "flow", "title": "栈流转(灵魂图)", "items": [
    "用户栈", "内核栈", "调度器栈 ★", "另一进程|内核栈", "另一进程|用户栈"],
    "cap": "调度器有自己的栈, 不属于任何进程 —— 物业办公室不属于任何住户"},
  {"kind": "cards", "title": "swtch = 搬家公司", "items": [
    "只搬家具|s0–s11 + ra / sp = 14 个|赌编译器守『调用约定』这份合同",
    "衣物自理|t / a 系寄存器调用者自己管|所以 trapframe 才要存 31 个"]},
  {"kind": "cards", "title": "排队规则(每人一种)", "items": [
    "轮转 / 优先级|先来先到 / VIP 通道",
    "MLFQ|新客快服务, 老客慢慢排队|防霸占",
    "彩票 / 步长|按持券比例抽签 / 精确记账"],
    "cap": "策略不难, 难的是『换规则时账本不出错』 —— 问答就问这里"},
  {"kind": "cards", "title": "丢失唤醒(最重要的并发原型)", "items": [
    "事故|A 查完『没数据』正要睡|B 恰在此刻喊了一声 —— 没人听见|A 随后睡着, 永远",
    "解法|检查和入睡|在同一间『锁死』的屋里完成"]},
  {"kind": "bullets", "title": "衔接 & 自检", "items": [
    "持锁为什么不能睡? kill 为什么不能硬拽? (验收必问)",
    "swtch 返回后, 执行的是谁的代码?",
    "fork 复制整套房子太贵 → lab5 合租"]},
]},
{"name": "lab5 写到才复制", "slides": [
  {"kind": "section", "big": "lab5 · 系统调用与 COW fork", "sub": "全课程难度顶点 —— 账本是主角(40 分钟)"},
  {"kind": "bullets", "title": "优雅到近乎偷懒", "items": [
    "fork 之后常常立刻 exec —— 复印的房子转眼拆掉",
    "COW: fork 时一套房子两家共享(全标只读)",
    "谁真要动墙, 物业当场给他复印一间",
    "你的计数器要证明这一点 —— 伪 COW 骗不过数字"]},
  {"kind": "cards", "title": "引用计数 = 合租人数登记", "items": [
    "fork 共享|计数 +1",
    "缺页复制|旧页 −1",
    "exit|−1, 减到 0 才 free"],
    "cap": "最后一人离开, 才关灯退房"},
  {"kind": "flow", "title": "缺页判定决策树", "items": [
    "地址无效|→ 杀", "有效且可写|→ 不该进来",
    "只读 + COW 标|计数>1: 复制", "计数=1|原地改权限"],
    "cap": "两张图(时机表 + 决策树)就是思考题与验收问答的原题"},
  {"kind": "cards", "title": "三种账本(每人一种)", "items": [
    "PTE 保留位|不占内存|但只有两位, 会溢出",
    "全局数组|简单|但锁粒度是学问",
    "页表扫描|零额外存储|但扫描时表在变"],
    "cap": "各有各的坑 —— 坑要自己踩过, 验收才讲得清"},
  {"kind": "cards", "title": "两颗最凶险的雷", "items": [
    "丢失 +1|数人头时不许搬家|账错很久之后才爆: 房子被重复退掉",
    "exec|先签新房, 再退旧房|否则失败时无家可归, 连 −1 都返回不了"]},
  {"kind": "bullets", "title": "衔接 & 自检", "items": [
    "内存里的世界断电即失 → lab6",
    "丢失一次 +1 的最终症状? (验收追问)",
    "fork 后立即 exec, 物理页复制几次? (≈ 0)"]},
]},
{"name": "lab6 写给断电世界的账本", "slides": [
  {"kind": "section", "big": "lab6 · 文件系统", "sub": "缓冲区缓存 与 日志 —— 崩溃一致性(40 分钟)"},
  {"kind": "bullets", "title": "最漂亮的一类问题", "items": [
    "进程崩溃可以重启, 内存数据可以重算",
    "文件系统元数据错一格, 整个磁盘的账平不了",
    "『写一半断电』如何恢复到 要么做了 / 要么没做?",
    "武器: 日志 —— 先抄草稿、签名、再誊正"]},
  {"kind": "flow", "title": "WAL 块流动(灵魂图)", "items": [
    "write", "日志区|草稿", "签名块 n|唯一判据 ★", "install|誊写原位", "完成"],
    "cap": "『多处原子』化为『单处原子』 —— 单块原子由磁盘硬件保证"},
  {"kind": "cards", "title": "三道闪电, 实为两类", "items": [
    "签名前断电 ⚡|撕掉草稿, 当无事发生",
    "签名后断电 ⚡|照草稿重誊(含誊一半)|誊写幂等, 可重放到底"],
    "cap": "两类闪电, 不是八类 —— 崩溃表的直观捷径"},
  {"kind": "cards", "title": "缓存 = 办公桌", "items": [
    "桌面有限|常用块放手边(buf 层)|先收哪份 = 替换策略(每人一种)",
    "铁律|带未保存修改的文件, 不许收进柜子|(脏页淘汰前必须写回)"]},
  {"kind": "cards", "title": "数据 / 元数据的边界", "items": [
    "元数据(账本结构)|错了 = 系统坏|必须进日志",
    "数据(文件内容)|旧了 = 内容旧|按 xv6 语义可不进日志"],
    "cap": "这条线必须想清楚 —— 验收专问『什么不归日志管』"},
  {"kind": "bullets", "title": "衔接 & 自检", "items": [
    "六大子系统全部到手, exec 从磁盘加载 → lab7 路考",
    "恢复时怎么知道断在哪? 只看签名块",
    "脏 buf 被淘汰前, 必须做什么?"]},
]},
{"name": "lab7 期末路考", "slides": [
  {"kind": "section", "big": "lab7 · 综合攻防 + 限时设计", "sub": "不考背交规, 考上路(30 分钟)"},
  {"kind": "bullets", "title": "最后两周", "items": [
    "没有新知识, 只有综合运用",
    "每人一个混了 3 只典型 bug 的内核",
    "期末 60 分钟纸质闭卷现场设计题",
    "考两样: 诊断的手感 + 架构师的笔头"]},
  {"kind": "cards", "title": "三问分诊(拿到 bug 的前三步)", "items": [
    "响 / 静?|崩溃, 还是数据悄悄错",
    "单核 / 多核?|复现条件本身是线索",
    "必然 / 概率?|概率 → 先放大再定位"],
    "cap": "三问定方向, 方向定工具(-d int / gdb / 计数差分 / crash 点)"},
  {"kind": "cards", "title": "修复引入 = 医源性损伤", "items": [
    "三大典型|锁范围扩大 · 回滚顺序变化 · 错误码语义漂移",
    "修复引入的新伤, 根因简报里必须自己交代"]},
  {"kind": "cards", "title": "限时设计的评分", "items": [
    "考什么|分解(模块怎么切) · 结构(数据与不变式) · 远见(并发与失败路径)",
    "不考什么|没有代码分, 伪代码仅作为表达工具"]},
  {"kind": "bullets", "title": "备考", "items": [
    "重读你自己的所有提交 —— 问答只问你自己做的东西",
    "设计笔记里的『不变式清单』是复习重点",
    "实在找不到 bug? 排除链本身计分"]},
]},
]

def main():
    import argparse
    ap = argparse.ArgumentParser(
        description="重新生成导学板书幻灯片(默认原位覆盖 导学材料/ 下同名 pptx)")
    ap.add_argument("--out", metavar="DIR或FILE",
                    help="输出到指定目录或文件(默认原位覆盖;"
                         "若曾手工编辑过 pptx,务必用 --out 另存避免覆盖丢失)")
    args = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    target_dir = os.path.join(os.path.dirname(here), "导学材料")
    if not os.path.isdir(target_dir):
        parent2 = os.path.dirname(os.path.dirname(here))
        target_dir = os.path.join(parent2, "导学材料")
    default = os.path.join(target_dir, "教师版-导学板书幻灯片.pptx")
    if args.out:
        out = args.out
        if os.path.isdir(out) or out.endswith("/"):
            out = os.path.join(out, "教师版-导学板书幻灯片.pptx")
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    else:
        out = default
        print("[提示] 未指定 --out,将原位覆盖默认 pptx(手工修改会丢失;"
              "如需另存请加 --out)")
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(W), Inches(H)
    n = 0
    for sec in SECTIONS:
        for payload in sec["slides"]:
            RENDER[payload["kind"]](prs, payload)
            n += 1
    prs.save(out)
    print(f"生成 {out}: 共 {n} 页 / {len(SECTIONS)} 讲(浅色大字版, 无页脚)")

if __name__ == "__main__":
    main()
