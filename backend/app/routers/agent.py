"""AI 智能体：总 agent + 三个子 agent。

总 agent 判断"这句话该交给谁"，子 agent 负责真正执行。
模型只在有密钥时用于路由判断；没密钥走关键词规则，功能不受影响。
"""

import json
import urllib.request
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from .. import config, db, errors
from ..deps import current_user
from .search import search as search_api

router = APIRouter(prefix="/api/v1/agent", tags=["AI 智能体"])

SYSTEM_PROMPT = (
    "你是校园社区平台的路由器。判断用户请求属于哪个域，只输出一行 JSON。\n"
    "可选域：chat 聊天室 / post 帖子 / search 搜索。\n"
    "输出格式：第一个字段名为 agent，值取 chat、post、search 之一。"
)


class AgentIn(BaseModel):
    message: str = Field(min_length=1, max_length=500)


# ------------------------------------------------------------------ 模型
def _llm_available() -> bool:
    return config.AI_ENABLED and bool(config.AI_API_KEY)


def _llm_route(text: str) -> str | None:
    """调用 OpenAI 兼容接口，只用来判断路由。失败返回 None。"""
    if not _llm_available():
        return None
    body = json.dumps({
        "model": config.AI_MODEL,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{config.AI_BASE_URL}/chat/completions",
        data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {config.AI_API_KEY}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=config.AI_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"].strip()
        content = content.replace("```json", "").replace("```", "").strip()
        agent = json.loads(content).get("agent", "")
        return agent if agent in ("chat", "post", "search") else None
    except Exception as exc:
        print(f"[agent] 模型路由失败，降级规则：{exc}")
        return None


def _rule_route(text: str) -> str:
    if any(k in text for k in ("聊天室", "房间", "群聊", "消息", "发言", "禁言", "自习室")):
        return "chat"
    if "说" in text or "发消息" in text:
        return "chat"
    if any(k in text for k in ("帖子", "发帖", "回帖", "博客", "楼主")):
        return "post"
    return "search"


# ------------------------------------------------------------------ 子 agent
def _chat_agent(user: dict, text: str) -> dict:
    room = None
    if "在" in text and ("说" in text or "发" in text):
        head = text.split("在", 1)[1]
        for sep in ("说", "发消息", "发"):
            if sep in head:
                room_name, content = head.split(sep, 1)
                content = content.lstrip("：: ").strip()
                room = db.query_one(
                    "SELECT * FROM chat_room WHERE name LIKE %s LIMIT 1",
                    (f"%{room_name.strip()}%",))
                if room and content:
                    now = datetime.now()
                    db.execute(
                        "INSERT INTO message (room_id, sender_id, msg_type, content, "
                        "status, ai_processed, created_at) VALUES (%s,%s,1,%s,0,0,%s)",
                        (room["id"], user["id"], content, now))
                    db.execute("UPDATE chat_room SET last_active_at=%s WHERE id=%s",
                               (now, room["id"]))
                    return {"agent": "chat", "action": "sendMessage",
                            "reply": f"已在「{room['name']}」发出：{content}",
                            "data": {"roomId": room["id"], "content": content}}
    if "加入" in text or "进入" in text:
        name = text.replace("加入", "").replace("进入", "").strip()
        room = db.query_one("SELECT * FROM chat_room WHERE name LIKE %s LIMIT 1",
                            (f"%{name}%",))
        if room:
            exists = db.query_one(
                "SELECT 1 AS x FROM chat_room_member WHERE room_id=%s AND user_id=%s",
                (room["id"], user["id"]))
            if not exists:
                db.execute(
                    "INSERT INTO chat_room_member (room_id, user_id, role, muted, joined_at) "
                    "VALUES (%s,%s,0,0,%s)", (room["id"], user["id"], datetime.now()))
                db.execute("UPDATE chat_room SET member_count = member_count + 1 "
                           "WHERE id=%s", (room["id"],))
            return {"agent": "chat", "action": "joinRoom",
                    "reply": f"已加入「{room['name']}」。",
                    "data": {"roomId": room["id"], "roomName": room["name"]}}

    rooms = db.query_all(
        "SELECT * FROM chat_room WHERE status=0 ORDER BY last_active_at DESC LIMIT 5")
    if not rooms:
        return {"agent": "chat", "action": "listRooms", "reply": "还没有聊天室。",
                "data": {"rooms": []}}
    names = "、".join(f"「{r['name']}」({r['member_count']}人)" for r in rooms)
    return {"agent": "chat", "action": "listRooms",
            "reply": f"当前有 {len(rooms)} 个聊天室：{names}。",
            "data": {"rooms": [{"id": r["id"], "name": r["name"],
                                "memberCount": r["member_count"]} for r in rooms]}}


def _post_agent(user: dict, text: str) -> dict:
    if "发帖" in text or "发布" in text:
        content = text.replace("发帖", "").replace("发布", "").strip("：: ")
        title = content[:20] if content else "无标题"
        board = db.query_one("SELECT * FROM board ORDER BY sort_no LIMIT 1")
        now = datetime.now()
        post_id = db.execute(
            "INSERT INTO post (board_id, author_id, title, body, status, view_count, "
            "like_count, favorite_count, created_at) VALUES (%s,%s,%s,%s,0,0,0,0,%s)",
            (board["id"], user["id"], title, content, now))
        return {"agent": "post", "action": "createPost",
                "reply": f"已发布到「{board['name']}」：{title}",
                "data": {"postId": post_id, "status": 0}}

    posts = db.query_all(
        "SELECT * FROM post WHERE status=0 ORDER BY created_at DESC LIMIT 5")
    if not posts:
        return {"agent": "post", "action": "listPosts", "reply": "还没有帖子。",
                "data": {"posts": []}}
    names = "、".join(f"「{p['title']}」" for p in posts)
    return {"agent": "post", "action": "listPosts",
            "reply": f"最新 {len(posts)} 篇帖子：{names}。",
            "data": {"posts": [{"id": p["id"], "title": p["title"],
                                "likeCount": p["like_count"]} for p in posts]}}


def _search_agent(user: dict, text: str) -> dict:
    keyword = text
    for w in ("帮我", "请", "搜索一下", "搜索", "搜一下", "搜", "查找", "找一下", "找",
              "查一下", "查询"):
        keyword = keyword.replace(w, "")
    keyword = keyword.strip() or text.strip()

    result = search_api(q=keyword, tagId=None, limit=5, user=user)
    items = result["data"]
    if not items:
        return {"agent": "search", "action": "search",
                "reply": f"没有找到和「{keyword}」相关的内容。",
                "data": {"keyword": keyword, "count": 0}}
    names = "、".join(f"《{i['title']}》(score {i['score']})" for i in items)
    return {"agent": "search", "action": "search",
            "reply": f"「{keyword}」找到 {len(items)} 条：{names}。"
                     "排序 = 0.5×相关度 + 0.3×热度 + 0.2×你的偏好。",
            "data": {"keyword": keyword, "items": items}}


# ------------------------------------------------------------------ 总入口
@router.post("/chat")
def agent_chat(body: AgentIn, user: dict = Depends(current_user)):
    text = body.message.strip()
    trace = []
    agent = _llm_route(text)
    if agent:
        trace.append(f"router:llm->{agent}")
    else:
        agent = _rule_route(text)
        trace.append(f"router:rules->{agent}")
    trace.append("model:" + (config.AI_MODEL if _llm_available() else "local-rules"))

    handler = {"chat": _chat_agent, "post": _post_agent, "search": _search_agent}[agent]
    result = handler(user, text)
    result["trace"] = trace
    return errors.ok(result)


@router.get("/info")
def agent_info(user: dict = Depends(current_user)):
    return errors.ok({
        "llmAvailable": _llm_available(),
        "model": config.AI_MODEL if _llm_available() else "local-rules",
        "subAgents": ["chat", "post", "search"],
    })
