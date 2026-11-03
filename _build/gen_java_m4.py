# -*- coding: utf-8 -*-
"""生成 M4「检索 + 行为 + 热度」模块。"""
import os

ROOT = (r"C:\Users\saxtul\Documents\ds harness区\知屿校园\software\campus"
        r"\src\main\java\com\zhiyu\campus")
F = {}

F["behavior/entity/BehaviorLog.java"] = """package com.zhiyu.campus.behavior.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/** 对应表 行为日志 behavior_log。 */
@Data
@TableName("behavior_log")
public class BehaviorLog {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long userId;

    /** 1 浏览 2 发言 3 发帖 4 点赞 5 收藏 6 停留 */
    private Integer action;

    /** 1 聊天室 2 消息 3 帖子 4 回帖 5 标签 */
    private Integer targetType;

    private Long targetId;

    private Integer stayMs;

    private LocalDateTime createdAt;
}
"""

F["behavior/mapper/BehaviorLogMapper.java"] = """package com.zhiyu.campus.behavior.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.zhiyu.campus.behavior.entity.BehaviorLog;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface BehaviorLogMapper extends BaseMapper<BehaviorLog> {
}
"""

F["behavior/dto/BehaviorRequest.java"] = """package com.zhiyu.campus.behavior.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;

/** A-20 行为上报入参。 */
public record BehaviorRequest(

        @NotNull(message = "不能为空")
        @Min(value = 1, message = "取值需为 1~6")
        @Max(value = 6, message = "取值需为 1~6")
        Integer action,

        @NotNull(message = "不能为空")
        @Min(value = 1, message = "取值需为 1~5")
        @Max(value = 5, message = "取值需为 1~5")
        Integer targetType,

        @NotNull(message = "不能为空")
        Long targetId,

        /** 停留时长（毫秒），仅 action=6 时有效 */
        Integer stayMs) {
}
"""

F["behavior/controller/BehaviorController.java"] = """package com.zhiyu.campus.behavior.controller;

import com.zhiyu.campus.behavior.dto.BehaviorRequest;
import com.zhiyu.campus.behavior.entity.BehaviorLog;
import com.zhiyu.campus.behavior.mapper.BehaviorLogMapper;
import com.zhiyu.campus.common.ApiResponse;
import com.zhiyu.campus.security.CurrentUser;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;

@Tag(name = "行为采集")
@RestController
@RequestMapping("/api/v1/behaviors")
public class BehaviorController {

    private final BehaviorLogMapper behaviorMapper;

    public BehaviorController(BehaviorLogMapper behaviorMapper) {
        this.behaviorMapper = behaviorMapper;
    }

    /** 返回 202：行为是异步采集，不阻塞用户操作。 */
    @Operation(summary = "A-20 上报行为（浏览/停留/点赞等）")
    @PostMapping
    public ResponseEntity<ApiResponse<Void>> report(@Valid @RequestBody BehaviorRequest request) {
        BehaviorLog log = new BehaviorLog();
        log.setUserId(CurrentUser.id());
        log.setAction(request.action());
        log.setTargetType(request.targetType());
        log.setTargetId(request.targetId());
        log.setStayMs(request.stayMs() == null ? 0 : request.stayMs());
        log.setCreatedAt(LocalDateTime.now());
        behaviorMapper.insert(log);
        return ResponseEntity.status(HttpStatus.ACCEPTED).body(ApiResponse.ok());
    }
}
"""

F["search/SearchProperties.java"] = """package com.zhiyu.campus.search;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.DefaultValue;

/**
 * 检索参数，对应报告表 26。权重放在配置里，答辩时可以现场改数值演示排序变化。
 */
@ConfigurationProperties(prefix = "app.search")
public record SearchProperties(
        @DefaultValue("0.5") double relWeight,
        @DefaultValue("0.3") double heatWeight,
        @DefaultValue("0.2") double prefWeight,
        @DefaultValue("0.05") double recencyLambda,
        @DefaultValue("200") int recallLimit,
        @DefaultValue("20") int defaultLimit) {
}
"""

