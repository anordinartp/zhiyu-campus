package com.zhiyu.campus.chat.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

import java.util.List;

/** A-07 创建聊天室入参。 */
public record CreateRoomRequest(

        @NotBlank(message = "不能为空")
        @Size(max = 60, message = "长度不能超过 60")
        String name,

        @Size(max = 500, message = "长度不能超过 500")
        String intro,

        /** 可选的标签 ID 列表，用于“标签把聊天室分类” */
        List<Long> tagIds) {
}
