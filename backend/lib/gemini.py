import json
import os
from typing import NoReturn

from google import genai
from google.genai.errors import APIError


class RateLimitError(Exception):
    pass


class GeminiClient:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash") -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def _handle_api_error(self, e: APIError) -> NoReturn:
        if e.code == 429:
            raise RateLimitError("AIの利用上限に達しました。しばらく時間をおいて再度お試しください。") from e
        raise

    def generate(self, prompt: str) -> str:
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
            )
        except APIError as e:
            self._handle_api_error(e)
        return response.text  # type: ignore[return-value]

    def generate_json(self, prompt: str) -> list | dict:
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
        except APIError as e:
            self._handle_api_error(e)
        return json.loads(response.text)  # type: ignore[arg-type]


def create_gemini_client(model: str = "gemini-2.5-flash") -> GeminiClient:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    return GeminiClient(api_key=api_key, model=model)
