import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sse_starlette.sse import EventSourceResponse

from app.database import get_db, async_session as _async_session_factory
from app.models import Conversation, Message
from app.schemas import ChatSendRequest
from app.services.llm import stream_claude_response

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/{conv_id}/send")
async def send_message(conv_id: int, data: ChatSendRequest, db: AsyncSession = Depends(get_db)):
    # 获取会话
    result = await db.execute(select(Conversation).where(Conversation.id == conv_id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # 保存用户消息
    user_msg = Message(conversation_id=conv_id, role="user", content=data.content)
    db.add(user_msg)
    if not conv.title:
        conv.title = data.content[:30] + ("..." if len(data.content) > 30 else "")
    await db.commit()

    session_id = conv.claude_session_id or ""

    async def event_generator():
        full_reply = ""
        new_session_id = session_id

        try:
            async for event in stream_claude_response(
                prompt=data.content,
                session_id=session_id,
            ):
                event_type = event.get("type", "")

                if event_type == "system" and event.get("subtype") == "init":
                    sid = event.get("session_id", "")
                    if sid and not session_id:
                        new_session_id = sid

                elif event_type == "assistant":
                    msg = event.get("message", {})
                    for item in msg.get("content", []):
                        if item.get("type") == "text":
                            text = item.get("text", "")
                            full_reply += text
                            yield {
                                "event": "delta",
                                "data": json.dumps({"content": text}, ensure_ascii=False),
                            }
                        elif item.get("type") == "tool_use":
                            yield {
                                "event": "tool",
                                "data": json.dumps({
                                    "tool": item.get("name", "?"),
                                    "input": str(item.get("input", {}))[:200],
                                }, ensure_ascii=False),
                            }

                elif event_type == "result":
                    break

                elif event_type == "error":
                    yield {
                        "event": "error",
                        "data": json.dumps({"error": event.get("error", "Unknown")}),
                    }
                    return

            # 保存 AI 回复 + session_id
            if full_reply:
                async with _async_session_factory() as s:
                    s.add(Message(conversation_id=conv_id, role="assistant", content=full_reply))
                    if new_session_id and new_session_id != session_id:
                        await s.execute(
                            update(Conversation)
                            .where(Conversation.id == conv_id)
                            .values(claude_session_id=new_session_id)
                        )
                    await s.commit()

            yield {
                "event": "done",
                "data": json.dumps({"session_id": new_session_id}),
            }

        except Exception as e:
            import traceback
            detail = f"{type(e).__name__}: {e}"
            yield {
                "event": "error",
                "data": json.dumps({"error": detail}),
            }

    return EventSourceResponse(event_generator())
