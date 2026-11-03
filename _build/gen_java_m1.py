# -*- coding: utf-8 -*-
"""生成 M1「用户与权限」的 Java 源码。

一次写全部文件，避免逐个调用；生成后由 Maven 编译验证。
"""
import base64
import os

ROOT = (r"C:\Users\saxtul\Documents\ds harness区\知屿校园\software\campus"
        r"\src\main\java\com\zhiyu\campus")
RES = (r"C:\Users\saxtul\Documents\ds harness区\知屿校园\software\campus"
       r"\src\main\resources")

SECRET = base64.b64encode(b"zhiyu-campus-dev-secret-key-32bytes!!").decode()

FILES = {}

FILES["CampusApplication.java"] = """package com.zhiyu.campus;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication
@ConfigurationPropertiesScan
public class CampusApplication {

    public static void main(String[] args) {
        SpringApplication.run(CampusApplication.class, args);
    }
}
"""

FILES["common/ErrorCode.java"] = """package com.zhiyu.campus.common;

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
"""

FILES["common/TraceId.java"] = """package com.zhiyu.campus.common;

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
"""

FILES["common/TraceIdFilter.java"] = """package com.zhiyu.campus.common;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

/** 为每个请求生成或透传 X-Trace-Id。 */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class TraceIdFilter extends OncePerRequestFilter {

    public static final String HEADER = "X-Trace-Id";

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
                                    FilterChain chain) throws ServletException, IOException {
        String traceId = request.getHeader(HEADER);
        if (traceId == null || traceId.isBlank()) {
            traceId = TraceId.generate();
        }
        TraceId.set(traceId);
        response.setHeader(HEADER, traceId);
        try {
            chain.doFilter(request, response);
        } finally {
            TraceId.clear();
        }
    }
}
"""

FILES["common/ApiResponse.java"] = """package com.zhiyu.campus.common;

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
"""

FILES["common/BizException.java"] = """package com.zhiyu.campus.common;

/** 业务异常：携带错误码，由全局异常处理器转成统一响应。 */
public class BizException extends RuntimeException {

    private final ErrorCode errorCode;

    public BizException(ErrorCode errorCode) {
        this(errorCode, errorCode.defaultMessage());
    }

    public BizException(ErrorCode errorCode, String message) {
        super(message);
        this.errorCode = errorCode;
    }

    public ErrorCode errorCode() {
        return errorCode;
    }
}
"""

FILES["common/GlobalExceptionHandler.java"] = """package com.zhiyu.campus.common;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.HttpMediaTypeNotSupportedException;
import org.springframework.web.servlet.resource.NoResourceFoundException;
import org.springframework.web.HttpRequestMethodNotSupportedException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.stream.Collectors;

@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(BizException.class)
    public ResponseEntity<ApiResponse<Void>> handleBiz(BizException e) {
        ErrorCode code = e.errorCode();
        HttpStatus status = switch (code) {
            case UNAUTHORIZED -> HttpStatus.UNAUTHORIZED;
            case FORBIDDEN -> HttpStatus.FORBIDDEN;
            case NOT_FOUND -> HttpStatus.NOT_FOUND;
            case CONFLICT -> HttpStatus.CONFLICT;
            case RATE_LIMIT -> HttpStatus.TOO_MANY_REQUESTS;
            case DEPENDENCY_DOWN -> HttpStatus.SERVICE_UNAVAILABLE;
            default -> HttpStatus.BAD_REQUEST;
        };
        return ResponseEntity.status(status).body(ApiResponse.fail(code, e.getMessage()));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponse<Void>> handleInvalid(MethodArgumentNotValidException e) {
        String detail = e.getBindingResult().getFieldErrors().stream()
                .map(this::describe)
                .collect(Collectors.joining("；"));
        return ResponseEntity.badRequest()
                .body(ApiResponse.fail(ErrorCode.PARAM_ERROR, detail));
    }

    @ExceptionHandler(HttpMediaTypeNotSupportedException.class)
    public ResponseEntity<ApiResponse<Void>> handleMediaType(HttpMediaTypeNotSupportedException e) {
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body(ApiResponse.fail(ErrorCode.PARAM_ERROR, "请求头 Content-Type 需为 application/json"));
    }

    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<ApiResponse<Void>> handleUnreadable(HttpMessageNotReadableException e) {
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body(ApiResponse.fail(ErrorCode.PARAM_ERROR, "请求体格式错误"));
    }

    @ExceptionHandler(HttpRequestMethodNotSupportedException.class)
    public ResponseEntity<ApiResponse<Void>> handleMethod(HttpRequestMethodNotSupportedException e) {
        return ResponseEntity.status(HttpStatus.METHOD_NOT_ALLOWED)
                .body(ApiResponse.fail(ErrorCode.PARAM_ERROR, "不支持的请求方法 " + e.getMethod()));
    }

    @ExceptionHandler(NoResourceFoundException.class)
    public ResponseEntity<ApiResponse<Void>> handleNoResource(NoResourceFoundException e) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
                .body(ApiResponse.fail(ErrorCode.NOT_FOUND, "接口不存在"));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<Void>> handleOther(Exception e) {
        log.error("未捕获异常 traceId={}", TraceId.current(), e);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ApiResponse.fail(ErrorCode.INTERNAL, "服务内部错误，请联系管理员"));
    }

    private String describe(FieldError error) {
        return error.getField() + " " + error.getDefaultMessage();
    }
}
"""

