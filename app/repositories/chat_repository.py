from datetime import UTC, datetime, timedelta

from sqlalchemy import case
from sqlalchemy.orm import Session

from app.models.chat import ChatSession
from app.models.message import Message

MESSAGE_ROLE_ORDER = case(
    (Message.role == "user", 0),
    (Message.role == "assistant", 1),
    else_=2,
)


class ChatRepository:

    def _message_timestamp_pair(self) -> tuple[datetime, datetime]:
        user_created_at = datetime.now(UTC)
        assistant_created_at = user_created_at + timedelta(microseconds=1)
        return user_created_at, assistant_created_at

    def list_by_user(
        self,
        db: Session,
        user_id: str,
    ) -> list[ChatSession]:
        return (
            db.query(ChatSession)
            .filter(ChatSession.user_id == user_id)
            .order_by(ChatSession.created_at.desc())
            .all()
        )

    def get_by_id(
        self,
        db: Session,
        chat_id: str,
        user_id: str,
    ) -> ChatSession | None:
        return (
            db.query(ChatSession)
            .filter(
                ChatSession.id == chat_id,
                ChatSession.user_id == user_id,
            )
            .first()
        )

    def create(
        self,
        db: Session,
        user_id: str,
        title: str = "New chat",
    ) -> ChatSession:
        chat = ChatSession(
            user_id=user_id,
            title=title,
        )
        db.add(chat)
        db.commit()
        db.refresh(chat)

        return chat

    def create_session_with_messages(
        self,
        db: Session,
        user_id: str,
        user_content: str,
        assistant_content: str,
    ) -> ChatSession:
        title = user_content.strip()[:60] or "New chat"
        if len(user_content.strip()) > 60:
            title = f"{title}..."

        chat = ChatSession(
            user_id=user_id,
            title=title,
        )
        db.add(chat)
        db.flush()

        user_created_at, assistant_created_at = self._message_timestamp_pair()

        db.add(
            Message(
                chat_id=chat.id,
                role="user",
                content=user_content,
                created_at=user_created_at,
            )
        )
        db.add(
            Message(
                chat_id=chat.id,
                role="assistant",
                content=assistant_content,
                created_at=assistant_created_at,
            )
        )
        db.commit()
        db.refresh(chat)

        return chat

    def add_exchange(
        self,
        db: Session,
        chat_id: str,
        user_content: str,
        assistant_content: str,
    ) -> None:
        user_created_at, assistant_created_at = self._message_timestamp_pair()

        db.add(
            Message(
                chat_id=chat_id,
                role="user",
                content=user_content,
                created_at=user_created_at,
            )
        )
        db.add(
            Message(
                chat_id=chat_id,
                role="assistant",
                content=assistant_content,
                created_at=assistant_created_at,
            )
        )
        db.commit()

    def update_title(
        self,
        db: Session,
        chat: ChatSession,
        title: str,
    ) -> ChatSession:
        chat.title = title
        db.commit()
        db.refresh(chat)

        return chat

    def add_message(
        self,
        db: Session,
        chat_id: str,
        role: str,
        content: str,
    ) -> Message:
        message = Message(
            chat_id=chat_id,
            role=role,
            content=content,
        )
        db.add(message)
        db.commit()
        db.refresh(message)

        return message

    def get_messages(
        self,
        db: Session,
        chat_id: str,
    ) -> list[Message]:
        return (
            db.query(Message)
            .filter(Message.chat_id == chat_id)
            .order_by(
                Message.created_at.asc(),
                MESSAGE_ROLE_ORDER.asc(),
                Message.id.asc(),
            )
            .all()
        )

    def get_messages_page(
        self,
        db: Session,
        chat_id: str,
        limit: int = 30,
        before: datetime | None = None,
    ) -> tuple[list[Message], bool]:
        query = db.query(Message).filter(Message.chat_id == chat_id)

        if before is not None:
            query = query.filter(Message.created_at < before)

        rows = (
            query.order_by(
                Message.created_at.desc(),
                MESSAGE_ROLE_ORDER.desc(),
                Message.id.desc(),
            )
            .limit(limit + 1)
            .all()
        )

        has_more = len(rows) > limit
        rows = rows[:limit]
        rows.reverse()

        return rows, has_more
