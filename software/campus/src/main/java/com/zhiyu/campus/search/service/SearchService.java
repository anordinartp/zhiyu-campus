package com.zhiyu.campus.search.service;

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
