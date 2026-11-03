package com.zhiyu.campus.behavior.controller;

import com.zhiyu.campus.behavior.dto.BehaviorRequest;
import com.zhiyu.campus.behavior.entity.BehaviorLog;
import com.zhiyu.campus.behavior.mapper.BehaviorLogMapper;
import com.zhiyu.campus.common.ApiResponse;
import com.zhiyu.campus.security.CurrentUser;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;

@Tag(name = "行为采集")
@RestController
@RequestMapping("/api/v1/behaviors")
public class BehaviorController {

    private final BehaviorLogMapper behaviorMapper;

    public BehaviorController(BehaviorLogMapper behaviorMapper) {
        this.behaviorMapper = behaviorMapper;
    }

    /** 返回 202：行为是异步采集，不阻塞用户操作。 */
    @Operation(summary = "A-20 上报行为（浏览/停留/点赞等）")
    @PostMapping
    public ResponseEntity<ApiResponse<Void>> report(@Valid @RequestBody BehaviorRequest request) {
        BehaviorLog log = new BehaviorLog();
        log.setUserId(CurrentUser.id());
        log.setAction(request.action());
        log.setTargetType(request.targetType());
        log.setTargetId(request.targetId());
        log.setStayMs(request.stayMs() == null ? 0 : request.stayMs());
        log.setCreatedAt(LocalDateTime.now());
        behaviorMapper.insert(log);
        return ResponseEntity.status(HttpStatus.ACCEPTED).body(ApiResponse.ok());
    }
}
