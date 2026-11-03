package com.zhiyu.campus.blog.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/** 收藏表 favorite，复合主键（用户，帖子）。 */
@Data
@TableName("favorite")
public class Favorite {

    private Long userId;

    private Long postId;

    private LocalDateTime createdAt;
}
