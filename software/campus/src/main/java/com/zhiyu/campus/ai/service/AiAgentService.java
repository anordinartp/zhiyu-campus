package com.zhiyu.campus.ai.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.zhiyu.campus.ai.entity.AiResult;
import com.zhiyu.campus.ai.entity.AiResultTag;
import com.zhiyu.campus.ai.mapper.AiResultMapper;
import com.zhiyu.campus.ai.mapper.AiResultTagMapper;
import com.zhiyu.campus.ai.vo.AiResultVO;
import com.zhiyu.campus.blog.entity.Post;
import com.zhiyu.campus.blog.mapper.PostMapper;
import com.zhiyu.campus.common.BizException;
import com.zhiyu.campus.common.ErrorCode;
import com.zhiyu.campus.tag.entity.Tag;
import com.zhiyu.campus.tag.mapper.TagMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * AI 智能体：对帖子做摘要、情感、违规判定与自动打标，实现报告 UC-10 与 8.3.3。
 *
 * 判定分档（表 27）：
 *   违规置信度 >= 0.8 -> 待审（高置信）
 *   0.5 ~ 0.8        -> 待审（低置信，优先复核）
 *   < 0.5            -> 保持正常
 * 无论置信度多高都不自动删除，只置为待审。
 */
@Service
public class AiAgentService {

    private static final Logger log = LoggerFactory.getLogger(AiAgentService.class);
    private static final int MAX_RETRY = 3;

    private final AiModelClient modelClient;
    private final AiResultMapper resultMapper;
    private final AiResultTagMapper resultTagMapper;
    private final PostMapper postMapper;
    private final TagMapper tagMapper;

    public AiAgentService(AiModelClient modelClient, AiResultMapper resultMapper,
                          AiResultTagMapper resultTagMapper, PostMapper postMapper,
                          TagMapper tagMapper) {
        this.modelClient = modelClient;
        this.resultMapper = resultMapper;
        this.resultTagMapper = resultTagMapper;
        this.postMapper = postMapper;
        this.tagMapper = tagMapper;
    }

    /** 带重试的处理入口，对应 UC-10 备选流 2a（模型超时重试 3 次）。 */
    public void processPostWithRetry(Long postId) {
        for (int attempt = 1; attempt <= MAX_RETRY; attempt++) {
            try {
                processPost(postId);
                return;
            } catch (Exception e) {
                log.warn("AI 处理帖子 {} 第 {} 次失败：{}", postId, attempt, e.getMessage());
                if (attempt == MAX_RETRY) {
                    log.error("AI 处理帖子 {} 放弃，内容保持“待处理”状态", postId);
                    return;
                }
                try {
                    Thread.sleep(200L * attempt);
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    return;
                }
            }
        }
    }

    @Transactional
    public AiResultVO processPost(Long postId) {
        Post post = postMapper.selectById(postId);
        if (post == null) {
            throw new BizException(ErrorCode.NOT_FOUND, "帖子不存在");
        }
        AiModelClient.ModelOutput output =
                modelClient.analyze(post.getTitle(), post.getBody());

        AiResult result = resultMapper.selectOne(new LambdaQueryWrapper<AiResult>()
                .eq(AiResult::getPostId, postId).last("limit 1"));
        boolean isNew = result == null;
        if (isNew) {
            result = new AiResult();
            result.setPostId(postId);
        }
        result.setSummary(output.summary());
        result.setSentiment(output.sentiment());
        result.setViolation(output.violation());
        result.setConfidence(BigDecimal.valueOf(output.confidence())
                .setScale(3, RoundingMode.HALF_UP));
        result.setProcessedAt(LocalDateTime.now());
        if (isNew) {
            resultMapper.insert(result);
        } else {
            resultMapper.updateById(result);
            resultTagMapper.delete(new LambdaQueryWrapper<AiResultTag>()
                    .eq(AiResultTag::getResultId, result.getId()));
        }

        Map<String, Long> tagIds = tagMapper.selectList(new LambdaQueryWrapper<Tag>())
                .stream().collect(Collectors.toMap(Tag::getName, Tag::getId, (a, b) -> a));
        List<AiResultVO.TagScore> scores = new ArrayList<>();
        for (String name : output.tagNames()) {
            Long tagId = tagIds.get(name);
            if (tagId == null) {
                continue;
            }
            AiResultTag tag = new AiResultTag();
            tag.setResultId(result.getId());
            tag.setTagId(tagId);
            tag.setConfidence(BigDecimal.valueOf(0.8));
            tag.setSource(1);
            resultTagMapper.insert(tag);
            scores.add(new AiResultVO.TagScore(tagId, name, 0.8));
        }

        // 违规判定只决定是否进入待审，不自动删除（NFR-08）
        if (output.violation() && output.confidence() >= 0.5
                && (post.getStatus() == null || post.getStatus() == 0)) {
            postMapper.update(null, new LambdaUpdateWrapper<Post>()
                    .eq(Post::getId, postId)
                    .set(Post::getStatus, 1));
            log.info("帖子 {} 判定违规（置信度 {}），已置为待审", postId, output.confidence());
        }

        return new AiResultVO(result.getId(), postId, result.getSummary(),
                result.getSentiment(), Boolean.TRUE.equals(result.getViolation()),
                result.getConfidence().doubleValue(), scores, result.getProcessedAt());
    }

    public AiResultVO detail(Long postId) {
        AiResult result = resultMapper.selectOne(new LambdaQueryWrapper<AiResult>()
                .eq(AiResult::getPostId, postId).last("limit 1"));
        if (result == null) {
            throw new BizException(ErrorCode.NOT_FOUND, "该内容尚未被 AI 处理");
        }
        Map<Long, String> names = tagMapper.selectList(new LambdaQueryWrapper<Tag>())
                .stream().collect(Collectors.toMap(Tag::getId, Tag::getName));
        List<AiResultVO.TagScore> tags = resultTagMapper.selectList(
                        new LambdaQueryWrapper<AiResultTag>()
                                .eq(AiResultTag::getResultId, result.getId()))
                .stream()
                .map(t -> new AiResultVO.TagScore(t.getTagId(),
                        names.getOrDefault(t.getTagId(), null),
                        t.getConfidence().doubleValue()))
                .toList();
        return new AiResultVO(result.getId(), result.getPostId(), result.getSummary(),
                result.getSentiment(), Boolean.TRUE.equals(result.getViolation()),
                result.getConfidence().doubleValue(), tags, result.getProcessedAt());
    }
}
