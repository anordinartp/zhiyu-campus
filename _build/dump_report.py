# -*- coding: utf-8 -*-
"""Dump the report structure (headings, images, tables) for review."""
import io
import os

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

SRC = r"C:\Users\saxtul\Downloads\知屿校园-需求分析与建模实验报告(5).docx"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report_dump.txt")


def iter_blocks(doc):
    for child in doc.element.body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, doc)
        elif child.tag == qn("w:tbl"):
            yield Table(child, doc)


doc = Document(SRC)
buf = io.StringIO()
buf.write("paragraphs=%d tables=%d sections=%d\n" %
          (len(doc.paragraphs), len(doc.tables), len(doc.sections)))
sec = doc.sections[0]
buf.write("page %.1f x %.1f pt\n" % (sec.page_width.pt, sec.page_height.pt))
buf.write("=" * 76 + "\n")

ti = 0
pi = 0
for blk in iter_blocks(doc):
    if isinstance(blk, Paragraph):
        txt = blk.text.strip()
        has_img = "graphicData" in blk._p.xml
        if not txt and not has_img:
            pi += 1
            continue
        tag = "[IMG] " if has_img else ""
        buf.write("P%03d [%s] %s%s\n" % (pi, blk.style.name, tag, txt))
        pi += 1
    else:
        buf.write("--- TABLE %d (%dx%d) ---\n" % (ti, len(blk.rows), len(blk.columns)))
        for r in blk.rows:
            cells = [c.text.strip().replace("\n", " / ") for c in r.cells]
            buf.write("  | " + " | ".join(cells) + "\n")
        buf.write("--- END TABLE %d ---\n" % ti)
        ti += 1

with open(OUT, "w", encoding="utf-8") as fh:
    fh.write(buf.getvalue())
print("wrote", OUT, len(buf.getvalue()), "chars")
