package com.zhiyu.campus.agent;

import com.zhiyu.campus.chat.dto.SendMessageRequest;
import com.zhiyu.campus.chat.service.ChatRoomService;
import com.zhiyu.campus.chat.service.MessageService;
import com.zhiyu.campus.chat.vo.MessagePageVO;
import com.zhiyu.campus.chat.vo.RoomVO;
import com.zhiyu.campus.agent.vo.AgentReply;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** 聊天室子 agent：查房间、进房间、发消息、看消息。 */
@Component
public class ChatSubAgent {

    private static final Pattern SEND = Pattern.compile("(?:在|给)(.{1,20}?)(?:说|发|发消息)[：: ]+(.+)");

    private final ChatRoomService roomService;
    private final MessageService messageService;

    public ChatSubAgent(ChatRoomService roomService, MessageService messageService) {
        this.roomService = roomService;
        this.messageService = messageService;
    }

    public AgentReply handle(Long userId, String text) {
        try {
            Matcher m = SEND.matcher(text);
            if (m.find()) {
                return send(userId, m.group(1).trim(), m.group(2).trim());
            }
            if (text.matches(".*(加入|进入).*")) {
                return join(userId, text.replaceAll(".*(加入|进入)", "").trim());
            }
            if (text.matches(".*(消息|聊天记录).*")) {
                return readMessages(userId, text);
            }
            return listRooms(userId);
        } catch (Exception e) {
            return new AgentReply("chat", "error", "聊天室操作失败：" + e.getMessage(),
                    Map.of(), List.of("chat"));
        }
    }

    private AgentReply listRooms(Long userId) {
        List<RoomVO> rooms = roomService.list(userId, null, 1, 5);
        StringBuilder sb = new StringBuilder("当前有 " + rooms.size() + " 个聊天室：");
        List<Map<String, Object>> items = new ArrayList<>();
        for (RoomVO r : rooms) {
            sb.append("「").append(r.name()).append("」(").append(r.memberCount()).append(" 人) ");
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("id", r.id());
            item.put("name", r.name());
            item.put("memberCount", r.memberCount());
            item.put("tags", r.tags());
            items.add(item);
        }
        sb.append("。想看某个房间的消息，对我说“看 XX 的消息”。");
        return new AgentReply("chat", "listRooms", sb.toString(), Map.of("rooms", items), List.of("chat"));
    }

    private AgentReply join(Long userId, String roomName) {
        List<RoomVO> rooms = roomService.list(userId, null, 1, 50);
        for (RoomVO r : rooms) {
            if (roomName.isEmpty() || r.name().contains(roomName) || roomName.contains(r.name())) {
                roomService.join(userId, r.id());
                return new AgentReply("chat", "joinRoom", "已加入「" + r.name() + "」。",
                        Map.of("roomId", r.id(), "roomName", r.name()), List.of("chat"));
            }
        }
        return new AgentReply("chat", "joinRoom", "没找到叫「" + roomName + "」的聊天室。",
                Map.of(), List.of("chat"));
    }

    private AgentReply send(Long userId, String roomName, String content) {
        List<RoomVO> rooms = roomService.list(userId, null, 1, 50);
        for (RoomVO r : rooms) {
            if (r.name().contains(roomName) || roomName.contains(r.name())) {
                messageService.send(userId, r.id(), new SendMessageRequest(1, content));
                return new AgentReply("chat", "sendMessage",
                        "已在「" + r.name() + "」发出：" + content,
                        Map.of("roomId", r.id(), "content", content), List.of("chat"));
            }
        }
        return new AgentReply("chat", "sendMessage", "没找到叫「" + roomName + "」的聊天室。",
                Map.of(), List.of("chat"));
    }

    private AgentReply readMessages(Long userId, String text) {
        List<RoomVO> rooms = roomService.list(userId, null, 1, 50);
        for (RoomVO r : rooms) {
            if (text.contains(r.name())) {
                MessagePageVO page = messageService.history(userId, r.id(), null, 5);
                StringBuilder sb = new StringBuilder("「" + r.name() + "」最近 " + page.items().size() + " 条消息：");
                for (var msg : page.items()) {
                    sb.append(msg.senderNickname()).append("：").append(msg.content()).append("；");
                }
                return new AgentReply("chat", "readMessages", sb.toString(),
                        Map.of("roomId", r.id(), "count", page.items().size()), List.of("chat"));
            }
        }
        return listRooms(userId);
    }
}
