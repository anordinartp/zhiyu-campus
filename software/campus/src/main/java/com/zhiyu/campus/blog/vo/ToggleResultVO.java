package com.zhiyu.campus.blog.vo;

/** 点赞/收藏后的最新状态与计数，前端可直接用来刷新按钮。 */
public record ToggleResultVO(boolean active, long count) {
}
