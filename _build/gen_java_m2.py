# -*- coding: utf-8 -*-
"""生成 M2「聊天室」模块的 Java 源码（含标签查询）。"""
import os

ROOT = (r"C:\Users\saxtul\Documents\ds harness区\知屿校园\software\campus"
        r"\src\main\java\com\zhiyu\campus")

F = {}

# ----------------------------------------------------------------- 实体
F["chat/entity/ChatRoom.java"] = """package com.zhiyu.campus.chat.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/** 对应表 10 聊天室表 chat_room。 */
@Data
@TableName("chat_room")
public class ChatRoom {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String name;

    private String intro;

    private Long creatorId;

    /** 成员数（冗余），见报告 6.1 第 7 条 */
    private Integer memberCount;

    /** 0 正常 1 禁言 2 关闭 */
    private Integer status;

    private LocalDateTime lastActiveAt;

    private LocalDateTime createdAt;
}
"""

F["chat/entity/ChatRoomMember.java"] = """package com.zhiyu.campus.chat.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 对应表 11 聊天室成员表 chat_room_member。
 * 复合主键 (room_id, user_id)，因此不使用 @TableId，统一用条件构造器操作。
 */
@Data
@TableName("chat_room_member")
public class ChatRoomMember {

    private Long roomId;

    private Long userId;

    /** 0 成员 1 管理员 2 群主 */
    private Integer role;

    /** 0 未禁言 1 禁言 */
    private Integer muted;

    private LocalDateTime mutedUntil;

    private LocalDateTime joinedAt;
}
"""

F["chat/entity/Message.java"] = """package com.zhiyu.campus.chat.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/** 对应表 12 消息表 message。 */
@Data
@TableName("message")
public class Message {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long roomId;

    private Long senderId;

    /** 1 文本 2 图片 3 文件 */
    private Integer msgType;

    private String content;

    /** 0 正常 1 屏蔽 2 删除 */
    private Integer status;

    private Integer aiProcessed;

    private LocalDateTime createdAt;
}
"""

F["chat/entity/ChatRoomTag.java"] = """package com.zhiyu.campus.chat.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/** 对应关联表 chat_room_tag，复合主键同样不使用 @TableId。 */
@Data
@TableName("chat_room_tag")
public class ChatRoomTag {

    private Long roomId;

    private Long tagId;

    private LocalDateTime createdAt;
}
"""

F["tag/entity/Tag.java"] = """package com.zhiyu.campus.tag.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/** 对应表 15 标签表 tag。 */
@Data
@TableName("tag")
public class Tag {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String name;

    /** 1 仅聊天室 2 仅博客 3 通用 */
    private Integer scope;

    private Long creatorId;

    private Integer heat;

    private LocalDateTime createdAt;
}
"""

# ----------------------------------------------------------------- mapper
F["chat/mapper/ChatRoomMapper.java"] = """package com.zhiyu.campus.chat.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.zhiyu.campus.chat.entity.ChatRoom;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface ChatRoomMapper extends BaseMapper<ChatRoom> {
}
"""

F["chat/mapper/ChatRoomMemberMapper.java"] = """package com.zhiyu.campus.chat.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.zhiyu.campus.chat.entity.ChatRoomMember;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface ChatRoomMemberMapper extends BaseMapper<ChatRoomMember> {
}
"""

F["chat/mapper/MessageMapper.java"] = """package com.zhiyu.campus.chat.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.zhiyu.campus.chat.entity.Message;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface MessageMapper extends BaseMapper<Message> {
}
"""

F["chat/mapper/ChatRoomTagMapper.java"] = """package com.zhiyu.campus.chat.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.zhiyu.campus.chat.entity.ChatRoomTag;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface ChatRoomTagMapper extends BaseMapper<ChatRoomTag> {
}
"""

F["tag/mapper/TagMapper.java"] = """package com.zhiyu.campus.tag.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.zhiyu.campus.tag.entity.Tag;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface TagMapper extends BaseMapper<Tag> {
}
"""

