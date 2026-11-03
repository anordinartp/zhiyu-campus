package com.zhiyu.campus.tag.controller;

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
