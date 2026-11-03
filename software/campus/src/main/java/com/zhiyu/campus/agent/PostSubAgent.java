package com.zhiyu.campus.agent;

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

    private static final Pattern POST = Pattern.compile("标题[：:]([^，,。]+)[，,。]?\\s*内容[：:](.+)", Pattern.DOTALL);
    private static final Pattern REPLY = Pattern.compile("帖子\\s*(\\d+).*?内容[：:](.+)", Pattern.DOTALL);

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
