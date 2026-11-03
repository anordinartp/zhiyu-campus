package com.zhiyu.campus.blog.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/** 对应表 14 回帖表 reply，父回帖为空表示一级回帖。 */
@Data
@TableName("reply")
public class Reply {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long postId;

    private Long authorId;

    private Long parentReplyId;

    private String content;

    private Integer likeCount;

    private Integer status;

    private LocalDateTime createdAt;
}
