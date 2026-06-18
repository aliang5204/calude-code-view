import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sse_starlette.sse import EventSourceResponse

from app.database import get_db
from app.models import Conversation, Message, ApiConfig
from app.schemas import ChatSendRequest
from app.services.llm import stream_llm_response, build_messages

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/{conv_id}/send")
async def send_message(conv_id: int, data: ChatSendRequest, db: AsyncSession = Depends(get_db)):
    # 1. 获取会话
    result = await db.execute(select(Conversation).where(Conversation.id == conv_id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # 2. 获取 API 配置（优先使用会话绑定的，其次使用第一个启用的）
    api_config = None
    if conv.model_config_id:
        cfg_result = await db.execute(select(ApiConfig).where(ApiConfig.id == conv.model_config_id))
        api_config = cfg_result.scalar_one_or_none()

    if not api_config:
        cfg_result = await db.execute(select(ApiConfig).where(ApiConfig.is_active == True))
        api_config = cfg_result.scalar_one_or_none()

    if not api_config:
        raise HTTPException(status_code=400, detail="No API config available. Please configure one in Settings.")

    # 3. 保存用户消息
    user_msg = Message(conversation_id=conv_id, role="user", content=data.content)
    db.add(user_msg)

    # 4. 自动更新会话标题（使用首条消息的前30个字符）
    if not conv.title:
        conv.title = data.content[:30] + ("..." if len(data.content) > 30 else "")
    await db.flush()

    # 5. 加载全部历史消息（包含刚保存的用户消息）
    msgs_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conv_id)
        .order_by(Message.created_at.asc())
    )
    all_messages = msgs_result.scalars().all()

    # 6. 组装文件上下文（前端传过来的文件内容 + 后端挂载的目录）
    file_contexts_dict = {}
    if data.file_contexts:
        for fc in data.file_contexts:
            file_contexts_dict[fc.path] = fc.content

    # 7. 组装消息（按 1MB 上限自动截断旧消息）
    llm_messages = await build_messages(
        conversation_messages=list(all_messages),
        user_content=data.content,
        project_path=conv.project_path,
        file_paths_str=conv.file_paths,
        file_contexts=file_contexts_dict,
    )

    # 7. SSE 流式响应
    async def event_generator():
        full_reply = ""
        try:
            async for chunk in stream_llm_response(api_config, llm_messages):
                full_reply += chunk
                yield {"event": "delta", "data": json.dumps({"content": chunk}, ensure_ascii=False)}

            # 流结束后保存 AI 回复
            assistant_msg = Message(conversation_id=conv_id, role="assistant", content=full_reply)
            db.add(assistant_msg)
            await db.commit()

            yield {
                "event": "done",
                "data": json.dumps({"message_id": assistant_msg.id if assistant_msg.id else 0})
            }

        except Exception as e:
            # 即使出错也保存部分回复
            if full_reply:
                assistant_msg = Message(
                    conversation_id=conv_id,
                    role="assistant",
                    content=full_reply + f"\n\n[Error: {str(e)}]"
                )
                db.add(assistant_msg)
                await db.commit()
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_generator())
