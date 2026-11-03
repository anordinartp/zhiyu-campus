# -*- coding: utf-8 -*-
"""生成 M3「博客」模块的 Java 源码。"""
import os

ROOT = (r"C:\Users\saxtul\Documents\ds harness区\知屿校园\software\campus"
        r"\src\main\java\com\zhiyu\campus")
F = {}

# ------------------------------------------------------------------ 实体
F["blog/entity/Post.java"] = """package com.zhiyu.campus.blog.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/** 对应表 13 帖子表 post。 */
@Data
@TableName("post")
public class Post {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long boardId;

    private Long authorId;

    private String title;

    private String body;

    /** 0 正常 1 待审 2 删除 */
    private Integer status;

    private Integer viewCount;

    private Integer likeCount;

    private Integer favoriteCount;

    private LocalDateTime createdAt;

    private LocalDateTime updatedAt;
}
"""

F["blog/entity/Reply.java"] = """package com.zhiyu.campus.blog.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/** 对应表 14 回帖表 reply，父回帖为空表示一级回帖。 */
@Data
@TableName("reply")
public class Reply {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long postId;

    private Long authorId;

    private Long parentReplyId;

    private String content;

    private Integer likeCount;

    private Integer status;

    private LocalDateTime createdAt;
}
"""

F["blog/entity/Board.java"] = """package com.zhiyu.campus.blog.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/** 对应表 10 之外的板块表 board。 */
@Data
@TableName("board")
public class Board {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String name;

    private String intro;

    private Long adminId;

    private Integer sortNo;

    private LocalDateTime createdAt;
}
"""

F["blog/entity/PostTag.java"] = """package com.zhiyu.campus.blog.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/** 帖子—标签关联表 post_tag，复合主键，不使用 @TableId。 */
@Data
@TableName("post_tag")
public class PostTag {

    private Long postId;

    private Long tagId;

    /** 1 作者手动 2 AI 自动 */
    private Integer source;

    private LocalDateTime createdAt;
}
"""

F["blog/entity/LikeRecord.java"] = """package com.zhiyu.campus.blog.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/** 点赞明细 like_record，复合主键保证“同一用户对同一目标只点一次”。 */
@Data
@TableName("like_record")
public class LikeRecord {

    private Long userId;

    /** 1 消息 2 帖子 3 回帖 */
    private Integer targetType;

    private Long targetId;

    private LocalDateTime createdAt;
}
"""

F["blog/entity/Favorite.java"] = """package com.zhiyu.campus.blog.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/** 收藏表 favorite，复合主键（用户，帖子）。 */
@Data
@TableName("favorite")
public class Favorite {

    private Long userId;

    private Long postId;

    private LocalDateTime createdAt;
}
"""

# ---------------------------------------------------------------- mapper
for name, pkg, ent in (
        ("PostMapper", "Post", "Post"),
        ("ReplyMapper", "Reply", "Reply"),
        ("BoardMapper", "Board", "Board"),
        ("PostTagMapper", "PostTag", "PostTag"),
        ("LikeRecordMapper", "LikeRecord", "LikeRecord"),
        ("FavoriteMapper", "Favorite", "Favorite")):
    F["blog/mapper/%s.java" % name] = """package com.zhiyu.campus.blog.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.zhiyu.campus.blog.entity.%s;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface %s extends BaseMapper<%s> {
}
""" % (ent, name, ent)

# ------------------------------------------------------------------- dto
F["blog/dto/CreatePostRequest.java"] = """package com.zhiyu.campus.blog.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.util.List;

/** A-13 发帖入参，长度限制对应 UC-06 业务规则。 */
public record CreatePostRequest(

        @NotNull(message = "不能为空")
        Long boardId,

        @NotBlank(message = "不能为空")
        @Size(max = 100, message = "长度不能超过 100 字")
        String title,

        @NotBlank(message = "不能为空")
        @Size(max = 20000, message = "长度不能超过 20000 字")
        String body,

        @Size(max = 5, message = "最多 5 个标签")
        List<Long> tagIds) {
}
"""

