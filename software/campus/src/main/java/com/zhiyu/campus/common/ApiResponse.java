package com.zhiyu.campus.common;

/**
 * 统一响应体：{code, message, data, traceId}，见报告 7.4.1 第 6 条。
 */
public record ApiResponse<T>(int code, String message, T data, String traceId) {

    public static <T> ApiResponse<T> ok(T data) {
        return new ApiResponse<>(ErrorCode.SUCCESS.code(), "success", data, TraceId.current());
    }

    public static ApiResponse<Void> ok() {
        return new ApiResponse<>(ErrorCode.SUCCESS.code(), "success", null, TraceId.current());
    }

    public static <T> ApiResponse<T> fail(ErrorCode code, String message) {
        return new ApiResponse<>(code.code(), message, null, TraceId.current());
    }
}
