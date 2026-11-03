package com.zhiyu.campus.chat.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 对应表 11 聊天室成员表 chat_room_member。
 * 复合主键 (room_id, user_id)，因此不使用 @TableId，统一用条件构造器操作。
 */
@Data
@TableName("chat_room_member")
public class ChatRoomMember {

    private Long roomId;

    private Long userId;

    /** 0 成员 1 管理员 2 群主 */
    private Integer role;

    /** 0 未禁言 1 禁言 */
    private Integer muted;

    private LocalDateTime mutedUntil;

    private LocalDateTime joinedAt;
}
