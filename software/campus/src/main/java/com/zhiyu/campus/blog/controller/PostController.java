package com.zhiyu.campus.blog.controller;

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
