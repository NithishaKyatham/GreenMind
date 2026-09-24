import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.chat import ChatMessage
from app.agent.agent_service import get_agent_reply
from app.agent.tools.base import ToolContext
from app.schemas.chat import ChatMessageIn, ChatMessageOut, ChatHistoryItem

router = APIRouter(prefix="/chatbot", tags=["AI Assistant"])

DISCLAIMER = (
    "GreenMind Assistant provides general agricultural guidance and does not "
    "replace a qualified agricultural expert, especially for severe or uncertain cases."
)


@router.post("/message", response_model=ChatMessageOut)
async def send_message(
    payload: ChatMessageIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation_id = payload.conversation_id or str(uuid.uuid4())

    # Pull recent context for this conversation.
    prior = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.user_id == current_user.id,
            ChatMessage.conversation_id == conversation_id,
        )
        .order_by(ChatMessage.created_at.asc())
        .limit(10)
        .all()
    )

    history = [(m.role, m.content) for m in prior]

    # Build the tool context from the authenticated user.
    ctx = ToolContext(db=db, current_user=current_user)

    reply_text, mode, tools_used = await get_agent_reply(
        ctx=ctx,
        message=payload.message,
        history=history,
        locale=payload.locale,
    )

    db.add(
        ChatMessage(
            user_id=current_user.id,
            conversation_id=conversation_id,
            role="user",
            content=payload.message,
        )
    )

    db.add(
        ChatMessage(
            user_id=current_user.id,
            conversation_id=conversation_id,
            role="assistant",
            content=reply_text,
        )
    )

    db.commit()

    return ChatMessageOut(
        conversation_id=conversation_id,
        reply=reply_text,
        mode=mode,
        disclaimer=DISCLAIMER,
        tools_used=tools_used,
    )


@router.get(
    "/history/{conversation_id}",
    response_model=list[ChatHistoryItem],
)
def get_chat_history(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(ChatMessage)
        .filter(
            ChatMessage.user_id == current_user.id,
            ChatMessage.conversation_id == conversation_id,
        )
        .order_by(ChatMessage.created_at.asc())
        .all()
    )