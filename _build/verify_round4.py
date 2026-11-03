# -*- coding: utf-8 -*-
"""Verify round 4: chapter 8 present, figure/table numbering continuous."""
import io
import os
import re

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

WS = r"C:\Users\saxtul\Documents\ds harness区\知屿校园"
DOCX = os.path.join(WS, "知屿校园-需求分析与建模实验报告-第4轮修订.docx")
DUMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "round4_dump.txt")


def iter_blocks(doc):
    for child in doc.element.body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, doc)
        elif child.tag == qn("w:tbl"):
            yield Table(child, doc)


doc = Document(DOCX)
buf = io.StringIO()
ti = 0
for blk in iter_blocks(doc):
    if isinstance(blk, Paragraph):
        txt = blk.text.strip()
        img = "graphicData" in blk._p.xml
        if not txt and not img:
            continue
        buf.write("[%s] %s%s\n" % (blk.style.name, "[IMG] " if img else "", txt))
    else:
        buf.write("--- TABLE %d ---\n" % ti)
        for r in blk.rows:
            buf.write("  | " + " | ".join(c.text.strip() for c in r.cells) + "\n")
        ti += 1
with open(DUMP, "w", encoding="utf-8") as fh:
    fh.write(buf.getvalue())

print("paragraphs=%d tables=%d images=%d" % (
    len(doc.paragraphs), len(doc.tables),
    sum(1 for p in doc.paragraphs if "graphicData" in p._p.xml)))

tcaps = [p.text.strip() for p in doc.paragraphs if p.text.strip().startswith("表 ")]
fcaps = [p.text.strip() for p in doc.paragraphs if p.text.strip().startswith("图 ")]
tn = [int(re.match(r"表\s*(\d+)", c).group(1)) for c in tcaps if re.match(r"表\s*(\d+)", c)]
fn = [int(re.match(r"图\s*(\d+)", c).group(1)) for c in fcaps if re.match(r"图\s*(\d+)", c)]
print("表 captions:", tn, "ok:", tn == list(range(1, len(tn) + 1)))
print("图 captions:", fn, "ok:", fn == list(range(1, len(fn) + 1)))

heads = [(p.style.name, p.text.strip()) for p in doc.paragraphs if p.style.name.startswith("Heading")]
print("headings:", len(heads))
for s, t in heads[-10:]:
    print("   %-10s %s" % (s, t))
