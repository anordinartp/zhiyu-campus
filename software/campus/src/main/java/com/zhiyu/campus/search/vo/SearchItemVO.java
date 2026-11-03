package com.zhiyu.campus.search.vo;

import java.util.List;

/**
 * 检索结果项。score 与三个分项都返回，便于解释“为什么排在这里”。
 */
public record SearchItemVO(
        String type,
        Long id,
        String title,
        String excerpt,
        double score,
        double rel,
        double heat,
        double pref,
        List<String> tags) {
}
