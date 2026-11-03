package com.zhiyu.campus.common;

/**
 * 统一错误码，与报告表 23 一一对应。
 * 4xxxx 为调用方问题，5xxxx 为服务端问题。
 */
public enum ErrorCode {

    SUCCESS(0, "成功"),
    PARAM_ERROR(40001, "参数校验失败"),
    UNAUTHORIZED(40101, "未登录或令牌失效"),
    FORBIDDEN(40301, "无权限"),
    NOT_FOUND(40401, "资源不存在"),
    CONFLICT(40901, "重复操作"),
    RATE_LIMIT(42901, "请求过于频繁"),
    INTERNAL(50001, "服务内部错误"),
    DEPENDENCY_DOWN(50301, "依赖服务不可用");

    private final int code;
    private final String defaultMessage;

    ErrorCode(int code, String defaultMessage) {
        this.code = code;
        this.defaultMessage = defaultMessage;
    }

    public int code() {
        return code;
    }

    public String defaultMessage() {
        return defaultMessage;
    }
}
