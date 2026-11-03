package com.zhiyu.campus.blog.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/** A-15 回帖入参，parentReplyId 为空表示一级回帖。 */
public record CreateReplyRequest(

        @NotBlank(message = "不能为空")
        @Size(max = 2000, message = "长度不能超过 2000 字")
        String content,

        Long parentReplyId) {
}