FILES["config/MybatisPlusConfig.java"] = """package com.zhiyu.campus.config;

import com.baomidou.mybatisplus.annotation.DbType;
import com.baomidou.mybatisplus.extension.plugins.MybatisPlusInterceptor;
import com.baomidou.mybatisplus.extension.plugins.inner.PaginationInnerInterceptor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class MybatisPlusConfig {

    /** 分页插件：报告 7.4.1 约定列表统一用 limit 分页。 */
    @Bean
    public MybatisPlusInterceptor mybatisPlusInterceptor() {
        MybatisPlusInterceptor interceptor = new MybatisPlusInterceptor();
        interceptor.addInnerInterceptor(new PaginationInnerInterceptor(DbType.MYSQL));
        return interceptor;
    }
}
"""

FILES["config/OpenApiConfig.java"] = """package com.zhiyu.campus.config;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.security.SecurityScheme;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI campusOpenApi() {
        return new OpenAPI()
                .info(new Info().title("知屿校园 API").version("v1")
                        .description("接口与报告表 21 一一对应；除标注“公开”外均需 Bearer 令牌"))
                .components(new Components().addSecuritySchemes("bearerAuth",
                        new SecurityScheme()
                                .type(SecurityScheme.Type.HTTP)
                                .scheme("bearer")
                                .bearerFormat("JWT")));
    }
}
"""

FILES["security/JwtProperties.java"] = """package com.zhiyu.campus.security;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * JWT 配置。secret 为 Base64 编码的 HS256 密钥。
 * 生产环境必须由环境变量覆盖，不得写入仓库。
 */
@ConfigurationProperties(prefix = "app.jwt")
public record JwtProperties(String secret, long accessMinutes, long refreshDays) {
}
"""

FILES["security/JwtService.java"] = """package com.zhiyu.campus.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import org.springframework.stereotype.Service;

import javax.crypto.SecretKey;
import java.time.Duration;
import java.time.Instant;
import java.util.Date;

@Service
public class JwtService {

    private final SecretKey key;
    private final JwtProperties props;

    public JwtService(JwtProperties props) {
        this.props = props;
        this.key = Keys.hmacShaKeyFor(Decoders.BASE64.decode(props.secret()));
    }

    public String issueAccess(Long userId, Integer role) {
        return build(userId, role, Duration.ofMinutes(props.accessMinutes()), "access");
    }

    public String issueRefresh(Long userId) {
        return build(userId, 0, Duration.ofDays(props.refreshDays()), "refresh");
    }

    public long accessSeconds() {
        return Duration.ofMinutes(props.accessMinutes()).toSeconds();
    }

    public Claims parse(String token) {
        return Jwts.parser().verifyWith(key).build()
                .parseSignedClaims(token).getPayload();
    }

    private String build(Long userId, Integer role, Duration ttl, String type) {
        Instant now = Instant.now();
        return Jwts.builder()
                .subject(String.valueOf(userId))
                .claim("role", role)
                .claim("typ", type)
                .issuedAt(Date.from(now))
                .expiration(Date.from(now.plus(ttl)))
                .signWith(key)
                .compact();
    }
}
"""

FILES["security/CurrentUser.java"] = """package com.zhiyu.campus.security;

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
"""

FILES["security/JwtInterceptor.java"] = """package com.zhiyu.campus.security;

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
"""

FILES["config/WebConfig.java"] = """package com.zhiyu.campus.config;

import com.zhiyu.campus.security.JwtInterceptor;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    private final JwtInterceptor jwtInterceptor;

    public WebConfig(JwtInterceptor jwtInterceptor) {
        this.jwtInterceptor = jwtInterceptor;
    }

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(jwtInterceptor)
                .addPathPatterns("/api/**")
                .excludePathPatterns("/api/v1/auth/**");
    }
}
"""

FILES["user/entity/User.java"] = """package com.zhiyu.campus.user.entity;

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
"""

FILES["user/mapper/UserMapper.java"] = """package com.zhiyu.campus.user.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.zhiyu.campus.user.entity.User;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface UserMapper extends BaseMapper<User> {
}
"""

