package com.zhiyu.campus.security;

import com.zhiyu.campus.common.BizException;
import com.zhiyu.campus.common.ErrorCode;
import io.jsonwebtoken.Claims;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

@Component
public class JwtInterceptor implements HandlerInterceptor {

    private static final String PREFIX = "Bearer ";

    private final JwtService jwtService;

    public JwtInterceptor(JwtService jwtService) {
        this.jwtService = jwtService;
    }

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        String header = request.getHeader("Authorization");
        if (header == null || !header.startsWith(PREFIX)) {
            throw new BizException(ErrorCode.UNAUTHORIZED, "缺少访问令牌");
        }
        Claims claims;
        try {
            claims = jwtService.parse(header.substring(PREFIX.length()));
        } catch (Exception e) {
            throw new BizException(ErrorCode.UNAUTHORIZED, "令牌无效或已过期");
        }
        if (!"access".equals(claims.get("typ"))) {
            throw new BizException(ErrorCode.UNAUTHORIZED, "请使用访问令牌");
        }
        Long userId = Long.valueOf(claims.getSubject());
        Integer role = claims.get("role", Integer.class);
        CurrentUser.set(new CurrentUser.Principal(userId, role));
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response,
                                Object handler, Exception ex) {
        CurrentUser.clear();
    }
}
