package com.zhiyu.campus.chat.vo;

import java.time.LocalDateTime;

public record MemberVO(
        Long userId,
        String nickname,
        Integer role,
        Integer muted,
        LocalDateTime mutedUntil,
        LocalDateTime joinedAt) {
}
