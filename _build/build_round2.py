# -*- coding: utf-8 -*-
"""Round 2: append 六、概要设计——数据库设计 to the round-1 report.

Table text is rendered from schema_def.TABLES, the same definition that
generates schema.sql, so the report and the runnable DDL stay in sync.
"""
import os
import sys

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_round1 as R1  # noqa: E402  (helper functions + table builder)
import schema_def as S  # noqa: E402

WS = r"C:\Users\saxtul\Documents\ds harness区\知屿校园"
SRC = os.path.join(WS, "知屿校园-需求分析与建模实验报告-第1轮修订.docx")
OUT = os.path.join(WS, "知屿校园-需求分析与建模实验报告-第2轮修订.docx")

BODY_PT = 10.5


def main():
    doc = Document(SRC)
    R1.DOC = doc

    tpl4 = doc.tables[1]._tbl     # 4 列模板
    tpl5 = doc.tables[2]._tbl     # 5 列模板
    sectPr = doc.element.body.find(qn("w:sectPr"))

    def H1(text):
        return R1.new_para(text, style="Heading 1")

    def H2(text):
        return R1.new_para(text, style="Heading 2", space_before=10.0)

    def P(text, **kw):
        return R1.new_para(text, **kw)

    def CAP(text):
        p = R1.new_para(text, align=WD_ALIGN_PARAGRAPH.CENTER, size=9.0)
        p.paragraph_format.keep_with_next = True    # 表题不与表格分页
        return p

    def fmt_default(d):
        if d is None:
            return None
        if "ON UPDATE" in d:
            return "当前时间，更新时刷新"
        if d.startswith("CURRENT_TIMESTAMP"):
            return "当前时间"
        return d

    def TBL(template, head, rows, widths):
        el = R1.build_table(template, head, rows, widths)
        return el

    def attach(el):
        sectPr.addprevious(el)

    # 先修正第一轮留下的两处，与关系模式对齐 -------------------------------
    dict_tbl = doc.tables[5]
    for row in dict_tbl.rows[1:]:
        if row.cells[1].text.strip() == "消息":
            R1.set_cell_text(
                row.cells[3]._tc,
                "内容、类型（文本/图片/文件）、发送者ID、聊天室ID、发送时间、"
                "状态（正常/屏蔽/删除）、是否被AI处理")
        elif row.cells[1].text.strip() == "AI处理结果":
            R1.set_cell_text(
                row.cells[3]._tc,
                "消息ID 或 帖子ID（二者取一）、摘要、情感倾向、违规判定、置信度、处理时间")

    rel_tbl = doc.tables[6]
    for row in rel_tbl.rows[1:]:
        if row.cells[1].text.strip() == "举报":
            R1.set_cell_text(row.cells[3]._tc, "M:N")
            R1.set_cell_text(
                row.cells[4]._tc,
                "经“举报”实体实现（举报ID、理由、证据、状态、处置人），"
                "一条内容可由多人举报")

    # =====================================================================
    H1("六、概要设计——数据库设计")
    P("本章把第四节的 E-R 模型转换为可直接建库的关系模式，并给出表结构、索引与建库脚本。"
      "设计遵循两条原则：一是字段与《数据字典》逐项对应，二是所有表格由同一份定义生成，"
      "保证报告文字与可执行脚本不会出现偏差。")

    # ---- 6.1 -------------------------------------------------------------
    H2("6.1 设计约定")
    P("为避免三人分头开发时出现同义不同名，先行约定以下规则，全库统一执行。")
    for text in (
        "（1）命名：表名与列名统一用小写英文与下划线（snake_case），中文含义写入列注释（COMMENT），"
        "以便与数据字典逐一对照。",
        "（2）主键：实体表使用 BIGINT UNSIGNED 自增主键；M:N 关系对应的关联表使用两端主键组合作为复合主键，"
        "复合主键天然实现“同一组合只存一行”的约束。",
        "（3）存储：字符集 utf8mb4、排序规则 utf8mb4_0900_ai_ci、存储引擎 InnoDB；"
        "时间统一用 DATETIME，消息表精确到毫秒。",
        "（4）外键：建立物理外键，由数据库保证参照完整性。为避免建表顺序依赖，外键不写进建表语句，"
        "而是在全部表建完后统一用 ALTER TABLE 追加。删除行为按语义分三类：明细与关联表用 "
        "ON DELETE CASCADE（如消息随聊天室删除），内容主体用 RESTRICT（如作者的帖子不随账号删除），"
        "可空引用用 SET NULL（如板块负责人离任）。",
        "（5）状态：一律用 TINYINT 表示，取值写进列注释，不用 ENUM，方便后续扩展取值。",
        "（6）删除：采用逻辑删除，用 status 字段标记（如帖子 2=删除），不物理删除，保留审计线索。",
        "（7）冗余计数：成员数、浏览数、点赞数、收藏数、热度等为冗余列，由明细表聚合维护，"
        "与“五、建模说明”第 6 条一致。",
    ):
        P(text)

    # ---- 6.2 -------------------------------------------------------------
    H2("6.2 E-R 模型到关系模式的转换")
    P("按下列五条规则，把第四节的 10 个实体与 8 个 M:N 联系转换为 18 张表。")
    for text in (
        "（1）实体转表：每个实体转换为一张表，实体的标识属性作为主键，其余属性转换为列。",
        "（2）1:N 联系外键化：在“多”端表中增加指向“一”端的外键列，如 post.board_id、message.room_id。",
        "（3）M:N 联系独立成表：转换为关联表，主键为两端主键的组合，联系自身的属性作为普通列，"
        "如 chat_room_member 承载“加入”联系的加入时间与禁言状态。",
        "（4）1:1 联系合并：消息与帖子各自与“AI处理结果”一对一，采用“目标类型 + 目标ID”的多态方式"
        "合并为一张 ai_result 表，并用唯一索引 (target_type, target_id) 保证一对一。",
        "（5）自嵌套联系自引用：回帖的层次关系用同表的 parent_reply_id 自引用实现，parent 为空表示一级回帖。",
    ):
        P(text)

    CAP("表 8  关系模式总览（18 张表）")
    rows = []
    for i, t in enumerate(S.TABLES, start=1):
        rows.append([str(i), t["name"], t["cn"], t["key"], t["note"]])
    attach(TBL(tpl5, ["序号", "表名", "中文名", "主键", "说明"], rows,
               [600, 1700, 1200, 1700, 1944]))

    # ---- 6.3 -------------------------------------------------------------
    H2("6.3 表结构设计")
    P("核心 8 张表给出完整字段清单（表 9~表 16），“键”列中 PK 表示主键、UK 表示唯一键、"
      "FK 表示外键；其余 10 张表以要点形式汇总于表 17，完整定义见随附的 schema.sql。")

    core_titles = {
        "user": "表 9  用户表 user",
        "chat_room": "表 10  聊天室表 chat_room",
        "chat_room_member": "表 11  聊天室成员表 chat_room_member",
        "message": "表 12  消息表 message",
        "post": "表 13  帖子表 post",
        "reply": "表 14  回帖表 reply",
        "tag": "表 15  标签表 tag",
        "ai_result": "表 16  AI 处理结果表 ai_result",
    }
    for t in S.TABLES:
        if t["name"] not in S.CORE:
            continue
        CAP(core_titles[t["name"]])
        rows = []
        for (name, ftype, nullable, default, kflag, comment) in t["fields"]:
            flag = "非空" if not nullable else "可空"
            short = fmt_default(default)
            if short is not None and short != "NULL":
                flag += "；默认 " + short
            rows.append([name, ftype, flag, (kflag or "—").replace("*", ""), comment])
        attach(TBL(tpl5, ["字段", "类型", "可空/默认", "键", "说明"], rows,
                   [1400, 1700, 2100, 550, 1394]))

    CAP("表 17  其余 10 张表要点")
    rows = []
    for t in S.TABLES:
        if t["name"] in S.CORE:
            continue
        cols = [f[0] for f in t["fields"] if f[4] not in ("PK",)]
        brief = "、".join(cols[:4]) + ("……" if len(cols) > 4 else "")
        rows.append([t["name"], t["cn"], t["key"], brief + "；" + t["note"]])
    attach(TBL(tpl4, ["表名", "中文名", "主键", "主要字段与说明"], rows,
               [1700, 1200, 1800, 2444]))

    # ---- 6.4 -------------------------------------------------------------
    H2("6.4 索引与完整性约束")
    P("索引按“真实查询场景”设计，不做无差别全字段索引。表 18 列出全部二级索引及其用途。")

    CAP("表 18  索引设计")
    idx_rows = [
        ["post", "idx_board_list", "board_id, status, created_at", "板块帖子列表，按时间倒序分页"],
        ["post", "idx_author", "author_id, created_at", "“我的帖子”列表"],
        ["post", "idx_status_time", "status, created_at", "审核台按状态取待审内容"],
        ["message", "idx_room_time", "room_id, created_at", "聊天记录按房间分页拉取"],
        ["message", "idx_ai", "ai_processed, id", "取待 AI 处理的增量队列"],
        ["reply", "idx_post_time", "post_id, created_at", "帖子下的回帖列表"],
        ["chat_room_member", "idx_user", "user_id", "“我加入的聊天室”"],
        ["like_record", "PRIMARY", "user_id, target_type, target_id", "防重复点赞 + 我的点赞"],
        ["favorite", "PRIMARY", "user_id, post_id", "防重复收藏 + 我的收藏"],
        ["behavior_log", "idx_user_time", "user_id, created_at", "用户行为时序，供推荐计算"],
        ["behavior_log", "idx_target", "target_type, target_id", "按内容统计热度"],
        ["ai_result", "uk_message", "message_id", "一条消息只有一条处理结果"],
        ["ai_result", "uk_post", "post_id", "一个帖子只有一条处理结果"],
        ["ai_result", "idx_violation", "violation, confidence", "待人工复核的违规队列"],
        ["tag", "idx_heat", "heat", "热门标签排序"],
    ]
    attach(TBL(tpl4, ["表", "索引名", "字段", "用途"], idx_rows,
               [1350, 1650, 1800, 2344]))

    for text in (
        "约束说明：",
        "（1）实体完整性：每张表都有主键，关联表用组合主键；账号、标签名、板块名等业务唯一属性另建唯一键。",
        "（2）参照完整性：共 30 条物理外键，统一在脚本末尾用 ALTER TABLE 追加；"
        "ON DELETE 按语义分三类——关联与明细表 CASCADE、内容主体 RESTRICT、可空引用 SET NULL。",
        "（3）唯一性约束：like_record 的复合主键保证同一用户对同一目标只点一次；"
        "ai_result 的 uk_message、uk_post 保证一条内容只有一条处理结果，"
        "ck_ai_one_target 保证 message_id 与 post_id 只能有一个非空。",
        "（4）大表处理：behavior_log 写入量最大，按 created_at 做月分区，"
        "并配合热度聚合表避免每次实时统计。",
    ):
        P(text)

    # ---- 6.5 -------------------------------------------------------------
    H2("6.5 与数据字典的差异说明")
    P("关系模式与第三节数据字典并非逐字相同，差异均为设计细化的结果，逐条说明如下。")
    for text in (
        "（1）字段名英文化：数据字典用中文属性名便于阅读，关系模式用英文列名便于建库，"
        "两者含义由列注释（表 9~表 16 的“说明”列）一一对应，不存在新增或丢失属性。",
        "（2）消息表补充 status：原数据字典的“消息”只有内容、类型、发送时间等属性，"
        "无法表达“违规屏蔽”与“作者撤回”，本次在表中增加状态列，并在表 6 同步补入该属性。",
        "（3）AI处理结果的关联方式：消息与帖子各与 AI 结果一对一。若沿用“目标类型 + 目标 ID”的多态写法，"
        "数据库无法建外键；改为 message_id、post_id 两条可空外键，配合 CHECK 约束保证二者互斥，"
        "两个唯一索引保证一对一，既保留单表结构，又获得完整的参照完整性。",
        "（4）多值属性落地：“自动标签”与“兴趣标签”这类多值属性不存为字符串，而是拆成 "
        "ai_result_tag、user_interest_tag 两张关联表，符合第一范式。",
        "（5）二期内容：report（举报）表本期只建库、不实现功能，"
        "与 1.5 节把 UC-13 列为 P2 的处理保持一致。",
    ):
        P(text)

    # ---- 6.6 -------------------------------------------------------------
    H2("6.6 建库脚本")
    P("随附的 schema.sql 由与本章相同的表定义生成，共 18 张表、24 个二级索引、30 条外键，"
      "并含 3 个板块与 6 个标签的初始数据，可直接在 MySQL 8.0 上执行：")
    for text in (
        "（1）建库：脚本首行创建 zhiyu_campus 库并切换，无需手工准备。",
        "（2）建表与加外键：先按 user → … → ai_result_tag 建表，再用 30 条 ALTER TABLE 追加外键，"
        "因此建表顺序不影响结果。",
        "（3）初始化：末尾的 INSERT 语句写入板块与标签字典，供检索与打标使用。",
    ):
        P(text)
    P("执行方式：mysql -u root -p < schema.sql，或在客户端中整体运行该文件。"
      "脚本已包含全部 30 条外键，执行完即为完整结构；若某个环境不支持外键，"
      "只需跳过脚本末尾的 ALTER TABLE 段落即可。")

    doc.save(OUT)
    print("saved:", OUT)


if __name__ == "__main__":
    main()
