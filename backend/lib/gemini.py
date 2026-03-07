import json
import os

import google.generativeai as genai


class GeminiClient:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash") -> None:
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model)

    def generate(self, prompt: str) -> str:
        response = self._model.generate_content(prompt)
        return response.text

    def generate_json(self, prompt: str) -> list | dict:
        response = self._model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
            ),
        )
        return json.loads(response.text)


def create_gemini_client(model: str = "gemini-2.5-flash") -> GeminiClient:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    return GeminiClient(api_key=api_key, model=model)
