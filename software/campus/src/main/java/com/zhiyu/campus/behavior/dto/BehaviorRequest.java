package com.zhiyu.campus.behavior.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;

/** A-20 行为上报入参。 */
public record BehaviorRequest(

        @NotNull(message = "不能为空")
        @Min(value = 1, message = "取值需为 1~6")
        @Max(value = 6, message = "取值需为 1~6")
        Integer action,

        @NotNull(message = "不能为空")
        @Min(value = 1, message = "取值需为 1~5")
        @Max(value = 5, message = "取值需为 1~5")
        Integer targetType,

        @NotNull(message = "不能为空")
        Long targetId,

        /** 停留时长（毫秒），仅 action=6 时有效 */
        Integer stayMs) {
}
