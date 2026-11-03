# -*- coding: utf-8 -*-
"""详细设计的两张图：领域类图（图 10）与内容状态图（图 11）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_arch import Fig, run, STROKE, BLACK  # noqa: E402


def _ellipse_dot(self, x, y, r=0.075, fill=BLACK):
    self.spec["shapes"].append({
        "type": "ellipse", "x": x, "y": y, "w": r * 2, "h": r * 2,
        "strokePt": STROKE, "stroke": BLACK, "fill": fill,
    })


Fig.ellipse_dot = _ellipse_dot

# ----------------------------------------------------------------- 图 10 类图
CW, CH = 1.80, 1.28
CLASSES = {
    "room": (1.10, 4.30, "ChatRoom 聊天室",
             "-id : Long\n-name : String\n-status : RoomStatus\n-memberCount : int\n"
             "——————\n+join(user) : void\n+sendMessage(msg)"),
    "msg": (3.30, 4.30, "Message 消息",
            "-id : Long\n-content : String\n-status : ContentStatus\n-createdAt : DateTime\n"
            "——————\n+hide(reason)\n+toIndex()"),
    "ai": (5.50, 4.30, "AiResult 处理结果",
           "-summary : String\n-violation : boolean\n-confidence : double\n"
           "——————\n+markViolation()\n+attachTags()"),
    "user": (1.10, 2.50, "User 用户",
             "-id : Long\n-account : String\n-nickname : String\n-role : Role\n"
             "——————\n+login() : Token\n+updateProfile()"),
    "post": (3.30, 2.50, "Post 帖子",
             "-id : Long\n-title : String\n-status : ContentStatus\n-likeCount : int\n"
             "——————\n+publish()\n+addReply()"),
    "reply": (5.50, 2.50, "Reply 回帖",
              "-id : Long\n-content : String\n-parentId : Long\n"
              "——————\n+addReply()"),
    "board": (1.10, 0.70, "Board 板块",
              "-id : Long\n-name : String\n-sortNo : int\n"
              "——————\n+aggregate(tag)"),
    "tag": (3.30, 0.70, "Tag 标签",
            "-id : Long\n-name : String\n-heat : int\n"
            "——————\n+recalcHeat()"),
}

EDGES = [
    ("user", "room", "1", "*", "加入"),
    ("user", "msg", "1", "*", "发送"),
    ("room", "msg", "1", "*", "包含"),
    ("user", "post", "1", "*", "发布"),
    ("post", "reply", "1", "*", "含有"),
    ("board", "post", "1", "*", "归属"),
    ("post", "tag", "*", "*", "标注"),
    ("board", "tag", "*", "*", "聚合"),
    ("msg", "ai", "1", "1", "生成"),
    ("post", "ai", "1", "1", "生成"),
]


def rect_edge(cx, cy, w, h, tx, ty):
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    sx = (w / 2) / abs(dx) if dx else float("inf")
    sy = (h / 2) / abs(dy) if dy else float("inf")
    s = min(sx, sy)
    return cx + dx * s, cy + dy * s


def build_class():
    f = Fig(5.30)
    for key, (x, y, title, body) in CLASSES.items():
        f.rect(x, y, CW, CH, title + "\n" + body, size=7.0)

    for (a, b, ca, cb, label) in EDGES:
        ax, ay = CLASSES[a][0], CLASSES[a][1]
        bx, by = CLASSES[b][0], CLASSES[b][1]
        ex, ey = rect_edge(ax, ay, CW, CH, bx, by)
        fx, fy = rect_edge(bx, by, CW, CH, ax, ay)
        f.line(ex, ey, fx, fy)
        f.text(ex + (fx - ex) * 0.16, ey + (fy - ey) * 0.16 + 0.07,
               0.42, 0.16, ca, size=7.0)
        f.text(fx + (ex - fx) * 0.16, fy + (ey - fy) * 0.16 + 0.07,
               0.42, 0.16, cb, size=7.0)
        f.text(ex + (fx - ex) * 0.40, ey + (fy - ey) * 0.40 - 0.10, 0.62, 0.16, label, size=7.0)

    # 聊天室与标签的多对多关系见第四节 E-R 图与表 7，类图不重复画长连线，避免穿过实体框
    return f.spec


# --------------------------------------------------------------- 图 11 状态图
def build_state():
    f = Fig(3.95)
    f.ellipse_dot(0.62, 2.30)
    f.rect(1.90, 2.30, 1.15, 0.52, "正常", size=9.0, round_=0.22)
    f.rect(3.95, 3.10, 1.20, 0.52, "待审", size=9.0, round_=0.22)
    f.rect(3.95, 1.55, 1.20, 0.52, "已删除", size=9.0, round_=0.22)
    f.rect(5.55, 1.55, 0.62, 0.52, "终态", size=8.0, round_=0.26)

    f.line(0.70, 2.30, 1.325, 2.30, arrow=3)
    f.text(0.98, 2.40, 0.70, 0.18, "① 创建", size=7.0)

    # 正常 → 待审（右上）
    f.line(2.35, 2.52, 3.35, 3.00, arrow=3)
    f.text(2.30, 2.80, 1.45, 0.18, "② 违规判定/敏感词/举报", size=6.5)

    # 待审 → 正常（左下，错开）
    f.line(3.40, 2.95, 2.42, 2.56, arrow=3)
    f.text(2.28, 3.06, 1.30, 0.18, "③ 审核不成立·恢复", size=6.5)

    # 待审 → 已删除（竖线，靠右）
    f.line(4.35, 2.84, 4.35, 1.81, arrow=3)
    f.text(4.45, 2.26, 0.95, 0.18, "④ 审核成立·删除", size=6.5, align="left")

    # 正常 → 已删除（右下斜线，下侧留空放标签）
    f.line(2.45, 2.08, 3.50, 1.68, arrow=3)
    f.text(2.05, 1.72, 1.55, 0.18, "⑤ 作者删除/管理员处置", size=6.5)

    # 已删除 → 正常（左下斜线，更高一点）
    f.line(3.55, 1.80, 2.50, 2.14, arrow=3)
    f.text(2.10, 2.00, 1.55, 0.18, "⑥ 撤销处置（24 h 内）", size=6.5)

    f.line(4.55, 1.55, 5.24, 1.55, arrow=3)
    f.text(4.88, 1.64, 0.40, 0.16, "⑦", size=7.0)
    return f.spec


def main():
    for name, fn in (("图10-领域类图", build_class), ("图11-内容状态图", build_state)):
        print("[%s]" % name)
        spec = fn()
        run(name, spec)
        print("   shapes=%d" % len(spec["shapes"]))


if __name__ == "__main__":
    main()
