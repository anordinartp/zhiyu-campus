package com.zhiyu.campus.chat.controller;

import com.zhiyu.campus.chat.dto.CreateRoomRequest;
import com.zhiyu.campus.chat.dto.UpdateMemberRequest;
import com.zhiyu.campus.chat.service.ChatRoomService;
import com.zhiyu.campus.chat.vo.MemberVO;
import com.zhiyu.campus.chat.vo.RoomVO;
import com.zhiyu.campus.common.ApiResponse;
import com.zhiyu.campus.security.CurrentUser;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@Tag(name = "聊天室")
@RestController
@RequestMapping("/api/v1/rooms")
public class ChatRoomController {

    private final ChatRoomService roomService;

    public ChatRoomController(ChatRoomService roomService) {
        this.roomService = roomService;
    }

    @Operation(summary = "A-06 聊天室列表（可按标签过滤）")
    @GetMapping
    public ApiResponse<List<RoomVO>> list(@RequestParam(required = false) Long tagId,
                                          @RequestParam(defaultValue = "1") int page,
                                          @RequestParam(defaultValue = "20") int size) {
        return ApiResponse.ok(roomService.list(CurrentUser.id(), tagId, page, size));
    }

    @Operation(summary = "A-07 创建聊天室")
    @PostMapping
    public ApiResponse<RoomVO> create(@Valid @RequestBody CreateRoomRequest request) {
        return ApiResponse.ok(roomService.create(CurrentUser.id(), request));
    }

    @Operation(summary = "聊天室详情")
    @GetMapping("/{id}")
    public ApiResponse<RoomVO> detail(@PathVariable Long id) {
        return ApiResponse.ok(roomService.detail(CurrentUser.id(), id));
    }

    @Operation(summary = "A-08 加入聊天室")
    @PostMapping("/{id}/join")
    public ApiResponse<Void> join(@PathVariable Long id) {
        roomService.join(CurrentUser.id(), id);
        return ApiResponse.ok();
    }

    @Operation(summary = "成员列表")
    @GetMapping("/{id}/members")
    public ApiResponse<List<MemberVO>> members(@PathVariable Long id) {
        return ApiResponse.ok(roomService.members(CurrentUser.id(), id));
    }

    @Operation(summary = "A-11 调整成员角色或禁言")
    @PatchMapping("/{id}/members/{userId}")
    public ApiResponse<Void> updateMember(@PathVariable Long id, @PathVariable Long userId,
                                          @Valid @RequestBody UpdateMemberRequest request) {
        roomService.updateMember(CurrentUser.id(), id, userId, request);
        return ApiResponse.ok();
    }
}
