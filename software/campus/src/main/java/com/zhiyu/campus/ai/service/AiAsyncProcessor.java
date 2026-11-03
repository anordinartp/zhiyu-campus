package com.zhiyu.campus.ai.service;

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
