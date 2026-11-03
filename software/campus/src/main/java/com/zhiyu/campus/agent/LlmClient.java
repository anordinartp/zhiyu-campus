package com.zhiyu.campus.agent;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.time.Duration;
import java.util.List;
import java.util.Map;

/**
 * OpenAI 兼容的对话补全客户端（DeepSeek / 通义 / Moonshot 等都是这个协议）。
 * 任何异常都返回 null，由上层降级到本地规则——模型不可用不能拖垮业务。
 */
@Component
public class LlmClient {

    private static final Logger log = LoggerFactory.getLogger(LlmClient.class);

    private final AgentProperties props;
    private final ObjectMapper mapper = new ObjectMapper();
    private final RestClient client;

    public LlmClient(AgentProperties props) {
        this.props = props;
        this.client = RestClient.builder()
                .baseUrl(props.baseUrl())
                .requestFactory(new org.springframework.http.client.SimpleClientHttpRequestFactory() {{
                    setConnectTimeout((int) Duration.ofSeconds(5).toMillis());
                    setReadTimeout((int) Duration.ofSeconds(props.timeoutSeconds()).toMillis());
                }})
                .build();
    }

    public boolean available() {
        return props.usable();
    }

    public String model() {
        return props.model();
    }

    /** 返回模型文本；失败返回 null。 */
    public String chat(String system, String user) {
        if (!props.usable()) {
            return null;
        }
        try {
            Map<String, Object> body = Map.of(
                    "model", props.model(),
                    "temperature", 0.1,
                    "messages", List.of(
                            Map.of("role", "system", "content", system),
                            Map.of("role", "user", "content", user)));
            String raw = client.post()
                    .uri("/chat/completions")
                    .contentType(MediaType.APPLICATION_JSON)
                    .header("Authorization", "Bearer " + props.apiKey())
                    .body(body)
                    .retrieve()
                    .body(String.class);
            JsonNode node = mapper.readTree(raw);
            return node.path("choices").path(0).path("message").path("content").asText(null);
        } catch (Exception e) {
            log.warn("模型调用失败，降级到本地规则：{}", e.getMessage());
            return null;
        }
    }
}
