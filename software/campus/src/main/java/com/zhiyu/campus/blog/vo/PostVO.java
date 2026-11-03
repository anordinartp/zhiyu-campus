package com.zhiyu.campus.blog.vo;

import java.time.LocalDateTime;
import java.util.List;

public record PostVO(
        Long id,
        Long boardId,
        String boardName,
        Long authorId,
        String authorNickname,
        String title,
        String body,
        String excerpt,
        Integer status,
        Integer viewCount,
        Integer likeCount,
        Integer favoriteCount,
        LocalDateTime createdAt,
        List<String> tags,
        boolean liked,
        boolean favorited) {
}
