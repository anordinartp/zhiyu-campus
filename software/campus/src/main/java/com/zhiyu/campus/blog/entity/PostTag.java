package com.zhiyu.campus.blog.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/** 帖子—标签关联表 post_tag，复合主键，不使用 @TableId。 */
@Data
@TableName("post_tag")
public class PostTag {

    private Long postId;

    private Long tagId;

    /** 1 作者手动 2 AI 自动 */
    private Integer source;

    private LocalDateTime createdAt;
}