F["blog/dto/CreateReplyRequest.java"] = """package com.zhiyu.campus.blog.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/** A-15 回帖入参，parentReplyId 为空表示一级回帖。 */
public record CreateReplyRequest(

        @NotBlank(message = "不能为空")
        @Size(max = 2000, message = "长度不能超过 2000 字")
        String content,

        Long parentReplyId) {
}
"""

F["blog/dto/ToggleRequest.java"] = """package com.zhiyu.campus.blog.dto;

/**
 * A-16 / A-17 的点赞与收藏入参。
 * liked 为空时按 true 处理；重复提交同一动作是幂等的（对应测试用例 TC-15）。
 */
public record ToggleRequest(Boolean liked) {

    public boolean target() {
        return liked == null || liked;
    }
}
"""

# -------------------------------------------------------------------- vo
F["blog/vo/PostVO.java"] = """package com.zhiyu.campus.blog.vo;

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
"""

F["blog/vo/ReplyVO.java"] = """package com.zhiyu.campus.blog.vo;

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
"""

F["blog/vo/BoardVO.java"] = """package com.zhiyu.campus.blog.vo;

public record BoardVO(Long id, String name, String intro, Integer sortNo) {
}
"""

F["blog/vo/ToggleResultVO.java"] = """package com.zhiyu.campus.blog.vo;

/** 点赞/收藏后的最新状态与计数，前端可直接用来刷新按钮。 */
public record ToggleResultVO(boolean active, long count) {
}
"""

# --------------------------------------------------------------- 服务
F["blog/service/SensitiveWordChecker.java"] = """package com.zhiyu.campus.blog.service;

import org.springframework.stereotype.Component;

import java.util.List;

/**
 * 敏感词规则检查，对应报告 8.3.3 表 27 第一条：
 * 命中规则库的内容直接置为待审，不自动删除。
 * 生产环境应改为可配置词库 + 前缀树，这里用最小实现保证行为可演示。
 */
@Component
public class SensitiveWordChecker {

    private static final List<String> WORDS = List.of("代写", "代考", "赌博", "毒品", "枪");

    public String firstHit(String text) {
        if (text == null) {
            return null;
        }
        for (String w : WORDS) {
            if (text.contains(w)) {
                return w;
            }
        }
        return null;
    }
}
"""

