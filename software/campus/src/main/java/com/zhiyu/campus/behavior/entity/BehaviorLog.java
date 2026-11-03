package com.zhiyu.campus.behavior.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/** 对应表 行为日志 behavior_log。 */
@Data
@TableName("behavior_log")
public class BehaviorLog {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long userId;

    /** 1 浏览 2 发言 3 发帖 4 点赞 5 收藏 6 停留 */
    private Integer action;

    /** 1 聊天室 2 消息 3 帖子 4 回帖 5 标签 */
    private Integer targetType;

    private Long targetId;

    private Integer stayMs;

    private LocalDateTime createdAt;
}
