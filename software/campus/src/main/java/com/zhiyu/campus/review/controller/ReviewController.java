package com.zhiyu.campus.review.controller;

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
