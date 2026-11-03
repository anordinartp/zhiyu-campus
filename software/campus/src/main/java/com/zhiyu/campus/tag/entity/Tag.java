package com.zhiyu.campus.tag.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/** 对应表 15 标签表 tag。 */
@Data
@TableName("tag")
public class Tag {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String name;

    /** 1 仅聊天室 2 仅博客 3 通用 */
    private Integer scope;

    private Long creatorId;

    private Integer heat;

    private LocalDateTime createdAt;
}
