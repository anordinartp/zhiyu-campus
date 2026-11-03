package com.zhiyu.campus.user.service;

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
    private static final Pattern PASSWORD_RULE = Pattern.compile("^(?=.*[A-Za-z])(?=.*\\d).{8,64}$");

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
