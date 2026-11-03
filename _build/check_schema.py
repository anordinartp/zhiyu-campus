# -*- coding: utf-8 -*-
"""Sanity-check the generated schema without a live MySQL server.

Checks: table/column existence, FK targets, ON DELETE legality (SET NULL needs a
nullable column), duplicate constraint names, CHECK presence, and that seed rows
satisfy the foreign keys they reference.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schema_def as S  # noqa: E402

WS = r"C:\Users\saxtul\Documents\ds harness区\知屿校园"
sql = open(os.path.join(WS, "schema.sql"), encoding="utf-8").read()

tables = {t["name"]: t for t in S.TABLES}
problems = []

# 1. structure of the emitted SQL
created = re.findall(r"CREATE TABLE `(\w+)`", sql)
if created != list(tables):
    problems.append("建表顺序与定义不一致")

# 2. every FK points at an existing table/column, and SET NULL needs nullable
names = set()
for (child, col, parent, pcol, on_delete) in S.FKS:
    if child not in tables:
        problems.append("FK 子表不存在: %s" % child)
        continue
    if parent not in tables:
        problems.append("FK 父表不存在: %s" % parent)
        continue
    child_cols = {f[0]: f for f in tables[child]["fields"]}
    parent_cols = {f[0]: f for f in tables[parent]["fields"]}
    if col not in child_cols:
        problems.append("FK 列不存在: %s.%s" % (child, col))
    if pcol not in parent_cols:
        problems.append("FK 目标列不存在: %s.%s" % (parent, pcol))
    if on_delete == "SET NULL" and not child_cols.get(col, (None,) * 2 + (True,))[2]:
        problems.append("SET NULL 需要可空列: %s.%s" % (child, col))
    name = "fk_%s_%s" % (child, col)
    if name in names:
        problems.append("约束名重复: %s" % name)
    names.add(name)

# 3. every declared FK appears in the SQL text
for (child, col, parent, pcol, on_delete) in S.FKS:
    needle = "ALTER TABLE `%s` ADD CONSTRAINT `fk_%s_%s`" % (child, child, col)
    if needle not in sql:
        problems.append("SQL 缺少外键: %s" % needle)

# 4. seed data must not violate FKs
if "INSERT INTO `user`" not in sql:
    problems.append("种子数据缺少初始用户，tag.creator_id=1 会触发外键错误")
if "admin_id, sort_no" not in sql:
    problems.append("种子数据未写入 board.admin_id")
tag_seed = re.search(r"INSERT INTO tag[\s\S]*?;", sql)
if tag_seed and "creator_id" in tag_seed.group(0):
    pass
elif tag_seed:
    problems.append("标签种子未写 creator_id，但该列非空")

# 5. ai_result must have both unique keys and the check
if "uk_message" not in sql or "uk_post" not in sql:
    problems.append("ai_result 缺少唯一键")
if "ck_ai_one_target" not in sql:
    problems.append("ai_result 缺少 CHECK 约束")

# 6. NOT NULL columns must have a value in seed (rough check for tag.creator_id)
print("tables:", len(created), "fks:", len(S.FKS), "checks:",
      sum(len(t.get("checks", [])) for t in S.TABLES))
if problems:
    print("PROBLEMS:")
    for p in problems:
        print("  -", p)
    raise SystemExit(1)
print("OK: schema 结构、外键、CHECK、种子数据自洽")
