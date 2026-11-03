package com.zhiyu.campus.chat.vo;

import java.util.List;

/**
 * 游标分页返回体：nextCursor 为空表示没有更多。
 * 与报告 7.4.1 第 3 条“列表统一用游标分页”一致。
 */
public record MessagePageVO(List<MessageVO> items, Long nextCursor, boolean hasMore) {
}
