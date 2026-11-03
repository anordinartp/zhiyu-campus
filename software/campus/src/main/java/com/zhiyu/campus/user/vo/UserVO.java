package com.zhiyu.campus.user.vo;

import java.time.LocalDateTime;

/** 用户信息返回体（不含口令哈希）。 */
public record UserVO(
        Long id,
        String account,
        String nickname,
        Integer role,
        Integer points,
        Integer status,
        LocalDateTime createdAt) {
}
