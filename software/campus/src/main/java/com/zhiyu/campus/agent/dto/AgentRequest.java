package com.zhiyu.campus.agent.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/** 与总 agent 对话的入参。 */
public record AgentRequest(
        @NotBlank(message = "不能为空")
        @Size(max = 500, message = "长度不能超过 500")
        String message) {
}