# ------------------------------------------------------------------- dto
F["chat/dto/CreateRoomRequest.java"] = """package com.zhiyu.campus.chat.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

import java.util.List;

/** A-07 创建聊天室入参。 */
public record CreateRoomRequest(

        @NotBlank(message = "不能为空")
        @Size(max = 60, message = "长度不能超过 60")
        String name,

        @Size(max = 500, message = "长度不能超过 500")
        String intro,

        /** 可选的标签 ID 列表，用于“标签把聊天室分类” */
        List<Long> tagIds) {
}
"""

F["chat/dto/SendMessageRequest.java"] = """package com.zhiyu.campus.chat.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/** A-10 发送消息入参。 */
public record SendMessageRequest(

        /** 1 文本 2 图片 3 文件，默认文本 */
        Integer msgType,

        @NotBlank(message = "不能为空")
        @Size(max = 2000, message = "长度不能超过 2000 字")
        String content) {
}
"""

F["chat/dto/UpdateMemberRequest.java"] = """package com.zhiyu.campus.chat.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;

/** A-11 成员角色与禁言调整入参，两者至少传一个。 */
public record UpdateMemberRequest(

        @Min(value = 0, message = "取值需为 0~1")
        @Max(value = 1, message = "取值需为 0~1")
        Integer role,

        Integer muted,

        /** 禁言时长（分钟），为空表示永久 */
        Integer mutedMinutes) {
}
"""

# -------------------------------------------------------------------- vo
F["chat/vo/RoomVO.java"] = """package com.zhiyu.campus.chat.vo;

import java.time.LocalDateTime;
import java.util.List;

public record RoomVO(
        Long id,
        String name,
        String intro,
        Long creatorId,
        Integer memberCount,
        Integer status,
        LocalDateTime lastActiveAt,
        LocalDateTime createdAt,
        List<String> tags) {
}
"""

F["chat/vo/MemberVO.java"] = """package com.zhiyu.campus.chat.vo;

import java.time.LocalDateTime;

public record MemberVO(
        Long userId,
        String nickname,
        Integer role,
        Integer muted,
        LocalDateTime mutedUntil,
        LocalDateTime joinedAt) {
}
"""

F["chat/vo/MessageVO.java"] = """package com.zhiyu.campus.chat.vo;

import java.time.LocalDateTime;

public record MessageVO(
        Long id,
        Long roomId,
        Long senderId,
        String senderNickname,
        Integer msgType,
        String content,
        Integer status,
        LocalDateTime createdAt) {
}
"""

F["chat/vo/MessagePageVO.java"] = """package com.zhiyu.campus.chat.vo;

import java.util.List;

/**
 * 游标分页返回体：nextCursor 为空表示没有更多。
 * 与报告 7.4.1 第 3 条“列表统一用游标分页”一致。
 */
public record MessagePageVO(List<MessageVO> items, Long nextCursor, boolean hasMore) {
}
"""

