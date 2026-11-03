# -*- coding: utf-8 -*-
"""Inspect document styling so inserted content matches the existing report."""
import json

from docx import Document
from docx.shared import Pt

SRC = r"C:\Users\saxtul\Downloads\知屿校园-需求分析与建模实验报告(5).docx"
doc = Document(SRC)

print("=== SECTIONS ===")
for s in doc.sections:
    print("page %.1f x %.1f pt, margins L%.1f R%.1f T%.1f B%.1f" % (
        s.page_width.pt, s.page_height.pt, s.left_margin.pt,
        s.right_margin.pt, s.top_margin.pt, s.bottom_margin.pt))

print("\n=== STYLES IN USE ===")
used = {}
for p in doc.paragraphs:
    used.setdefault(p.style.name, 0)
    used[p.style.name] += 1
print(used)

print("\n=== KEY STYLE DEFINITIONS ===")
for name in ("Normal", "Heading 1", "Heading 2", "Normal (Web)",
             "Table Grid", "Caption"):
    try:
        st = doc.styles[name]
    except KeyError:
        print("%-12s MISSING" % name)
        continue
    f = st.font
    pf = st.paragraph_format
    print("%-12s font=%r size=%s bold=%s color=%s" % (
        name, f.name, f.size.pt if f.size else None, f.bold,
        f.color.rgb if f.color and f.color.type is not None else None))
    print("             align=%s space_before=%s space_after=%s line=%s first_indent=%s" % (
        pf.alignment,
        pf.space_before.pt if pf.space_before else None,
        pf.space_after.pt if pf.space_after else None,
        pf.line_spacing, pf.first_line_indent))

print("\n=== TITLE/BODY PARAGRAPH DETAIL ===")
for idx in (0, 1, 2, 3, 4):
    p = doc.paragraphs[idx]
    print("P%03d style=%s align=%s" % (idx, p.style.name, p.paragraph_format.alignment))
    for r in p.runs[:3]:
        print("    run %r font=%r size=%s bold=%s eastasia=%s" % (
            r.text[:24], r.font.name, r.font.size.pt if r.font.size else None,
            r.font.bold,
            r._element.find(
                "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr/"
                "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rFonts"
            ) is not None))

print("\n=== TABLE PROPERTIES ===")
for i, t in enumerate(doc.tables):
    tblPr = t._tbl.tblPr
    style = tblPr.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tblStyle")
    width = tblPr.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tblW")
    borders = tblPr.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tblBorders")
    print("TABLE %d style=%s width=%s borders=%s" % (
        i,
        style.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val") if style is not None else None,
        (width.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}w"),
         width.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type")) if width is not None else None,
        "yes" if borders is not None else "no"))
    # header row formatting
    if t.rows:
        for cell in t.rows[0].cells[:2]:
            for p in cell.paragraphs:
                for r in p.runs[:1]:
                    print("    header run %r font=%r size=%s bold=%s" % (
                        r.text, r.font.name,
                        r.font.size.pt if r.font.size else None, r.font.bold))
    if len(t.rows) > 1:
        for cell in t.rows[1].cells[:1]:
            for p in cell.paragraphs:
                for r in p.runs[:1]:
                    print("    body run %r font=%r size=%s bold=%s" % (
                        r.text, r.font.name,
                        r.font.size.pt if r.font.size else None, r.font.bold))

print("\n=== HEADER/FOOTER ===")
s = doc.sections[0]
print("header text:", repr("".join(p.text for p in s.header.paragraphs)))
print("footer text:", repr("".join(p.text for p in s.footer.paragraphs)))

print("\n=== DOC DEFAULTS ===")
with open(r"C:\Users\saxtul\Documents\ds harness区\知屿校园\_build\styles_dump.txt", "w",
          encoding="utf-8") as fh:
    fh.write(str(doc.styles["Normal"].element.xml)[:4000])
print("styles xml written")
