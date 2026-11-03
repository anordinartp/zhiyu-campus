package com.zhiyu.campus.common;

import java.util.UUID;

/** 请求级 traceId，便于按一次调用串起日志。 */
public final class TraceId {

    private static final ThreadLocal<String> HOLDER = new ThreadLocal<>();

    private TraceId() {
    }

    public static void set(String value) {
        HOLDER.set(value);
    }

    public static String current() {
        String v = HOLDER.get();
        return v != null ? v : "-";
    }

    public static String generate() {
        return UUID.randomUUID().toString().replace("-", "").substring(0, 16);
    }

    public static void clear() {
        HOLDER.remove();
    }
}
