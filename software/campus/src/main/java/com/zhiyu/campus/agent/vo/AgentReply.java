package com.zhiyu.campus.agent.vo;

import java.util.List;
import java.util.Map;

/** 智能体回复：说明交给哪个子 agent、做了什么、返回了什么数据。 */
public record AgentReply(
        String agent,
        String action,
        String reply,
        Map<String, Object> data,
        List<String> trace) {
}
