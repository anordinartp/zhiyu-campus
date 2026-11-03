package com.zhiyu.campus.ai.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;

/** 对应关联表 ai_result_tag。 */
@Data
@TableName("ai_result_tag")
public class AiResultTag {

    private Long resultId;

    private Long tagId;

    private BigDecimal confidence;

    /** 1 模型自动 2 人工修正 */
    private Integer source;
}
