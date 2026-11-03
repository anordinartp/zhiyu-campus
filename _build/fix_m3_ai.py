# -*- coding: utf-8 -*-
"""修正上一次补丁误伤：从 PostController 中移除多出的 aiAsyncProcessor 字段。"""
import io

PATH = r"C:\Users\saxtul\Documents\ds harness区\知屿校园\_build\gen_java_m3.py"

with io.open(PATH, encoding="utf-8") as fh:
    src = fh.read()

MARK = 'F["blog/controller/PostController.java"]'
idx = src.index(MARK)
head, tail = src[:idx], src[idx:]

bad = "    private final InteractionService interactionService;\n    private final AiAsyncProcessor aiAsyncProcessor;"
good = "    private final InteractionService interactionService;"

if bad in tail:
    tail = tail.replace(bad, good, 1)
    print("fixed PostController field")
else:
    print("pattern not found in PostController segment")

# 控制器也不需要这个 import
tail = tail.replace("import com.zhiyu.campus.ai.service.AiAsyncProcessor;\n", "", 1)

with io.open(PATH, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(head + tail)

print("AiAsyncProcessor in PostController:",
      "AiAsyncProcessor" in tail.split('F["blog/controller/BoardController.java"]')[0])
