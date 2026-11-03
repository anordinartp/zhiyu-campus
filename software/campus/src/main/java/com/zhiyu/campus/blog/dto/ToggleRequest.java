package com.zhiyu.campus.blog.dto;

/**
 * A-16 / A-17 的点赞与收藏入参。
 * liked 为空时按 true 处理；重复提交同一动作是幂等的（对应测试用例 TC-15）。
 */
public record ToggleRequest(Boolean liked) {

    public boolean target() {
        return liked == null || liked;
    }
}