FILES["user/dto/RegisterRequest.java"] = """package com.zhiyu.campus.user.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/** A-01 注册入参。 */
public record RegisterRequest(

        @NotBlank(message = "不能为空")
        @Pattern(regexp = "^[A-Za-z0-9]{4,32}$", message = "需为 4~32 位字母或数字")
        String account,

        @NotBlank(message = "不能为空")
        @Size(max = 32, message = "长度不能超过 32")
        String nickname,

        @NotBlank(message = "不能为空")
        @Size(min = 8, max = 64, message = "长度需为 8~64 位")
        String password) {
}
"""

FILES["user/dto/LoginRequest.java"] = """package com.zhiyu.campus.user.dto;

import jakarta.validation.constraints.NotBlank;

/** A-02 登录入参。 */
public record LoginRequest(

        @NotBlank(message = "不能为空") String account,
        @NotBlank(message = "不能为空") String password) {
}
"""

FILES["user/dto/RefreshRequest.java"] = """package com.zhiyu.campus.user.dto;

import jakarta.validation.constraints.NotBlank;

/** A-03 刷新令牌入参。 */
public record RefreshRequest(
        @NotBlank(message = "不能为空") String refreshToken) {
}
"""

FILES["user/vo/LoginVO.java"] = """package com.zhiyu.campus.user.vo;

/** 登录成功返回体。 */
public record LoginVO(
        String accessToken,
        String refreshToken,
        String tokenType,
        long expiresIn,
        Long userId,
        String nickname,
        Integer role) {
}
"""

FILES["user/vo/UserVO.java"] = """package com.zhiyu.campus.user.vo;

import java.time.LocalDateTime;

/** 用户信息返回体（不含口令哈希）。 */
public record UserVO(
        Long id,
        String account,
        String nickname,
        Integer role,
        Integer points,
        Integer status,
        LocalDateTime createdAt) {
}
"""

FILES["user/service/LoginAttemptService.java"] = """package com.zhiyu.campus.user.service;

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
"""

FILES["user/service/AuthService.java"] = """package com.zhiyu.campus.user.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.zhiyu.campus.common.BizException;
import com.zhiyu.campus.common.ErrorCode;
import com.zhiyu.campus.security.JwtService;
import com.zhiyu.campus.user.dto.LoginRequest;
import com.zhiyu.campus.user.dto.RegisterRequest;
import com.zhiyu.campus.user.entity.User;
import com.zhiyu.campus.user.mapper.UserMapper;
import com.zhiyu.campus.user.vo.LoginVO;
import com.zhiyu.campus.user.vo.UserVO;
import io.jsonwebtoken.Claims;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.regex.Pattern;

@Service
public class AuthService {

    /** 口令规则见报告 UC-01 业务规则：≥ 8 位且含字母与数字。 */
    private static final Pattern PASSWORD_RULE = Pattern.compile("^(?=.*[A-Za-z])(?=.*\\\\d).{8,64}$");

    private final UserMapper userMapper;
    private final JwtService jwtService;
    private final LoginAttemptService attemptService;
    private final PasswordEncoder passwordEncoder = new BCryptPasswordEncoder();

    public AuthService(UserMapper userMapper, JwtService jwtService,
                       LoginAttemptService attemptService) {
        this.userMapper = userMapper;
        this.jwtService = jwtService;
        this.attemptService = attemptService;
    }

    @Transactional
    public UserVO register(RegisterRequest request) {
        if (!PASSWORD_RULE.matcher(request.password()).matches()) {
            throw new BizException(ErrorCode.PARAM_ERROR, "口令需 8~64 位且同时包含字母与数字");
        }
        if (findByAccount(request.account()) != null) {
            throw new BizException(ErrorCode.CONFLICT, "账号已注册");
        }
        User user = new User();
        user.setAccount(request.account());
        user.setNickname(request.nickname());
        user.setPasswordHash(passwordEncoder.encode(request.password()));
        user.setRole(0);
        user.setPoints(0);
        user.setStatus(0);
        userMapper.insert(user);
        return toVO(user);
    }

    public LoginVO login(LoginRequest request) {
        if (attemptService.isLocked(request.account())) {
            throw new BizException(ErrorCode.RATE_LIMIT, "失败次数过多，请 10 分钟后再试");
        }
        User user = findByAccount(request.account());
        if (user == null || !passwordEncoder.matches(request.password(), user.getPasswordHash())) {
            attemptService.recordFailure(request.account());
            throw new BizException(ErrorCode.UNAUTHORIZED, "账号或口令错误");
        }
        if (user.getStatus() != null && user.getStatus() != 0) {
            throw new BizException(ErrorCode.FORBIDDEN, "账号已被禁用");
        }
        attemptService.reset(request.account());
        return issueTokens(user);
    }

    public LoginVO refresh(String refreshToken) {
        Claims claims;
        try {
            claims = jwtService.parse(refreshToken);
        } catch (Exception e) {
            throw new BizException(ErrorCode.UNAUTHORIZED, "刷新令牌无效或已过期");
        }
        if (!"refresh".equals(claims.get("typ"))) {
            throw new BizException(ErrorCode.UNAUTHORIZED, "请使用刷新令牌");
        }
        User user = userMapper.selectById(Long.valueOf(claims.getSubject()));
        if (user == null || (user.getStatus() != null && user.getStatus() != 0)) {
            throw new BizException(ErrorCode.UNAUTHORIZED, "账号不可用");
        }
        return issueTokens(user);
    }

    public UserVO profile(Long userId) {
        User user = userMapper.selectById(userId);
        if (user == null) {
            throw new BizException(ErrorCode.NOT_FOUND, "用户不存在");
        }
        return toVO(user);
    }

    private LoginVO issueTokens(User user) {
        String access = jwtService.issueAccess(user.getId(), user.getRole());
        String refresh = jwtService.issueRefresh(user.getId());
        return new LoginVO(access, refresh, "Bearer", jwtService.accessSeconds(),
                user.getId(), user.getNickname(), user.getRole());
    }

    private User findByAccount(String account) {
        return userMapper.selectOne(new LambdaQueryWrapper<User>()
                .eq(User::getAccount, account)
                .last("limit 1"));
    }

    private UserVO toVO(User user) {
        return new UserVO(user.getId(), user.getAccount(), user.getNickname(),
                user.getRole(), user.getPoints(), user.getStatus(), user.getCreatedAt());
    }
}
"""

