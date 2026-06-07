import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatSessionDetail,
    ChatSessionSummary,
    MessageResponse,
    SendMessageRequest,
    SendMessageResponse,
    SendOrCreateMessageRequest,
)
from app.services.ai_service import AIService, AIServiceError
from app.services.chat_service import ChatService

router = APIRouter()

_ai_service: AIService | None = None
_chat_service = ChatService()


def get_ai_service() -> AIService:
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service


def to_session_summary(session) -> ChatSessionSummary:
    return ChatSessionSummary(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
    )


def to_message_response(message) -> MessageResponse:
    return MessageResponse(
        id=message.id,
        role=message.role,
        content=message.content,
        created_at=message.created_at,
    )


def _list_chat_sessions(
    db: Session,
    current_user: User,
) -> list[ChatSessionSummary]:
    sessions = _chat_service.list_sessions(db, current_user)

    if not sessions:
        return []

    return [to_session_summary(session) for session in sessions]


def _stream_message_chunks(
    db: Session,
    current_user: User,
    message: str,
    chat_id: str | None,
):
    is_new_chat = chat_id is None

    try:
        for chunk in _chat_service.send_or_create_message_stream(
            db,
            current_user,
            message,
            chat_id,
        ):
            if isinstance(chunk, tuple) and chunk[0] == "session":
                if is_new_chat:
                    session = chunk[1]
                    payload = json.dumps(
                        {
                            "session": {
                                "id": session.id,
                                "title": session.title,
                                "created_at": session.created_at.isoformat(),
                            }
                        }
                    )
                    yield f"\n__SESSION__{payload}__".encode("utf-8")
                continue

            yield chunk.encode("utf-8")
    except ValueError as exc:
        payload = json.dumps({"error": str(exc)})
        yield f"[ERROR] {payload}".encode("utf-8")
    except AIServiceError as exc:
        payload = json.dumps({"error": exc.message})
        yield f"[ERROR] {payload}".encode("utf-8")


@router.get("", response_model=list[ChatSessionSummary])
def list_chat_sessions_get(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _list_chat_sessions(db, current_user)


@router.post("", response_model=list[ChatSessionSummary])
def list_chat_sessions_post(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _list_chat_sessions(db, current_user)


@router.post("/messages", response_model=SendMessageResponse)
async def send_or_create_message(
    request: SendOrCreateMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        session, answer = await asyncio.to_thread(
            _chat_service.send_or_create_message,
            db,
            current_user,
            request.message,
            request.chat_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AIServiceError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc

    return SendMessageResponse(
        response=answer,
        session=to_session_summary(session),
    )


@router.post("/messages/stream")
async def send_or_create_message_stream(
    request: SendOrCreateMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    headers = {}
    if request.chat_id:
        headers["X-Chat-Session-Id"] = request.chat_id

    return StreamingResponse(
        _stream_message_chunks(
            db,
            current_user,
            request.message,
            request.chat_id,
        ),
        media_type="text/plain; charset=utf-8",
        headers=headers,
    )


@router.post(
    "/ask",
    response_model=ChatResponse,
)
async def ask_ai(
    request: ChatRequest,
):
    try:
        answer = await asyncio.to_thread(
            get_ai_service().generate_response,
            request.message,
        )
    except AIServiceError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc

    return ChatResponse(
        response=answer
    )


@router.post("/ask/stream")
async def ask_ai_stream(
    request: ChatRequest,
):
    def generate():
        try:
            for chunk in get_ai_service().generate_response_stream(
                request.message,
            ):
                yield chunk.encode("utf-8")
        except AIServiceError as exc:
            yield f"[ERROR] {exc.message}".encode("utf-8")

    return StreamingResponse(
        generate(),
        media_type="text/plain; charset=utf-8",
    )


@router.get("/{chat_id}", response_model=ChatSessionDetail)
def get_chat_session(
    chat_id: str,
    limit: int = Query(default=30, ge=1, le=100),
    before: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    before_dt = None

    if before:
        from datetime import datetime

        try:
            before_dt = datetime.fromisoformat(before.replace("Z", "+00:00"))
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="Invalid before timestamp",
            ) from exc

    try:
        session, messages, has_more = _chat_service.get_session_messages_page(
            db,
            current_user,
            chat_id,
            limit,
            before_dt,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ChatSessionDetail(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        messages=[to_message_response(message) for message in messages],
        has_more=has_more,
    )


@router.post("/{chat_id}/messages", response_model=SendMessageResponse)
async def send_chat_message(
    chat_id: str,
    request: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        session, answer = await asyncio.to_thread(
            _chat_service.send_message,
            db,
            current_user,
            chat_id,
            request.message,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AIServiceError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc

    return SendMessageResponse(
        response=answer,
        session=to_session_summary(session),
    )


@router.post("/{chat_id}/messages/stream")
async def send_chat_message_stream(
    chat_id: str,
    request: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return StreamingResponse(
        _stream_message_chunks(
            db,
            current_user,
            request.message,
            chat_id,
        ),
        media_type="text/plain; charset=utf-8",
        headers={"X-Chat-Session-Id": chat_id},
    )
