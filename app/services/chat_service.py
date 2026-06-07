from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.chat import ChatSession
from app.models.user import User
from app.repositories.chat_repository import ChatRepository
from app.services.ai_service import AIService


class ChatService:

    def __init__(self):
        self.repository = ChatRepository()
        self._ai_service: AIService | None = None

    @property
    def ai_service(self) -> AIService:
        if self._ai_service is None:
            self._ai_service = AIService()
        return self._ai_service

    def _build_ai_messages(self, history) -> list[dict[str, str]]:
        ai_messages = [
            {
                "role": item.role,
                "content": item.content,
            }
            for item in history
        ]
        limit = settings.CHAT_HISTORY_LIMIT
        if limit > 0:
            ai_messages = ai_messages[-limit:]
        return ai_messages

    def _build_ai_messages_with_prompt(
        self,
        db: Session,
        chat_id: str,
        message: str,
    ) -> list[dict[str, str]]:
        history = self.repository.get_messages(db, chat_id)
        ai_messages = self._build_ai_messages(history)
        ai_messages.append(
            {
                "role": "user",
                "content": message,
            }
        )
        return ai_messages

    def list_sessions(
        self,
        db: Session,
        user: User,
    ) -> list[ChatSession]:
        return self.repository.list_by_user(db, user.id)

    def get_session(
        self,
        db: Session,
        user: User,
        chat_id: str,
    ) -> ChatSession | None:
        return self.repository.get_by_id(db, chat_id, user.id)

    def send_first_message(
        self,
        db: Session,
        user: User,
        message: str,
    ) -> tuple[ChatSession, str]:
        ai_messages = [
            {
                "role": "user",
                "content": message,
            }
        ]
        answer = self.ai_service.generate_response_with_history(ai_messages)

        chat = self.repository.create_session_with_messages(
            db,
            user.id,
            message,
            answer,
        )

        return chat, answer

    def send_message(
        self,
        db: Session,
        user: User,
        chat_id: str,
        message: str,
    ) -> tuple[ChatSession, str]:
        chat = self.repository.get_by_id(db, chat_id, user.id)

        if not chat:
            raise ValueError("Chat session not found")

        ai_messages = self._build_ai_messages_with_prompt(db, chat_id, message)
        answer = self.ai_service.generate_response_with_history(ai_messages)

        self.repository.add_exchange(db, chat_id, message, answer)

        return chat, answer

    def send_or_create_message(
        self,
        db: Session,
        user: User,
        message: str,
        chat_id: str | None = None,
    ) -> tuple[ChatSession, str]:
        if chat_id is None:
            return self.send_first_message(db, user, message)

        return self.send_message(db, user, chat_id, message)

    def send_first_message_stream(
        self,
        db: Session,
        user: User,
        message: str,
    ):
        ai_messages = [
            {
                "role": "user",
                "content": message,
            }
        ]

        chunks: list[str] = []

        for chunk in self.ai_service.generate_response_stream_with_history(
            ai_messages,
        ):
            chunks.append(chunk)
            yield chunk

        answer = "".join(chunks)

        if not answer:
            raise ValueError("AI returned an empty response")

        chat = self.repository.create_session_with_messages(
            db,
            user.id,
            message,
            answer,
        )

        yield ("session", chat)

    def send_message_stream(
        self,
        db: Session,
        user: User,
        chat_id: str,
        message: str,
    ):
        chat = self.repository.get_by_id(db, chat_id, user.id)

        if not chat:
            raise ValueError("Chat session not found")

        ai_messages = self._build_ai_messages_with_prompt(db, chat_id, message)

        chunks: list[str] = []

        for chunk in self.ai_service.generate_response_stream_with_history(
            ai_messages,
        ):
            chunks.append(chunk)
            yield chunk

        answer = "".join(chunks)

        if not answer:
            raise ValueError("AI returned an empty response")

        self.repository.add_exchange(db, chat_id, message, answer)

        yield ("session", chat)

    def send_or_create_message_stream(
        self,
        db: Session,
        user: User,
        message: str,
        chat_id: str | None = None,
    ):
        if chat_id is None:
            yield from self.send_first_message_stream(db, user, message)
            return

        yield from self.send_message_stream(db, user, chat_id, message)

    def get_session_messages_page(
        self,
        db: Session,
        user: User,
        chat_id: str,
        limit: int = 30,
        before=None,
    ) -> tuple[ChatSession, list, bool]:
        chat = self.repository.get_by_id(db, chat_id, user.id)

        if not chat:
            raise ValueError("Chat session not found")

        messages, has_more = self.repository.get_messages_page(
            db,
            chat_id,
            limit,
            before,
        )

        return chat, messages, has_more
