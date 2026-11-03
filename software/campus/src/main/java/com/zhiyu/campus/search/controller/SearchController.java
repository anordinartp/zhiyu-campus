package com.zhiyu.campus.search.controller;

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
