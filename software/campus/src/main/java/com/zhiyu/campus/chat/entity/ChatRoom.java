package com.zhiyu.campus.chat.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/** 对应表 10 聊天室表 chat_room。 */
@Data
@TableName("chat_room")
public class ChatRoom {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String name;

    private String intro;

    private Long creatorId;

    /** 成员数（冗余），见报告 6.1 第 7 条 */
    private Integer memberCount;

    /** 0 正常 1 禁言 2 关闭 */
    private Integer status;

    private LocalDateTime lastActiveAt;

    private LocalDateTime createdAt;
}
