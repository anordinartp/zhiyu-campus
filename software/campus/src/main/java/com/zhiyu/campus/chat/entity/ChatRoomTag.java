package com.zhiyu.campus.chat.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/** 对应关联表 chat_room_tag，复合主键同样不使用 @TableId。 */
@Data
@TableName("chat_room_tag")
public class ChatRoomTag {

    private Long roomId;

    private Long tagId;

    private LocalDateTime createdAt;
}
