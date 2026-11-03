package com.zhiyu.campus.blog.vo;

import java.time.LocalDateTime;

public record ReplyVO(
        Long id,
        Long postId,
        Long authorId,
        String authorNickname,
        Long parentReplyId,
        String content,
        Integer likeCount,
        LocalDateTime createdAt) {
}
