package com.zhiyu.campus.user.controller;

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
