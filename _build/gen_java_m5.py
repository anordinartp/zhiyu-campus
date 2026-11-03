# -*- coding: utf-8 -*-
"""生成 M5「AI 智能体 + 审核」模块。"""
import os

ROOT = (r"C:\Users\saxtul\Documents\ds harness区\知屿校园\software\campus"
        r"\src\main\java\com\zhiyu\campus")
F = {}

F["ai/entity/AiResult.java"] = """package com.zhiyu.campus.ai.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/** 对应表 16 ai_result，message_id 与 post_id 二者取一。 */
@Data
@TableName("ai_result")
public class AiResult {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long messageId;

    private Long postId;

    private String summary;

    /** 1 正面 0 中性 -1 负面 */
    private Integer sentiment;

    private Boolean violation;

    private BigDecimal confidence;

    private LocalDateTime processedAt;
}
"""

F["ai/entity/AiResultTag.java"] = """package com.zhiyu.campus.ai.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;

/** 对应关联表 ai_result_tag。 */
@Data
@TableName("ai_result_tag")
public class AiResultTag {

    private Long resultId;

    private Long tagId;

    private BigDecimal confidence;

    /** 1 模型自动 2 人工修正 */
    private Integer source;
}
"""

F["ai/mapper/AiResultMapper.java"] = """package com.zhiyu.campus.ai.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.zhiyu.campus.ai.entity.AiResult;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface AiResultMapper extends BaseMapper<AiResult> {
}
"""

F["ai/mapper/AiResultTagMapper.java"] = """package com.zhiyu.campus.ai.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.zhiyu.campus.ai.entity.AiResultTag;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface AiResultTagMapper extends BaseMapper<AiResultTag> {
}
"""

F["ai/vo/AiResultVO.java"] = """package com.zhiyu.campus.ai.vo;

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
"""

F["ai/service/AiModelClient.java"] = """package com.zhiyu.campus.ai.service;

import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 大模型调用的本地替身（mock）。
 *
 * 真实实现应调用外部大模型 API，契约见报告表 22。
 * 这里用确定性规则模拟，保证离线可演示、结果可复现：
 *   - 摘要：取正文前 60 字
 *   - 情感：命中正/负面词表
 *   - 违规：命中明确违规词给高置信，命中灰色词给中等置信
 *   - 标签：按关键词映射到已有标签
 *
 * 替换点：把本类换成 HTTP 调用即可，上层 AiAgentService 不需要改动。
 */
@Component
public class AiModelClient {

    private static final List<String> POSITIVE = List.of("谢谢", "感谢", "不错", "赞", "有用", "分享");
    private static final List<String> NEGATIVE = List.of("垃圾", "骗", "坑", "差评", "投诉");

    /** 明确违规，置信度 0.92 */
    private static final List<String> HARD_VIOLATION =
            List.of("代写", "代考", "赌博", "毒品", "枪", "色情", "诈骗");
    /** 灰色信号，置信度 0.65，进入低置信复核 */
    private static final List<String> SOFT_VIOLATION =
            List.of("收费", "私聊报价", "包过", "内部渠道");

    private static final Map<String, String> TAG_KEYWORDS = new LinkedHashMap<>();

    static {
        TAG_KEYWORDS.put("考研", "考研");
        TAG_KEYWORDS.put("选课", "选课");
        TAG_KEYWORDS.put("实习", "实习");
        TAG_KEYWORDS.put("社团", "社团");
        TAG_KEYWORDS.put("二手", "二手");
        TAG_KEYWORDS.put("求助", "求助");
        TAG_KEYWORDS.put("高数", "考研");
        TAG_KEYWORDS.put("期末", "选课");
    }

    public ModelOutput analyze(String title, String body) {
        String text = (title == null ? "" : title) + (body == null ? "" : body);

        String summary = body == null ? "" : body.strip();
        if (summary.length() > 60) {
            summary = summary.substring(0, 60) + "…";
        }

        int sentiment = 0;
        if (POSITIVE.stream().anyMatch(text::contains)) {
            sentiment = 1;
        } else if (NEGATIVE.stream().anyMatch(text::contains)) {
            sentiment = -1;
        }

        boolean violation = false;
        double confidence = 0.05;
        if (HARD_VIOLATION.stream().anyMatch(text::contains)) {
            violation = true;
            confidence = 0.92;
        } else if (SOFT_VIOLATION.stream().anyMatch(text::contains)) {
            violation = true;
            confidence = 0.65;
        }

        List<String> tagNames = new ArrayList<>();
        TAG_KEYWORDS.forEach((kw, tag) -> {
            if (text.contains(kw) && !tagNames.contains(tag)) {
                tagNames.add(tag);
            }
        });

        return new ModelOutput(summary, sentiment, violation, confidence, tagNames);
    }

    public record ModelOutput(String summary, int sentiment, boolean violation,
                              double confidence, List<String> tagNames) {
    }
}
"""

F["ai/service/AiAgentService.java"] = """package com.zhiyu.campus.ai.service;

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
"""

