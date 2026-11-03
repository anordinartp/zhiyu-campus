package com.zhiyu.campus.blog.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.util.List;

/** A-13 发帖入参，长度限制对应 UC-06 业务规则。 */
public record CreatePostRequest(

        @NotNull(message = "不能为空")
        Long boardId,

        @NotBlank(message = "不能为空")
        @Size(max = 100, message = "长度不能超过 100 字")
        String title,

        @NotBlank(message = "不能为空")
        @Size(max = 20000, message = "长度不能超过 20000 字")
        String body,

        @Size(max = 5, message = "最多 5 个标签")
        List<Long> tagIds) {
}
