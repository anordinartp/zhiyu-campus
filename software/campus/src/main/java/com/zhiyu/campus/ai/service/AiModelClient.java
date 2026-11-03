package com.zhiyu.campus.ai.service;

import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 大模型调用的本地替身（mock）。
 *
 * 真实实现应调用外部大模型 API，契约见报告表 22。
 * 这里用确定性规则模拟，保证离线可演示、结果可复现：
 *   - 摘要：取正文前 60 字
 *   - 情感：命中正/负面词表
 *   - 违规：命中明确违规词给高置信，命中灰色词给中等置信
 *   - 标签：按关键词映射到已有标签
 *
 * 替换点：把本类换成 HTTP 调用即可，上层 AiAgentService 不需要改动。
 */
@Component
public class AiModelClient {

    private static final List<String> POSITIVE = List.of("谢谢", "感谢", "不错", "赞", "有用", "分享");
    private static final List<String> NEGATIVE = List.of("垃圾", "骗", "坑", "差评", "投诉");

    /** 明确违规，置信度 0.92 */
    private static final List<String> HARD_VIOLATION =
            List.of("代写", "代考", "赌博", "毒品", "枪", "色情", "诈骗");
    /** 灰色信号，置信度 0.65，进入低置信复核 */
    private static final List<String> SOFT_VIOLATION =
            List.of("收费", "私聊报价", "包过", "内部渠道");

    private static final Map<String, String> TAG_KEYWORDS = new LinkedHashMap<>();

    static {
        TAG_KEYWORDS.put("考研", "考研");
        TAG_KEYWORDS.put("选课", "选课");
        TAG_KEYWORDS.put("实习", "实习");
        TAG_KEYWORDS.put("社团", "社团");
        TAG_KEYWORDS.put("二手", "二手");
        TAG_KEYWORDS.put("求助", "求助");
        TAG_KEYWORDS.put("高数", "考研");
        TAG_KEYWORDS.put("期末", "选课");
    }

    public ModelOutput analyze(String title, String body) {
        String text = (title == null ? "" : title) + (body == null ? "" : body);

        String summary = body == null ? "" : body.strip();
        if (summary.length() > 60) {
            summary = summary.substring(0, 60) + "…";
        }

        int sentiment = 0;
        if (POSITIVE.stream().anyMatch(text::contains)) {
            sentiment = 1;
        } else if (NEGATIVE.stream().anyMatch(text::contains)) {
            sentiment = -1;
        }

        boolean violation = false;
        double confidence = 0.05;
        if (HARD_VIOLATION.stream().anyMatch(text::contains)) {
            violation = true;
            confidence = 0.92;
        } else if (SOFT_VIOLATION.stream().anyMatch(text::contains)) {
            violation = true;
            confidence = 0.65;
        }

        List<String> tagNames = new ArrayList<>();
        TAG_KEYWORDS.forEach((kw, tag) -> {
            if (text.contains(kw) && !tagNames.contains(tag)) {
                tagNames.add(tag);
            }
        });

        return new ModelOutput(summary, sentiment, violation, confidence, tagNames);
    }

    public record ModelOutput(String summary, int sentiment, boolean violation,
                              double confidence, List<String> tagNames) {
    }
}
