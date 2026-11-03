package com.zhiyu.campus.blog.service;

import org.springframework.stereotype.Component;

import java.util.List;

/**
 * 敏感词规则检查，对应报告 8.3.3 表 27 第一条：
 * 命中规则库的内容直接置为待审，不自动删除。
 * 生产环境应改为可配置词库 + 前缀树，这里用最小实现保证行为可演示。
 */
@Component
public class SensitiveWordChecker {

    private static final List<String> WORDS = List.of("代写", "代考", "赌博", "毒品", "枪");

    public String firstHit(String text) {
        if (text == null) {
            return null;
        }
        for (String w : WORDS) {
            if (text.contains(w)) {
                return w;
            }
        }
        return null;
    }
}
