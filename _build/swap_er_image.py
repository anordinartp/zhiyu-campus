# -*- coding: utf-8 -*-
"""Replace the E-R picture inside the round-2 report with the redrawn figure."""
import os

from docx import Document
from docx.shared import Inches

WS = r"C:\Users\saxtul\Documents\ds harness区\知屿校园"
DOCX = os.path.join(WS, "知屿校园-需求分析与建模实验报告-第2轮修订.docx")
PNG = os.path.join(WS, "图6-ER模型图.png")

doc = Document(DOCX)
tpl4 = doc.tables[1]._tbl

# locate the 6th picture (the E-R diagram follows the five DFD figures)
target = None
count = 0
for para in doc.paragraphs:
    if "graphicData" in para._p.xml:
        count += 1
        if count == 6:
            target = para
            break
if target is None:
    raise SystemExit("找不到第 6 张图（E-R 图）")

run = None
for r in target.runs:
    if "graphicData" in r._element.xml:
        run = r
        break
if run is None:
    raise SystemExit("图中没有可替换的绘图 run")

# drop the old drawing, then insert the new one into the same run
for child in list(run._element):
    if child.tag.endswith("}drawing") or child.tag.endswith("}pict"):
        run._element.remove(child)

sec = doc.sections[0]
usable_emu = int(sec.page_width) - int(sec.left_margin) - int(sec.right_margin)
usable_in = usable_emu / 914400.0
run.add_picture(PNG, width=Inches(usable_in))

doc.save(DOCX)
print("replaced E-R image, width = %.2f in" % usable_in)
