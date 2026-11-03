# -*- coding: utf-8 -*-
"""把 AI 异步处理接入发帖流程（事务提交后再触发，避免读到未提交数据）。"""
import io
import re

PATH = (r"C:\Users\saxtul\Documents\ds harness区\知屿校园\_build\gen_java_m3.py")

with io.open(PATH, encoding="utf-8") as fh:
    src = fh.read()

# 1) import
src = src.replace(
    "import com.zhiyu.campus.blog.vo.ReplyVO;",
    "import com.zhiyu.campus.blog.vo.ReplyVO;\n"
    "import com.zhiyu.campus.ai.service.AiAsyncProcessor;")

# 2) 字段
src = src.replace(
    "    private final InteractionService interactionService;",
    "    private final InteractionService interactionService;\n"
    "    private final AiAsyncProcessor aiAsyncProcessor;")

# 3) 构造参数
src = src.replace(
    "                       SensitiveWordChecker sensitiveWordChecker,\n"
    "                       InteractionService interactionService) {",
    "                       SensitiveWordChecker sensitiveWordChecker,\n"
    "                       InteractionService interactionService,\n"
    "                       AiAsyncProcessor aiAsyncProcessor) {")

# 4) 构造体赋值
src = src.replace(
    "        this.interactionService = interactionService;",
    "        this.interactionService = interactionService;\n"
    "        this.aiAsyncProcessor = aiAsyncProcessor;")

# 5) 发帖后触发
src = src.replace(
    "        bindTags(post.getId(), request.tagIds());\n"
    "        return toVO(post, board, loadTagNames(List.of(post.getId())), userId);",
    "        bindTags(post.getId(), request.tagIds());\n"
    "        submitAiAfterCommit(post.getId());\n"
    "        return toVO(post, board, loadTagNames(List.of(post.getId())), userId);")

# 6) 辅助方法
anchor = "    // ------------------------------------------------------------ 内部方法"
helper = (
    "    /** 事务提交后再触发 AI 处理，避免异步线程读不到新帖。 */\n"
    "    private void submitAiAfterCommit(Long postId) {\n"
    "        if (TransactionSynchronizationManager.isSynchronizationActive()) {\n"
    "            TransactionSynchronizationManager.registerSynchronization(\n"
    "                    new TransactionSynchronization() {\n"
    "                        @Override\n"
    "                        public void afterCommit() {\n"
    "                            aiAsyncProcessor.submit(postId);\n"
    "                        }\n"
    "                    });\n"
    "        } else {\n"
    "            aiAsyncProcessor.submit(postId);\n"
    "        }\n"
    "    }\n\n")
src = src.replace(anchor, helper + anchor)

# 7) 事务同步相关 import
src = src.replace(
    "import org.springframework.transaction.annotation.Transactional;",
    "import org.springframework.transaction.annotation.Transactional;\n"
    "import org.springframework.transaction.support.TransactionSynchronization;\n"
    "import org.springframework.transaction.support.TransactionSynchronizationManager;")

with io.open(PATH, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(src)

checks = {
    "AiAsyncProcessor import": "AiAsyncProcessor;" in src,
    "field": "private final AiAsyncProcessor aiAsyncProcessor" in src,
    "ctor param": "AiAsyncProcessor aiAsyncProcessor) {" in src,
    "trigger": "submitAiAfterCommit(post.getId());" in src,
    "helper": "afterCommit()" in src,
    "sync import": "TransactionSynchronizationManager;" in src,
}
for k, v in checks.items():
    print(("OK  " if v else "MISS ") + k)
