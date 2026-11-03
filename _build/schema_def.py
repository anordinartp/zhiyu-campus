# -*- coding: utf-8 -*-
"""Single source of truth for the 知屿校园 relational schema.

The same definition renders both the report tables and schema.sql, so the
document and the runnable DDL can never drift apart.

Field tuple: (列名, 类型, 可空, 默认值, 键标记, 注释)
    键标记: "PK" 主键 / "UK" 唯一 / "FK*" 逻辑外键（不建物理外键） / "" 普通
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))

DB_NAME = "zhiyu_campus"
CHARSET = "utf8mb4"
COLLATE = "utf8mb4_0900_ai_ci"

# --------------------------------------------------------------------------
# 18 张表
# --------------------------------------------------------------------------
TABLES = [
    {
        "name": "user", "cn": "用户", "key": "id",
        "note": "账号主体，学生/教师/管理员共用一张表，用 role 区分",
        "fields": [
            ("id", "BIGINT UNSIGNED", False, None, "PK", "用户ID"),
            ("account", "VARCHAR(32)", False, None, "UK", "学号/工号，登录名"),
            ("nickname", "VARCHAR(32)", False, None, "", "昵称"),
            ("password_hash", "VARCHAR(100)", False, None, "", "口令哈希（bcrypt/Argon2）"),
            ("avatar_url", "VARCHAR(255)", True, "NULL", "", "头像地址"),
            ("role", "TINYINT", False, "0", "", "0学生 1教师 2管理员"),
            ("points", "INT", False, "0", "", "行为积分"),
            ("status", "TINYINT", False, "0", "", "0正常 1禁用"),
            ("created_at", "DATETIME", False, "CURRENT_TIMESTAMP", "", "注册时间"),
            ("updated_at", "DATETIME", False, "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP", "", "更新时间"),
        ],
        "keys": [("UNIQUE KEY uk_account (account)",)],
        "indexes": ["uk_account"],
    },
    {
        "name": "user_interest_tag", "cn": "用户兴趣标签", "key": "user_id, tag_id",
        "note": "用户—标签 M:N 的关联表，weight 供个性化推荐使用",
        "fields": [
            ("user_id", "BIGINT UNSIGNED", False, None, "PK", "用户ID"),
            ("tag_id", "BIGINT UNSIGNED", False, None, "PK", "标签ID"),
            ("weight", "DECIMAL(5,4)", False, "0.0000", "", "兴趣权重 0~1"),
            ("updated_at", "DATETIME", False, "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP", "", "更新时间"),
        ],
        "keys": [],
        "indexes": ["PRIMARY (user_id, tag_id)", "idx_tag (tag_id)"],
    },
    {
        "name": "chat_room", "cn": "聊天室", "key": "id",
        "note": "标签通过 chat_room_tag 归类，本表不存标签ID",
        "fields": [
            ("id", "BIGINT UNSIGNED", False, None, "PK", "聊天室ID"),
            ("name", "VARCHAR(60)", False, None, "", "名称"),
            ("intro", "VARCHAR(500)", True, "NULL", "", "简介"),
            ("creator_id", "BIGINT UNSIGNED", False, None, "FK*", "创建者"),
            ("member_count", "INT", False, "0", "", "成员数（冗余）"),
            ("status", "TINYINT", False, "0", "", "0正常 1禁言 2关闭"),
            ("last_active_at", "DATETIME", True, "NULL", "", "最后活跃时间"),
            ("created_at", "DATETIME", False, "CURRENT_TIMESTAMP", "", "创建时间"),
        ],
        "keys": [],
        "indexes": ["idx_active (last_active_at)", "idx_creator (creator_id)"],
    },
    {
        "name": "chat_room_member", "cn": "聊天室成员", "key": "room_id, user_id",
        "note": "“加入”联系的落点，承载身份、加入时间与禁言状态",
        "fields": [
            ("room_id", "BIGINT UNSIGNED", False, None, "PK", "聊天室ID"),
            ("user_id", "BIGINT UNSIGNED", False, None, "PK", "用户ID"),
            ("role", "TINYINT", False, "0", "", "0成员 1管理员 2群主"),
            ("muted", "TINYINT(1)", False, "0", "", "是否禁言"),
            ("muted_until", "DATETIME", True, "NULL", "", "禁言到期时间"),
            ("joined_at", "DATETIME", False, "CURRENT_TIMESTAMP", "", "加入时间"),
        ],
        "keys": [],
        "indexes": ["PRIMARY (room_id, user_id)", "idx_user (user_id)"],
    },
    {
        "name": "message", "cn": "消息", "key": "id",
        "note": "本轮新增 status，解决“违规消息无处处置”的模型缺口",
        "fields": [
            ("id", "BIGINT UNSIGNED", False, None, "PK", "消息ID"),
            ("room_id", "BIGINT UNSIGNED", False, None, "FK*", "所属聊天室"),
            ("sender_id", "BIGINT UNSIGNED", False, None, "FK*", "发送者"),
            ("msg_type", "TINYINT", False, "1", "", "1文本 2图片 3文件"),
            ("content", "TEXT", False, None, "", "消息内容或资源地址"),
            ("status", "TINYINT", False, "0", "", "0正常 1屏蔽 2删除"),
            ("ai_processed", "TINYINT(1)", False, "0", "", "是否已被AI处理（冗余标志）"),
            ("created_at", "DATETIME(3)", False, "CURRENT_TIMESTAMP(3)", "", "发送时间（毫秒精度）"),
        ],
        "keys": [],
        "indexes": ["idx_room_time (room_id, created_at)", "idx_ai (ai_processed, id)"],
    },
    {
        "name": "post", "cn": "帖子", "key": "id",
        "note": "列表页与热度排序用的计数为冗余字段，以明细为准重建",
        "fields": [
            ("id", "BIGINT UNSIGNED", False, None, "PK", "帖子ID"),
            ("board_id", "BIGINT UNSIGNED", False, None, "FK*", "所属板块"),
            ("author_id", "BIGINT UNSIGNED", False, None, "FK*", "作者"),
            ("title", "VARCHAR(100)", False, None, "", "标题"),
            ("body", "MEDIUMTEXT", False, None, "", "正文"),
            ("status", "TINYINT", False, "0", "", "0正常 1待审 2删除"),
            ("view_count", "INT UNSIGNED", False, "0", "", "浏览数（冗余）"),
            ("like_count", "INT UNSIGNED", False, "0", "", "点赞数（冗余）"),
            ("favorite_count", "INT UNSIGNED", False, "0", "", "收藏数（冗余）"),
            ("created_at", "DATETIME", False, "CURRENT_TIMESTAMP", "", "发布时间"),
            ("updated_at", "DATETIME", False, "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP", "", "更新时间"),
        ],
        "keys": [],
        "indexes": [
            "idx_board_list (board_id, status, created_at)",
            "idx_author (author_id, created_at)",
            "idx_status_time (status, created_at)",
        ],
    },
    {
        "name": "reply", "cn": "回帖", "key": "id",
        "note": "自嵌套通过 parent_reply_id 自引用实现，不再另设联系表",
        "fields": [
            ("id", "BIGINT UNSIGNED", False, None, "PK", "回帖ID"),
            ("post_id", "BIGINT UNSIGNED", False, None, "FK*", "所属帖子"),
            ("author_id", "BIGINT UNSIGNED", False, None, "FK*", "作者"),
            ("parent_reply_id", "BIGINT UNSIGNED", True, "NULL", "FK*", "父回帖，NULL 表示一级回帖"),
            ("content", "TEXT", False, None, "", "内容"),
            ("like_count", "INT UNSIGNED", False, "0", "", "点赞数（冗余）"),
            ("status", "TINYINT", False, "0", "", "0正常 1待审 2删除"),
            ("created_at", "DATETIME", False, "CURRENT_TIMESTAMP", "", "回复时间"),
        ],
        "keys": [],
        "indexes": ["idx_post_time (post_id, created_at)", "idx_parent (parent_reply_id)"],
    },
    {
        "name": "tag", "cn": "标签", "key": "id",
        "note": "聊天室与博客共用；scope 区分适用场景",
        "fields": [
            ("id", "BIGINT UNSIGNED", False, None, "PK", "标签ID"),
            ("name", "VARCHAR(30)", False, None, "UK", "标签名称"),
            ("scope", "TINYINT", False, "3", "UK", "1仅聊天室 2仅博客 3通用"),
            ("creator_id", "BIGINT UNSIGNED", False, None, "FK*", "创建者"),
            ("heat", "INT UNSIGNED", False, "0", "", "热度（冗余）"),
            ("created_at", "DATETIME", False, "CURRENT_TIMESTAMP", "", "创建时间"),
        ],
        "keys": [("UNIQUE KEY uk_name_scope (name, scope)",)],
        "indexes": ["uk_name_scope", "idx_heat (heat)"],
    },
    {
        "name": "board", "cn": "板块", "key": "id",
        "note": "博客的主题分区，聚合若干标签",
        "fields": [
            ("id", "BIGINT UNSIGNED", False, None, "PK", "板块ID"),
            ("name", "VARCHAR(50)", False, None, "UK", "板块名称"),
            ("intro", "VARCHAR(500)", True, "NULL", "", "简介"),
            ("admin_id", "BIGINT UNSIGNED", True, "NULL", "FK*", "负责的管理员"),
            ("sort_no", "INT", False, "0", "", "排序号"),
            ("created_at", "DATETIME", False, "CURRENT_TIMESTAMP", "", "创建时间"),
        ],
        "keys": [("UNIQUE KEY uk_board_name (name)",)],
        "indexes": ["uk_board_name", "idx_sort (sort_no)"],
    },
    {
        "name": "chat_room_tag", "cn": "聊天室标签", "key": "room_id, tag_id",
        "note": "聊天室—标签 M:N 的关联表",
        "fields": [
            ("room_id", "BIGINT UNSIGNED", False, None, "PK", "聊天室ID"),
            ("tag_id", "BIGINT UNSIGNED", False, None, "PK", "标签ID"),
            ("created_at", "DATETIME", False, "CURRENT_TIMESTAMP", "", "打标时间"),
        ],
        "keys": [],
        "indexes": ["PRIMARY (room_id, tag_id)", "idx_tag (tag_id)"],
    },
    {
        "name": "post_tag", "cn": "帖子标签", "key": "post_id, tag_id",
        "note": "帖子—标签 M:N 的关联表；AI 自动打的标签也写入此表并标记来源",
        "fields": [
            ("post_id", "BIGINT UNSIGNED", False, None, "PK", "帖子ID"),
            ("tag_id", "BIGINT UNSIGNED", False, None, "PK", "标签ID"),
            ("source", "TINYINT", False, "1", "", "1作者手动 2AI自动"),
            ("created_at", "DATETIME", False, "CURRENT_TIMESTAMP", "", "打标时间"),
        ],
        "keys": [],
        "indexes": ["PRIMARY (post_id, tag_id)", "idx_tag (tag_id)"],
    },
    {
        "name": "board_tag", "cn": "板块标签", "key": "board_id, tag_id",
        "note": "板块—标签 M:N 的关联表，体现“板块聚合标签”",
        "fields": [
            ("board_id", "BIGINT UNSIGNED", False, None, "PK", "板块ID"),
            ("tag_id", "BIGINT UNSIGNED", False, None, "PK", "标签ID"),
            ("sort_no", "INT", False, "0", "", "板块内排序"),
        ],
        "keys": [],
        "indexes": ["PRIMARY (board_id, tag_id)", "idx_tag (tag_id)"],
    },
    {
        "name": "like_record", "cn": "点赞明细", "key": "user_id, target_type, target_id",
        "note": "复合主键天然保证“同一用户对同一目标只点一次”",
        "fields": [
            ("user_id", "BIGINT UNSIGNED", False, None, "PK", "点赞人"),
            ("target_type", "TINYINT", False, None, "PK", "1消息 2帖子 3回帖"),
            ("target_id", "BIGINT UNSIGNED", False, None, "PK", "目标ID"),
            ("created_at", "DATETIME", False, "CURRENT_TIMESTAMP", "", "点赞时间"),
        ],
        "keys": [],
        "indexes": ["PRIMARY (user_id, target_type, target_id)", "idx_target (target_type, target_id)"],
    },
    {
        "name": "favorite", "cn": "收藏", "key": "user_id, post_id",
        "note": "对应报告业务描述中的“收藏”，此前数据模型缺失",
        "fields": [
            ("user_id", "BIGINT UNSIGNED", False, None, "PK", "收藏人"),
            ("post_id", "BIGINT UNSIGNED", False, None, "PK", "被收藏帖子"),
            ("created_at", "DATETIME", False, "CURRENT_TIMESTAMP", "", "收藏时间"),
        ],
        "keys": [],
        "indexes": ["PRIMARY (user_id, post_id)", "idx_post (post_id)"],
    },
    {
        "name": "report", "cn": "举报（二期）", "key": "id",
        "note": "二期扩展，本期只建表与字典，功能清单中为 P2",
        "fields": [
            ("id", "BIGINT UNSIGNED", False, None, "PK", "举报ID"),
            ("reporter_id", "BIGINT UNSIGNED", False, None, "FK*", "举报人"),
            ("target_type", "TINYINT", False, None, "", "1消息 2帖子 3回帖"),
            ("target_id", "BIGINT UNSIGNED", False, None, "", "被举报目标ID"),
            ("reason", "VARCHAR(200)", False, None, "", "举报理由"),
            ("evidence_url", "VARCHAR(500)", True, "NULL", "", "证据截图地址"),
            ("status", "TINYINT", False, "0", "", "0待处理 1成立 2不成立"),
            ("handler_id", "BIGINT UNSIGNED", True, "NULL", "FK*", "处置管理员"),
            ("handle_result", "VARCHAR(200)", True, "NULL", "", "处置结果"),
            ("created_at", "DATETIME", False, "CURRENT_TIMESTAMP", "", "举报时间"),
            ("handled_at", "DATETIME", True, "NULL", "", "处置时间"),
        ],
        "keys": [],
        "indexes": ["idx_status_time (status, created_at)", "idx_target (target_type, target_id)"],
    },
    {
        "name": "review_log", "cn": "审核日志", "key": "id",
        "note": "实现阶段补充：报告 5.2 要求“处置必须留痕”，但数据字典未列该表",
        "fields": [
            ("id", "BIGINT UNSIGNED", False, None, "PK", "日志ID"),
            ("target_type", "TINYINT", False, "2", "", "1消息 2帖子 3回帖（本期只用帖子）"),
            ("target_id", "BIGINT UNSIGNED", False, None, "", "被处置内容ID"),
            ("operator_id", "BIGINT UNSIGNED", False, None, "FK*", "处置人"),
            ("action", "TINYINT", False, None, "", "1通过 2删除"),
            ("remark", "VARCHAR(200)", True, "NULL", "", "处置备注"),
            ("created_at", "DATETIME", False, "CURRENT_TIMESTAMP", "", "处置时间"),
        ],
        "keys": [],
        "indexes": ["idx_target (target_type, target_id)", "idx_operator (operator_id, created_at)"],
    },    {
        "name": "behavior_log", "cn": "行为记录", "key": "id",
        "note": "写入量最大，按 created_at 月分区；详单表 + 热度聚合表",
        "fields": [
            ("id", "BIGINT UNSIGNED", False, None, "PK", "行为ID"),
            ("user_id", "BIGINT UNSIGNED", False, None, "FK*", "用户"),
            ("action", "TINYINT", False, None, "", "1浏览 2发言 3发帖 4点赞 5收藏 6停留"),
            ("target_type", "TINYINT", False, None, "", "1聊天室 2消息 3帖子 4回帖 5标签"),
            ("target_id", "BIGINT UNSIGNED", False, None, "", "目标ID"),
            ("stay_ms", "INT UNSIGNED", False, "0", "", "停留时长（毫秒）"),
            ("created_at", "DATETIME", False, "CURRENT_TIMESTAMP", "", "发生时间"),
        ],
        "keys": [],
        "indexes": ["idx_user_time (user_id, created_at)", "idx_target (target_type, target_id)"],
    },
    {
        "name": "ai_result", "cn": "AI处理结果", "key": "id",
        "note": "用 message_id / post_id 两条可空外键代替多态关联，二者互斥，可建物理外键",
        "fields": [
            ("id", "BIGINT UNSIGNED", False, None, "PK", "处理ID"),
            ("message_id", "BIGINT UNSIGNED", True, "NULL", "UK", "被处理的消息，与 post_id 二者取一"),
            ("post_id", "BIGINT UNSIGNED", True, "NULL", "UK", "被处理的帖子，与 message_id 二者取一"),
            ("summary", "VARCHAR(1000)", True, "NULL", "", "AI 摘要"),
            ("sentiment", "TINYINT", True, "NULL", "", "1正面 0中性 -1负面"),
            ("violation", "TINYINT(1)", False, "0", "", "是否判定违规"),
            ("confidence", "DECIMAL(4,3)", True, "NULL", "", "违规判定置信度 0~1"),
            ("processed_at", "DATETIME", False, "CURRENT_TIMESTAMP", "", "处理时间"),
        ],
        "keys": [
            ("UNIQUE KEY uk_message (message_id)",),
            ("UNIQUE KEY uk_post (post_id)",),
        ],
        "checks": [
            "CONSTRAINT ck_ai_one_target CHECK ((message_id IS NOT NULL AND post_id IS NULL) "
            "OR (message_id IS NULL AND post_id IS NOT NULL))",
        ],
        "indexes": ["uk_message", "uk_post", "idx_violation (violation, confidence)"],
    },
    {
        "name": "ai_result_tag", "cn": "AI标签结果", "key": "result_id, tag_id",
        "note": "承载模型自动打标及其置信度",
        "fields": [
            ("result_id", "BIGINT UNSIGNED", False, None, "PK", "处理ID"),
            ("tag_id", "BIGINT UNSIGNED", False, None, "PK", "标签ID"),
            ("confidence", "DECIMAL(4,3)", False, "1.000", "", "置信度"),
            ("source", "TINYINT", False, "1", "", "1模型自动 2人工修正"),
        ],
        "keys": [],
        "indexes": ["PRIMARY (result_id, tag_id)", "idx_tag (tag_id)"],
    },
]

CORE = ["user", "chat_room", "chat_room_member", "message", "post", "reply",
        "tag", "ai_result"]

# (子表, 列, 父表, 父列, ON DELETE)
FKS = [
    ("user_interest_tag", "user_id", "user", "id", "CASCADE"),
    ("user_interest_tag", "tag_id", "tag", "id", "CASCADE"),
    ("chat_room", "creator_id", "user", "id", "RESTRICT"),
    ("chat_room_member", "room_id", "chat_room", "id", "CASCADE"),
    ("chat_room_member", "user_id", "user", "id", "CASCADE"),
    ("message", "room_id", "chat_room", "id", "CASCADE"),
    ("message", "sender_id", "user", "id", "RESTRICT"),
    ("post", "board_id", "board", "id", "RESTRICT"),
    ("post", "author_id", "user", "id", "RESTRICT"),
    ("reply", "post_id", "post", "id", "CASCADE"),
    ("reply", "author_id", "user", "id", "RESTRICT"),
    ("reply", "parent_reply_id", "reply", "id", "CASCADE"),
    ("tag", "creator_id", "user", "id", "RESTRICT"),
    ("board", "admin_id", "user", "id", "SET NULL"),
    ("chat_room_tag", "room_id", "chat_room", "id", "CASCADE"),
    ("chat_room_tag", "tag_id", "tag", "id", "CASCADE"),
    ("post_tag", "post_id", "post", "id", "CASCADE"),
    ("post_tag", "tag_id", "tag", "id", "CASCADE"),
    ("board_tag", "board_id", "board", "id", "CASCADE"),
    ("board_tag", "tag_id", "tag", "id", "CASCADE"),
    ("like_record", "user_id", "user", "id", "CASCADE"),
    ("favorite", "user_id", "user", "id", "CASCADE"),
    ("favorite", "post_id", "post", "id", "CASCADE"),
    ("report", "reporter_id", "user", "id", "CASCADE"),
    ("report", "handler_id", "user", "id", "SET NULL"),
    ("behavior_log", "user_id", "user", "id", "CASCADE"),
    ("ai_result", "message_id", "message", "id", "CASCADE"),
    ("ai_result", "post_id", "post", "id", "CASCADE"),
    ("ai_result_tag", "result_id", "ai_result", "id", "CASCADE"),
    ("ai_result_tag", "tag_id", "tag", "id", "CASCADE"),
    ("review_log", "operator_id", "user", "id", "RESTRICT"),
]

SEED = """\
-- 初始管理员账号（口令哈希为占位值，正式部署前替换为真实 bcrypt 哈希）
INSERT INTO `user` (id, account, nickname, password_hash, role)
VALUES (1, 'admin', '管理员', '$2a$10$Xfo7yrbqb41DVDWQux45xeGlN2/kfvQwwk9Vr5kZIqqzetGFVW0ba', 2);

