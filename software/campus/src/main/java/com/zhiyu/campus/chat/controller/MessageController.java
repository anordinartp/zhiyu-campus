package com.zhiyu.campus.chat.controller;

import com.zhiyu.campus.chat.dto.SendMessageRequest;
import com.zhiyu.campus.chat.service.MessageService;
import com.zhiyu.campus.chat.vo.MessagePageVO;
import com.zhiyu.campus.chat.vo.MessageVO;
import com.zhiyu.campus.common.ApiResponse;
import com.zhiyu.campus.security.CurrentUser;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@Tag(name = "消息")
@RestController
@RequestMapping("/api/v1/rooms/{roomId}/messages")
public class MessageController {

    private final MessageService messageService;

    public MessageController(MessageService messageService) {
        this.messageService = messageService;
    }

    @Operation(summary = "A-09 拉取消息（游标分页）")
    @GetMapping
    public ApiResponse<MessagePageVO> history(@PathVariable Long roomId,
                                              @RequestParam(required = false) Long cursor,
                                              @RequestParam(defaultValue = "20") int limit) {
        return ApiResponse.ok(messageService.history(CurrentUser.id(), roomId, cursor, limit));
    }

    @Operation(summary = "A-10 发送消息")
    @PostMapping
    public ApiResponse<MessageVO> send(@PathVariable Long roomId,
                                       @Valid @RequestBody SendMessageRequest request) {
        return ApiResponse.ok(messageService.send(CurrentUser.id(), roomId, request));
    }
}
