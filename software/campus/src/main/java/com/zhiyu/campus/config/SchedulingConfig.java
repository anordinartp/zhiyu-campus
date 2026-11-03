package com.zhiyu.campus.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableScheduling;

/** 开启定时任务：热度重算每小时执行一次。 */
@Configuration
@EnableScheduling
public class SchedulingConfig {
}
