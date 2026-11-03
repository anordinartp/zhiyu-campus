package com.zhiyu.campus.ai.controller;

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
