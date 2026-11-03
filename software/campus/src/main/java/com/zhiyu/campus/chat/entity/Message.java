package com.zhiyu.campus.chat.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/** 对应表 12 消息表 message。 */
@Data
@TableName("message")
public class Message {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long roomId;

    private Long senderId;

    /** 1 文本 2 图片 3 文件 */
    private Integer msgType;

    private String content;

    /** 0 正常 1 屏蔽 2 删除 */
    private Integer status;

    private Integer aiProcessed;

    private LocalDateTime createdAt;
}
