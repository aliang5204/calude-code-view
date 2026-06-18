from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.database import get_db
from app.models import Conversation, Message
from app.schemas import (
    ConversationCreate, ConversationUpdate, ConversationOut, ConversationListItem, MessageOut
)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post("", response_model=ConversationOut)
async def create_conversation(data: ConversationCreate, db: AsyncSession = Depends(get_db)):
    conv = Conversation(**data.model_dump())
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


@router.get("", response_model=list[ConversationListItem])
async def list_conversations(
    tag: str = Query(default="", description="按标签过滤"),
    db: AsyncSession = Depends(get_db),
):
    # 子查询：每个会话的首条用户消息
    first_msg_subq = (
        select(Message.content)
        .where(Message.conversation_id == Conversation.id, Message.role == "user")
        .order_by(Message.created_at.asc())
        .limit(1)
        .correlate(Conversation)
        .scalar_subquery()
    )
    msg_count_subq = (
        select(func.count(Message.id))
        .where(Message.conversation_id == Conversation.id)
        .correlate(Conversation)
        .scalar_subquery()
    )

    query = select(
        Conversation.id,
        Conversation.title,
        Conversation.group_tag,
        Conversation.updated_at,
        first_msg_subq.label("first_message"),
        msg_count_subq.label("message_count"),
    )

    if tag:
        query = query.where(Conversation.group_tag == tag)

    query = query.order_by(desc(Conversation.updated_at))

    result = await db.execute(query)
    rows = result.all()

    return [
        ConversationListItem(
            id=row.id,
            title=row.title,
            group_tag=row.group_tag,
            first_message=row.first_message,
            message_count=row.message_count,
            updated_at=row.updated_at,
        )
        for row in rows
    ]


@router.get("/{conv_id}", response_model=ConversationOut)
async def get_conversation(conv_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Conversation).where(Conversation.id == conv_id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.patch("/{conv_id}", response_model=ConversationOut)
async def update_conversation(conv_id: int, data: ConversationUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Conversation).where(Conversation.id == conv_id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(conv, key, value)
    await db.commit()
    await db.refresh(conv)
    return conv


@router.delete("/{conv_id}")
async def delete_conversation(conv_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Conversation).where(Conversation.id == conv_id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db.delete(conv)
    await db.commit()
    return {"ok": True}


@router.get("/{conv_id}/messages", response_model=list[MessageOut])
async def get_messages(conv_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conv_id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()
    return messages
