package com.zhiyu.campus.heat.controller;

import com.zhiyu.campus.common.ApiResponse;
import com.zhiyu.campus.common.BizException;
import com.zhiyu.campus.common.ErrorCode;
import com.zhiyu.campus.heat.service.HeatService;
import com.zhiyu.campus.security.CurrentUser;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@Tag(name = "管理")
@RestController
@RequestMapping("/api/v1/admin")
public class AdminHeatController {

    private final HeatService heatService;

    public AdminHeatController(HeatService heatService) {
        this.heatService = heatService;
    }

    @Operation(summary = "手动触发热度重算（仅管理员）")
    @PostMapping("/heat/recalc")
    public ApiResponse<Map<String, Integer>> recalc() {
        CurrentUser.Principal principal = CurrentUser.get();
        if (principal == null || principal.role() == null || principal.role() != 2) {
            throw new BizException(ErrorCode.FORBIDDEN, "仅管理员可触发热度重算");
        }
        int tags = heatService.recalcAll();
        return ApiResponse.ok(Map.of("tags", tags));
    }
}
