package com.zhiyu.campus.chat.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;

/** A-11 成员角色与禁言调整入参，两者至少传一个。 */
public record UpdateMemberRequest(

        @Min(value = 0, message = "取值需为 0~1")
        @Max(value = 1, message = "取值需为 0~1")
        Integer role,

        Integer muted,

        /** 禁言时长（分钟），为空表示永久 */
        Integer mutedMinutes) {
}
