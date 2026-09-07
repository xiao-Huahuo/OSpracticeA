#!/usr/bin/env python3
"""gen_first_class_slides.py — 生成《开学第一课-第0课与lab0.pptx》

课程组教师版:只覆盖开学第一课的两大块——
  第0课(课程怎么进行+评分) 与 lab0(阅读与剖析,当堂开工)。
后续各轮导学由任课教师按《实验导学授课大纲》自行备课,不提供逐字讲稿。

浅色投影风格与母包一致:米白底、深墨字、深蓝强调、大字号。
用法: python3 os-course-labs/tools/gen_first_class_slides.py
      → 输出到 导学材料/开学第一课-第0课与lab0.pptx
"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

BG      = RGBColor(0xFD, 0xFC, 0xF8)
INK     = RGBColor(0x23, 0x2A, 0x31)
ACCENT  = RGBColor(0x1B, 0x3F, 0x8A)
BOXBG   = RGBColor(0xEE, 0xF2, 0xF8)
BOXLINE = RGBColor(0x3A, 0x55, 0x7A)
GRAY    = RGBColor(0x55, 0x60, 0x6C)
LINE    = RGBColor(0xB9, 0xC2, 0xCE)
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

def title_of(slide, text, sub=None):
    txbox(slide, 0.6, 0.22, W - 1.2, 1.05, [text], 44, ACCENT, True)
    if sub:
        txbox(slide, 0.65, 1.12, W - 1.3, 0.5, [sub], 20, GRAY)
    box(slide, 0.65, 1.62 if sub else 1.18, W - 1.35, 0.04, fill=LINE,
        line=LINE, lw=1.0, shape=MSO_SHAPE.RECTANGLE)

def caption(slide, text, y=6.75):
    txbox(slide, 0.8, y, W - 1.6, 0.7, ["✎ " + text], 21, GRAY)

def new_slide(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = BG
    return s

def h_arrow(s, x, y, w):
    ar = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y),
                            Inches(w), Inches(0.34))
    ar.fill.solid(); ar.fill.fore_color.rgb = ACCENT
    ar.line.fill.background(); ar.shadow.inherit = False

def flow4(s, items, y=2.6, bw=2.7, gap=0.55, x0=0.7):
    """四段横向流程:框+箭头"""
    x = x0
    for i, lines in enumerate(items):
        box_text(box(s, x, y, bw, 1.5), lines, size=19)
        x += bw
        if i < len(items) - 1:
            h_arrow(s, x + 0.08, y + 0.58, gap - 0.16)
            x += gap

def two_cards(s, c1, c2, y=2.5, h=3.4):
    box_text(box(s, 0.7, y, 5.9, h), c1, size=20)
    box_text(box(s, 6.85, y, 5.8, h), c2, size=20)

def bullets(s, items, y=2.2, size=22, x=0.9, w=11.6, gap=1.0):
    yy = y
    for head, body in items:
        txbox(s, x, yy, w, gap, [f"• {head}", f"   {body}"], size, INK)
        yy += gap + 0.12

# ---------------------------------------------------------------- 构建幻灯片

def build(path):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(W), Inches(H)
    n = 0

    # 1 封面
    s = new_slide(prs)
    txbox(s, 0.8, 1.5, W - 1.6, 1.6, ["操作系统实践 · 开学第一课"], 54, ACCENT, True)
    txbox(s, 0.8, 3.1, W - 1.6, 1.0,
          ["今天两件事:一、这门课怎么进行、怎么评分;二、lab0 开工——先学看地图"],
          26, INK)
    box_text(box(s, 0.8, 4.6, W - 1.6, 1.4),
             ["你将从一棵空树开始,十五周后长出一个真正属于你自己的操作系统"],
             size=22)
    caption(s, "本课程的一切规则公示于《学生须知》,现在讲重点")
    n += 1

    # 2 原理课 vs 实践课
    s = new_slide(prs)
    title_of(s, "这门课和原理课的区别", "你们是架构师, AI 是程序员")
    two_cards(s,
              ["原理课:操作系统是什么",
               "进程、页表、调度算法",
               "考试考概念,实验验证别人的设计"],
              ["本课:操作系统怎么造出来",
               "从空树到能跑的内核,每行代码你做主",
               "规格、测试、诊断、验收——四件事归你;写代码本身不再稀缺"])
    flow4(s, [["思考题", "动手前想清楚规格"],
              ["自写测试", "先定怎么证明对"],
              ["指挥 AI 实现", "你翻译参数与规格"],
              ["验收问答", "当面讲清因果链"]], y=4.35)
    caption(s, "四段式每两周一轮;自写测试是设计保险,官方测试随增量包发放判功能")
    n += 1

    # 3 从零累积构建
    s = new_slide(prs)
    title_of(s, "从零累积构建", "两周为一轮 · 每周一次课(4 学时) · 每轮 2 次课")
    two_cards(s,
              ["第 1 次课(4 学时)",
               "导学:动机/灵魂图/雷区",
               "当堂开工:领基线或合入增量包",
               "Git 首检:逐人核查 init+commit"],
              ["第 2 次课(4 学时)",
               "集中编码 + 教师巡场答疑",
               "验收专场:每人 5–8 分钟",
               "提前完成者课间课余随时来验"])
    caption(s, "第 1 周发基线(按学号个性化,全学期唯一个人化分发);此后每轮发全班同份增量包")
    n += 1

    # 4 评分
    s = new_slide(prs)
    title_of(s, "怎么评分", "功能只定上限, 档位由现场问答决定")
    two_cards(s,
              ["现场验收 —— 占总评 70%",
               "lab1 占 10%, lab2–7 各占 15%",
               "官方测试判功能(逐字节/计数/崩溃表)",
               "三题问答定档:机理/个性化/定位"],
              ["期末考查 —— 占总评 30%",
               "第 14 周闭卷架构设计(20 分)",
               "第 15 周综合实验报告",
               "合计折算 30%"])
    box_text(box(s, 0.7, 5.15, W - 1.4, 1.35),
             ["档位:单核做精即可 A 档 95 分;双核(-smp 2)是自愿的独立加分 +3;各轮完全解耦,绝无连带降档",
              "反面:功能全通但答非所问 → 可低至 40;功能未完成 → 封顶 40。AI 托管跑通 ≠ 分数"],
             size=20)
    n += 1

    # 5 两条游戏规则
    s = new_slide(prs)
    title_of(s, "两条游戏规则")
    two_cards(s,
              ["规则一 · AI 政策",
               "允许用、鼓励用,任何环节,不交对话记录",
               "但验收问的是你的参数与你的代码",
               "一句\"帮我实现\"和一段精确指挥,做出来的是两个系统"],
              ["规则二 · 个性化参数",
               "15 项系统参数按学号派生,全班无人相同",
               "协议格式/缓冲语义/调度策略/淘汰策略…",
               "任何现成通用答案都过不了你的测试——想抄都没得抄"])
    caption(s, "把参数翻译给 AI 就需要懂;懂,才指挥得动")
    n += 1

    # 6 两条红线
    s = new_slide(prs)
    title_of(s, "两条红线")
    two_cards(s,
              ["红线一 · 验收问答没有替身",
               "当场打开代码:\"这一段处理你的哪个参数?\"",
               "\"把它换掉,哪一行会先出问题?\"",
               "10 秒内指到行 = 真作者;翻找慌乱 = 代写"],
              ["红线二 · 验收必须到场",
               "每轮只有一次正式验收 + 一次补验",
               "缺席/E 档:一周内补验,封顶 60 分",
               "强烈建议:第 1 次课开工,尽早提前验收"])
    n += 1

    # 7 当堂装环境
    s = new_slide(prs)
    title_of(s, "现在当堂做:装环境 + 自检", "工具与手册都在课程平台\"环境材料\"目录")
    bullets(s, [
        ("按《学生环境安装指引》安装", "macOS(brew)/Linux/WSL2 三套命令,约 20–40 分钟;macOS 记得做软链接"),
        ("跑自检", "python3 preflight.py —— 全 [ ok ] 即通过(gdb 缺失属正常,课程不用 gdb)"),
        ("自检通过 → 领取你的基线包", "按学号自取 <学号>-kernel.zip,解压后立刻 git init + 首次 commit"),
        ("调试用什么", "读《学生无gdb调试手册》:-d int / -d in_asm / monitor 三板斧,全学期就靠它们"),
    ], y=2.3, gap=0.92, size=21)
    caption(s, "装不上别慌:按指引末尾\"排障三步\",把完整输出发教师;今天装不完的下次课集中处理")
    n += 1

    # 8 lab0 封面页
    s = new_slide(prs)
    txbox(s, 0.8, 1.9, W - 1.6, 1.2, ["lab0 · 阅读与剖析"], 48, ACCENT, True)
    txbox(s, 0.8, 3.2, W - 1.6, 1.0,
          ["不写代码。画出你未来 14 周要亲手构建的操作系统的全景地图。"], 26, INK)
    box_text(box(s, 0.8, 4.5, W - 1.6, 1.5),
             ["通过制,不计分 —— 但未通过者不能进入后续实验",
              "lab1 验收时随机抽验;三张图要自己理解并亲手绘制"])
    caption(s, "阅读对象:课程参考树(xv6-riscv 快照) + xv6 book rev5 两章精读")
    n += 1

    # 9 阅读路线
    s = new_slide(prs)
    title_of(s, "lab0 · 推荐阅读路线", "切忌从 kernel/ 第一个文件硬啃;每读一个核心函数问三个问题")
    bullets(s, [
        ("① user/sh.c 的 main 循环", "先从用户视角看发生了什么"),
        ("② user/usys.pl + kernel/syscall.c", "一个系统调用如何跨越特权级边界"),
        ("③ kernel/trampoline.S + kernel/trap.c", "特权边界上发生了什么(C 为主,汇编看注释)"),
        ("④ kernel/exec.c + vm.c 的 uvmcopy", "echo 进程从何而来"),
        ("⑤ kernel/file.c + console.c", "字符串 \"hi\" 如何输出到外设"),
        ("三问:它被谁调用?可能阻塞吗,谁唤醒?出错如何回滚?", "对照 book《Operating system interfaces》《Traps and system calls》两章"),
    ], y=2.25, gap=0.62, size=20)
    n += 1

    # 10 三张图
    s = new_slide(prs)
    title_of(s, "lab0 · 交付三张图", "全链条追踪 shell 执行 echo hi 的生命周期")
    bullets(s, [
        ("图一 · 全系统控制流图", "read→fork→exec→write→exit 全链路;每个阶段标注:哪个栈 / 哪个特权级 / 是否持锁"),
        ("图二 · 核心数据结构三本账", "进程表 + 页表(标 trampoline/trapframe 边界与权限位) + 文件表,选 exec 刚完毕的截面"),
        ("图三 · 一次时钟中断的微观旅程", "从 scause 进入 usertrap 到 sret 返回,寄存器现场/调度决策全程"),
        ("纸上要有 ≥3 处你自己的批注", "疑问点、边界特例、启发点——这是你的思考痕迹,也是验收谈资"),
    ], y=2.25, gap=0.95, size=21)
    n += 1

    # 11 通过标准与耗时
    s = new_slide(prs)
    title_of(s, "lab0 · 通过标准与耗时", "教师抽验:满足即通过;这是你进入 lab1 的入场券")
    two_cards(s,
              ["通过标准(抽验)",
               "① 控制流全链路闭环",
               "② 关键跳转标注栈归属与特权级",
               "③ 三本账字段完整、引用链清晰",
               "④ trampoline/trapframe 边界与权限位正确",
               "⑤ 时钟中断:现场保护→调度→sret 完整"],
              ["耗时与求助",
               "控制流图(含阅读):6–8 小时",
               "三本账全字段快照:约 +4 小时",
               "第 1 周内完成,快照可与 lab1 并行",
               "超过 10 小时卡住 → 带草稿找教师答疑",
               "遇到卡点是正常的,闷头停滞才是损失"])
    n += 1

    # 12 衔接收尾
    s = new_slide(prs)
    title_of(s, "今天画下的每一条线", "都是你接下来要亲手实现的")
    two_cards(s,
              ["你画的",
               "特权级跨越与中断分发",
               "页表与地址转换树",
               "fork/exit/wait 状态流转",
               "内存复制开销",
               "文件描述符引用链"],
              ["你将实现的",
               "实验 2:陷入、系统调用与控制台",
               "实验 3:SV39 页表与物理内存",
               "实验 4:进程状态机与调度器",
               "实验 5:写时复制 COW",
               "实验 6:缓冲缓存与日志文件系统"])
    caption(s, "下节课:lab1 从按下电源到第一行 C 代码——记得带上已通过自检的环境和你的 git 仓库")
    n += 1

    prs.save(path)
    return n

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    default = os.path.join(os.path.dirname(here), "..", "导学材料",
                           "开学第一课-第0课与lab0.pptx")
    ap_out = os.environ.get("SLIDES_OUT")
    out = ap_out or default
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    n = build(out)
    print(f"生成 {out}: 共 {n} 页(第0课 6 页 + lab0 5 页 + 封面/衔接)")
