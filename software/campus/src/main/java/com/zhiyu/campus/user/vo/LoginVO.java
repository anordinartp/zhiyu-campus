package com.zhiyu.campus.user.vo;

/** 登录成功返回体。 */
public record LoginVO(
        String accessToken,
        String refreshToken,
        String tokenType,
        long expiresIn,
        Long userId,
        String nickname,
        Integer role) {
}
