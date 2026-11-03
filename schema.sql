-- 知屿校园平台 数据库建表脚本 (MySQL 8.0)
-- 由 schema_def.py 生成，字段与报告「六、概要设计」表 9~表 16 一致
-- 约定：utf8mb4 / InnoDB / 主键自增 BIGINT / 物理外键统一在表建完后用 ALTER TABLE 追加

CREATE DATABASE IF NOT EXISTS `zhiyu_campus`
  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE `zhiyu_campus`;

SET NAMES utf8mb4;

-- 用户：账号主体，学生/教师/管理员共用一张表，用 role 区分
CREATE TABLE `user` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `account` VARCHAR(32) NOT NULL COMMENT '学号/工号，登录名',
  `nickname` VARCHAR(32) NOT NULL COMMENT '昵称',
  `password_hash` VARCHAR(100) NOT NULL COMMENT '口令哈希（bcrypt/Argon2）',
  `avatar_url` VARCHAR(255) NULL DEFAULT NULL COMMENT '头像地址',
  `role` TINYINT NOT NULL DEFAULT 0 COMMENT '0学生 1教师 2管理员',
  `points` INT NOT NULL DEFAULT 0 COMMENT '行为积分',
  `status` TINYINT NOT NULL DEFAULT 0 COMMENT '0正常 1禁用',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY uk_account (account)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户';

