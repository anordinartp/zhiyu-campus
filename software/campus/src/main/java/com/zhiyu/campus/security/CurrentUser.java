package com.zhiyu.campus.security;

/** 当前请求的登录主体，由拦截器写入、请求结束时清理。 */
public final class CurrentUser {

    public record Principal(Long userId, Integer role) {
    }

    private static final ThreadLocal<Principal> HOLDER = new ThreadLocal<>();

    private CurrentUser() {
    }

    public static void set(Principal principal) {
        HOLDER.set(principal);
    }

    public static Principal get() {
        return HOLDER.get();
    }

    public static Long id() {
        Principal p = HOLDER.get();
        return p == null ? null : p.userId();
    }

    public static void clear() {
        HOLDER.remove();
    }
}
