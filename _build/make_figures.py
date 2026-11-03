# -*- coding: utf-8 -*-
"""Build the 用例图 (use case) and 顺序图 (sequence) figures for 知屿校园.

Emits a JSON drawing spec per figure; visio_host.ps1 renders each spec to
.vsdx + .png + .pdf.  Geometry is computed here (0.001" precision) so the
layout can be collision-checked before it is drawn.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PS1 = os.path.join(HERE, "visio_host.ps1")
PY = sys.executable

PAGE_W, PAGE_H = 11.69, 8.27          # A4 landscape
FONT = "SimSun"
BASE_PT = 10.5
STROKE = 1.0                          # points
TITLE_PT = 13
BLACK = "#000000"
WHITE = "#ffffff"
DASH = 2                              # visLinePatternDashed

TITLES = {
    "d1": "图 7  知屿校园平台用例图——聊天室管理",
    "d2": "图 8  知屿校园平台用例图——博客管理",
    "d3": "图 9  知屿校园平台用例图——AI 智能体与检索",
    "d4": "图 10  知屿校园平台顺序图——AI 智能体内容处理",
}


# --------------------------------------------------------------- spec helpers
def new_spec():
    return {"font": FONT, "sizePt": BASE_PT, "pageWidth": PAGE_W,
            "pageHeight": PAGE_H, "shapes": [], "links": []}


def title(spec, text, y=7.86, x=PAGE_W / 2.0):
    spec["shapes"].append({
        "type": "text", "x": x, "y": y, "w": 11.0, "h": 0.30,
        "text": text, "sizePt": TITLE_PT, "style": "bold",
        "align": "center", "strokePt": 0, "stroke": BLACK,
    })


BOUND_TOP = 7.02        # top edge of every system-boundary frame
BOUND_LABEL_Y = 6.86    # the frame's name sits inside its top-left corner


def boundary(spec, x, y, w, h, label, label_y=BOUND_LABEL_Y):
    """System boundary frame; the label sits at the top-left, just above the frame."""
    spec["shapes"].append({
        "type": "rect", "key": "boundary", "x": x, "y": y, "w": w, "h": h,
        "strokePt": STROKE, "stroke": BLACK, "fill": None,
    })
    spec["shapes"].append({
        "type": "text", "anchor": "topleft",
        "x": x - w / 2 + 1.80, "y": label_y, "w": 2.4, "h": 0.30,
        "text": label, "sizePt": 10.5, "align": "left",
        "strokePt": 0, "stroke": BLACK,
    })


def actor(spec, key, x, y, label, scale=0.95):
    spec["shapes"].append({
        "type": "stick", "key": key, "x": x, "y": y, "scale": scale,
        "strokePt": STROKE, "stroke": BLACK, "text": label, "sizePt": BASE_PT,
    })


def usecase(spec, key, x, y, label, w=1.65, h=0.46):
    spec["shapes"].append({
        "type": "ellipse", "key": key, "x": x, "y": y, "w": w, "h": h,
        "strokePt": STROKE, "stroke": BLACK, "fill": WHITE,
        "text": label, "sizePt": BASE_PT, "align": "center",
    })
    return (x, y, w, h)


def assoc(spec, actor_key, uc_key):
    """actor -- use case association (plain straight line)."""
    spec["links"].append({
        "from": {"key": actor_key, "at": "C"},
        "to": {"key": uc_key, "at": "C"},
        "strokePt": STROKE, "stroke": BLACK, "endArrow": 0, "dash": False,
    })


def rel(spec, a_key, b_key, label, dash=True, arrow=True):
    spec["links"].append({
        "from": {"key": a_key, "at": "C"},
        "to": {"key": b_key, "at": "C"},
        "strokePt": STROKE, "stroke": BLACK,
        "endArrow": 1 if arrow else 0, "dash": dash, "text": label,
    })


def note(spec, x, y, w, h, text, anchor="left", opaque=False):
    spec["shapes"].append({
        "type": "text", "x": x, "y": y, "w": w, "h": h, "text": text,
        "sizePt": 9.0, "align": anchor, "strokePt": 0, "stroke": BLACK,
        "fill": WHITE if opaque else None,
    })


def label_rect(spec, cx, cy, text, size_pt=9.5, height=0.20):
    """A one-line label on an opaque background.

    Message labels must not be attached to a Visio line shape: that renders the
    text with a solid black background, so each label gets its own white box.
    """
    width = len(text) * size_pt / 72.0 + 0.14
    spec["shapes"].append({
        "type": "rect", "x": cx, "y": cy, "w": width, "h": height,
        "strokePt": 0, "stroke": BLACK, "fill": WHITE,
        "text": text, "sizePt": size_pt, "align": "center",
    })


def verify_links(spec, ignore=()):
    """Assert no connector passes through any solid shape it is not joining."""
    boxes = {}
    for s in spec["shapes"]:
        if s["type"] in ("rect", "ellipse") and s.get("key"):
            if s["key"] in ignore or s.get("fill") is None:
                continue
            boxes[s["key"]] = (s["x"] - s["w"] / 2, s["x"] + s["w"] / 2,
                               s["y"] - s["h"] / 2, s["y"] + s["h"] / 2)
    centers = {k: ((b[0] + b[1]) / 2, (b[2] + b[3]) / 2) for k, b in boxes.items()}
    problems = []
    for link in spec["links"]:
        f, t = link["from"], link["to"]
        if not (isinstance(f, dict) and "key" in f and isinstance(t, dict) and "key" in t):
            continue
        if f["key"] not in centers or t["key"] not in centers:
            continue
        p = centers[f["key"]]
        q = centers[t["key"]]
        for k, b in boxes.items():
            if k in (f["key"], t["key"]):
                continue
            if _seg_hits_box(p, q, b):
                problems.append("%s->%s crosses %s" % (f["key"], t["key"], k))
    return problems


def _seg_hits_box(p, q, box, pad=0.0):
    """Liang-Barsky segment/rectangle overlap test."""
    x0, x1, y0, y1 = box[0] - pad, box[1] + pad, box[2] - pad, box[3] + pad
    dx, dy = q[0] - p[0], q[1] - p[1]
    t0, t1 = 0.0, 1.0
    for pp, qq in ((-dx, p[0] - x0), (dx, x1 - p[0]), (-dy, p[1] - y0), (dy, y1 - p[1])):
        if pp == 0:
            if qq < 0:
                return False
        else:
            r = qq / pp
            if pp < 0:
                if r > t1:
                    return False
                if r > t0:
                    t0 = r
            else:
                if r < t0:
                    return False
                if r < t1:
                    t1 = r
    return t0 < t1


# ------------------------------------------------------------- 图 7 聊天室管理
def build_d1():
    spec = new_spec()
    title(spec, TITLES["d1"])
    boundary(spec, 5.30, 3.70, 9.20, 6.50, "知屿校园平台")
    actor(spec, "user", 1.15, 5.20, "用户")
    actor(spec, "admin", 1.15, 1.30, "管理员")

    for key, x, y, label in [
        ("c1", 3.25, 6.55, "创建或加入聊天室"),
        ("c2", 3.25, 5.80, "消息收发"),
        ("c3", 3.25, 5.05, "成员与权限管理"),
        ("c4", 3.25, 4.30, "违规内容识别与预警"),
        ("c5", 3.25, 3.55, "聊天室标签分类"),
        ("c6", 3.25, 2.80, "浏览聊天室与消息"),
        ("b1", 5.35, 1.30, "审核与处置违规内容"),
        ("b2", 5.35, 0.55, "聊天室与标签维护"),
    ]:
        usecase(spec, key, x, y, label)

    # link order follows |y - actor.y| so the fan of association lines never crosses
    for a_key, order in (("user", ["c6", "c5", "c4", "c3", "c2", "c1"]),
                         ("admin", ["b1", "b2"])):
        for uc in order:
            assoc(spec, a_key, uc)
    return spec


# --------------------------------------------------------------- 图 8 博客管理
def build_d2():
    spec = new_spec()
    title(spec, TITLES["d2"])
    boundary(spec, 4.45, 3.80, 7.5, 6.44, "知屿校园平台")
    actor(spec, "user", 1.15, 4.15, "用户")

    uc = [
        ("c1", 1.85, 6.55, "发布帖子"),
        ("c2", 1.85, 5.60, "回复帖子"),
        ("c3", 3.75, 6.55, "浏览帖子与板块"),
        ("c4", 3.75, 5.60, "编辑与删除自己的帖子"),
        ("c5", 5.65, 6.55, "点赞与收藏"),
        ("c6", 5.65, 5.60, "板块与标签聚合"),
        ("c7", 5.65, 1.90, "举报与审核处置"),
        ("c8", 6.60, 1.15, "板块与标签维护"),
    ]
    for key, x, y, label in uc:
        usecase(spec, key, x, y, label, w=1.6)

    actor(spec, "admin", 1.15, 2.40, "管理员")
    # kept below the boundary so both lines enter through the right edge without
    # crossing the 回复帖子 / 板块与标签聚合 ellipses
    actor(spec, "llm", 8.85, 1.60, "大模型服务")

    # ascending |y - actor.y| keeps each actor's fan of lines crossing-free
    for key in ("c2", "c1", "c4", "c3", "c6", "c5"):
        assoc(spec, "user", key)
    for key in ("c8", "c7"):
        assoc(spec, "admin", key)
    for key in ("c2", "c1"):
        assoc(spec, "llm", key)
    return spec


# ----------------------------------------------------- 图 9 AI 智能体与检索
def build_d3():
    spec = new_spec()
    title(spec, TITLES["d3"])
    boundary(spec, 4.62, 3.80, 7.84, 6.44, "知屿校园平台")
    actor(spec, "user", 0.85, 4.10, "用户")
    actor(spec, "admin", 0.85, 5.40, "管理员")

    uc = [
        ("c1", 1.55, 2.10, "浏览与检索"),
        ("c2", 3.30, 2.10, "摘要与自动打标"),
        ("c3", 5.05, 2.10, "建立内容索引"),
        ("c4", 1.55, 3.85, "投稿与发布"),
        ("c5", 3.30, 3.85, "违规内容识别与预警"),
        ("c6", 5.05, 3.85, "收藏与点赞"),
        ("c7", 1.55, 6.00, "检索条件解析与排序"),
        ("c8", 3.30, 6.00, "内容采集"),
        ("c9", 5.05, 6.00, "处理结果查询"),
    ]
    for key, x, y, label in uc:
        usecase(spec, key, x, y, label, w=1.65)

    actor(spec, "llm", 8.90, 2.10, "大模型服务")

    for key in ("c1", "c2", "c3", "c6", "c4", "c5", "c8", "c7", "c9"):
        assoc(spec, "user", key)
    assoc(spec, "admin", "c5")
    for key in ("c1", "c2", "c3"):
        assoc(spec, "llm", key)
    return spec


# --------------------------------------------- 图 10 顺序图 AI 智能体内容处理
LIFELINES = [
    ("user", 1.05, "用户"),
    ("ui", 2.63, "前端界面"),
    ("agent", 4.44, "AI 智能体"),
    ("llm", 6.25, "大模型服务"),
    ("search", 8.05, "检索服务"),
    ("db", 9.86, "数据库"),
]
HEAD_TOP = 7.66
HEAD_H = 0.38
MSG_TOP = 6.88
MSG_GAP = 0.44
ACT_W = 0.16


def build_d4():
    spec = new_spec()
    title(spec, TITLES["d4"], y=7.98)
    X = {k: x for k, x, _ in LIFELINES}

    for key, x, label in LIFELINES:
        spec["shapes"].append({
            "type": "rect", "key": "h_" + key, "x": x,
            "y": HEAD_TOP - HEAD_H / 2 + 0.01, "w": 1.26, "h": HEAD_H,
            "strokePt": STROKE, "stroke": BLACK, "fill": WHITE,
            "text": label, "sizePt": 10.0, "align": "center",
        })
    for key, x, _ in LIFELINES:
        spec["shapes"].append({
            "type": "line", "x1": x, "y1": HEAD_TOP - HEAD_H, "x2": x, "y2": 0.72,
            "strokePt": STROKE, "stroke": BLACK, "dash": True,
        })

    rows = []
    y = MSG_TOP
    for spec_row in [
        ("user", "ui", "提交新内容（聊天消息或帖子）", "call"),
        ("ui", "agent", "内容处理请求", "call"),
        ("agent", "db", "读取原始内容", "call"),
        ("db", "agent", "文本与元数据", "ret"),
        ("agent", "agent", "组装提示词，调用内容理解接口", "self"),
        ("agent", "llm", "摘要生成请求", "call"),
        ("agent", "llm", "自动标签请求", "call"),
        ("agent", "llm", "违规内容判定请求", "call"),
        ("llm", "agent", "摘要、标签与违规判定（含置信度）", "ret"),
        ("agent", "db", "写入处理结果（D6 内容索引表）", "call"),
        ("agent", "search", "通知索引更新", "call"),
        ("agent", "ui", "摘要、自动标签与处理状态", "ret"),
        ("ui", "user", "展示摘要与标签", "ret"),
    ]:
        rows.append((y,) + spec_row)
        y -= MSG_GAP

    ys = [r[0] for r in rows]
    cx = {}

    def act(key, y_top, y_bot, offset=0.0):
        """Draw an activation bar; returns its centre x."""
        c = X[key] + offset
        spec["shapes"].append({
            "type": "rect", "x": c, "y": (y_top + y_bot) / 2, "w": ACT_W,
            "h": y_top - y_bot, "strokePt": STROKE, "stroke": BLACK, "fill": WHITE,
        })
        return c

    cx["ui"] = act("ui", ys[0], ys[11])
    cx["agent"] = act("agent", ys[1], ys[11])
    act("db", ys[2], ys[3], offset=0.08)
    act("agent", ys[4], ys[4] - 0.22, offset=0.23)
    act("llm", ys[5], ys[8], offset=0.08)
    act("db", ys[9], ys[9] - 0.20, offset=0.08)
    act("search", ys[10], ys[10] - 0.20, offset=0.08)

    def edge(key, y_row, right_side):
        c = cx.get(key, X[key])
        return c + ACT_W / 2 if right_side else c - ACT_W / 2

    for yy, a, b, label, kind in rows:
        if kind == "self":
            xa = edge("agent", yy, True)
            xb = xa + 0.42
            spec["shapes"].append({
                "type": "poly",
                "points": [[xa, yy], [xb, yy], [xb, yy - 0.22], [xa, yy - 0.22]],
                "strokePt": STROKE, "stroke": BLACK, "endArrow": 1,
            })
            label_rect(spec, xb + 0.10 + (len(label) * 9.5 / 72.0 + 0.14) / 2,
                       yy + 0.13, label)
            continue
        left_to_right = X[b] > X[a]
        x1 = edge(a, yy, left_to_right)
        x2 = edge(b, yy, not left_to_right)
        spec["shapes"].append({
            "type": "line", "x1": x1, "y1": yy, "x2": x2, "y2": yy,
            "strokePt": STROKE, "stroke": BLACK,
            "endArrow": 3 if kind == "call" else 1,
        })
        label_rect(spec, (x1 + x2) / 2, yy + 0.13, label)

    note(spec, 0.62, 1.06, 10.8, 0.78,
         "说明：AI 智能体对聊天消息与帖子的处理为异步过程，与内容发布不互斥；处理结果写入 D6 内容索引表后供检索服务使用；"
         "识别出的违规内容由智能体预警给管理员审核处置。\n"
         "符号：实心箭头＝同步消息调用，空心箭头＝返回消息，自调用箭头＝智能体内部处理步骤。",
         anchor="left", opaque=True)
    return spec


# ------------------------------------------------------------------- driver
def write_spec(spec, name):
    path = os.path.join(HERE, "spec_%s.json" % name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=1)
    return path


def run(name, spec, ignore=()):
    problems = verify_links(spec, ignore=ignore)
    if problems:
        print("  layout warnings:")
        for p in problems:
            print("    -", p)
    vsdx = os.path.join(ROOT, "%s.vsdx" % name)
    png = os.path.join(ROOT, "%s.png" % name)
    pdf = os.path.join(ROOT, "%s.pdf" % name)
    if spec.get("_blackbox_labels"):
        for i, l in enumerate(spec["links"]):
            if l.get("text"):
                print("    ERROR black-box label still on link %d: %r" % (i, l["text"]))
                raise SystemExit("links must not carry text; use label rects")
    # ASCII spec name + plain argv, so no non-ASCII path crosses the process boundary
    tag = name.split("-")[0].replace("图", "fig")
    spec_path = write_spec(spec, tag)
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
           "-File", PS1,
           "-Spec", spec_path,
           "-OutVsdx", vsdx, "-OutPng", png, "-OutPdf", "",
           "-PageName", name]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (res.stdout or "").strip()
    err = (res.stderr or "").strip()
    if out:
        print("  " + out.replace("\n", "\n  "))
    if res.returncode != 0:
        print("--- host stderr ---")
        print(err[-3000:] if err else "(empty)")
        raise SystemExit("build failed for %s" % name)
    if err:
        print("  [host stderr] " + err.replace("\n", "\n  ")[-1500:])
    for path in (vsdx, png):
        if not os.path.isfile(path):
            raise SystemExit("expected output missing: %s" % path)
    make_pdf(png, pdf)
    return spec


LO_NODE = r"D:\harness桌面\resources\runtime\primary-runtime\dependencies\node\bin\node.exe"
LO_CLI = (r"D:\harness桌面\resources\app.asar.unpacked\dsh\node_modules"
          r"\@deepseek-ai\libreoffice-kit\lib\cli.js")


def _png_decode(path):
    """Minimal non-interlaced 8-bit PNG reader.

    Returns (width, height, dpi, colorspace, raw_pixel_bytes).  Written out
    longhand so PDF generation does not depend on an image library.
    """
    import struct
    import zlib

    with open(path, "rb") as fh:
        if fh.read(8) != b"\x89PNG\r\n\x1a\n":
            raise ValueError("not a PNG: %s" % path)
        width = height = depth = ctype = interlace = None
        dpi = 96.0
        idat = bytearray()
        palette = None
        trns = None
        while True:
            raw = fh.read(8)
            if len(raw) < 8:
                break
            length, kind = struct.unpack(">I4s", raw)
            payload = fh.read(length)
            fh.read(4)  # CRC
            if kind == b"IHDR":
                width, height, depth, ctype, _comp, _filt, interlace = struct.unpack(">IIBBBBB", payload)
            elif kind == b"pHYs":
                px, _py, unit = struct.unpack(">IIB", payload[:9])
                if unit == 1 and px:
                    dpi = px * 0.0254
            elif kind == b"PLTE":
                palette = payload
            elif kind == b"tRNS":
                trns = payload
            elif kind == b"IDAT":
                idat += payload
            elif kind == b"IEND":
                break

    if depth != 8:
        raise ValueError("unsupported PNG bit depth %s in %s" % (depth, path))
    if interlace:
        raise ValueError("interlaced PNG not supported: %s" % path)
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(ctype)
    if channels is None:
        raise ValueError("unsupported PNG colour type %s" % ctype)

    data = zlib.decompress(bytes(idat))
    stride = width * channels
    prev = bytearray(stride)
    rows = []
    pos = 0
    for _y in range(height):
        ftype = data[pos]
        pos += 1
        line = bytearray(data[pos:pos + stride])
        pos += stride
        if ftype == 1:
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 0xFF
        elif ftype == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ftype == 3:
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif ftype == 4:
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                up = prev[i]
                upleft = prev[i - channels] if i >= channels else 0
                p = left + up - upleft
                pa, pb, pc = abs(p - left), abs(p - up), abs(p - upleft)
                pred = left if (pa <= pb and pa <= pc) else (up if pb <= pc else upleft)
                line[i] = (line[i] + pred) & 0xFF
        elif ftype != 0:
            raise ValueError("bad PNG filter type %d" % ftype)
        rows.append(bytes(line))
        prev = line

    raw = b"".join(rows)
    if ctype == 0:
        return width, height, dpi, "/DeviceGray", raw
    if ctype == 2:
        return width, height, dpi, "/DeviceRGB", raw
    if ctype == 6:                      # strip alpha
        out = bytearray()
        for i in range(0, len(raw), 4):
            out += raw[i:i + 3]
        return width, height, dpi, "/DeviceRGB", bytes(out)
    if ctype == 4:                      # gray + alpha
        out = bytearray()
        for i in range(0, len(raw), 2):
            out.append(raw[i])
        return width, height, dpi, "/DeviceGray", bytes(out)
    if ctype == 3:                      # palette
        out = bytearray()
        for idx in raw:
            out += palette[idx * 3:idx * 3 + 3]
        return width, height, dpi, "/DeviceRGB", bytes(out)
    raise ValueError("unsupported PNG colour type %s" % ctype)


def make_pdf(png, pdf):
    """Write a single-page PDF sized to the render, embedding it losslessly.

    Visio's Page.Export cannot emit PDF in this environment and the bundled
    LibreOffice kit refuses image input, so the page is assembled directly.
    """
    import zlib
    w_px, h_px, dpi, colorspace, raw = _png_decode(png)
    packed = zlib.compress(raw, 9)

    pw = w_px / dpi * 72.0
    ph = h_px / dpi * 72.0
    content = ("q\n%.4f 0 0 %.4f 0 0 cm\n/Im0 Do\nQ\n" % (pw, ph)).encode()

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %.2f %.2f] "
         b"/Resources << /XObject << /Im0 5 0 R >> >> /Contents 4 0 R >>" % (pw, ph)),
        (b"<< /Length %d >>\nstream\n" % len(content)) + content + b"endstream",
        (b"<< /Type /XObject /Subtype /Image /Width %d /Height %d "
         b"/ColorSpace %s /BitsPerComponent 8 /Filter /FlateDecode /Length %d >>\nstream\n"
         % (w_px, h_px, colorspace.encode(), len(packed))) + packed + b"\nendstream",
    ]

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for i, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += ("%d 0 obj\n" % i).encode() + body + b"\nendobj\n"
    xref_at = len(out)
    out += ("xref\n0 %d\n" % (len(objects) + 1)).encode()
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += ("%010d 00000 n \n" % off).encode()
    out += ("trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
            % (len(objects) + 1, xref_at)).encode()
    with open(pdf, "wb") as fh:
        fh.write(bytes(out))
    print("  PDF: %s (%.1f x %.1f pt, %.0f dpi)" % (os.path.basename(pdf), pw, ph, dpi))
    return True


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else "all"
    if only in ("all", "d1"):
        print("[1/4] 图 7 用例图-聊天室管理")
        run("图7-用例图-聊天室管理", build_d1(), ignore=("boundary",))
    if only in ("all", "d2"):
        print("[2/4] 图 8 用例图-博客管理")
        run("图8-用例图-博客管理", build_d2(), ignore=("boundary",))
    if only in ("all", "d3"):
        print("[3/4] 图 9 用例图-AI智能体与检索")
        run("图9-用例图-AI智能体与检索", build_d3(), ignore=("boundary",))
    if only in ("all", "d4"):
        print("[4/4] 图 10 顺序图-AI智能体内容处理")
        run("图10-顺序图-AI智能体内容处理", build_d4())


if __name__ == "__main__":
    main()
