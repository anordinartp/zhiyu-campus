package com.zhiyu.campus.chat.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/** A-10 发送消息入参。 */
public record SendMessageRequest(

        /** 1 文本 2 图片 3 文件，默认文本 */
        Integer msgType,

        @NotBlank(message = "不能为空")
        @Size(max = 2000, message = "长度不能超过 2000 字")
        String content) {
}
