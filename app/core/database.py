from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

from app.core.config import settings

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    echo=settings.DB_ECHO,
    connect_args={"connect_timeout": 5},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


class Base(DeclarativeBase):
    pass


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = inspect(engine)
    columns = inspector.get_columns(table_name)
    return any(column["name"] == column_name for column in columns)


def sync_schema():
    with engine.begin() as connection:
        if not _column_exists("chat_sessions", "created_at"):
            connection.execute(
                text(
                    "ALTER TABLE chat_sessions "
                    "ADD COLUMN created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"
                )
            )

        if not _column_exists("messages", "created_at"):
            connection.execute(
                text(
                    "ALTER TABLE messages "
                    "ADD COLUMN created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"
                )
            )


def init_db():
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    sync_schema()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
