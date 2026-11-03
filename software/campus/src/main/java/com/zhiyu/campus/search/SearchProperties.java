package com.zhiyu.campus.search;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.DefaultValue;

/**
 * 检索参数，对应报告表 26。权重放在配置里，答辩时可以现场改数值演示排序变化。
 */
@ConfigurationProperties(prefix = "app.search")
public record SearchProperties(
        @DefaultValue("0.5") double relWeight,
        @DefaultValue("0.3") double heatWeight,
        @DefaultValue("0.2") double prefWeight,
        @DefaultValue("0.05") double recencyLambda,
        @DefaultValue("200") int recallLimit,
        @DefaultValue("20") int defaultLimit) {
}