F["ai/service/AiAsyncProcessor.java"] = """package com.zhiyu.campus.ai.service;

import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

/**
 * 异步触发 AI 处理，对应 UC-10 的“异步处理，不阻塞发布”。
 * 使用虚拟线程执行器（见 AsyncConfig）。
 */
@Component
public class AiAsyncProcessor {

    private final AiAgentService agentService;

    public AiAsyncProcessor(AiAgentService agentService) {
        this.agentService = agentService;
    }

    @Async("aiExecutor")
    public void submit(Long postId) {
        agentService.processPostWithRetry(postId);
    }
}
"""

F["config/AsyncConfig.java"] = """package com.zhiyu.campus.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.task.SimpleAsyncTaskExecutor;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

/** 异步执行器：用虚拟线程跑 AI 处理，避免占用业务线程。 */
@Configuration
@EnableAsync
@EnableScheduling
public class AsyncConfig {

    @Bean("aiExecutor")
    public SimpleAsyncTaskExecutor aiExecutor() {
        SimpleAsyncTaskExecutor executor = new SimpleAsyncTaskExecutor("ai-");
        executor.setVirtualThreads(true);
        executor.setConcurrencyLimit(20);   // 对应表 22 的并发上限
        return executor;
    }
}
"""

F["review/entity/ReviewLog.java"] = """package com.zhiyu.campus.review.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/** 审核日志表 review_log（实现阶段补充，见报告说明）。 */
@Data
@TableName("review_log")
public class ReviewLog {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Integer targetType;

    private Long targetId;

    private Long operatorId;

    /** 1 通过 2 删除 */
    private Integer action;

    private String remark;

    private LocalDateTime createdAt;
}
"""

F["review/mapper/ReviewLogMapper.java"] = """package com.zhiyu.campus.review.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.zhiyu.campus.review.entity.ReviewLog;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface ReviewLogMapper extends BaseMapper<ReviewLog> {
}
"""

F["review/dto/ReviewRequest.java"] = """package com.zhiyu.campus.review.dto;

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
"""

F["review/vo/PendingItemVO.java"] = """package com.zhiyu.campus.review.vo;

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
"""

F["review/service/ReviewService.java"] = """package com.zhiyu.campus.review.service;

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
"""

F["review/controller/ReviewController.java"] = """package com.zhiyu.campus.review.controller;

import com.zhiyu.campus.common.ApiResponse;
import com.zhiyu.campus.common.BizException;
import com.zhiyu.campus.common.ErrorCode;
import com.zhiyu.campus.review.dto.ReviewRequest;
import com.zhiyu.campus.review.service.ReviewService;
import com.zhiyu.campus.review.vo.PendingItemVO;
import com.zhiyu.campus.security.CurrentUser;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@Tag(name = "审核台")
@RestController
@RequestMapping("/api/v1/admin/review")
public class ReviewController {

    private final ReviewService reviewService;

    public ReviewController(ReviewService reviewService) {
        this.reviewService = reviewService;
    }

    @Operation(summary = "A-21 待审列表")
    @GetMapping("/tasks")
    public ApiResponse<List<PendingItemVO>> tasks(@RequestParam(defaultValue = "1") int page,
                                                  @RequestParam(defaultValue = "20") int size) {
        requireAdmin();
        return ApiResponse.ok(reviewService.pending(page, size));
    }

    @Operation(summary = "A-22 审核处置（approve / reject）")
    @PostMapping("/{postId}")
    public ApiResponse<Void> review(@PathVariable Long postId,
                                    @Valid @RequestBody ReviewRequest request) {
        requireAdmin();
        reviewService.review(CurrentUser.id(), postId, request);
        return ApiResponse.ok();
    }

    @Operation(summary = "撤销处置（24 小时内）")
    @PostMapping("/{postId}/undo")
    public ApiResponse<Void> undo(@PathVariable Long postId,
                                  @RequestBody(required = false) ReviewRequest ignored) {
        requireAdmin();
        reviewService.undo(CurrentUser.id(), postId, "撤销处置");
        return ApiResponse.ok();
    }

    private void requireAdmin() {
        CurrentUser.Principal principal = CurrentUser.get();
        if (principal == null || principal.role() == null || principal.role() != 2) {
            throw new BizException(ErrorCode.FORBIDDEN, "仅管理员可访问审核台");
        }
    }
}
"""

F["ai/controller/AiResultController.java"] = """package com.zhiyu.campus.ai.controller;

import com.zhiyu.campus.ai.service.AiAgentService;
import com.zhiyu.campus.ai.vo.AiResultVO;
import com.zhiyu.campus.common.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Tag(name = "AI 智能体")
@RestController
@RequestMapping("/api/v1/posts/{postId}/ai-result")
public class AiResultController {

    private final AiAgentService agentService;

    public AiResultController(AiAgentService agentService) {
        this.agentService = agentService;
    }

    @Operation(summary = "查看帖子的 AI 摘要、标签与违规判定")
    @GetMapping
    public ApiResponse<AiResultVO> detail(@PathVariable Long postId) {
        return ApiResponse.ok(agentService.detail(postId));
    }
}
"""


def main():
    for rel, content in F.items():
        path = os.path.join(ROOT, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
    print("files:", len(F))


if __name__ == "__main__":
    main()
