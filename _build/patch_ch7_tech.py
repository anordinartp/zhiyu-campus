# -*- coding: utf-8 -*-
"""把报告第 7 章的技术选型段落改成与已实现工程一致。"""
import os

from docx import Document

WS = r"C:\Users\saxtul\Documents\ds harness区\知屿校园"
DOCX = os.path.join(WS, "知屿校园-需求分析与建模实验报告-第5轮修订.docx")

NEW = ("技术选型（与已实现的工程保持一致，可按团队熟悉程度替换，不改变本节的分层结论）："
       "前端 Vue 3 + Vite + Element Plus；后端 Spring Boot 4.1.2（Java 21）+ MyBatis-Plus 3.5.18；"
       "数据库 MySQL 8.0；缓存 Redis；检索引擎 Elasticsearch；对象存储 MinIO；"
       "接口文档 Springdoc OpenAPI；并发模型启用 Java 21 虚拟线程。"
       "大模型通过适配层对接，可替换为任一兼容服务。")

doc = Document(DOCX)
hit = 0
for p in doc.paragraphs:
    if p.text.strip().startswith("技术选型建议"):
        if p.runs:
            p.runs[0].text = NEW
            for extra in p.runs[1:]:
                extra._element.getparent().remove(extra._element)
        else:
            p.add_run(NEW)
        hit += 1
if hit == 0:
    raise SystemExit("未找到技术选型段落")
doc.save(DOCX)
print("updated paragraphs:", hit)
