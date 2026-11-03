# -*- coding: utf-8 -*-
"""生成 M6「AI 智能体编排」模块：总 agent + 三个子 agent。

设计：
  - LlmClient：OpenAI 兼容接口（DeepSeek 等），无密钥时自动降级
  - MasterAgent：判断该交给哪个子 agent
  - ChatSubAgent / PostSubAgent / SearchSubAgent：各自调用已有的业务服务
"""
import os

ROOT = (r"C:\Users\saxtul\Documents\ds harness区\知屿校园\software\campus"
        r"\src\main\java\com\zhiyu\campus")
F = {}

F["agent/AgentProperties.java"] = """package com.zhiyu.campus.agent;

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
"""

F["agent/LlmClient.java"] = """package com.zhiyu.campus.agent;

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
"""

F["agent/vo/AgentReply.java"] = """package com.zhiyu.campus.agent.vo;

import java.util.List;
import java.util.Map;

/** 智能体回复：说明交给哪个子 agent、做了什么、返回了什么数据。 */
public record AgentReply(
        String agent,
        String action,
        String reply,
        Map<String, Object> data,
        List<String> trace) {
}
"""

F["agent/dto/AgentRequest.java"] = """package com.zhiyu.campus.agent.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/** 与总 agent 对话的入参。 */
public record AgentRequest(
        @NotBlank(message = "不能为空")
        @Size(max = 500, message = "长度不能超过 500")
        String message) {
}
"""

F["agent/ChatSubAgent.java"] = """package com.zhiyu.campus.agent;

import com.zhiyu.campus.chat.dto.SendMessageRequest;
import com.zhiyu.campus.chat.service.ChatRoomService;
import com.zhiyu.campus.chat.service.MessageService;
import com.zhiyu.campus.chat.vo.MessagePageVO;
import com.zhiyu.campus.chat.vo.RoomVO;
import com.zhiyu.campus.agent.vo.AgentReply;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** 聊天室子 agent：查房间、进房间、发消息、看消息。 */
@Component
public class ChatSubAgent {

    private static final Pattern SEND = Pattern.compile("(?:在|给)(.{1,20}?)(?:说|发|发消息)[：: ]+(.+)");

    private final ChatRoomService roomService;
    private final MessageService messageService;

    public ChatSubAgent(ChatRoomService roomService, MessageService messageService) {
        this.roomService = roomService;
        this.messageService = messageService;
    }

    public AgentReply handle(Long userId, String text) {
        try {
            Matcher m = SEND.matcher(text);
            if (m.find()) {
                return send(userId, m.group(1).trim(), m.group(2).trim());
            }
            if (text.matches(".*(加入|进入).*")) {
                return join(userId, text.replaceAll(".*(加入|进入)", "").trim());
            }
            if (text.matches(".*(消息|聊天记录).*")) {
                return readMessages(userId, text);
            }
            return listRooms(userId);
        } catch (Exception e) {
            return new AgentReply("chat", "error", "聊天室操作失败：" + e.getMessage(),
                    Map.of(), List.of("chat"));
        }
    }

    private AgentReply listRooms(Long userId) {
        List<RoomVO> rooms = roomService.list(userId, null, 1, 5);
        StringBuilder sb = new StringBuilder("当前有 " + rooms.size() + " 个聊天室：");
        List<Map<String, Object>> items = new ArrayList<>();
        for (RoomVO r : rooms) {
            sb.append("「").append(r.name()).append("」(").append(r.memberCount()).append(" 人) ");
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("id", r.id());
            item.put("name", r.name());
            item.put("memberCount", r.memberCount());
            item.put("tags", r.tags());
            items.add(item);
        }
        sb.append("。想看某个房间的消息，对我说“看 XX 的消息”。");
        return new AgentReply("chat", "listRooms", sb.toString(), Map.of("rooms", items), List.of("chat"));
    }

    private AgentReply join(Long userId, String roomName) {
        List<RoomVO> rooms = roomService.list(userId, null, 1, 50);
        for (RoomVO r : rooms) {
            if (roomName.isEmpty() || r.name().contains(roomName) || roomName.contains(r.name())) {
                roomService.join(userId, r.id());
                return new AgentReply("chat", "joinRoom", "已加入「" + r.name() + "」。",
                        Map.of("roomId", r.id(), "roomName", r.name()), List.of("chat"));
            }
        }
        return new AgentReply("chat", "joinRoom", "没找到叫「" + roomName + "」的聊天室。",
                Map.of(), List.of("chat"));
    }

    private AgentReply send(Long userId, String roomName, String content) {
        List<RoomVO> rooms = roomService.list(userId, null, 1, 50);
        for (RoomVO r : rooms) {
            if (r.name().contains(roomName) || roomName.contains(r.name())) {
                messageService.send(userId, r.id(), new SendMessageRequest(1, content));
                return new AgentReply("chat", "sendMessage",
                        "已在「" + r.name() + "」发出：" + content,
                        Map.of("roomId", r.id(), "content", content), List.of("chat"));
            }
        }
        return new AgentReply("chat", "sendMessage", "没找到叫「" + roomName + "」的聊天室。",
                Map.of(), List.of("chat"));
    }

    private AgentReply readMessages(Long userId, String text) {
        List<RoomVO> rooms = roomService.list(userId, null, 1, 50);
        for (RoomVO r : rooms) {
            if (text.contains(r.name())) {
                MessagePageVO page = messageService.history(userId, r.id(), null, 5);
                StringBuilder sb = new StringBuilder("「" + r.name() + "」最近 " + page.items().size() + " 条消息：");
                for (var msg : page.items()) {
                    sb.append(msg.senderNickname()).append("：").append(msg.content()).append("；");
                }
                return new AgentReply("chat", "readMessages", sb.toString(),
                        Map.of("roomId", r.id(), "count", page.items().size()), List.of("chat"));
            }
        }
        return listRooms(userId);
    }
}
"""