F["search/vo/SearchItemVO.java"] = """package com.zhiyu.campus.search.vo;

import java.util.List;

/**
 * 检索结果项。score 与三个分项都返回，便于解释“为什么排在这里”。
 */
public record SearchItemVO(
        String type,
        Long id,
        String title,
        String excerpt,
        double score,
        double rel,
        double heat,
        double pref,
        List<String> tags) {
}
"""

F["search/service/SearchService.java"] = """package com.zhiyu.campus.search.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.zhiyu.campus.behavior.entity.BehaviorLog;
import com.zhiyu.campus.behavior.mapper.BehaviorLogMapper;
import com.zhiyu.campus.blog.entity.Post;
import com.zhiyu.campus.blog.entity.PostTag;
import com.zhiyu.campus.blog.mapper.PostMapper;
import com.zhiyu.campus.blog.mapper.PostTagMapper;
import com.zhiyu.campus.chat.entity.ChatRoom;
import com.zhiyu.campus.chat.entity.ChatRoomTag;
import com.zhiyu.campus.chat.mapper.ChatRoomMapper;
import com.zhiyu.campus.chat.mapper.ChatRoomTagMapper;
import com.zhiyu.campus.search.SearchProperties;
import com.zhiyu.campus.search.vo.SearchItemVO;
import com.zhiyu.campus.tag.entity.Tag;
import com.zhiyu.campus.tag.mapper.TagMapper;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * 统一检索，实现报告 8.3.1：
 *   score = w1 * rel + w2 * heat + w3 * pref
 * 三个分项各归一化到 [0,1]，因此 score 也在 [0,1]，便于解释与调参。
 */
@Service
public class SearchService {

    /** 行为目标类型：1 聊天室 2 消息 3 帖子 4 回帖 5 标签（对应表 18） */
    private static final int POST = 3;
    private static final int ROOM = 1;

    private final PostMapper postMapper;
    private final PostTagMapper postTagMapper;
    private final ChatRoomMapper roomMapper;
    private final ChatRoomTagMapper roomTagMapper;
    private final TagMapper tagMapper;
    private final BehaviorLogMapper behaviorMapper;
    private final SearchProperties props;

    public SearchService(PostMapper postMapper, PostTagMapper postTagMapper,
                         ChatRoomMapper roomMapper, ChatRoomTagMapper roomTagMapper,
                         TagMapper tagMapper, BehaviorLogMapper behaviorMapper,
                         SearchProperties props) {
        this.postMapper = postMapper;
        this.postTagMapper = postTagMapper;
        this.roomMapper = roomMapper;
        this.roomTagMapper = roomTagMapper;
        this.tagMapper = tagMapper;
        this.behaviorMapper = behaviorMapper;
        this.props = props;
    }

    public List<SearchItemVO> search(Long userId, String keyword, Long tagId, Integer limit) {
        String q = keyword == null ? "" : keyword.trim();
        int size = limit == null ? props.defaultLimit() : Math.max(1, Math.min(limit, 50));

        List<Post> posts = recallPosts(q, tagId);
        List<ChatRoom> rooms = recallRooms(q, tagId);
        if (posts.isEmpty() && rooms.isEmpty()) {
            return List.of();
        }

        Map<Long, List<Long>> postTags = tagMapOfPosts(posts.stream().map(Post::getId).toList());
        Map<Long, List<Long>> roomTags = tagMapOfRooms(rooms.stream().map(ChatRoom::getId).toList());
        Map<Long, String> tagNames = tagNames(postTags, roomTags);
        Map<Long, Double> preference = preferenceByTag(userId);

        List<Row> rows = new ArrayList<>();
        for (Post p : posts) {
            double rel = relevance(q, p.getTitle(), p.getBody());
            double heat = postHeat(p);
            double pref = preference(postTags.getOrDefault(p.getId(), List.of()), preference);
            rows.add(new Row("post", p.getId(), p.getTitle(), excerpt(p.getBody()),
                    rel, heat, pref, names(postTags.getOrDefault(p.getId(), List.of()), tagNames)));
        }
        for (ChatRoom r : rooms) {
            double rel = relevance(q, r.getName(), r.getIntro());
            double heat = roomHeat(r);
            double pref = preference(roomTags.getOrDefault(r.getId(), List.of()), preference);
            rows.add(new Row("room", r.getId(), r.getName(), excerpt(r.getIntro()),
                    rel, heat, pref, names(roomTags.getOrDefault(r.getId(), List.of()), tagNames)));
        }

        normalize(rows);
        return rows.stream()
                .map(r -> new SearchItemVO(r.type, r.id, r.title, r.excerpt,
                        round(props.relWeight() * r.rel + props.heatWeight() * r.heat
                                + props.prefWeight() * r.pref),
                        round(r.rel), round(r.heat), round(r.pref), r.tags))
                .sorted(Comparator.comparingDouble(SearchItemVO::score).reversed())
                .limit(size)
                .toList();
    }

    // ------------------------------------------------------------- 召回

    private List<Post> recallPosts(String q, Long tagId) {
        LambdaQueryWrapper<Post> wrapper = new LambdaQueryWrapper<Post>().eq(Post::getStatus, 0);
        if (!q.isBlank()) {
            wrapper.and(w -> w.like(Post::getTitle, q).or().like(Post::getBody, q));
        }
        if (tagId != null) {
            List<Long> ids = postTagMapper.selectList(
                            new LambdaQueryWrapper<PostTag>().eq(PostTag::getTagId, tagId))
                    .stream().map(PostTag::getPostId).distinct().toList();
            if (ids.isEmpty()) {
                return List.of();
            }
            wrapper.in(Post::getId, ids);
        }
        wrapper.orderByDesc(Post::getId).last("limit " + props.recallLimit());
        return postMapper.selectList(wrapper);
    }

    private List<ChatRoom> recallRooms(String q, Long tagId) {
        LambdaQueryWrapper<ChatRoom> wrapper = new LambdaQueryWrapper<ChatRoom>()
                .eq(ChatRoom::getStatus, 0);
        if (!q.isBlank()) {
            wrapper.and(w -> w.like(ChatRoom::getName, q).or().like(ChatRoom::getIntro, q));
        }
        if (tagId != null) {
            List<Long> ids = roomTagMapper.selectList(
                            new LambdaQueryWrapper<ChatRoomTag>().eq(ChatRoomTag::getTagId, tagId))
                    .stream().map(ChatRoomTag::getRoomId).distinct().toList();
            if (ids.isEmpty()) {
                return List.of();
            }
            wrapper.in(ChatRoom::getId, ids);
        }
        wrapper.orderByDesc(ChatRoom::getId).last("limit " + props.recallLimit());
        return roomMapper.selectList(wrapper);
    }

    // ------------------------------------------------------------- 打分

    /** 标题命中权重是正文的 2 倍，简单可解释。 */
    private double relevance(String q, String title, String body) {
        if (q.isBlank()) {
            return 0.5;                       // 无关键词时按标签/热度排序，给中性值
        }
        return 2.0 * occurrences(title, q) + occurrences(body, q);
    }

    private int occurrences(String text, String q) {
        if (text == null || q.isEmpty()) {
            return 0;
        }
        int count = 0;
        int from = 0;
        while (true) {
            int idx = text.indexOf(q, from);
            if (idx < 0) {
                break;
            }
            count++;
            from = idx + q.length();
        }
        return count;
    }

    /** 8.3.2：计数加权后乘时间衰减 e^(-λ·Δt)。 */
    private double postHeat(Post p) {
        double raw = p.getViewCount() + 3.0 * p.getLikeCount() + 4.0 * p.getFavoriteCount();
        return raw * decay(p.getCreatedAt());
    }

    private double roomHeat(ChatRoom r) {
        double raw = 5.0 * (r.getMemberCount() == null ? 0 : r.getMemberCount());
        return raw * decay(r.getLastActiveAt() == null ? r.getCreatedAt() : r.getLastActiveAt());
    }

    private double decay(LocalDateTime time) {
        if (time == null) {
            return 1.0;
        }
        double days = Duration.between(time, LocalDateTime.now()).toHours() / 24.0;
        return Math.exp(-props.recencyLambda() * Math.max(days, 0));
    }

    /** 用户对各标签的行为权重，用于 pref 分项。 */
    private Map<Long, Double> preferenceByTag(Long userId) {
        Map<Long, Double> result = new HashMap<>();
        if (userId == null) {
            return result;
        }
        List<BehaviorLog> logs = behaviorMapper.selectList(new LambdaQueryWrapper<BehaviorLog>()
                .eq(BehaviorLog::getUserId, userId)
                .orderByDesc(BehaviorLog::getId)
                .last("limit 500"));
        if (logs.isEmpty()) {
            return result;
        }
        Map<Long, List<Long>> postTags = tagMapOfPosts(logs.stream()
                .filter(l -> l.getTargetType() != null && l.getTargetType() == POST)
                .map(BehaviorLog::getTargetId).distinct().toList());
        for (BehaviorLog log : logs) {
            if (log.getTargetType() == null || log.getTargetType() != POST) {
                continue;
            }
            double weight = weightOf(log);
            for (Long tagId : postTags.getOrDefault(log.getTargetId(), List.of())) {
                result.merge(tagId, weight, Double::sum);
            }
        }
        return result;
    }

    private double weightOf(BehaviorLog log) {
        return switch (log.getAction() == null ? 0 : log.getAction()) {
            case 1 -> 1.0;                                  // 浏览
            case 2 -> 2.0;                                  // 发言
            case 3 -> 5.0;                                  // 发帖
            case 4 -> 3.0;                                  // 点赞
            case 5 -> 4.0;                                  // 收藏
            case 6 -> (log.getStayMs() == null ? 0 : log.getStayMs()) / 10000.0;  // 每 10 秒 1 分
            default -> 0.0;
        };
    }

    private double preference(List<Long> tags, Map<Long, Double> weightByTag) {
        if (tags.isEmpty() || weightByTag.isEmpty()) {
            return 0.0;
        }
        double sum = 0;
        for (Long t : tags) {
            sum += weightByTag.getOrDefault(t, 0.0);
        }
        return sum / tags.size();
    }

    // ------------------------------------------------------------- 归一化

    private void normalize(List<Row> rows) {
        normalizeOne(rows, r -> r.rel, (r, v) -> r.rel = v);
        normalizeOne(rows, r -> r.heat, (r, v) -> r.heat = v);
        normalizeOne(rows, r -> r.pref, (r, v) -> r.pref = v);
    }

    private void normalizeOne(List<Row> rows, java.util.function.ToDoubleFunction<Row> getter,
                              java.util.function.ObjDoubleConsumer<Row> setter) {
        double max = rows.stream().mapToDouble(getter).max().orElse(0);
        if (max <= 0) {
            rows.forEach(r -> setter.accept(r, 0));
            return;
        }
        rows.forEach(r -> setter.accept(r, getter.applyAsDouble(r) / max));
    }

    private double round(double v) {
        return Math.round(v * 10000.0) / 10000.0;
    }

    // ------------------------------------------------------------- 辅助

    private Map<Long, List<Long>> tagMapOfPosts(List<Long> postIds) {
        Map<Long, List<Long>> map = new HashMap<>();
        if (postIds == null || postIds.isEmpty()) {
            return map;
        }
        postTagMapper.selectList(new LambdaQueryWrapper<PostTag>().in(PostTag::getPostId, postIds))
                .forEach(link -> map.computeIfAbsent(link.getPostId(), k -> new ArrayList<>())
                        .add(link.getTagId()));
        return map;
    }

    private Map<Long, List<Long>> tagMapOfRooms(List<Long> roomIds) {
        Map<Long, List<Long>> map = new HashMap<>();
        if (roomIds == null || roomIds.isEmpty()) {
            return map;
        }
        roomTagMapper.selectList(new LambdaQueryWrapper<ChatRoomTag>()
                        .in(ChatRoomTag::getRoomId, roomIds))
                .forEach(link -> map.computeIfAbsent(link.getRoomId(), k -> new ArrayList<>())
                        .add(link.getTagId()));
        return map;
    }

    private Map<Long, String> tagNames(Map<Long, List<Long>> a, Map<Long, List<Long>> b) {
        List<Long> ids = new ArrayList<>();
        a.values().forEach(ids::addAll);
        b.values().forEach(ids::addAll);
        if (ids.isEmpty()) {
            return Map.of();
        }
        return tagMapper.selectList(new LambdaQueryWrapper<Tag>()
                        .in(Tag::getId, ids.stream().distinct().toList()))
                .stream().collect(Collectors.toMap(Tag::getId, Tag::getName));
    }

    private List<String> names(List<Long> ids, Map<Long, String> dict) {
        return ids.stream().map(id -> dict.getOrDefault(id, String.valueOf(id))).toList();
    }

    private String excerpt(String text) {
        if (text == null) {
            return null;
        }
        return text.length() <= 60 ? text : text.substring(0, 60) + "…";
    }

    /** 可变打分容器，归一化时就地修改。 */
    private static final class Row {
        final String type;
        final Long id;
        final String title;
        final String excerpt;
        double rel;
        double heat;
        double pref;
        final List<String> tags;

        Row(String type, Long id, String title, String excerpt,
            double rel, double heat, double pref, List<String> tags) {
            this.type = type;
            this.id = id;
            this.title = title;
            this.excerpt = excerpt;
            this.rel = rel;
            this.heat = heat;
            this.pref = pref;
            this.tags = tags;
        }
    }
}
"""

