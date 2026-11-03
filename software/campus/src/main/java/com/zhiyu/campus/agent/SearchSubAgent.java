package com.zhiyu.campus.agent;

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