F["agent/PostSubAgent.java"] = """package com.zhiyu.campus.agent;

import com.zhiyu.campus.agent.vo.AgentReply;
import com.zhiyu.campus.blog.dto.CreatePostRequest;
import com.zhiyu.campus.blog.dto.CreateReplyRequest;
import com.zhiyu.campus.blog.entity.Board;
import com.zhiyu.campus.blog.mapper.BoardMapper;
import com.zhiyu.campus.blog.service.PostService;
import com.zhiyu.campus.blog.vo.PostVO;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** 帖子子 agent：浏览、发帖、回帖。 */
@Component
public class PostSubAgent {

    private static final Pattern POST = Pattern.compile("标题[：:]([^，,。]+)[，,。]?\\\\s*内容[：:](.+)", Pattern.DOTALL);
    private static final Pattern REPLY = Pattern.compile("帖子\\\\s*(\\\\d+).*?内容[：:](.+)", Pattern.DOTALL);

    private final PostService postService;
    private final BoardMapper boardMapper;

    public PostSubAgent(PostService postService, BoardMapper boardMapper) {
        this.postService = postService;
        this.boardMapper = boardMapper;
    }

    public AgentReply handle(Long userId, String text) {
        try {
            Matcher reply = REPLY.matcher(text);
            if (reply.find()) {
                Long postId = Long.valueOf(reply.group(1));
                postService.addReply(userId, postId, new CreateReplyRequest(reply.group(2).trim(), null));
                return new AgentReply("post", "addReply",
                        "已在帖子 " + postId + " 下回帖。",
                        Map.of("postId", postId), List.of("post"));
            }
            Matcher post = POST.matcher(text);
            if (post.find()) {
                return createPost(userId, post.group(1).trim(), post.group(2).trim());
            }
            if (text.matches(".*(发帖|发布).*")) {
                String body = text.replaceAll(".*(发帖|发布)", "").trim();
                String title = body.length() > 20 ? body.substring(0, 20) : body;
                return createPost(userId, title, body);
            }
            return listPosts(userId);
        } catch (Exception e) {
            return new AgentReply("post", "error", "帖子操作失败：" + e.getMessage(),
                    Map.of(), List.of("post"));
        }
    }

    private AgentReply createPost(Long userId, String title, String body) {
        Board board = boardMapper.selectList(new LambdaQueryWrapper<Board>()
                .orderByAsc(Board::getSortNo).last("limit 1")).stream().findFirst().orElse(null);
        if (board == null) {
            return new AgentReply("post", "createPost", "系统里还没有板块，无法发帖。",
                    Map.of(), List.of("post"));
        }
        PostVO vo = postService.create(userId, new CreatePostRequest(board.getId(), title, body, List.of()));
        String extra = vo.status() != null && vo.status() == 1 ? "（内容含敏感词，已进入待审）" : "";
        return new AgentReply("post", "createPost",
                "已发布到「" + board.getName() + "」：" + title + extra,
                Map.of("postId", vo.id(), "status", vo.status()), List.of("post"));
    }

    private AgentReply listPosts(Long userId) {
        List<PostVO> posts = postService.list(userId, null, null, "latest", 1, 5);
        StringBuilder sb = new StringBuilder("最新 " + posts.size() + " 篇帖子：");
        List<Map<String, Object>> items = new ArrayList<>();
        for (PostVO p : posts) {
            sb.append("「").append(p.title()).append("」");
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("id", p.id());
            item.put("title", p.title());
            item.put("likeCount", p.likeCount());
            items.add(item);
        }
        sb.append("。想看详情可以搜索标题。");
        return new AgentReply("post", "listPosts", sb.toString(), Map.of("posts", items), List.of("post"));
    }
}
"""

