package com.zhiyu.campus.review.vo;

import java.time.LocalDateTime;

/** 审核台列表项：内容 + AI 判定依据，供管理员决策。 */
public record PendingItemVO(
        Long postId,
        String title,
        String excerpt,
        Long authorId,
        String authorNickname,
        String summary,
        Integer sentiment,
        boolean violation,
        double confidence,
        LocalDateTime createdAt) {
}