# ---------------------------------------------------------------- service
F["chat/service/ChatRoomService.java"] = """package com.zhiyu.campus.chat.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.zhiyu.campus.chat.dto.CreateRoomRequest;
import com.zhiyu.campus.chat.dto.UpdateMemberRequest;
import com.zhiyu.campus.chat.entity.ChatRoom;
import com.zhiyu.campus.chat.entity.ChatRoomMember;
import com.zhiyu.campus.chat.entity.ChatRoomTag;
import com.zhiyu.campus.chat.mapper.ChatRoomMapper;
import com.zhiyu.campus.chat.mapper.ChatRoomMemberMapper;
import com.zhiyu.campus.chat.mapper.ChatRoomTagMapper;
import com.zhiyu.campus.chat.vo.MemberVO;
import com.zhiyu.campus.chat.vo.RoomVO;
import com.zhiyu.campus.common.BizException;
import com.zhiyu.campus.common.ErrorCode;
import com.zhiyu.campus.tag.entity.Tag;
import com.zhiyu.campus.tag.mapper.TagMapper;
import com.zhiyu.campus.user.entity.User;
import com.zhiyu.campus.user.mapper.UserMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class ChatRoomService {

    private final ChatRoomMapper roomMapper;
    private final ChatRoomMemberMapper memberMapper;
    private final ChatRoomTagMapper roomTagMapper;
    private final TagMapper tagMapper;
    private final UserMapper userMapper;

    public ChatRoomService(ChatRoomMapper roomMapper, ChatRoomMemberMapper memberMapper,
                           ChatRoomTagMapper roomTagMapper, TagMapper tagMapper,
                           UserMapper userMapper) {
        this.roomMapper = roomMapper;
        this.memberMapper = memberMapper;
        this.roomTagMapper = roomTagMapper;
        this.tagMapper = tagMapper;
        this.userMapper = userMapper;
    }

    @Transactional
    public RoomVO create(Long userId, CreateRoomRequest request) {
        ChatRoom room = new ChatRoom();
        room.setName(request.name());
        room.setIntro(request.intro());
        room.setCreatorId(userId);
        room.setMemberCount(1);
        room.setStatus(0);
        room.setLastActiveAt(LocalDateTime.now());
        room.setCreatedAt(LocalDateTime.now());
        roomMapper.insert(room);

        ChatRoomMember owner = new ChatRoomMember();
        owner.setRoomId(room.getId());
        owner.setUserId(userId);
        owner.setRole(2);
        owner.setMuted(0);
        owner.setJoinedAt(LocalDateTime.now());
        memberMapper.insert(owner);

        bindTags(room.getId(), request.tagIds());
        return toVO(room, loadTagNames(Collections.singletonList(room.getId())));
    }

    public List<RoomVO> list(Long userId, Long tagId, int page, int size) {
        List<Long> roomIds = null;
        if (tagId != null) {
            roomIds = roomTagMapper.selectList(new LambdaQueryWrapper<ChatRoomTag>()
                            .eq(ChatRoomTag::getTagId, tagId))
                    .stream().map(ChatRoomTag::getRoomId).distinct().toList();
            if (roomIds.isEmpty()) {
                return List.of();
            }
        }
        LambdaQueryWrapper<ChatRoom> wrapper = new LambdaQueryWrapper<ChatRoom>()
                .eq(ChatRoom::getStatus, 0)
                .orderByDesc(ChatRoom::getLastActiveAt)
                .orderByDesc(ChatRoom::getId);
        if (roomIds != null) {
            wrapper.in(ChatRoom::getId, roomIds);
        }
        Page<ChatRoom> result = roomMapper.selectPage(new Page<>(Math.max(1, page), Math.max(1, Math.min(size, 50))), wrapper);
        Map<Long, List<String>> tags = loadTagNames(
                result.getRecords().stream().map(ChatRoom::getId).toList());
        return result.getRecords().stream().map(r -> toVO(r, tags)).toList();
    }

    public RoomVO detail(Long userId, Long roomId) {
        ChatRoom room = requireRoom(roomId);
        return toVO(room, loadTagNames(Collections.singletonList(roomId)));
    }

    @Transactional
    public void join(Long userId, Long roomId) {
        ChatRoom room = requireRoom(roomId);
        if (room.getStatus() != null && room.getStatus() == 2) {
            throw new BizException(ErrorCode.FORBIDDEN, "聊天室已关闭");
        }
        if (findMember(roomId, userId) != null) {
            throw new BizException(ErrorCode.CONFLICT, "已加入该聊天室");
        }
        ChatRoomMember member = new ChatRoomMember();
        member.setRoomId(roomId);
        member.setUserId(userId);
        member.setRole(0);
        member.setMuted(0);
        member.setJoinedAt(LocalDateTime.now());
        memberMapper.insert(member);

        roomMapper.update(null, new LambdaUpdateWrapper<ChatRoom>()
                .eq(ChatRoom::getId, roomId)
                .setSql("member_count = member_count + 1"));
    }

    public List<MemberVO> members(Long userId, Long roomId) {
        ChatRoom room = requireRoom(roomId);
        requireMember(room.getId(), userId);

        List<ChatRoomMember> members = memberMapper.selectList(
                new LambdaQueryWrapper<ChatRoomMember>().eq(ChatRoomMember::getRoomId, roomId));
        if (members.isEmpty()) {
            return List.of();
        }
        List<Long> userIds = members.stream().map(ChatRoomMember::getUserId).toList();
        Map<Long, String> nicknames = userMapper.selectList(
                        new LambdaQueryWrapper<User>().in(User::getId, userIds))
                .stream().collect(Collectors.toMap(User::getId, User::getNickname));
        List<MemberVO> result = new ArrayList<>();
        for (ChatRoomMember m : members) {
            result.add(new MemberVO(m.getUserId(), nicknames.get(m.getUserId()), m.getRole(),
                    m.getMuted(), m.getMutedUntil(), m.getJoinedAt()));
        }
        return result;
    }

    @Transactional
    public void updateMember(Long operatorId, Long roomId, Long targetUserId,
                             UpdateMemberRequest request) {
        if (request.role() == null && request.muted() == null) {
            throw new BizException(ErrorCode.PARAM_ERROR, "role 与 muted 至少传一个");
        }
        requireRoom(roomId);
        ChatRoomMember operator = requireMember(roomId, operatorId);
        if (operator.getRole() == null || operator.getRole() < 1) {
            throw new BizException(ErrorCode.FORBIDDEN, "仅群主或管理员可管理成员");
        }
        ChatRoomMember target = findMember(roomId, targetUserId);
        if (target == null) {
            throw new BizException(ErrorCode.NOT_FOUND, "该用户不在聊天室中");
        }
        if (target.getRole() != null && target.getRole() == 2) {
            throw new BizException(ErrorCode.FORBIDDEN, "不能修改群主");
        }
        LambdaUpdateWrapper<ChatRoomMember> update = new LambdaUpdateWrapper<ChatRoomMember>()
                .eq(ChatRoomMember::getRoomId, roomId)
                .eq(ChatRoomMember::getUserId, targetUserId);
        if (request.role() != null) {
            update.set(ChatRoomMember::getRole, request.role());
        }
        if (request.muted() != null) {
            update.set(ChatRoomMember::getMuted, request.muted());
            update.set(ChatRoomMember::getMutedUntil,
                    request.muted() == 1 && request.mutedMinutes() != null
                            ? LocalDateTime.now().plusMinutes(request.mutedMinutes())
                            : null);
        }
        memberMapper.update(null, update);
    }

    // ------------------------------------------------------------- 内部方法

    public ChatRoom requireRoom(Long roomId) {
        ChatRoom room = roomMapper.selectById(roomId);
        if (room == null) {
            throw new BizException(ErrorCode.NOT_FOUND, "聊天室不存在");
        }
        return room;
    }

    public ChatRoomMember requireMember(Long roomId, Long userId) {
        ChatRoomMember member = findMember(roomId, userId);
        if (member == null) {
            throw new BizException(ErrorCode.FORBIDDEN, "请先加入该聊天室");
        }
        return member;
    }

    public ChatRoomMember findMember(Long roomId, Long userId) {
        return memberMapper.selectOne(new LambdaQueryWrapper<ChatRoomMember>()
                .eq(ChatRoomMember::getRoomId, roomId)
                .eq(ChatRoomMember::getUserId, userId)
                .last("limit 1"));
    }

    private void bindTags(Long roomId, List<Long> tagIds) {
        if (tagIds == null || tagIds.isEmpty()) {
            return;
        }
        List<Long> existing = tagMapper.selectList(
                        new LambdaQueryWrapper<Tag>().in(Tag::getId, tagIds))
                .stream().map(Tag::getId).toList();
        for (Long tagId : existing) {
            ChatRoomTag link = new ChatRoomTag();
            link.setRoomId(roomId);
            link.setTagId(tagId);
            link.setCreatedAt(LocalDateTime.now());
            roomTagMapper.insert(link);
        }
    }

    private Map<Long, List<String>> loadTagNames(List<Long> roomIds) {
        Map<Long, List<String>> result = new LinkedHashMap<>();
        if (roomIds == null || roomIds.isEmpty()) {
            return result;
        }
        List<ChatRoomTag> links = roomTagMapper.selectList(
                new LambdaQueryWrapper<ChatRoomTag>().in(ChatRoomTag::getRoomId, roomIds));
        if (links.isEmpty()) {
            return result;
        }
        Map<Long, String> names = tagMapper.selectList(
                        new LambdaQueryWrapper<Tag>().in(Tag::getId,
                                links.stream().map(ChatRoomTag::getTagId).distinct().toList()))
                .stream().collect(Collectors.toMap(Tag::getId, Tag::getName));
        for (ChatRoomTag link : links) {
            result.computeIfAbsent(link.getRoomId(), k -> new ArrayList<>())
                    .add(names.getOrDefault(link.getTagId(), String.valueOf(link.getTagId())));
        }
        return result;
    }

    private RoomVO toVO(ChatRoom room, Map<Long, List<String>> tagMap) {
        return new RoomVO(room.getId(), room.getName(), room.getIntro(), room.getCreatorId(),
                room.getMemberCount(), room.getStatus(), room.getLastActiveAt(),
                room.getCreatedAt(),
                tagMap.getOrDefault(room.getId(), List.of()));
    }
}
"""

