package com.zhiyu.campus.chat.vo;

import java.time.LocalDateTime;
import java.util.List;

public record RoomVO(
        Long id,
        String name,
        String intro,
        Long creatorId,
        Integer memberCount,
        Integer status,
        LocalDateTime lastActiveAt,
        LocalDateTime createdAt,
        List<String> tags) {
}
