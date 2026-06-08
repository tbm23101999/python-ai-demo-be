from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


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

    @field_validator("chat_id", mode="before")
    @classmethod
    def normalize_chat_id(cls, value):
        if value is None or value == "":
            return None
        return value


class SendMessageResponse(BaseModel):
    response: str
    session: ChatSessionSummary


class SendMessageStreamResponse(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        ser_json_by_alias=True,
    )

    ai_response: str = Field(serialization_alias="aiResponse")
    session: ChatSessionSummary


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
