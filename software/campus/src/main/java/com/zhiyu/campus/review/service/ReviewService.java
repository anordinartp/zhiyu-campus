package com.zhiyu.campus.review.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.zhiyu.campus.ai.entity.AiResult;
import com.zhiyu.campus.ai.mapper.AiResultMapper;
import com.zhiyu.campus.blog.entity.Post;
import com.zhiyu.campus.blog.mapper.PostMapper;
import com.zhiyu.campus.common.BizException;
import com.zhiyu.campus.common.ErrorCode;
import com.zhiyu.campus.review.dto.ReviewRequest;
import com.zhiyu.campus.review.entity.ReviewLog;
import com.zhiyu.campus.review.mapper.ReviewLogMapper;
import com.zhiyu.campus.review.vo.PendingItemVO;
import com.zhiyu.campus.user.entity.User;
import com.zhiyu.campus.user.mapper.UserMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/** 审核台：只处理 status=1 的内容，处置结果写 review_log 留痕。 */
@Service
public class ReviewService {

    private final PostMapper postMapper;
    private final AiResultMapper aiResultMapper;
    private final ReviewLogMapper reviewLogMapper;
    private final UserMapper userMapper;

    public ReviewService(PostMapper postMapper, AiResultMapper aiResultMapper,
                         ReviewLogMapper reviewLogMapper, UserMapper userMapper) {
        this.postMapper = postMapper;
        this.aiResultMapper = aiResultMapper;
        this.reviewLogMapper = reviewLogMapper;
        this.userMapper = userMapper;
    }

    public List<PendingItemVO> pending(int page, int size) {
        Page<Post> result = postMapper.selectPage(
                new Page<>(Math.max(1, page), Math.max(1, Math.min(size, 50))),
                new LambdaQueryWrapper<Post>()
                        .eq(Post::getStatus, 1)
                        .orderByAsc(Post::getId));
        List<Post> posts = result.getRecords();
        if (posts.isEmpty()) {
            return List.of();
        }
        List<Long> postIds = posts.stream().map(Post::getId).toList();
        Map<Long, AiResult> aiMap = aiResultMapper.selectList(
                        new LambdaQueryWrapper<AiResult>().in(AiResult::getPostId, postIds))
                .stream().collect(Collectors.toMap(AiResult::getPostId, r -> r, (a, b) -> a));
        Map<Long, String> authors = userMapper.selectList(new LambdaQueryWrapper<User>()
                        .in(User::getId, posts.stream().map(Post::getAuthorId).distinct().toList()))
                .stream().collect(Collectors.toMap(User::getId, User::getNickname));

        return posts.stream().map(p -> {
            AiResult ai = aiMap.get(p.getId());
            String excerpt = p.getBody() == null ? null
                    : (p.getBody().length() <= 60 ? p.getBody() : p.getBody().substring(0, 60) + "…");
            return new PendingItemVO(p.getId(), p.getTitle(), excerpt, p.getAuthorId(),
                    authors.get(p.getAuthorId()),
                    ai == null ? null : ai.getSummary(),
                    ai == null ? null : ai.getSentiment(),
                    ai != null && Boolean.TRUE.equals(ai.getViolation()),
                    ai == null || ai.getConfidence() == null ? 0.0 : ai.getConfidence().doubleValue(),
                    p.getCreatedAt());
        }).toList();
    }

    @Transactional
    public void review(Long operatorId, Long postId, ReviewRequest request) {
        Post post = postMapper.selectById(postId);
        if (post == null) {
            throw new BizException(ErrorCode.NOT_FOUND, "帖子不存在");
        }
        if (post.getStatus() == null || post.getStatus() != 1) {
            throw new BizException(ErrorCode.CONFLICT, "该内容不在待审状态");
        }
        int newStatus = "approve".equals(request.action()) ? 0 : 2;
        postMapper.update(null, new LambdaUpdateWrapper<Post>()
                .eq(Post::getId, postId)
                .set(Post::getStatus, newStatus));

        writeLog(operatorId, postId, "approve".equals(request.action()) ? 1 : 2, request.remark());
    }

    /** 撤销处置：删除后 24 小时内可恢复（对应状态图 ⑥）。 */
    @Transactional
    public void undo(Long operatorId, Long postId, String remark) {
        Post post = postMapper.selectById(postId);
        if (post == null) {
            throw new BizException(ErrorCode.NOT_FOUND, "帖子不存在");
        }
        if (post.getStatus() == null || post.getStatus() != 2) {
            throw new BizException(ErrorCode.CONFLICT, "只有已删除的内容可以撤销");
        }
        ReviewLog last = reviewLogMapper.selectOne(new LambdaQueryWrapper<ReviewLog>()
                .eq(ReviewLog::getTargetType, 2)
                .eq(ReviewLog::getTargetId, postId)
                .eq(ReviewLog::getAction, 2)
                .orderByDesc(ReviewLog::getId)
                .last("limit 1"));
        if (last == null) {
            throw new BizException(ErrorCode.CONFLICT, "找不到删除记录，无法撤销");
        }
        if (last.getCreatedAt().plusHours(24).isBefore(LocalDateTime.now())) {
            throw new BizException(ErrorCode.FORBIDDEN, "已超过 24 小时撤销窗口");
        }
        postMapper.update(null, new LambdaUpdateWrapper<Post>()
                .eq(Post::getId, postId)
                .set(Post::getStatus, 0));
        writeLog(operatorId, postId, 3, remark);
    }

    private void writeLog(Long operatorId, Long postId, int action, String remark) {
        ReviewLog log = new ReviewLog();
        log.setTargetType(2);
        log.setTargetId(postId);
        log.setOperatorId(operatorId);
        log.setAction(action);
        log.setRemark(remark);
        log.setCreatedAt(LocalDateTime.now());
        reviewLogMapper.insert(log);
    }
}
