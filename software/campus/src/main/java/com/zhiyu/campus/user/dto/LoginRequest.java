package com.zhiyu.campus.user.dto;

import jakarta.validation.constraints.NotBlank;

/** A-02 登录入参。 */
public record LoginRequest(

        @NotBlank(message = "不能为空") String account,
        @NotBlank(message = "不能为空") String password) {
}
