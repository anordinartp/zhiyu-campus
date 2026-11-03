package com.zhiyu.campus.agent;

import com.zhiyu.campus.agent.dto.AgentRequest;
import com.zhiyu.campus.agent.vo.AgentReply;
import com.zhiyu.campus.common.ApiResponse;
import com.zhiyu.campus.security.CurrentUser;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@Tag(name = "AI 智能体")
@RestController
@RequestMapping("/api/v1/agent")
public class AgentController {

    private final MasterAgent masterAgent;

    public AgentController(MasterAgent masterAgent) {
        this.masterAgent = masterAgent;
    }

    @Operation(summary = "与总 agent 对话：自动路由到聊天室 / 帖子 / 搜索子 agent")
    @PostMapping("/chat")
    public ApiResponse<AgentReply> chat(@Valid @RequestBody AgentRequest request) {
        return ApiResponse.ok(masterAgent.handle(CurrentUser.id(), request));
    }

    @Operation(summary = "查看当前使用的模型与可用能力")
    @GetMapping("/info")
    public ApiResponse<Map<String, Object>> info() {
        return ApiResponse.ok(Map.of(
                "llmAvailable", masterAgent.llmAvailable(),
                "model", masterAgent.modelName(),
                "subAgents", java.util.List.of("chat", "post", "search")));
    }
}