F["search/controller/SearchController.java"] = """package com.zhiyu.campus.search.controller;

import com.zhiyu.campus.common.ApiResponse;
import com.zhiyu.campus.search.service.SearchService;
import com.zhiyu.campus.search.vo.SearchItemVO;
import com.zhiyu.campus.security.CurrentUser;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@Tag(name = "检索")
@RestController
@RequestMapping("/api/v1/search")
public class SearchController {

    private final SearchService searchService;

    public SearchController(SearchService searchService) {
        this.searchService = searchService;
    }

    @Operation(summary = "A-19 统一检索（帖子 + 聊天室）")
    @GetMapping
    public ApiResponse<List<SearchItemVO>> search(
            @RequestParam(required = false) String q,
            @RequestParam(required = false) Long tagId,
            @RequestParam(required = false) Integer limit) {
        return ApiResponse.ok(searchService.search(CurrentUser.id(), q, tagId, limit));
    }
}
"""

F["heat/service/HeatService.java"] = """package com.zhiyu.campus.heat.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.zhiyu.campus.blog.entity.Post;
import com.zhiyu.campus.blog.entity.PostTag;
import com.zhiyu.campus.blog.mapper.PostMapper;
import com.zhiyu.campus.blog.mapper.PostTagMapper;
import com.zhiyu.campus.tag.entity.Tag;
import com.zhiyu.campus.tag.mapper.TagMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 热度重算，实现报告 8.3.2：
 *   heat = Σ(权重 × e^(-λ·Δt))
 * 这里按帖子维度聚合后写回 tag.heat，定时任务每小时跑一次，避免查询时实时聚合。
 */
@Service
public class HeatService {

    private static final Logger log = LoggerFactory.getLogger(HeatService.class);

    private final PostMapper postMapper;
    private final PostTagMapper postTagMapper;
    private final TagMapper tagMapper;

    @Value("${app.search.recency-lambda:0.05}")
    private double lambda;

    public HeatService(PostMapper postMapper, PostTagMapper postTagMapper, TagMapper tagMapper) {
        this.postMapper = postMapper;
        this.postTagMapper = postTagMapper;
        this.tagMapper = tagMapper;
    }

    @Transactional
    @Scheduled(fixedDelayString = "PT1H", initialDelayString = "PT5M")
    public int recalcAll() {
        List<Post> posts = postMapper.selectList(new LambdaQueryWrapper<Post>()
                .eq(Post::getStatus, 0));
        Map<Long, Double> postHeat = new HashMap<>();
        for (Post p : posts) {
            double raw = p.getViewCount() + 3.0 * p.getLikeCount() + 4.0 * p.getFavoriteCount();
            postHeat.put(p.getId(), raw * decay(p.getCreatedAt()));
        }

        Map<Long, Double> tagHeat = new HashMap<>();
        if (!postHeat.isEmpty()) {
            List<PostTag> links = postTagMapper.selectList(new LambdaQueryWrapper<PostTag>()
                    .in(PostTag::getPostId, postHeat.keySet()));
            for (PostTag link : links) {
                tagHeat.merge(link.getTagId(), postHeat.getOrDefault(link.getPostId(), 0.0), Double::sum);
            }
        }

        List<Tag> tags = tagMapper.selectList(new LambdaQueryWrapper<Tag>());
        for (Tag tag : tags) {
            long heat = Math.round(tagHeat.getOrDefault(tag.getId(), 0.0));
            tagMapper.update(null, new LambdaUpdateWrapper<Tag>()
                    .eq(Tag::getId, tag.getId())
                    .set(Tag::getHeat, (int) Math.min(heat, Integer.MAX_VALUE)));
        }
        log.info("热度重算完成：{} 篇帖子、{} 个标签", posts.size(), tags.size());
        return tags.size();
    }

    private double decay(LocalDateTime time) {
        if (time == null) {
            return 1.0;
        }
        double days = Duration.between(time, LocalDateTime.now()).toHours() / 24.0;
        return Math.exp(-lambda * Math.max(days, 0));
    }
}
"""