F["chat/service/MessageService.java"] = """package com.zhiyu.campus.chat.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.zhiyu.campus.chat.dto.SendMessageRequest;
import com.zhiyu.campus.chat.entity.ChatRoom;
import com.zhiyu.campus.chat.entity.ChatRoomMember;
import com.zhiyu.campus.chat.entity.Message;
import com.zhiyu.campus.chat.mapper.ChatRoomMapper;
import com.zhiyu.campus.chat.mapper.MessageMapper;
import com.zhiyu.campus.chat.vo.MessagePageVO;
import com.zhiyu.campus.chat.vo.MessageVO;
import com.zhiyu.campus.common.BizException;
import com.zhiyu.campus.common.ErrorCode;
import com.zhiyu.campus.user.entity.User;
import com.zhiyu.campus.user.mapper.UserMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class MessageService {

    private static final int MAX_LIMIT = 50;

    private final MessageMapper messageMapper;
    private final ChatRoomMapper roomMapper;
    private final ChatRoomService roomService;
    private final UserMapper userMapper;

    public MessageService(MessageMapper messageMapper, ChatRoomMapper roomMapper,
                          ChatRoomService roomService, UserMapper userMapper) {
        this.messageMapper = messageMapper;
        this.roomMapper = roomMapper;
        this.roomService = roomService;
        this.userMapper = userMapper;
    }

    @Transactional
    public MessageVO send(Long userId, Long roomId, SendMessageRequest request) {
        ChatRoom room = roomService.requireRoom(roomId);
        if (room.getStatus() != null && room.getStatus() == 2) {
            throw new BizException(ErrorCode.FORBIDDEN, "聊天室已关闭，无法发言");
        }
        ChatRoomMember member = roomService.requireMember(roomId, userId);
        if (member.getMuted() != null && member.getMuted() == 1
                && (member.getMutedUntil() == null || member.getMutedUntil().isAfter(LocalDateTime.now()))) {
            throw new BizException(ErrorCode.FORBIDDEN, "你已被禁言");
        }

        Message message = new Message();
        message.setRoomId(roomId);
        message.setSenderId(userId);
        message.setMsgType(request.msgType() == null ? 1 : request.msgType());
        message.setContent(request.content());
        message.setStatus(0);
        message.setAiProcessed(0);
        message.setCreatedAt(LocalDateTime.now());
        messageMapper.insert(message);

        roomMapper.update(null, new LambdaUpdateWrapper<ChatRoom>()
                .eq(ChatRoom::getId, roomId)
                .set(ChatRoom::getLastActiveAt, LocalDateTime.now()));

        return toVO(message, nicknameOf(userId));
    }

    /** 游标分页：cursor 为上一页最后一条消息 ID，返回按时间正序的列表。 */
    public MessagePageVO history(Long userId, Long roomId, Long cursor, int limit) {
        roomService.requireRoom(roomId);
        roomService.requireMember(roomId, userId);

        int size = Math.min(Math.max(limit, 1), MAX_LIMIT);
        LambdaQueryWrapper<Message> wrapper = new LambdaQueryWrapper<Message>()
                .eq(Message::getRoomId, roomId)
                .eq(Message::getStatus, 0)
                .orderByDesc(Message::getId)
                .last("limit " + (size + 1));
        if (cursor != null && cursor > 0) {
            wrapper.lt(Message::getId, cursor);
        }
        List<Message> rows = messageMapper.selectList(wrapper);
        boolean hasMore = rows.size() > size;
        if (hasMore) {
            rows = rows.subList(0, size);
        }
        List<Message> ordered = new ArrayList<>(rows);
        Collections.reverse(ordered);

        Map<Long, String> nicknames = nicknameMap(ordered.stream().map(Message::getSenderId).toList());
        List<MessageVO> items = ordered.stream()
                .map(m -> toVO(m, nicknames.get(m.getSenderId())))
                .toList();
        Long nextCursor = hasMore && !ordered.isEmpty() ? ordered.get(0).getId() : null;
        return new MessagePageVO(items, nextCursor, hasMore);
    }

    private Map<Long, String> nicknameMap(List<Long> userIds) {
        if (userIds.isEmpty()) {
            return Map.of();
        }
        return userMapper.selectList(new LambdaQueryWrapper<User>()
                        .in(User::getId, userIds.stream().distinct().toList()))
                .stream().collect(Collectors.toMap(User::getId, User::getNickname));
    }

    private String nicknameOf(Long userId) {
        User user = userMapper.selectById(userId);
        return user == null ? null : user.getNickname();
    }

    private MessageVO toVO(Message m, String senderNickname) {
        return new MessageVO(m.getId(), m.getRoomId(), m.getSenderId(), senderNickname,
                m.getMsgType(), m.getContent(), m.getStatus(), m.getCreatedAt());
    }
}
"""

