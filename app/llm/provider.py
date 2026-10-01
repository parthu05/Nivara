from __future__ import annotations

from openai import OpenAI

from app.config import settings


class LLMProvider:
    """Single interface so Ollama (dev) and hosted OpenAI-compatible APIs (prod) swap via env."""

    def __init__(self) -> None:
        self.provider = settings.llm_provider.lower().strip()
        if self.provider == "ollama":
            self.chat_model = settings.ollama_chat_model
            self.embed_model = settings.ollama_embed_model
            self.client = OpenAI(
                base_url=f"{settings.ollama_base_url.rstrip('/')}/v1",
                api_key="ollama",
            )
        else:
            self.chat_model = settings.openai_chat_model
            self.embed_model = settings.openai_embed_model
            self.client = OpenAI(
                base_url=settings.openai_base_url,
                api_key=settings.openai_api_key,
            )

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.4, max_tokens: int = 700) -> str:
        options = (
            {"extra_body": {"keep_alive": settings.ollama_keep_alive}}
            if self.provider == "ollama"
            else {}
        )
        response = self.client.chat.completions.create(
            model=self.chat_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **options,
        )
        return (response.choices[0].message.content or "").strip()

    def embed(self, texts: list[str]) -> list[list[float]]:
        options = (
            {"extra_body": {"keep_alive": settings.ollama_keep_alive}}
            if self.provider == "ollama"
            else {}
        )
        response = self.client.embeddings.create(
            model=self.embed_model, input=texts, **options
        )
        ordered = sorted(response.data, key=lambda item: item.index)
        return [item.embedding for item in ordered]


llm = LLMProvider()
