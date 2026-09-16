from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class ChatMessageIn(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    locale: Optional[str] = None


class ChatMessageOut(BaseModel):
    conversation_id: str
    reply: str
    mode: str  # "llm" | "rule_based_fallback"
    disclaimer: str
    tools_used: List[str] = Field(default_factory=list)


class ChatHistoryItem(BaseModel):
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True