F["heat/controller/AdminHeatController.java"] = """package com.zhiyu.campus.heat.controller;

import com.zhiyu.campus.common.ApiResponse;
import com.zhiyu.campus.common.BizException;
import com.zhiyu.campus.common.ErrorCode;
import com.zhiyu.campus.heat.service.HeatService;
import com.zhiyu.campus.security.CurrentUser;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@Tag(name = "管理")
@RestController
@RequestMapping("/api/v1/admin")
public class AdminHeatController {

    private final HeatService heatService;

    public AdminHeatController(HeatService heatService) {
        this.heatService = heatService;
    }

    @Operation(summary = "手动触发热度重算（仅管理员）")
    @PostMapping("/heat/recalc")
    public ApiResponse<Map<String, Integer>> recalc() {
        CurrentUser.Principal principal = CurrentUser.get();
        if (principal == null || principal.role() == null || principal.role() != 2) {
            throw new BizException(ErrorCode.FORBIDDEN, "仅管理员可触发热度重算");
        }
        int tags = heatService.recalcAll();
        return ApiResponse.ok(Map.of("tags", tags));
    }
}
"""

F["config/SchedulingConfig.java"] = """package com.zhiyu.campus.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableScheduling;

/** 开启定时任务：热度重算每小时执行一次。 */
@Configuration
@EnableScheduling
public class SchedulingConfig {
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
