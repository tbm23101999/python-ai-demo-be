from datetime import datetime

from pydantic import BaseModel


class ChatSessionSummary(BaseModel):
    id: str
    title: str
    created_at: datetime


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime


class ChatSessionDetail(BaseModel):
    id: str
    title: str
    created_at: datetime
    messages: list[MessageResponse]
    has_more: bool = False


class SendMessageRequest(BaseModel):
    message: str


class SendOrCreateMessageRequest(BaseModel):
    message: str
    chat_id: str | None = None


class SendMessageResponse(BaseModel):
    response: str
    session: ChatSessionSummary


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
