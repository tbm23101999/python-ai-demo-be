from google import genai
from google.genai.errors import APIError

from app.core.config import settings


class AIServiceError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AIService:

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise AIServiceError(
                "GEMINI_API_KEY is not set. Add it to your .env file.",
                status_code=500,
            )

        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options={
                "timeout": settings.GEMINI_TIMEOUT_MS,
            },
        )

    def generate_response(
        self,
        prompt: str
    ) -> str:
        return self.generate_response_with_history(
            [
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        )

    def generate_response_with_history(
        self,
        messages: list[dict[str, str]],
    ) -> str:
        contents = []

        for message in messages:
            role = "model" if message["role"] == "assistant" else "user"
            contents.append(
                {
                    "role": role,
                    "parts": [{"text": message["content"]}],
                }
            )

        try:
            response = self.client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=contents,
            )
        except APIError as exc:
            raise AIServiceError(
                f"Gemini API error: {exc.message or str(exc)}",
                status_code=exc.code if 400 <= exc.code < 600 else 502,
            ) from exc

        text = response.text
        if not text:
            raise AIServiceError(
                "Gemini returned an empty response.",
                status_code=502,
            )

        return text

    def generate_response_stream(
        self,
        prompt: str,
    ):
        return self.generate_response_stream_with_history(
            [
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        )

    def generate_response_stream_with_history(
        self,
        messages: list[dict[str, str]],
    ):
        contents = []

        for message in messages:
            role = "model" if message["role"] == "assistant" else "user"
            contents.append(
                {
                    "role": role,
                    "parts": [{"text": message["content"]}],
                }
            )

        try:
            for chunk in self.client.models.generate_content_stream(
                model=settings.GEMINI_MODEL,
                contents=contents,
            ):
                if chunk.text:
                    yield chunk.text
        except APIError as exc:
            raise AIServiceError(
                f"Gemini API error: {exc.message or str(exc)}",
                status_code=exc.code if 400 <= exc.code < 600 else 502,
            ) from exc
