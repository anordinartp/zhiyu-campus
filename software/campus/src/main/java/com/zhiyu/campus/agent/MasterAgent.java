package com.zhiyu.campus.agent;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.zhiyu.campus.agent.dto.AgentRequest;
import com.zhiyu.campus.agent.vo.AgentReply;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

/**
 * 总 agent：先判断意图属于哪个域，再交给对应子 agent 执行。
 *
 * 两种路由方式：
 *   1) 配了模型密钥：让模型输出 {"agent":"chat|post|search"}，严格 JSON
 *   2) 没配或调用失败：关键词规则兜底
 * 无论哪种，最终动作都由子 agent 调用真实业务服务完成，模型不直接碰数据库。
 */
@Service
public class MasterAgent {

    private static final Logger log = LoggerFactory.getLogger(MasterAgent.class);
    private static final String SYSTEM =
            "你是校园社区平台的路由器。判断用户请求属于哪个域，只输出一行 JSON。\n"
            + "可选域：\n"
            + "  chat   聊天室：查房间、加入房间、发消息、看聊天记录\n"
            + "  post   帖子：浏览帖子、发帖、回帖\n"
            + "  search 搜索：查找内容、按关键词检索\n"
            + "输出格式：第一个字段名为 agent，值取 chat、post、search 之一。\n"
            + "不要输出解释，不要加代码块标记。";

    private final ChatSubAgent chatAgent;
    private final PostSubAgent postAgent;
    private final SearchSubAgent searchAgent;
    private final LlmClient llm;
    private final ObjectMapper mapper = new ObjectMapper();

    public MasterAgent(ChatSubAgent chatAgent, PostSubAgent postAgent,
                       SearchSubAgent searchAgent, LlmClient llm) {
        this.chatAgent = chatAgent;
        this.postAgent = postAgent;
        this.searchAgent = searchAgent;
        this.llm = llm;
    }

    public AgentReply handle(Long userId, AgentRequest request) {
        String text = request.message().trim();
        List<String> trace = new ArrayList<>();
        String agent = routeByLlm(text, trace);
        if (agent == null) {
            agent = routeByRules(text);
            trace.add("router:rules->" + agent);
        } else {
            trace.add("router:llm->" + agent);
        }
        trace.add("model:" + (llm.available() ? llm.model() : "local-rules"));

        AgentReply reply = switch (agent) {
            case "chat" -> chatAgent.handle(userId, text);
            case "post" -> postAgent.handle(userId, text);
            default -> searchAgent.handle(userId, text);
        };
        return new AgentReply(reply.agent(), reply.action(), reply.reply(), reply.data(), trace);
    }

    private String routeByLlm(String text, List<String> trace) {
        if (!llm.available()) {
            return null;
        }
        String out = llm.chat(SYSTEM, text);
        if (out == null) {
            trace.add("llm:failed");
            return null;
        }
        try {
            String json = out.trim().replaceAll("^```(json)?", "").replaceAll("```$", "").trim();
            JsonNode node = mapper.readTree(json);
            String agent = node.path("agent").asText("").trim();
            return switch (agent) {
                case "chat", "post", "search" -> agent;
                default -> null;
            };
        } catch (Exception e) {
            log.warn("路由 JSON 解析失败：{}", out);
            return null;
        }
    }

    private String routeByRules(String text) {
        String t = text.toLowerCase();
        if (t.matches(".*(聊天室|房间|群聊|消息|发言|禁言|自习室).*")
                || t.matches(".*(在|给).{1,20}(说|发).*")) {
            return "chat";
        }
        if (t.matches(".*(帖子|发帖|回帖|楼主|博客).*")) {
            return "post";
        }
        return "search";
    }

    public boolean llmAvailable() {
        return llm.available();
    }

    public String modelName() {
        return llm.available() ? llm.model() : "local-rules";
    }
}
