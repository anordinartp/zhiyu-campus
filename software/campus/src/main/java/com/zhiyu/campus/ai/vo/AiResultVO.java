package com.zhiyu.campus.ai.vo;

import java.time.LocalDateTime;
import java.util.List;

/** AI 处理结果展示体，含标签与置信度，便于答辩时解释判定依据。 */
public record AiResultVO(
        Long id,
        Long postId,
        String summary,
        Integer sentiment,
        boolean violation,
        double confidence,
        List<TagScore> tags,
        LocalDateTime processedAt) {

    public record TagScore(Long tagId, String name, double confidence) {
    }
}
