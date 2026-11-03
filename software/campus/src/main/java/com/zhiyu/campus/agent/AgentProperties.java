package com.zhiyu.campus.agent;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.DefaultValue;

/**
 * 模型接入配置。
 * 不配 api-key 时自动使用本地规则，功能仍然可用（答辩断网也能演示）。
 * 配置示例（环境变量优先）：
 *   AI_API_KEY=sk-xxx  AI_MODEL=deepseek-chat  AI_BASE_URL=https://api.deepseek.com/v1
 */
@ConfigurationProperties(prefix = "app.agent")
public record AgentProperties(
        @DefaultValue("false") boolean llmEnabled,
        @DefaultValue("") String apiKey,
        @DefaultValue("https://api.deepseek.com/v1") String baseUrl,
        @DefaultValue("deepseek-chat") String model,
        @DefaultValue("20") int timeoutSeconds) {

    /** 有密钥且开关打开才算可用。 */
    public boolean usable() {
        return llmEnabled && apiKey != null && !apiKey.isBlank();
    }
}
