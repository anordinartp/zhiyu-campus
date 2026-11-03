package com.zhiyu.campus.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.task.SimpleAsyncTaskExecutor;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

/** 异步执行器：用虚拟线程跑 AI 处理，避免占用业务线程。 */
@Configuration
@EnableAsync
@EnableScheduling
public class AsyncConfig {

    @Bean("aiExecutor")
    public SimpleAsyncTaskExecutor aiExecutor() {
        SimpleAsyncTaskExecutor executor = new SimpleAsyncTaskExecutor("ai-");
        executor.setVirtualThreads(true);
        executor.setConcurrencyLimit(20);   // 对应表 22 的并发上限
        return executor;
    }
}
