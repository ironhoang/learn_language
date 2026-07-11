"""Abstract LLM provider interface — adding a new provider means adding one
class here and one factory entry, never touching stage code (Open/Closed)."""

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

_MOCK_STORY = json.dumps({
    "title": "Mock Story",
    "language": "english",
    "level": "A2",
    "paragraphs": ["Good morning everyone.", "Let's start the meeting."],
})

_MOCK_CHUNKS = json.dumps({
    "chunks": [
        {"sentence": "Good morning everyone.", "parts": ["Good morning", "everyone."]},
        {"sentence": "Let's start the meeting.", "parts": ["Let's start", "the meeting."]},
    ],
    "keywords": ["standup", "meeting"],
    "reusable_expressions": ["Good morning", "Let's start"],
    "sentence_patterns": ["Let's start ___"],
})

_MOCK_METADATA = json.dumps({
    "title": "Mock Story English\nA2 Listening Practice",
    "description": "Practice your English by listening and shadowing.",
    "hashtags": ["#english", "#shadowing", "#dailyenglish"],
})


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        ...


class MockLLMProvider(LLMProvider):
    """Test double used to verify pipeline wiring before/without real providers.

    With no override, it inspects the prompt to guess which stage is calling
    (each stage's prompt template asks for a different JSON shape) so a full
    mock pipeline run still passes schema validation for every stage.
    """

    def __init__(self, response: str | None = None):
        self.response = response

    def generate(self, prompt: str, **kwargs) -> str:
        if self.response is not None:
            return self.response
        if "hashtags" in prompt:
            return _MOCK_METADATA
        if "sentence_patterns" in prompt:
            return _MOCK_CHUNKS
        return _MOCK_STORY


class GeminiLLMProvider(LLMProvider):
    """google-genai text generation. Requires GEMINI_API_KEY or GOOGLE_API_KEY."""

    MODEL = "gemini-2.5-flash"

    def __init__(self):
        from google import genai

        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY (or GOOGLE_API_KEY) not set — see content-pipeline/.env.example"
            )
        self._client = genai.Client(api_key=api_key)

    def generate(self, prompt: str, **kwargs) -> str:
        from google.genai import types

        gen_config = None
        if kwargs.get("json_mode"):
            gen_config = types.GenerateContentConfig(response_mime_type="application/json")

        response = self._client.models.generate_content(
            model=self.MODEL,
            contents=prompt,
            config=gen_config,
        )
        return response.text


class DeepSeekLLMProvider(LLMProvider):
    """DeepSeek via its OpenAI-compatible API. Requires DEEPSEEK_API_KEY.

    Same base_url/model/max_tokens as this repo's existing
    scripts/generate_lesson_deepseek.py — that script hit a real truncation
    bug ("Unterminated string") from not setting max_tokens high enough for a
    full JSON response, so this reuses its already-fixed value (16000)
    instead of re-discovering the same bug here.
    """

    BASE_URL = "https://api.deepseek.com"
    MODEL = "deepseek-chat"

    def __init__(self):
        from openai import OpenAI

        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError("DEEPSEEK_API_KEY not set — see content-pipeline/.env.example")
        self._client = OpenAI(api_key=api_key, base_url=self.BASE_URL)

    def generate(self, prompt: str, **kwargs) -> str:
        response_format = {"type": "json_object"} if kwargs.get("json_mode") else None
        response = self._client.chat.completions.create(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format=response_format,
            max_tokens=16000,
        )
        return response.choices[0].message.content


_PROVIDERS: dict[str, type[LLMProvider]] = {
    "mock": MockLLMProvider,
    "gemini": GeminiLLMProvider,
    "deepseek": DeepSeekLLMProvider,
}


def get_llm_provider(name: str) -> LLMProvider:
    try:
        cls = _PROVIDERS[name]
    except KeyError:
        raise ValueError(f"Unknown LLM provider: {name!r}. Available: {list(_PROVIDERS)}")
    return cls()
