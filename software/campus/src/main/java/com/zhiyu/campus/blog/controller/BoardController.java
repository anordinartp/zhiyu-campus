package com.zhiyu.campus.blog.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.zhiyu.campus.blog.entity.Board;
import com.zhiyu.campus.blog.mapper.BoardMapper;
import com.zhiyu.campus.blog.vo.BoardVO;
import com.zhiyu.campus.common.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@Tag(name = "板块")
@RestController
@RequestMapping("/api/v1/boards")
public class BoardController {

    private final BoardMapper boardMapper;

    public BoardController(BoardMapper boardMapper) {
        this.boardMapper = boardMapper;
    }

    @Operation(summary = "板块列表")
    @GetMapping
    public ApiResponse<List<BoardVO>> list() {
        List<BoardVO> boards = boardMapper.selectList(new LambdaQueryWrapper<Board>()
                        .orderByAsc(Board::getSortNo))
                .stream().map(b -> new BoardVO(b.getId(), b.getName(), b.getIntro(), b.getSortNo()))
                .toList();
        return ApiResponse.ok(boards);
    }
}
