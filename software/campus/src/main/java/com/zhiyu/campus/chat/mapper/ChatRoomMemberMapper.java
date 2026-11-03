package com.zhiyu.campus.chat.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.zhiyu.campus.chat.entity.ChatRoomMember;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface ChatRoomMemberMapper extends BaseMapper<ChatRoomMember> {
}
