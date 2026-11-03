package com.zhiyu.campus.security;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * JWT 配置。secret 为 Base64 编码的 HS256 密钥。
 * 生产环境必须由环境变量覆盖，不得写入仓库。
 */
@ConfigurationProperties(prefix = "app.jwt")
public record JwtProperties(String secret, long accessMinutes, long refreshDays) {
}
