# -*- coding: utf-8 -*-
"""给图 6 单独开一个横向页。

做法：在图片前后各插一个分节符（sectPr 放在段落属性里），中间那一节的
页面方向设为横向、页边距收窄到 0.6 英寸，并据此把图片放大。
"""
import copy
import os

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

WS = r"C:\Users\saxtul\Documents\ds harness区\知屿校园"
DOCX = os.path.join(WS, "知屿校园-需求分析与建模实验报告-第2轮修订.docx")

WP = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
TWIPS_PER_IN = 1440

doc = Document(DOCX)
body = doc.element.body
body_sect = body.find(qn("w:sectPr"))
if body_sect is None:
    raise SystemExit("找不到文档级 sectPr")


def sect_para(sect_pr):
    p = OxmlElement("w:p")
    pPr = OxmlElement("w:pPr")
    pPr.append(sect_pr)
    p.append(pPr)
    return p


def landscape_sect(margin_in=0.6):
    sp = copy.deepcopy(body_sect)
    pgSz = sp.find(qn("w:pgSz"))
    w = int(pgSz.get(qn("w:w")))
    h = int(pgSz.get(qn("w:h")))
    pgSz.set(qn("w:w"), str(max(w, h)))
    pgSz.set(qn("w:h"), str(min(w, h)))
    pgSz.set(qn("w:orient"), "landscape")
    pgMar = sp.find(qn("w:pgMar"))
    m = str(int(margin_in * TWIPS_PER_IN))
    for k in ("w:top", "w:bottom", "w:left", "w:right"):
        pgMar.set(qn(k), m)
    return sp


# 1) 定位"四、E-R 模型"标题、第 6 张图（E-R 图）与它的题注
heading = None
for p in doc.paragraphs:
    if p.style.name == "Heading 1" and p.text.strip().startswith("四、E-R"):
        heading = p
        break
if heading is None:
    raise SystemExit("找不到“四、E-R 模型”标题")

images = [p for p in doc.paragraphs if "graphicData" in p._p.xml]
if len(images) < 6:
    raise SystemExit("图片数量不足")
img_para = images[5]

cap_para = None
nxt = img_para._p.getnext()
while nxt is not None:
    if nxt.tag == qn("w:p"):
        cand = Paragraph(nxt, img_para._parent)
        if cand.text.strip().startswith("图 6"):
            cap_para = cand
        break
    nxt = nxt.getnext()
if cap_para is None:
    raise SystemExit("图 6 的题注不在图片后一段")

# 2) 前分节符放在标题之前：标题、引言、图、题注同处一个横向页，
#    这样前一页不会因为强行分页而留下大片空白
before = sect_para(copy.deepcopy(body_sect))
heading._p.addprevious(before)

# 3) 后分节符（横向、窄边距），结束这一节
after = sect_para(landscape_sect(0.6))
cap_para._p.addnext(after)

# 4) 图片按横向页可用宽度放大（11in - 2*0.6in = 9.8in，留 0.1in 余量）
usable_in = 11.0 - 1.2 - 0.1
cx = int(usable_in * 914400)
cy = int(cx * 1601 / 3238)
for extent in img_para._p.findall(".//" + WP + "extent"):
    extent.set("cx", str(cx))
    extent.set("cy", str(cy))
for ext in img_para._p.findall(".//" + A + "ext"):
    ext.set("cx", str(cx))
    ext.set("cy", str(cy))

doc.save(DOCX)
print("landscape section inserted; image %.2f x %.2f in" % (usable_in, cy / 914400))
