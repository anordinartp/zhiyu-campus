package com.zhiyu.campus.blog.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.zhiyu.campus.blog.entity.Favorite;
import com.zhiyu.campus.blog.entity.LikeRecord;
import com.zhiyu.campus.blog.entity.Post;
import com.zhiyu.campus.blog.mapper.FavoriteMapper;
import com.zhiyu.campus.blog.mapper.LikeRecordMapper;
import com.zhiyu.campus.blog.mapper.PostMapper;
import com.zhiyu.campus.blog.vo.ToggleResultVO;
import com.zhiyu.campus.common.BizException;
import com.zhiyu.campus.common.ErrorCode;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;

import java.time.LocalDateTime;

/**
 * 点赞与收藏。两者都遵循“先判断再改计数”，
 * 保证重复提交不改变计数（表 18 的复合主键是最后一道防线）。
 */
@Service
public class InteractionService {

    private static final int TARGET_POST = 2;

    private final LikeRecordMapper likeMapper;
    private final FavoriteMapper favoriteMapper;
    private final PostMapper postMapper;

    public InteractionService(LikeRecordMapper likeMapper, FavoriteMapper favoriteMapper,
                              PostMapper postMapper) {
        this.likeMapper = likeMapper;
        this.favoriteMapper = favoriteMapper;
        this.postMapper = postMapper;
    }

    public boolean liked(Long userId, int targetType, Long targetId) {
        if (userId == null) {
            return false;
        }
        return likeMapper.selectCount(new LambdaQueryWrapper<LikeRecord>()
                .eq(LikeRecord::getUserId, userId)
                .eq(LikeRecord::getTargetType, targetType)
                .eq(LikeRecord::getTargetId, targetId)) > 0;
    }

    public boolean favorited(Long userId, Long postId) {
        if (userId == null) {
            return false;
        }
        return favoriteMapper.selectCount(new LambdaQueryWrapper<Favorite>()
                .eq(Favorite::getUserId, userId)
                .eq(Favorite::getPostId, postId)) > 0;
    }

    @Transactional
    public ToggleResultVO like(Long userId, Long postId, boolean liked) {
        requirePost(postId);
        boolean exists = liked(userId, TARGET_POST, postId);
        if (liked && !exists) {
            LikeRecord record = new LikeRecord();
            record.setUserId(userId);
            record.setTargetType(TARGET_POST);
            record.setTargetId(postId);
            record.setCreatedAt(LocalDateTime.now());
            likeMapper.insert(record);
            adjustCount(postId, "like_count", 1);
        } else if (!liked && exists) {
            likeMapper.delete(new LambdaQueryWrapper<LikeRecord>()
                    .eq(LikeRecord::getUserId, userId)
                    .eq(LikeRecord::getTargetType, TARGET_POST)
                    .eq(LikeRecord::getTargetId, postId));
            adjustCount(postId, "like_count", -1);
        }
        Post post = postMapper.selectById(postId);
        return new ToggleResultVO(liked, post.getLikeCount());
    }

    @Transactional
    public ToggleResultVO favorite(Long userId, Long postId, boolean favorited) {
        requirePost(postId);
        boolean exists = favorited(userId, postId);
        if (favorited && !exists) {
            Favorite favorite = new Favorite();
            favorite.setUserId(userId);
            favorite.setPostId(postId);
            favorite.setCreatedAt(LocalDateTime.now());
            favoriteMapper.insert(favorite);
            adjustCount(postId, "favorite_count", 1);
        } else if (!favorited && exists) {
            favoriteMapper.delete(new LambdaQueryWrapper<Favorite>()
                    .eq(Favorite::getUserId, userId)
                    .eq(Favorite::getPostId, postId));
            adjustCount(postId, "favorite_count", -1);
        }
        Post post = postMapper.selectById(postId);
        return new ToggleResultVO(favorited, post.getFavoriteCount());
    }

    private void requirePost(Long postId) {
        Post post = postMapper.selectById(postId);
        if (post == null) {
            throw new BizException(ErrorCode.NOT_FOUND, "帖子不存在");
        }
        if (post.getStatus() != null && post.getStatus() != 0) {
            throw new BizException(ErrorCode.FORBIDDEN, "该帖子当前不可互动");
        }
    }

    private void adjustCount(Long postId, String column, int delta) {
        postMapper.update(null, new LambdaUpdateWrapper<Post>()
                .eq(Post::getId, postId)
                .setSql(column + " = GREATEST(" + column + " + (" + delta + "), 0)"));
    }
}
