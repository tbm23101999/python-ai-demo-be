from dotenv import load_dotenv
import os

load_dotenv()


class Settings:
    GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    GEMINI_TIMEOUT_MS = int(os.getenv("GEMINI_TIMEOUT_MS", 60000))
    CHAT_HISTORY_LIMIT = int(os.getenv("CHAT_HISTORY_LIMIT", 20))
    DB_ECHO = os.getenv("DB_ECHO", "false").lower() == "true"
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
    JWT_EXPIRE_MINUTES = int(
        os.getenv("JWT_EXPIRE_MINUTES", 60)
    )


settings = Settings()
