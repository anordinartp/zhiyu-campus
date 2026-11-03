package com.zhiyu.campus.user.dto;

import jakarta.validation.constraints.NotBlank;

/** A-03 刷新令牌入参。 */
public record RefreshRequest(
        @NotBlank(message = "不能为空") String refreshToken) {
}
