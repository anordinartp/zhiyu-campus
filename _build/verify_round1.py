# -*- coding: utf-8 -*-
"""Verify the round-1 revision: structure, captions and table integrity."""
import io
import os

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

OUT = os.path.join(r"C:\Users\saxtul\Documents\ds harness区\知屿校园",
                   "知屿校园-需求分析与建模实验报告-第1轮修订.docx")
DUMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "round1_dump.txt")


def iter_blocks(doc):
    for child in doc.element.body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, doc)
        elif child.tag == qn("w:tbl"):
            yield Table(child, doc)


doc = Document(OUT)
buf = io.StringIO()
buf.write("paragraphs=%d tables=%d\n" %
          (len(doc.paragraphs), len(doc.tables)))
buf.write("=" * 76 + "\n")

ti = 0
for blk in iter_blocks(doc):
    if isinstance(blk, Paragraph):
        txt = blk.text.strip()
        img = "graphicData" in blk._p.xml
        if not txt and not img:
            continue
        buf.write("[%s] %s%s\n" % (blk.style.name, "[IMG] " if img else "", txt))
    else:
        buf.write("--- TABLE %d (%dx%d) ---\n" % (ti, len(blk.rows), len(blk.columns)))
        for r in blk.rows:
            cells = [c.text.strip().replace("\n", " / ") for c in r.cells]
            buf.write("  | " + " | ".join(cells) + "\n")
        buf.write("--- END TABLE %d ---\n" % ti)
        ti += 1

with open(DUMP, "w", encoding="utf-8") as fh:
    fh.write(buf.getvalue())

# ---- assertions ----------------------------------------------------------
texts = [p.text for p in doc.paragraphs]
caps = [t for t in texts if t.strip().startswith("表 ")]
print("table captions (%d):" % len(caps))
for c in caps:
    print("   ", c)
print("tables:", len(doc.tables), "->", [(len(t.rows), len(t.columns)) for t in doc.tables])
print("headings:")
for p in doc.paragraphs:
    if p.style.name.startswith("Heading"):
        print("   %-10s %s" % (p.style.name, p.text.strip()))
print("dump chars:", len(buf.getvalue()))