F["blog/service/PostService.java"] = """package com.zhiyu.campus.blog.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.zhiyu.campus.blog.dto.CreatePostRequest;
import com.zhiyu.campus.blog.dto.CreateReplyRequest;
import com.zhiyu.campus.blog.entity.Board;
import com.zhiyu.campus.blog.entity.Post;
import com.zhiyu.campus.blog.entity.PostTag;
import com.zhiyu.campus.blog.entity.Reply;
import com.zhiyu.campus.blog.mapper.BoardMapper;
import com.zhiyu.campus.blog.mapper.PostMapper;
import com.zhiyu.campus.blog.mapper.PostTagMapper;
import com.zhiyu.campus.blog.mapper.ReplyMapper;
import com.zhiyu.campus.blog.vo.PostVO;
import com.zhiyu.campus.blog.vo.ReplyVO;
import com.zhiyu.campus.ai.service.AiAsyncProcessor;
import com.zhiyu.campus.common.BizException;
import com.zhiyu.campus.common.ErrorCode;
import com.zhiyu.campus.tag.entity.Tag;
import com.zhiyu.campus.tag.mapper.TagMapper;
import com.zhiyu.campus.user.entity.User;
import com.zhiyu.campus.user.mapper.UserMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class PostService {

    private static final int MAX_BODY_IN_LIST = 80;

    private final PostMapper postMapper;
    private final ReplyMapper replyMapper;
    private final BoardMapper boardMapper;
    private final PostTagMapper postTagMapper;
    private final TagMapper tagMapper;
    private final UserMapper userMapper;
    private final SensitiveWordChecker sensitiveWordChecker;
    private final InteractionService interactionService;
    private final AiAsyncProcessor aiAsyncProcessor;

    public PostService(PostMapper postMapper, ReplyMapper replyMapper, BoardMapper boardMapper,
                       PostTagMapper postTagMapper, TagMapper tagMapper, UserMapper userMapper,
                       SensitiveWordChecker sensitiveWordChecker,
                       InteractionService interactionService,
                       AiAsyncProcessor aiAsyncProcessor) {
        this.postMapper = postMapper;
        this.replyMapper = replyMapper;
        this.boardMapper = boardMapper;
        this.postTagMapper = postTagMapper;
        this.tagMapper = tagMapper;
        this.userMapper = userMapper;
        this.sensitiveWordChecker = sensitiveWordChecker;
        this.interactionService = interactionService;
        this.aiAsyncProcessor = aiAsyncProcessor;
    }

    @Transactional
    public PostVO create(Long userId, CreatePostRequest request) {
        Board board = boardMapper.selectById(request.boardId());
        if (board == null) {
            throw new BizException(ErrorCode.NOT_FOUND, "板块不存在");
        }
        String hit = sensitiveWordChecker.firstHit(request.title() + request.body());

        Post post = new Post();
        post.setBoardId(board.getId());
        post.setAuthorId(userId);
        post.setTitle(request.title());
        post.setBody(request.body());
        post.setStatus(hit == null ? 0 : 1);
        post.setViewCount(0);
        post.setLikeCount(0);
        post.setFavoriteCount(0);
        post.setCreatedAt(LocalDateTime.now());
        postMapper.insert(post);

        bindTags(post.getId(), request.tagIds());
        submitAiAfterCommit(post.getId());
        return toVO(post, board, loadTagNames(List.of(post.getId())), userId);
    }

    public List<PostVO> list(Long userId, Long boardId, Long tagId, String sort, int page, int size) {
        List<Long> postIds = null;
        if (tagId != null) {
            postIds = postTagMapper.selectList(new LambdaQueryWrapper<PostTag>()
                            .eq(PostTag::getTagId, tagId))
                    .stream().map(PostTag::getPostId).distinct().toList();
            if (postIds.isEmpty()) {
                return List.of();
            }
        }
        LambdaQueryWrapper<Post> wrapper = new LambdaQueryWrapper<Post>()
                .eq(Post::getStatus, 0);
        if (boardId != null) {
            wrapper.eq(Post::getBoardId, boardId);
        }
        if (postIds != null) {
            wrapper.in(Post::getId, postIds);
        }
        if ("hot".equalsIgnoreCase(sort)) {
            wrapper.orderByDesc(Post::getLikeCount).orderByDesc(Post::getViewCount);
        } else {
            wrapper.orderByDesc(Post::getCreatedAt);
        }
        wrapper.orderByDesc(Post::getId);

        Page<Post> result = postMapper.selectPage(
                new Page<>(Math.max(1, page), Math.max(1, Math.min(size, 50))), wrapper);
        List<Post> posts = result.getRecords();
        if (posts.isEmpty()) {
            return List.of();
        }
        Map<Long, Board> boards = boardMap(posts);
        Map<Long, List<String>> tags = loadTagNames(posts.stream().map(Post::getId).toList());
        Map<Long, String> authors = nicknameMap(posts.stream().map(Post::getAuthorId).toList());

        List<PostVO> list = new ArrayList<>();
        for (Post p : posts) {
            PostVO vo = toVO(p, boards.get(p.getBoardId()), tags, userId);
            list.add(new PostVO(vo.id(), vo.boardId(), vo.boardName(), vo.authorId(),
                    authors.get(p.getAuthorId()), vo.title(), null, excerpt(p.getBody()),
                    vo.status(), vo.viewCount(), vo.likeCount(), vo.favoriteCount(),
                    vo.createdAt(), vo.tags(), vo.liked(), vo.favorited()));
        }
        return list;
    }

    @Transactional
    public PostVO detail(Long userId, Long postId) {
        Post post = requireVisible(userId, postId);
        postMapper.update(null, new LambdaUpdateWrapper<Post>()
                .eq(Post::getId, postId)
                .setSql("view_count = view_count + 1"));
        post.setViewCount(post.getViewCount() + 1);
        return toVO(post, boardMapper.selectById(post.getBoardId()),
                loadTagNames(List.of(postId)), userId);
    }

    @Transactional
    public ReplyVO addReply(Long userId, Long postId, CreateReplyRequest request) {
        Post post = requireVisible(userId, postId);
        if (post.getStatus() != null && post.getStatus() != 0) {
            throw new BizException(ErrorCode.FORBIDDEN, "该帖子不可回复");
        }
        if (request.parentReplyId() != null) {
            Reply parent = replyMapper.selectById(request.parentReplyId());
            if (parent == null || !parent.getPostId().equals(postId)) {
                throw new BizException(ErrorCode.PARAM_ERROR, "父回帖不属于该帖子");
            }
        }
        Reply reply = new Reply();
        reply.setPostId(postId);
        reply.setAuthorId(userId);
        reply.setParentReplyId(request.parentReplyId());
        reply.setContent(request.content());
        reply.setLikeCount(0);
        reply.setStatus(0);
        reply.setCreatedAt(LocalDateTime.now());
        replyMapper.insert(reply);
        return toReplyVO(reply, nicknameOf(userId));
    }

    public List<ReplyVO> replies(Long postId, int page, int size) {
        if (postMapper.selectById(postId) == null) {
            throw new BizException(ErrorCode.NOT_FOUND, "帖子不存在");
        }
        Page<Reply> result = replyMapper.selectPage(
                new Page<>(Math.max(1, page), Math.max(1, Math.min(size, 50))),
                new LambdaQueryWrapper<Reply>()
                        .eq(Reply::getPostId, postId)
                        .eq(Reply::getStatus, 0)
                        .orderByAsc(Reply::getId));
        List<Reply> rows = result.getRecords();
        Map<Long, String> authors = nicknameMap(rows.stream().map(Reply::getAuthorId).toList());
        return rows.stream().map(r -> toReplyVO(r, authors.get(r.getAuthorId()))).toList();
    }

    /** 事务提交后再触发 AI 处理，避免异步线程读不到新帖。 */
    private void submitAiAfterCommit(Long postId) {
        if (TransactionSynchronizationManager.isSynchronizationActive()) {
            TransactionSynchronizationManager.registerSynchronization(
                    new TransactionSynchronization() {
                        @Override
                        public void afterCommit() {
                            aiAsyncProcessor.submit(postId);
                        }
                    });
        } else {
            aiAsyncProcessor.submit(postId);
        }
    }

    // ------------------------------------------------------------ 内部方法

    Post requireVisible(Long userId, Long postId) {
        Post post = postMapper.selectById(postId);
        if (post == null) {
            throw new BizException(ErrorCode.NOT_FOUND, "帖子不存在");
        }
        if (post.getStatus() != null && post.getStatus() != 0
                && !post.getAuthorId().equals(userId)) {
            throw new BizException(ErrorCode.NOT_FOUND, "帖子不存在或未通过审核");
        }
        return post;
    }

    private void bindTags(Long postId, List<Long> tagIds) {
        if (tagIds == null || tagIds.isEmpty()) {
            return;
        }
        List<Long> valid = tagMapper.selectList(new LambdaQueryWrapper<Tag>()
                        .in(Tag::getId, tagIds))
                .stream().map(Tag::getId).toList();
        for (Long tagId : valid) {
            PostTag link = new PostTag();
            link.setPostId(postId);
            link.setTagId(tagId);
            link.setSource(1);
            link.setCreatedAt(LocalDateTime.now());
            postTagMapper.insert(link);
        }
    }

    private Map<Long, List<String>> loadTagNames(List<Long> postIds) {
        Map<Long, List<String>> result = new LinkedHashMap<>();
        if (postIds.isEmpty()) {
            return result;
        }
        List<PostTag> links = postTagMapper.selectList(
                new LambdaQueryWrapper<PostTag>().in(PostTag::getPostId, postIds));
        if (links.isEmpty()) {
            return result;
        }
        Map<Long, String> names = tagMapper.selectList(new LambdaQueryWrapper<Tag>()
                        .in(Tag::getId, links.stream().map(PostTag::getTagId).distinct().toList()))
                .stream().collect(Collectors.toMap(Tag::getId, Tag::getName));
        for (PostTag link : links) {
            result.computeIfAbsent(link.getPostId(), k -> new ArrayList<>())
                    .add(names.getOrDefault(link.getTagId(), String.valueOf(link.getTagId())));
        }
        return result;
    }

    private Map<Long, Board> boardMap(List<Post> posts) {
        List<Long> ids = posts.stream().map(Post::getBoardId).distinct().toList();
        return boardMapper.selectList(new LambdaQueryWrapper<Board>().in(Board::getId, ids))
                .stream().collect(Collectors.toMap(Board::getId, b -> b));
    }

    private Map<Long, String> nicknameMap(List<Long> userIds) {
        if (userIds.isEmpty()) {
            return Map.of();
        }
        return userMapper.selectList(new LambdaQueryWrapper<User>()
                        .in(User::getId, userIds.stream().distinct().toList()))
                .stream().collect(Collectors.toMap(User::getId, User::getNickname));
    }

    private String nicknameOf(Long userId) {
        User u = userMapper.selectById(userId);
        return u == null ? null : u.getNickname();
    }

    private String excerpt(String body) {
        if (body == null) {
            return null;
        }
        return body.length() <= MAX_BODY_IN_LIST ? body : body.substring(0, MAX_BODY_IN_LIST) + "…";
    }

    private ReplyVO toReplyVO(Reply r, String nickname) {
        return new ReplyVO(r.getId(), r.getPostId(), r.getAuthorId(), nickname,
                r.getParentReplyId(), r.getContent(), r.getLikeCount(), r.getCreatedAt());
    }

    private PostVO toVO(Post p, Board board, Map<Long, List<String>> tags, Long userId) {
        boolean liked = interactionService.liked(userId, 2, p.getId());
        boolean favorited = interactionService.favorited(userId, p.getId());
        return new PostVO(p.getId(), p.getBoardId(), board == null ? null : board.getName(),
                p.getAuthorId(), nicknameOf(p.getAuthorId()), p.getTitle(), p.getBody(), excerpt(p.getBody()),
                p.getStatus(), p.getViewCount(), p.getLikeCount(), p.getFavoriteCount(),
                p.getCreatedAt(), tags.getOrDefault(p.getId(), List.of()), liked, favorited);
    }
}
"""

