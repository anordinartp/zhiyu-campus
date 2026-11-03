# -*- coding: utf-8 -*-
"""生成第三轮的三张图：体系结构图、部署图、功能结构图。

页面宽度统一取 6.6 英寸，与报告版心一致，插入 Word 后按 1:1 显示，不再缩小。
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PS1 = os.path.join(HERE, "visio_host.ps1")

FONT = "SimSun"
STROKE = 1.0
BLACK = "#000000"
WHITE = "#ffffff"
GRAY = "#f2f2f2"

PAGE_W = 6.6


class Fig(object):
    def __init__(self, height):
        self.spec = {"font": FONT, "sizePt": 9.0, "pageWidth": PAGE_W,
                     "pageHeight": height, "shapes": [], "links": []}
        # 整页白底：把内容包围盒固定成整页，导出时不会裁到贴边
        self.spec["shapes"].append({
            "type": "rect", "x": PAGE_W / 2, "y": height / 2, "w": PAGE_W,
            "h": height, "strokePt": 0, "stroke": BLACK, "fill": WHITE,
            "noline": True,
        })

    def rect(self, x, y, w, h, text="", size=9.0, bold=False, fill=WHITE,
             dash=False, round_=None, align="center"):
        s = {"type": "rect", "x": x, "y": y, "w": w, "h": h, "strokePt": STROKE,
             "stroke": BLACK, "fill": fill, "text": text, "sizePt": size,
             "align": align}
        if bold:
            s["style"] = "bold"
        if dash:
            s["dash"] = 1
        if round_ is not None:
            s["round"] = round_
        self.spec["shapes"].append(s)

    def text(self, x, y, w, h, text, size=9.0, align="center", bold=False):
        s = {"type": "text", "x": x, "y": y, "w": w, "h": h, "text": text,
             "sizePt": size, "align": align, "strokePt": 0, "stroke": BLACK}
        if bold:
            s["style"] = "bold"
        self.spec["shapes"].append(s)

    def line(self, x1, y1, x2, y2, dash=False, arrow=0):
        s = {"type": "line", "x1": x1, "y1": y1, "x2": x2, "y2": y2,
             "strokePt": STROKE, "stroke": BLACK}
        if dash:
            s["dash"] = 1
        if arrow:
            s["endArrow"] = arrow
        self.spec["shapes"].append(s)

    def poly(self, pts, dash=False, arrow=0):
        s = {"type": "poly", "points": [[p[0], p[1]] for p in pts],
             "strokePt": STROKE, "stroke": BLACK}
        if dash:
            s["dash"] = 1
        if arrow:
            s["endArrow"] = arrow
        self.spec["shapes"].append(s)

    def band(self, y, h, label, x0=0.15, x1=PAGE_W - 0.15):
        """分层图的一条带：左侧写层名，整条用浅灰底。"""
        w = x1 - x0
        self.rect((x0 + x1) / 2, y, w, h, "", fill=GRAY, round_=0.08)
        self.text(x0 + 0.58, y, 1.05, 0.3, label, size=9.0, bold=True)


# --------------------------------------------------------------- 图 7 体系结构
def build_arch():
    f = Fig(4.55)
    right = 5.45                      # 留出右侧给“外部服务”竖条
    layers = [
        ("接入层", 4.02, 0.62, ["Web 前端", "管理后台", "移动端"]),
        ("网关层", 3.24, 0.56, ["API 网关：JWT 鉴权 · 限流 · 路由 · 日志"]),
        ("业务层", 2.28, 0.76,
         ["用户与权限", "聊天室", "博客", "标签与板块", "检索", "审核"]),
        ("智能层", 1.50, 0.56, ["AI 智能体（摘要 / 打标 / 违规识别）", "任务队列（重试 · 降级）"]),
        ("数据层", 0.66, 0.56,
         ["MySQL", "Redis 缓存", "检索引擎", "对象存储"]),
    ]
    for label, y, h, items in layers:
        f.band(y, h, label, x1=right)
        n = len(items)
        usable_l, usable_r = 1.30, right - 0.10
        span = (usable_r - usable_l) / n
        for i, it in enumerate(items):
            cx = usable_l + span * (i + 0.5)
            f.rect(cx, y, span - 0.08, h - 0.16, it, size=8.0)

    # 层间双向箭头
    for y_top, y_bot in ((3.71, 3.52), (2.96, 2.66), (1.90, 1.78), (1.22, 1.20)):
        f.line((0.15 + right) / 2, y_top, (0.15 + right) / 2, y_bot, arrow=3)

    # 外部大模型服务：右侧竖条，虚线表示在系统边界之外
    f.rect(6.02, 1.50, 1.02, 0.56, "大模型服务\nAPI（外部）", size=7.5, dash=True)
    f.line(right, 1.50, 5.51, 1.50, dash=True, arrow=3)
    return f.spec


# ----------------------------------------------------------------- 图 8 部署
def build_deploy():
    f = Fig(4.30)
    # 左列：客户端 → 网关；中列：应用 → 智能体 → 大模型；右列：数据设施
    f.rect(0.95, 3.45, 1.00, 0.50, "浏览器 /\n移动端", size=8.0)
    f.rect(2.32, 3.45, 1.05, 0.50, "Nginx 网关", size=8.0)
    f.rect(3.78, 3.25, 1.25, 0.90, "应用服务器\n（2 实例）", size=8.0)
    f.rect(3.78, 2.10, 1.25, 0.58, "AI 智能体服务\n（队列 + 重试）", size=8.0)
    f.rect(3.78, 0.85, 1.25, 0.50, "大模型服务 API", size=8.0, dash=True)

    f.rect(5.52, 3.45, 1.00, 0.50, "MySQL\n（主 + 从）", size=8.0)
    f.rect(5.52, 2.80, 1.00, 0.45, "Redis 缓存", size=8.0)
    f.rect(5.52, 2.15, 1.00, 0.45, "检索引擎", size=8.0)
    f.rect(5.52, 1.50, 1.00, 0.45, "对象存储", size=8.0)

    f.line(1.45, 3.70, 1.795, 3.70, arrow=3)
    f.text(1.62, 3.78, 0.8, 0.18, "HTTPS", size=7.0)
    f.line(2.845, 3.70, 3.155, 3.70, arrow=3)
    f.text(3.00, 3.78, 0.8, 0.18, "HTTP", size=7.0)

    f.line(3.78, 2.90, 3.78, 2.39, arrow=3)
    f.text(3.90, 2.58, 0.8, 0.18, "HTTP", size=7.0, align="left")
    f.line(3.78, 1.81, 3.78, 1.35, arrow=3)
    f.text(3.90, 1.52, 0.8, 0.18, "HTTPS", size=7.0, align="left")

    # 应用服务器 → 四个数据设施，从右侧扇出
    targets = [(3.72, "JDBC", 0.10), (2.98, "RESP", -0.02),
               (2.32, "HTTP", -0.02), (1.68, "S3/OSS", -0.02)]
    for y_to, label, dy in targets:
        f.line(4.405, 3.55, 5.02, y_to, arrow=3)
        f.text(4.72, (3.55 + y_to) / 2 + 0.06 + dy, 0.62, 0.18, label, size=7.0)
    return f.spec


# ------------------------------------------------------------- 图 9 功能结构
def build_modules():
    f = Fig(5.25)
    modules = [
        ("M1  用户与权限", "注册登录 · 鉴权与令牌 · 个人资料 · 兴趣标签"),
        ("M2  聊天室", "创建/加入 · 消息收发 · 成员与权限 · 标签分类"),
        ("M3  博客", "发帖 · 回帖与互动 · 板块标签聚合 · 内容浏览"),
        ("M4  标签与板块", "标签维护 · 板块维护 · 聚合关系配置"),
        ("M5  智能体", "内容采集 · 摘要与打标 · 违规识别 · 预警推送"),
        ("M6  检索", "查询解析 · 索引检索 · 热度与偏好排序"),
        ("M7  行为与推荐", "行为采集 · 热度计算 · 个性化推荐"),
        ("M8  审核与运营", "审核台 · 举报处理（二期） · 日志与监控"),
    ]
    top, step = 4.85, 0.60
    ys = [top - i * step for i in range(len(modules))]
    centre = (ys[0] + ys[-1]) / 2

    f.rect(0.95, centre, 1.30, 0.52, "知屿校园平台", size=9.0, bold=True)
    bus = 1.72
    f.line(1.60, centre, bus, centre)
    f.line(bus, ys[0], bus, ys[-1])

    for (name, funcs), y in zip(modules, ys):
        f.rect(2.75, y, 1.80, 0.46, name, size=8.5, bold=True)
        f.line(bus, y, 2.75 - 0.90, y)
        f.line(2.75 + 0.90, y, 3.72, y)
        f.text(5.20, y, 2.85, 0.46, funcs, size=8.0, align="left")
    return f.spec


FIGS = [
    ("图7-体系结构图", build_arch),
    ("图8-部署图", build_deploy),
    ("图9-功能结构图", build_modules),
]


def run(name, spec):
    spec["pageName"] = name
    path = os.path.join(HERE, "spec_%s.json" % name.split("-")[0].replace("图", "fig"))
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(spec, fh, ensure_ascii=False, indent=1)
    vsdx = os.path.join(ROOT, "%s.vsdx" % name)
    png = os.path.join(ROOT, "%s.png" % name)
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", PS1,
           "-Spec", path, "-OutVsdx", vsdx, "-OutPng", png, "-OutPdf", "",
           "-PageName", name]
    res = subprocess.run(cmd, capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    out = (res.stdout or "").strip()
    if out:
        print("  " + out.replace("\n", "\n  "))
    if res.returncode != 0:
        print((res.stderr or "")[-1500:])
        raise SystemExit("build failed: %s" % name)
    return png


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else "all"
    made = []
    for name, fn in FIGS:
        if only not in ("all", name.split("-")[0].replace("图", "fig")):
            continue
        print("[%s]" % name)
        spec = fn()
        made.append((name, run(name, spec), len(spec["shapes"])))
    for name, png, n in made:
        print("%-16s shapes=%d -> %s" % (name, n, os.path.basename(png)))


if __name__ == "__main__":
    main()
