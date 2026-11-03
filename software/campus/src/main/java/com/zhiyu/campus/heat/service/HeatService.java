package com.zhiyu.campus.heat.service;

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