FILES["user/controller/AuthController.java"] = """package com.zhiyu.campus.user.controller;

import com.zhiyu.campus.common.ApiResponse;
import com.zhiyu.campus.security.CurrentUser;
import com.zhiyu.campus.user.dto.LoginRequest;
import com.zhiyu.campus.user.dto.RefreshRequest;
import com.zhiyu.campus.user.dto.RegisterRequest;
import com.zhiyu.campus.user.service.AuthService;
import com.zhiyu.campus.user.vo.LoginVO;
import com.zhiyu.campus.user.vo.UserVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Tag(name = "认证与用户")
@RestController
@RequestMapping("/api/v1")
public class AuthController {

    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @Operation(summary = "A-01 注册")
    @PostMapping("/auth/register")
    public ApiResponse<UserVO> register(@Valid @RequestBody RegisterRequest request) {
        return ApiResponse.ok(authService.register(request));
    }

    @Operation(summary = "A-02 登录")
    @PostMapping("/auth/login")
    public ApiResponse<LoginVO> login(@Valid @RequestBody LoginRequest request) {
        return ApiResponse.ok(authService.login(request));
    }

    @Operation(summary = "A-03 刷新访问令牌")
    @PostMapping("/auth/refresh")
    public ApiResponse<LoginVO> refresh(@Valid @RequestBody RefreshRequest request) {
        return ApiResponse.ok(authService.refresh(request.refreshToken()));
    }

    @Operation(summary = "A-04 查看我的资料")
    @GetMapping("/users/me")
    public ApiResponse<UserVO> me() {
        return ApiResponse.ok(authService.profile(CurrentUser.id()));
    }
}
"""

YML = """server:
  port: 8080

spring:
  application:
    name: campus
  # Java 21 虚拟线程：高并发下无需线程池调优
  threads:
    virtual:
      enabled: true
  datasource:
    url: jdbc:mysql://127.0.0.1:3307/zhiyu_campus?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai&allowPublicKeyRetrieval=true&useSSL=false
    username: root
    password:
    driver-class-name: com.mysql.cj.jdbc.Driver
    hikari:
      maximum-pool-size: 10
      connection-timeout: 3000
  jackson:
    date-format: yyyy-MM-dd'T'HH:mm:ssXXX
    time-zone: Asia/Shanghai

mybatis-plus:
  configuration:
    map-underscore-to-camel-case: true
    log-impl: org.apache.ibatis.logging.stdout.StdOutImpl
  global-config:
    banner: false

springdoc:
  swagger-ui:
    path: /doc.html
  api-docs:
    path: /v3/api-docs

app:
  jwt:
    secret: %(secret)s
    access-minutes: 120
    refresh-days: 7

management:
  endpoints:
    web:
      exposure:
        include: health,info

logging:
  level:
    com.zhiyu.campus: DEBUG
""" % {"secret": SECRET}


def main():
    for rel, content in FILES.items():
        path = os.path.join(ROOT, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
    with open(os.path.join(RES, "application.yml"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(YML)
    print("java files:", len(FILES))
    print("secret:", SECRET)


if __name__ == "__main__":
    main()