# --------------------------------------------------------------- controller
F["chat/controller/ChatRoomController.java"] = """package com.zhiyu.campus.chat.controller;

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
"""

F["chat/controller/MessageController.java"] = """package com.zhiyu.campus.chat.controller;

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
"""

F["tag/controller/TagController.java"] = """package com.zhiyu.campus.tag.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.zhiyu.campus.common.ApiResponse;
import com.zhiyu.campus.tag.entity.Tag;
import com.zhiyu.campus.tag.mapper.TagMapper;
import io.swagger.v3.oas.annotations.Operation;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@io.swagger.v3.oas.annotations.tags.Tag(name = "标签")
@RestController
@RequestMapping("/api/v1/tags")
public class TagController {

    private final TagMapper tagMapper;

    public TagController(TagMapper tagMapper) {
        this.tagMapper = tagMapper;
    }

    @Operation(summary = "A-18 标签列表（按热度倒序）")
    @GetMapping
    public ApiResponse<List<Tag>> list(@RequestParam(required = false) Integer scope) {
        LambdaQueryWrapper<Tag> wrapper = new LambdaQueryWrapper<Tag>()
                .orderByDesc(Tag::getHeat)
                .orderByAsc(Tag::getId);
        if (scope != null) {
            wrapper.eq(Tag::getScope, scope);
        }
        return ApiResponse.ok(tagMapper.selectList(wrapper));
    }
}
"""


def main():
    for rel, content in F.items():
        path = os.path.join(ROOT, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
    print("files:", len(F))


if __name__ == "__main__":
    main()
