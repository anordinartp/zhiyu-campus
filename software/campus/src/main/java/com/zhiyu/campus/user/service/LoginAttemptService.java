package com.zhiyu.campus.user.service;

import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 登录失败计数（对应 UC-01 备选流 5a：连续 5 次锁定 10 分钟）。
 *
 * 说明：当前为进程内实现，单机够用；多实例部署时应换成 Redis，
 * 否则各实例计数不共享。这一点已在报告 9.2 的测试环境中标注。
 */
@Service
public class LoginAttemptService {

    private static final int MAX_FAILURES = 5;
    private static final Duration LOCK_DURATION = Duration.ofMinutes(10);
    private static final Duration WINDOW = Duration.ofHours(1);

    private record Attempt(int failures, Instant firstFailure, Instant lockedUntil) {
    }

    private final Map<String, Attempt> attempts = new ConcurrentHashMap<>();

    public boolean isLocked(String account) {
        Attempt a = attempts.get(account);
        if (a == null || a.lockedUntil() == null) {
            return false;
        }
        if (Instant.now().isAfter(a.lockedUntil())) {
            attempts.remove(account);
            return false;
        }
        return true;
    }

    public void recordFailure(String account) {
        attempts.compute(account, (key, old) -> {
            Instant now = Instant.now();
            if (old == null || old.firstFailure().plus(WINDOW).isBefore(now)) {
                return new Attempt(1, now, null);
            }
            int failures = old.failures() + 1;
            Instant lockedUntil = failures >= MAX_FAILURES ? now.plus(LOCK_DURATION) : null;
            return new Attempt(failures, old.firstFailure(), lockedUntil);
        });
    }

    public void reset(String account) {
        attempts.remove(account);
    }

    public int maxFailures() {
        return MAX_FAILURES;
    }
}
