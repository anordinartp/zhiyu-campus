package com.zhiyu.campus.blog.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/** 点赞明细 like_record，复合主键保证“同一用户对同一目标只点一次”。 */
@Data
@TableName("like_record")
public class LikeRecord {

    private Long userId;

    /** 1 消息 2 帖子 3 回帖 */
    private Integer targetType;

    private Long targetId;

    private LocalDateTime createdAt;
}
