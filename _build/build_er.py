# -*- coding: utf-8 -*-
"""重绘图 6：E-R 模型图（A3 横向）。

用 visio_host.ps1 的基本图元拼装：
    实体 = 白底矩形，联系 = 四条线拼成的菱形 + 透明文本框，连线两端标基数。
属性不画进图（10 个实体 + 20 条联系已很密），改由图注指向数据字典。
"""
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PS1 = os.path.join(HERE, "visio_host.ps1")

PAGE_W, PAGE_H = 16.54, 11.69
FONT = "SimSun"
STROKE = 1.0
BLACK = "#000000"
WHITE = "#ffffff"
DW, DH = 0.92, 0.42

# key: (x, y, label, w, h)
ENTITIES = {
    "user":     (2.15, 6.15, "用户",        1.60, 1.25),
    "room":     (4.90, 10.10, "聊天室",      1.55, 0.60),
    "msg":      (9.10, 10.10, "消息",        1.55, 0.60),
    "ai":       (13.55, 10.10, "AI处理结果", 1.95, 0.60),
    "post":     (9.10, 6.15, "帖子",        1.60, 1.25),
    "reply":    (14.05, 7.55, "回帖",        1.55, 0.60),
    "tag":      (9.10, 2.35, "标签",        1.55, 0.60),
    "board":    (12.35, 2.35, "板块",        1.55, 0.60),
    "behavior": (1.95, 2.35, "行为记录",      1.55, 0.60),
    "report":   (5.40, 4.20, "举报（二期）",  1.70, 0.60),
}

# (标签, 起点, 终点, 起点基数, 终点基数, 菱形位置或 None=取中点)
RELS = [
    ("加入", "user", "room", "M", "N", (3.35, 8.25)),
    ("发送", "user", "msg", "1", "N", (5.20, 7.95)),
    ("包含", "room", "msg", "1", "N", (7.00, 10.10)),
    ("发布", "user", "post", "1", "N", (4.30, 6.65)),
    ("点赞", "user", "post", "M", "N", (5.60, 6.15)),
    ("收藏", "user", "post", "M", "N", (6.90, 5.65)),
    ("回复", "user", "reply", "1", "N", (6.60, 7.10)),
    ("含有", "post", "reply", "1", "N", (11.85, 6.55)),
    ("标注", "room", "tag", "M", "N", (7.55, 4.35)),
    ("标注", "post", "tag", "M", "N", (9.10, 4.10)),
    ("聚合", "board", "tag", "M", "N", (10.75, 2.35)),
    ("归属", "board", "post", "1", "N", (11.15, 3.95)),
    ("生成", "msg", "ai", "1", "1", (11.30, 10.10)),
    ("生成", "post", "ai", "1", "1", (11.55, 8.55)),
    ("标注", "ai", "tag", "M", "N", (12.25, 7.30)),
    ("产生", "user", "behavior", "1", "N", (2.05, 4.10)),
    ("提交", "user", "report", "1", "N", (3.50, 5.00)),
    ("指向", "report", "post", "1", "N", (7.20, 5.05)),
]

TITLE = "图 6  知屿校园平台 E-R 模型图"
NOTE = ("说明：矩形为实体，菱形为联系，连线两端的 1、N、M 表示联系的基数；实体属性见第三节数据字典（表 6），"
        "联系与基数的完整清单见第四节表 7。“举报”为二期实体，本期只建模型不实现；"
        "回帖的自嵌套联系以右上角的回路表示。")


def spec_base():
    return {"font": FONT, "sizePt": 10.0, "pageWidth": PAGE_W,
            "pageHeight": PAGE_H, "shapes": [], "links": []}


def rect(spec, x, y, w, h, label, size=11.0):
    spec["shapes"].append({
        "type": "rect", "x": x, "y": y, "w": w, "h": h,
        "strokePt": STROKE, "stroke": BLACK, "fill": WHITE,
        "text": label, "sizePt": size, "align": "center", "style": "bold",
    })


def line(spec, x1, y1, x2, y2):
    spec["shapes"].append({
        "type": "line", "x1": x1, "y1": y1, "x2": x2, "y2": y2,
        "strokePt": STROKE, "stroke": BLACK,
    })


def poly(spec, pts):
    spec["shapes"].append({
        "type": "poly", "points": [[p[0], p[1]] for p in pts],
        "strokePt": STROKE, "stroke": BLACK,
    })


def diamond(spec, cx, cy, label, w=DW, h=DH):
    pts = [(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)]
    for i in range(4):
        line(spec, pts[i][0], pts[i][1], pts[(i + 1) % 4][0], pts[(i + 1) % 4][1])
    spec["shapes"].append({
        "type": "text", "x": cx, "y": cy, "w": w * 0.92, "h": h * 0.85,
        "text": label, "sizePt": 9.5, "align": "center",
        "strokePt": 0, "stroke": BLACK,
    })


