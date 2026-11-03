package com.zhiyu.campus.chat.service;

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
