package com.zhiyu.campus.review.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/** 审核日志表 review_log（实现阶段补充，见报告说明）。 */
@Data
@TableName("review_log")
public class ReviewLog {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Integer targetType;

    private Long targetId;

    private Long operatorId;

    /** 1 通过 2 删除 */
    private Integer action;

    private String remark;

    private LocalDateTime createdAt;
}