-- 用户兴趣标签：用户—标签 M:N 的关联表，weight 供个性化推荐使用
CREATE TABLE `user_interest_tag` (
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
  `tag_id` BIGINT UNSIGNED NOT NULL COMMENT '标签ID',
  `weight` DECIMAL(5,4) NOT NULL DEFAULT 0.0000 COMMENT '兴趣权重 0~1',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`user_id`, `tag_id`),
  KEY idx_tag (tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户兴趣标签';

-- 聊天室：标签通过 chat_room_tag 归类，本表不存标签ID
CREATE TABLE `chat_room` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '聊天室ID',
  `name` VARCHAR(60) NOT NULL COMMENT '名称',
  `intro` VARCHAR(500) NULL DEFAULT NULL COMMENT '简介',
  `creator_id` BIGINT UNSIGNED NOT NULL COMMENT '创建者',
  `member_count` INT NOT NULL DEFAULT 0 COMMENT '成员数（冗余）',
  `status` TINYINT NOT NULL DEFAULT 0 COMMENT '0正常 1禁言 2关闭',
  `last_active_at` DATETIME NULL DEFAULT NULL COMMENT '最后活跃时间',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY idx_active (last_active_at),
  KEY idx_creator (creator_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='聊天室';

-- 聊天室成员：“加入”联系的落点，承载身份、加入时间与禁言状态
CREATE TABLE `chat_room_member` (
  `room_id` BIGINT UNSIGNED NOT NULL COMMENT '聊天室ID',
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
  `role` TINYINT NOT NULL DEFAULT 0 COMMENT '0成员 1管理员 2群主',
  `muted` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否禁言',
  `muted_until` DATETIME NULL DEFAULT NULL COMMENT '禁言到期时间',
  `joined_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '加入时间',
  PRIMARY KEY (`room_id`, `user_id`),
  KEY idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='聊天室成员';

-- 消息：本轮新增 status，解决“违规消息无处处置”的模型缺口
CREATE TABLE `message` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '消息ID',
  `room_id` BIGINT UNSIGNED NOT NULL COMMENT '所属聊天室',
  `sender_id` BIGINT UNSIGNED NOT NULL COMMENT '发送者',
  `msg_type` TINYINT NOT NULL DEFAULT 1 COMMENT '1文本 2图片 3文件',
  `content` TEXT NOT NULL COMMENT '消息内容或资源地址',
  `status` TINYINT NOT NULL DEFAULT 0 COMMENT '0正常 1屏蔽 2删除',
  `ai_processed` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已被AI处理（冗余标志）',
  `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '发送时间（毫秒精度）',
  PRIMARY KEY (`id`),
  KEY idx_room_time (room_id, created_at),
  KEY idx_ai (ai_processed, id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='消息';

-- 帖子：列表页与热度排序用的计数为冗余字段，以明细为准重建
CREATE TABLE `post` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '帖子ID',
  `board_id` BIGINT UNSIGNED NOT NULL COMMENT '所属板块',
  `author_id` BIGINT UNSIGNED NOT NULL COMMENT '作者',
  `title` VARCHAR(100) NOT NULL COMMENT '标题',
  `body` MEDIUMTEXT NOT NULL COMMENT '正文',
  `status` TINYINT NOT NULL DEFAULT 0 COMMENT '0正常 1待审 2删除',
  `view_count` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '浏览数（冗余）',
  `like_count` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '点赞数（冗余）',
  `favorite_count` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '收藏数（冗余）',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发布时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY idx_board_list (board_id, status, created_at),
  KEY idx_author (author_id, created_at),
  KEY idx_status_time (status, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='帖子';

-- 回帖：自嵌套通过 parent_reply_id 自引用实现，不再另设联系表
CREATE TABLE `reply` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '回帖ID',
  `post_id` BIGINT UNSIGNED NOT NULL COMMENT '所属帖子',
  `author_id` BIGINT UNSIGNED NOT NULL COMMENT '作者',
  `parent_reply_id` BIGINT UNSIGNED NULL DEFAULT NULL COMMENT '父回帖，NULL 表示一级回帖',
  `content` TEXT NOT NULL COMMENT '内容',
  `like_count` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '点赞数（冗余）',
  `status` TINYINT NOT NULL DEFAULT 0 COMMENT '0正常 1待审 2删除',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '回复时间',
  PRIMARY KEY (`id`),
  KEY idx_post_time (post_id, created_at),
  KEY idx_parent (parent_reply_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='回帖';

-- 标签：聊天室与博客共用；scope 区分适用场景
CREATE TABLE `tag` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '标签ID',
  `name` VARCHAR(30) NOT NULL COMMENT '标签名称',
  `scope` TINYINT NOT NULL DEFAULT 3 COMMENT '1仅聊天室 2仅博客 3通用',
  `creator_id` BIGINT UNSIGNED NOT NULL COMMENT '创建者',
  `heat` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '热度（冗余）',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY uk_name_scope (name, scope),
  KEY idx_heat (heat)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='标签';

-- 板块：博客的主题分区，聚合若干标签
CREATE TABLE `board` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '板块ID',
  `name` VARCHAR(50) NOT NULL COMMENT '板块名称',
  `intro` VARCHAR(500) NULL DEFAULT NULL COMMENT '简介',
  `admin_id` BIGINT UNSIGNED NULL DEFAULT NULL COMMENT '负责的管理员',
  `sort_no` INT NOT NULL DEFAULT 0 COMMENT '排序号',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY uk_board_name (name),
  KEY idx_sort (sort_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='板块';

-- 聊天室标签：聊天室—标签 M:N 的关联表
CREATE TABLE `chat_room_tag` (
  `room_id` BIGINT UNSIGNED NOT NULL COMMENT '聊天室ID',
  `tag_id` BIGINT UNSIGNED NOT NULL COMMENT '标签ID',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '打标时间',
  PRIMARY KEY (`room_id`, `tag_id`),
  KEY idx_tag (tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='聊天室标签';

-- 帖子标签：帖子—标签 M:N 的关联表；AI 自动打的标签也写入此表并标记来源
CREATE TABLE `post_tag` (
  `post_id` BIGINT UNSIGNED NOT NULL COMMENT '帖子ID',
  `tag_id` BIGINT UNSIGNED NOT NULL COMMENT '标签ID',
  `source` TINYINT NOT NULL DEFAULT 1 COMMENT '1作者手动 2AI自动',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '打标时间',
  PRIMARY KEY (`post_id`, `tag_id`),
  KEY idx_tag (tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='帖子标签';

-- 板块标签：板块—标签 M:N 的关联表，体现“板块聚合标签”
CREATE TABLE `board_tag` (
  `board_id` BIGINT UNSIGNED NOT NULL COMMENT '板块ID',
  `tag_id` BIGINT UNSIGNED NOT NULL COMMENT '标签ID',
  `sort_no` INT NOT NULL DEFAULT 0 COMMENT '板块内排序',
  PRIMARY KEY (`board_id`, `tag_id`),
  KEY idx_tag (tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='板块标签';

-- 点赞明细：复合主键天然保证“同一用户对同一目标只点一次”
CREATE TABLE `like_record` (
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '点赞人',
  `target_type` TINYINT NOT NULL COMMENT '1消息 2帖子 3回帖',
  `target_id` BIGINT UNSIGNED NOT NULL COMMENT '目标ID',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '点赞时间',
  PRIMARY KEY (`user_id`, `target_type`, `target_id`),
  KEY idx_target (target_type, target_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='点赞明细';

-- 收藏：对应报告业务描述中的“收藏”，此前数据模型缺失
CREATE TABLE `favorite` (
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '收藏人',
  `post_id` BIGINT UNSIGNED NOT NULL COMMENT '被收藏帖子',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
  PRIMARY KEY (`user_id`, `post_id`),
  KEY idx_post (post_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='收藏';

-- 举报（二期）：二期扩展，本期只建表与字典，功能清单中为 P2
CREATE TABLE `report` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '举报ID',
  `reporter_id` BIGINT UNSIGNED NOT NULL COMMENT '举报人',
  `target_type` TINYINT NOT NULL COMMENT '1消息 2帖子 3回帖',
  `target_id` BIGINT UNSIGNED NOT NULL COMMENT '被举报目标ID',
  `reason` VARCHAR(200) NOT NULL COMMENT '举报理由',
  `evidence_url` VARCHAR(500) NULL DEFAULT NULL COMMENT '证据截图地址',
  `status` TINYINT NOT NULL DEFAULT 0 COMMENT '0待处理 1成立 2不成立',
  `handler_id` BIGINT UNSIGNED NULL DEFAULT NULL COMMENT '处置管理员',
  `handle_result` VARCHAR(200) NULL DEFAULT NULL COMMENT '处置结果',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '举报时间',
  `handled_at` DATETIME NULL DEFAULT NULL COMMENT '处置时间',
  PRIMARY KEY (`id`),
  KEY idx_status_time (status, created_at),
  KEY idx_target (target_type, target_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='举报（二期）';

-- 审核日志：实现阶段补充：报告 5.2 要求“处置必须留痕”，但数据字典未列该表
CREATE TABLE `review_log` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '日志ID',
  `target_type` TINYINT NOT NULL DEFAULT 2 COMMENT '1消息 2帖子 3回帖（本期只用帖子）',
  `target_id` BIGINT UNSIGNED NOT NULL COMMENT '被处置内容ID',
  `operator_id` BIGINT UNSIGNED NOT NULL COMMENT '处置人',
  `action` TINYINT NOT NULL COMMENT '1通过 2删除',
  `remark` VARCHAR(200) NULL DEFAULT NULL COMMENT '处置备注',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '处置时间',
  PRIMARY KEY (`id`),
  KEY idx_target (target_type, target_id),
  KEY idx_operator (operator_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='审核日志';

-- 行为记录：写入量最大，按 created_at 月分区；详单表 + 热度聚合表
CREATE TABLE `behavior_log` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '行为ID',
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '用户',
  `action` TINYINT NOT NULL COMMENT '1浏览 2发言 3发帖 4点赞 5收藏 6停留',
  `target_type` TINYINT NOT NULL COMMENT '1聊天室 2消息 3帖子 4回帖 5标签',
  `target_id` BIGINT UNSIGNED NOT NULL COMMENT '目标ID',
  `stay_ms` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '停留时长（毫秒）',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发生时间',
  PRIMARY KEY (`id`),
  KEY idx_user_time (user_id, created_at),
  KEY idx_target (target_type, target_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='行为记录';

-- AI处理结果：用 message_id / post_id 两条可空外键代替多态关联，二者互斥，可建物理外键
CREATE TABLE `ai_result` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '处理ID',
  `message_id` BIGINT UNSIGNED NULL DEFAULT NULL COMMENT '被处理的消息，与 post_id 二者取一',
  `post_id` BIGINT UNSIGNED NULL DEFAULT NULL COMMENT '被处理的帖子，与 message_id 二者取一',
  `summary` VARCHAR(1000) NULL DEFAULT NULL COMMENT 'AI 摘要',
  `sentiment` TINYINT NULL DEFAULT NULL COMMENT '1正面 0中性 -1负面',
  `violation` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否判定违规',
  `confidence` DECIMAL(4,3) NULL DEFAULT NULL COMMENT '违规判定置信度 0~1',
  `processed_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '处理时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY uk_message (message_id),
  UNIQUE KEY uk_post (post_id),
  CONSTRAINT ck_ai_one_target CHECK ((message_id IS NOT NULL AND post_id IS NULL) OR (message_id IS NULL AND post_id IS NOT NULL)),
  KEY idx_violation (violation, confidence)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='AI处理结果';

-- AI标签结果：承载模型自动打标及其置信度
CREATE TABLE `ai_result_tag` (
  `result_id` BIGINT UNSIGNED NOT NULL COMMENT '处理ID',
  `tag_id` BIGINT UNSIGNED NOT NULL COMMENT '标签ID',
  `confidence` DECIMAL(4,3) NOT NULL DEFAULT 1.000 COMMENT '置信度',
  `source` TINYINT NOT NULL DEFAULT 1 COMMENT '1模型自动 2人工修正',
  PRIMARY KEY (`result_id`, `tag_id`),
  KEY idx_tag (tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='AI标签结果';


-- ============ 外键约束（统一在表建完后追加，与建表顺序无关）============
ALTER TABLE `user_interest_tag` ADD CONSTRAINT `fk_user_interest_tag_user_id` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;
ALTER TABLE `user_interest_tag` ADD CONSTRAINT `fk_user_interest_tag_tag_id` FOREIGN KEY (`tag_id`) REFERENCES `tag` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;
ALTER TABLE `chat_room` ADD CONSTRAINT `fk_chat_room_creator_id` FOREIGN KEY (`creator_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE `chat_room_member` ADD CONSTRAINT `fk_chat_room_member_room_id` FOREIGN KEY (`room_id`) REFERENCES `chat_room` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;
ALTER TABLE `chat_room_member` ADD CONSTRAINT `fk_chat_room_member_user_id` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;
ALTER TABLE `message` ADD CONSTRAINT `fk_message_room_id` FOREIGN KEY (`room_id`) REFERENCES `chat_room` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;
ALTER TABLE `message` ADD CONSTRAINT `fk_message_sender_id` FOREIGN KEY (`sender_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE `post` ADD CONSTRAINT `fk_post_board_id` FOREIGN KEY (`board_id`) REFERENCES `board` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE `post` ADD CONSTRAINT `fk_post_author_id` FOREIGN KEY (`author_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE `reply` ADD CONSTRAINT `fk_reply_post_id` FOREIGN KEY (`post_id`) REFERENCES `post` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;
ALTER TABLE `reply` ADD CONSTRAINT `fk_reply_author_id` FOREIGN KEY (`author_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE `reply` ADD CONSTRAINT `fk_reply_parent_reply_id` FOREIGN KEY (`parent_reply_id`) REFERENCES `reply` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;
ALTER TABLE `tag` ADD CONSTRAINT `fk_tag_creator_id` FOREIGN KEY (`creator_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE `board` ADD CONSTRAINT `fk_board_admin_id` FOREIGN KEY (`admin_id`) REFERENCES `user` (`id`) ON DELETE SET NULL ON UPDATE RESTRICT;
ALTER TABLE `chat_room_tag` ADD CONSTRAINT `fk_chat_room_tag_room_id` FOREIGN KEY (`room_id`) REFERENCES `chat_room` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;
ALTER TABLE `chat_room_tag` ADD CONSTRAINT `fk_chat_room_tag_tag_id` FOREIGN KEY (`tag_id`) REFERENCES `tag` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;
ALTER TABLE `post_tag` ADD CONSTRAINT `fk_post_tag_post_id` FOREIGN KEY (`post_id`) REFERENCES `post` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;
ALTER TABLE `post_tag` ADD CONSTRAINT `fk_post_tag_tag_id` FOREIGN KEY (`tag_id`) REFERENCES `tag` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;
ALTER TABLE `board_tag` ADD CONSTRAINT `fk_board_tag_board_id` FOREIGN KEY (`board_id`) REFERENCES `board` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;
ALTER TABLE `board_tag` ADD CONSTRAINT `fk_board_tag_tag_id` FOREIGN KEY (`tag_id`) REFERENCES `tag` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;
ALTER TABLE `like_record` ADD CONSTRAINT `fk_like_record_user_id` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;
ALTER TABLE `favorite` ADD CONSTRAINT `fk_favorite_user_id` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;
ALTER TABLE `favorite` ADD CONSTRAINT `fk_favorite_post_id` FOREIGN KEY (`post_id`) REFERENCES `post` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;
ALTER TABLE `report` ADD CONSTRAINT `fk_report_reporter_id` FOREIGN KEY (`reporter_id`) REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;
ALTER TABLE `report` ADD CONSTRAINT `fk_report_handler_id` FOREIGN KEY (`handler_id`) REFERENCES `user` (`id`) ON DELETE SET NULL ON UPDATE RESTRICT;
ALTER TABLE `review_log` ADD CONSTRAINT `fk_review_log_operator_id` FOREIGN KEY (`operator_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE `behavior_log` ADD CONSTRAINT `fk_behavior_log_user_id` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;
ALTER TABLE `ai_result` ADD CONSTRAINT `fk_ai_result_message_id` FOREIGN KEY (`message_id`) REFERENCES `message` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;
ALTER TABLE `ai_result` ADD CONSTRAINT `fk_ai_result_post_id` FOREIGN KEY (`post_id`) REFERENCES `post` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;
ALTER TABLE `ai_result_tag` ADD CONSTRAINT `fk_ai_result_tag_result_id` FOREIGN KEY (`result_id`) REFERENCES `ai_result` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;
ALTER TABLE `ai_result_tag` ADD CONSTRAINT `fk_ai_result_tag_tag_id` FOREIGN KEY (`tag_id`) REFERENCES `tag` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;

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
