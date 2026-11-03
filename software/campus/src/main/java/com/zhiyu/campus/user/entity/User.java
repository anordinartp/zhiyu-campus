package com.zhiyu.campus.user.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/** 对应表 9 用户表 user。 */
@Data
@TableName("user")
public class User {

    @TableId(type = IdType.AUTO)
    private Long id;

    /** 学号/工号，登录名 */
    private String account;

    private String nickname;

    /** 口令哈希（BCrypt） */
    private String passwordHash;

    private String avatarUrl;

    /** 0 学生 1 教师 2 管理员 */
    private Integer role;

    private Integer points;

    /** 0 正常 1 禁用 */
    private Integer status;

    private LocalDateTime createdAt;

    private LocalDateTime updatedAt;
}
