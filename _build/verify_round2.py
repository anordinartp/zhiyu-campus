# -*- coding: utf-8 -*-
"""Verify round 2: chapter 6 present, tables/captions consistent, SQL sane."""
import io
import os
import re

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

WS = r"C:\Users\saxtul\Documents\ds harness区\知屿校园"
DOCX = os.path.join(WS, "知屿校园-需求分析与建模实验报告-第2轮修订.docx")
SQL = os.path.join(WS, "schema.sql")
DUMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "round2_dump.txt")


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
        buf.write("--- TABLE %d (%dx%d) ---\n" % (ti, len(blk.rows), len(blk.columns)))
        for r in blk.rows[-0:]:
            pass
        for r in blk.rows:
            cells = [c.text.strip() for c in r.cells]
            buf.write("  | " + " | ".join(cells) + "\n")
        buf.write("--- END TABLE %d ---\n" % ti)
        ti += 1
with open(DUMP, "w", encoding="utf-8") as fh:
    fh.write(buf.getvalue())

print("paragraphs=%d tables=%d" % (len(doc.paragraphs), len(doc.tables)))
print("table sizes:", [(len(t.rows), len(t.columns)) for t in doc.tables])

caps = [p.text.strip() for p in doc.paragraphs if p.text.strip().startswith("表 ")]
print("captions (%d): %s" % (len(caps), " / ".join(caps)))
nums = []
for c in caps:
    m = re.match(r"表\s*(\d+)", c)
    if m:
        nums.append(int(m.group(1)))
print("caption numbers:", nums, "sequential:", nums == list(range(1, len(nums) + 1)))

heads = [(p.style.name, p.text.strip()) for p in doc.paragraphs
         if p.style.name.startswith("Heading")]
print("headings:", len(heads))
for s, t in heads:
    print("   %-10s %s" % (s, t))

sql = open(SQL, encoding="utf-8").read()
print("\nSQL: CREATE TABLE =", len(re.findall(r"^CREATE TABLE", sql, re.M)))
print("SQL: KEY lines =", len(re.findall(r"^\s+KEY ", sql, re.M)))
print("SQL: tables =", re.findall(r"CREATE TABLE `(\w+)`", sql))
print("SQL ends with:", repr(sql.strip()[-40:]))
