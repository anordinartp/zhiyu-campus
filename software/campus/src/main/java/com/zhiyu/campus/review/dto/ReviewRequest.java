package com.zhiyu.campus.review.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/** A-22 审核处置入参。 */
public record ReviewRequest(

        @NotBlank(message = "不能为空")
        @Pattern(regexp = "^(approve|reject)$", message = "只能为 approve 或 reject")
        String action,

        @Size(max = 200, message = "长度不能超过 200")
        String remark) {
}