F["agent/SearchSubAgent.java"] = """package com.zhiyu.campus.agent;

import com.zhiyu.campus.agent.vo.AgentReply;
import com.zhiyu.campus.search.service.SearchService;
import com.zhiyu.campus.search.vo.SearchItemVO;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** 搜索子 agent：把自然语言变成检索，并解释排序。 */
@Component
public class SearchSubAgent {

    private final SearchService searchService;

    public SearchSubAgent(SearchService searchService) {
        this.searchService = searchService;
    }

    public AgentReply handle(Long userId, String text) {
        String keyword = text.replaceAll("(?i)(帮我|请|搜索一下|搜索|搜一下|搜|查找|找一下|找|查一下|查询)", "").trim();
        if (keyword.isEmpty()) {
            keyword = text.trim();
        }
        try {
            List<SearchItemVO> items = searchService.search(userId, keyword, null, 5);
            if (items.isEmpty()) {
                return new AgentReply("search", "search",
                        "没有找到和「" + keyword + "」相关的内容。",
                        Map.of("keyword", keyword, "count", 0), List.of("search"));
            }
            StringBuilder sb = new StringBuilder("「" + keyword + "」找到 " + items.size() + " 条：");
            List<Map<String, Object>> rows = new ArrayList<>();
            for (SearchItemVO it : items) {
                sb.append("《").append(it.title()).append("》(")
                  .append("score ").append(it.score()).append(") ");
                Map<String, Object> row = new LinkedHashMap<>();
                row.put("type", it.type());
                row.put("id", it.id());
                row.put("title", it.title());
                row.put("score", it.score());
                row.put("rel", it.rel());
                row.put("heat", it.heat());
                row.put("pref", it.pref());
                rows.add(row);
            }
            sb.append("。排序 = 0.5×相关度 + 0.3×热度 + 0.2×你的偏好。");
            return new AgentReply("search", "search", sb.toString(),
                    Map.of("keyword", keyword, "items", rows), List.of("search"));
        } catch (Exception e) {
            return new AgentReply("search", "error", "检索失败：" + e.getMessage(),
                    Map.of(), List.of("search"));
        }
    }
}
"""

F["agent/MasterAgent.java"] = """package com.zhiyu.campus.agent;

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
            "你是校园社区平台的路由器。判断用户请求属于哪个域，只输出一行 JSON。\\n"
            + "可选域：\\n"
            + "  chat   聊天室：查房间、加入房间、发消息、看聊天记录\\n"
            + "  post   帖子：浏览帖子、发帖、回帖\\n"
            + "  search 搜索：查找内容、按关键词检索\\n"
            + "输出格式：第一个字段名为 agent，值取 chat、post、search 之一。\\n"
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
"""

F["agent/AgentController.java"] = """package com.zhiyu.campus.agent;

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
