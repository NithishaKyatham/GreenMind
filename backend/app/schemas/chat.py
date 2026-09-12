from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ChatMessageIn(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatMessageOut(BaseModel):
    conversation_id: str
    reply: str
    mode: str  # "llm" | "rule_based_fallback"
    disclaimer: str


class ChatHistoryItem(BaseModel):
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