def text(spec, x, y, w, h, s, size=9.0, align="center"):
    spec["shapes"].append({
        "type": "text", "x": x, "y": y, "w": w, "h": h, "text": s,
        "sizePt": size, "align": align, "strokePt": 0, "stroke": BLACK,
    })


def rect_edge(cx, cy, w, h, tx, ty):
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    sx = (w / 2) / abs(dx) if dx else float("inf")
    sy = (h / 2) / abs(dy) if dy else float("inf")
    s = min(sx, sy)
    return cx + dx * s, cy + dy * s


def diamond_edge(cx, cy, w, h, tx, ty):
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    k = abs(dx) / (w / 2) + abs(dy) / (h / 2)
    return cx + dx / k, cy + dy / k


def _card_label(spec, x1, y1, x2, y2, t, label, off=0.17):
    """place a cardinality label beside the segment, not on it."""
    x = x1 + (x2 - x1) * t
    y = y1 + (y2 - y1) * t
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / length, dx / length
    if ny < 0:
        nx, ny = -nx, -ny          # 统一放在线的上方
    text(spec, x + nx * off, y + ny * off, 0.34, 0.24, label, size=9.0)


def build():
    spec = spec_base()
    # 标题由 Word 的图题提供，图内不再重复

    for key, (x, y, label, w, h) in ENTITIES.items():
        rect(spec, x, y, w, h, label)

    # ---- 普通联系：实体—菱形—实体 ------------------------------------------
    for (name, a, b, ca, cb, pos) in RELS:
        ax, ay, _, aw, ah = ENTITIES[a]
        bx, by, _, bw, bh = ENTITIES[b]

        if pos is None:
            pos = ((ax + bx) / 2, (ay + by) / 2)
        dx, dy = pos

        ex, ey = rect_edge(ax, ay, aw, ah, dx, dy)
        px, py = diamond_edge(dx, dy, DW, DH, ax, ay)
        line(spec, ex, ey, px, py)

        qx, qy = diamond_edge(dx, dy, DW, DH, bx, by)
        fx, fy = rect_edge(bx, by, bw, bh, dx, dy)
        line(spec, qx, qy, fx, fy)

        diamond(spec, dx, dy, name)

        # 基数标注沿连线法线偏移，避免被线穿过
        t = 0.30
        _card_label(spec, ex, ey, px, py, t, ca)
        _card_label(spec, fx, fy, qx, qy, t, cb)

    # ---- 关注：用户—标签，沿页面底部绕行，避开中部密集区 ---------------------
    ux, uy, _, uw, uh = ENTITIES["user"]
    tx_, ty_, _, tw, th = ENTITIES["tag"]
    route = [(ux - 0.15, uy - uh / 2), (ux - 0.15, 1.15),
             (tx_ - tw / 2, 1.15), (tx_ - tw / 2, ty_ - th / 2)]
    poly(spec, route)
    diamond(spec, 5.30, 1.15, "关注")
    text(spec, ux - 0.55, 5.60, 0.34, 0.24, "M", size=9.0)
    text(spec, tx_ - tw / 2 - 0.45, 2.60, 0.34, 0.24, "N", size=9.0)

    # ---- 回帖自嵌套：右上角画回路 -----------------------------------------
    rx, ry, _, rw, rh = ENTITIES["reply"]
    poly(spec, [(rx, ry + rh / 2), (rx, 8.75)])
    poly(spec, [(rx + 0.46, 8.75), (15.30, 8.75), (15.30, ry + rh / 2 - 0.08),
                (rx + rw / 2 - 0.05, ry + rh / 2 - 0.08)])
    diamond(spec, rx, 8.75, "自嵌套", w=0.86, h=0.40)
    text(spec, rx + 0.25, 8.30, 0.34, 0.24, "1", size=9.0)
    text(spec, rx + 1.05, 8.05, 0.34, 0.24, "N", size=9.0)

    text(spec, 0.55, 0.45, 15.4, 0.55, NOTE, size=8.5, align="left")
    return spec


def main():
    spec = build()
    spec["pageName"] = "图6-ER模型图"
    path = os.path.join(HERE, "spec_er.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(spec, fh, ensure_ascii=False, indent=1)
    vsdx = os.path.join(ROOT, "图6-ER模型图.vsdx")
    png = os.path.join(ROOT, "图6-ER模型图.png")
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", PS1,
           "-Spec", path, "-OutVsdx", vsdx, "-OutPng", png, "-OutPdf", "",
           "-PageName", "图6-ER模型图"]
    res = subprocess.run(cmd, capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    out = (res.stdout or "").strip()
    if out:
        print("  " + out.replace("\n", "\n  "))
    if res.returncode != 0:
        print((res.stderr or "")[-2000:])
        raise SystemExit("ER build failed")
    print("shapes:", len(spec["shapes"]))


if __name__ == "__main__":
    main()