F["blog/service/InteractionService.java"] = """package com.zhiyu.campus.blog.service;

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
"""

# -------------------------------------------------------------- controller
F["blog/controller/PostController.java"] = """package com.zhiyu.campus.blog.controller;

import com.zhiyu.campus.blog.dto.CreatePostRequest;
import com.zhiyu.campus.blog.dto.CreateReplyRequest;
import com.zhiyu.campus.blog.dto.ToggleRequest;
import com.zhiyu.campus.blog.service.InteractionService;
import com.zhiyu.campus.blog.service.PostService;
import com.zhiyu.campus.blog.vo.PostVO;
import com.zhiyu.campus.blog.vo.ReplyVO;
import com.zhiyu.campus.blog.vo.ToggleResultVO;
import com.zhiyu.campus.common.ApiResponse;
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

@Tag(name = "博客")
@RestController
@RequestMapping("/api/v1/posts")
public class PostController {

    private final PostService postService;
    private final InteractionService interactionService;

    public PostController(PostService postService, InteractionService interactionService) {
        this.postService = postService;
        this.interactionService = interactionService;
    }

    @Operation(summary = "A-12 帖子列表（板块/标签/热度）")
    @GetMapping
    public ApiResponse<List<PostVO>> list(@RequestParam(required = false) Long boardId,
                                          @RequestParam(required = false) Long tagId,
                                          @RequestParam(defaultValue = "latest") String sort,
                                          @RequestParam(defaultValue = "1") int page,
                                          @RequestParam(defaultValue = "20") int size) {
        return ApiResponse.ok(postService.list(CurrentUser.id(), boardId, tagId, sort, page, size));
    }

    @Operation(summary = "A-13 发帖")
    @PostMapping
    public ApiResponse<PostVO> create(@Valid @RequestBody CreatePostRequest request) {
        return ApiResponse.ok(postService.create(CurrentUser.id(), request));
    }

    @Operation(summary = "A-14 帖子详情（浏览数 +1）")
    @GetMapping("/{id}")
    public ApiResponse<PostVO> detail(@PathVariable Long id) {
        return ApiResponse.ok(postService.detail(CurrentUser.id(), id));
    }

    @Operation(summary = "A-15 回帖")
    @PostMapping("/{id}/replies")
    public ApiResponse<ReplyVO> reply(@PathVariable Long id,
                                      @Valid @RequestBody CreateReplyRequest request) {
        return ApiResponse.ok(postService.addReply(CurrentUser.id(), id, request));
    }

    @Operation(summary = "回帖列表")
    @GetMapping("/{id}/replies")
    public ApiResponse<List<ReplyVO>> replies(@PathVariable Long id,
                                              @RequestParam(defaultValue = "1") int page,
                                              @RequestParam(defaultValue = "20") int size) {
        return ApiResponse.ok(postService.replies(id, page, size));
    }

    @Operation(summary = "A-16 点赞 / 取消（幂等）")
    @PostMapping("/{id}/like")
    public ApiResponse<ToggleResultVO> like(@PathVariable Long id,
                                            @RequestBody(required = false) ToggleRequest request) {
        boolean liked = request == null || request.target();
        return ApiResponse.ok(interactionService.like(CurrentUser.id(), id, liked));
    }

    @Operation(summary = "A-17 收藏 / 取消（幂等）")
    @PostMapping("/{id}/favorite")
    public ApiResponse<ToggleResultVO> favorite(@PathVariable Long id,
                                                @RequestBody(required = false) ToggleRequest request) {
        boolean favorited = request == null || request.target();
        return ApiResponse.ok(interactionService.favorite(CurrentUser.id(), id, favorited));
    }
}
"""

F["blog/controller/BoardController.java"] = """package com.zhiyu.campus.blog.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.zhiyu.campus.blog.entity.Board;
import com.zhiyu.campus.blog.mapper.BoardMapper;
import com.zhiyu.campus.blog.vo.BoardVO;
import com.zhiyu.campus.common.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@Tag(name = "板块")
@RestController
@RequestMapping("/api/v1/boards")
public class BoardController {

    private final BoardMapper boardMapper;

    public BoardController(BoardMapper boardMapper) {
        this.boardMapper = boardMapper;
    }

    @Operation(summary = "板块列表")
    @GetMapping
    public ApiResponse<List<BoardVO>> list() {
        List<BoardVO> boards = boardMapper.selectList(new LambdaQueryWrapper<Board>()
                        .orderByAsc(Board::getSortNo))
                .stream().map(b -> new BoardVO(b.getId(), b.getName(), b.getIntro(), b.getSortNo()))
                .toList();
        return ApiResponse.ok(boards);
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
