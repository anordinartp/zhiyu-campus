package com.zhiyu.campus.chat.service;

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
