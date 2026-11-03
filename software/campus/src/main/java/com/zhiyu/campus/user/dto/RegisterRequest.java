package com.zhiyu.campus.user.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/** A-01 注册入参。 */
public record RegisterRequest(

        @NotBlank(message = "不能为空")
        @Pattern(regexp = "^[A-Za-z0-9]{4,32}$", message = "需为 4~32 位字母或数字")
        String account,

        @NotBlank(message = "不能为空")
        @Size(max = 32, message = "长度不能超过 32")
        String nickname,

        @NotBlank(message = "不能为空")
        @Size(min = 8, max = 64, message = "长度需为 8~64 位")
        String password) {
}
