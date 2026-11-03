package com.zhiyu.campus.blog.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.zhiyu.campus.blog.entity.Favorite;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface FavoriteMapper extends BaseMapper<Favorite> {
}
