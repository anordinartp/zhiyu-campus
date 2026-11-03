package com.zhiyu.campus.chat.vo;

import java.time.LocalDateTime;

public record MessageVO(
        Long id,
        Long roomId,
        Long senderId,
        String senderNickname,
        Integer msgType,
        String content,
        Integer status,
        LocalDateTime createdAt) {
}