-- 初始板块
INSERT INTO board (name, intro, admin_id, sort_no) VALUES
  ('学习交流', '课程、考试、资料互助', 1, 1),
  ('校园生活', '社团、活动、吃喝玩乐', 1, 2),
  ('跳蚤市场', '二手交易与求购', 1, 3);

-- 初始标签（scope: 1仅聊天室 2仅博客 3通用）
INSERT INTO tag (name, scope, creator_id) VALUES
  ('考研', 3, 1), ('选课', 3, 1), ('实习', 2, 1),
  ('社团', 1, 1), ('二手', 2, 1), ('求助', 3, 1);
"""


def _sql_type(field):
    return field[1]


def render_sql():
    buf = io.StringIO()
    buf.write("-- 知屿校园平台 数据库建表脚本 (MySQL 8.0)\n")
    buf.write("-- 由 schema_def.py 生成，字段与报告「六、概要设计」表 9~表 16 一致\n")
    buf.write("-- 约定：utf8mb4 / InnoDB / 主键自增 BIGINT / 物理外键统一在表建完后用 ALTER TABLE 追加\n\n")
    buf.write("CREATE DATABASE IF NOT EXISTS `%s`\n" % DB_NAME)
    buf.write("  DEFAULT CHARACTER SET %s COLLATE %s;\n" % (CHARSET, COLLATE))
    buf.write("USE `%s`;\n\n" % DB_NAME)
    buf.write("SET NAMES utf8mb4;\n\n")

    for t in TABLES:
        buf.write("-- %s：%s\n" % (t["cn"], t["note"]))
        buf.write("CREATE TABLE `%s` (\n" % t["name"])
        lines = []
        for (name, ftype, nullable, default, kflag, comment) in t["fields"]:
            parts = ["  `%s` %s" % (name, ftype)]
            parts.append("NULL" if nullable else "NOT NULL")
            if name == "id" and kflag == "PK":
                parts.append("AUTO_INCREMENT")   # 6.1 约定：实体表主键自增
            if default is not None:
                if default in ("CURRENT_TIMESTAMP", "CURRENT_TIMESTAMP(3)",
                               "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"):
                    parts.append("DEFAULT %s" % default)
                else:
                    parts.append("DEFAULT %s" % default)
            parts.append("COMMENT '%s'" % comment)
            lines.append(" ".join(parts))
        pk_cols = [f[0] for f in t["fields"] if f[4] == "PK"]
        if pk_cols:
            lines.append("  PRIMARY KEY (%s)" % ", ".join("`%s`" % c for c in pk_cols))
        for grp in t.get("keys", []):
            lines.append("  " + grp[0])
        for chk in t.get("checks", []):
            lines.append("  " + chk)
        for entry in t.get("indexes", []):
            if "(" not in entry or entry.startswith("PRIMARY"):
                continue          # 主键已在上面输出
            name, cols = entry.split(" (", 1)
            cols = cols.rstrip(")")
            if name in ("uk_account", "uk_name_scope", "uk_board_name",
                        "uk_message", "uk_post"):
                continue          # 唯一键已在 keys 中输出
            lines.append("  KEY %s (%s)" % (name, cols))
        buf.write(",\n".join(lines))
        buf.write("\n) ENGINE=InnoDB DEFAULT CHARSET=%s COLLATE=%s COMMENT='%s';\n\n"
                  % (CHARSET, COLLATE, t["cn"]))

    buf.write("\n-- ============ 外键约束（统一在表建完后追加，与建表顺序无关）============\n")
    by_table = {}
    for (tbl, col, ref_tbl, ref_col, on_delete) in FKS:
        by_table.setdefault(tbl, []).append((col, ref_tbl, ref_col, on_delete))
    for tbl in [t["name"] for t in TABLES]:
        if tbl not in by_table:
            continue
        for (col, ref_tbl, ref_col, on_delete) in by_table[tbl]:
            name = "fk_%s_%s" % (tbl, col)
            buf.write(
                "ALTER TABLE `%s` ADD CONSTRAINT `%s` FOREIGN KEY (`%s`) "
                "REFERENCES `%s` (`%s`) ON DELETE %s ON UPDATE RESTRICT;\n"
                % (tbl, name, col, ref_tbl, ref_col, on_delete))
    buf.write("\n")
    buf.write(SEED)
    return buf.getvalue()


def write_sql(path):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render_sql())


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(HERE), "schema.sql")
    write_sql(out)
    print("wrote", out)
    print("tables:", len(TABLES))
