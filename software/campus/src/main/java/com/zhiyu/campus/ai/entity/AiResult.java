package com.zhiyu.campus.ai.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/** 对应表 16 ai_result，message_id 与 post_id 二者取一。 */
@Data
@TableName("ai_result")
public class AiResult {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long messageId;

    private Long postId;

    private String summary;

    /** 1 正面 0 中性 -1 负面 */
    private Integer sentiment;

    private Boolean violation;

    private BigDecimal confidence;

    private LocalDateTime processedAt;
}
