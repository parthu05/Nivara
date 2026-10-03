from __future__ import annotations

from openai import OpenAI

from app.config import settings


class LLMProvider:
    """Single interface for local Ollama and cloud-hosted Gemini/OpenAI-compatible APIs."""

    def __init__(self) -> None:
        self.provider = settings.llm_provider.lower().strip()
        self.ollama_client = OpenAI(
            base_url=f"{settings.ollama_base_url.rstrip('/')}/v1",
            api_key="ollama",
        )
        self.ollama_available = False

        if self.provider == "ollama":
            self.chat_model = settings.ollama_chat_model
            self.embed_model = settings.ollama_embed_model
            self.client = self.ollama_client
        elif self.provider == "gemini":
            self.chat_model = settings.gemini_chat_model
            self.embed_model = settings.gemini_embed_model
            if settings.gemini_api_key:
                self.client = OpenAI(
                    base_url=settings.gemini_base_url.rstrip("/"),
                    api_key=settings.gemini_api_key,
                )
            else:
                self.client = None
        else:
            self.chat_model = settings.openai_chat_model
            self.embed_model = settings.openai_embed_model
            self.client = OpenAI(
                base_url=settings.openai_base_url,
                api_key=settings.openai_api_key,
            )

    def unavailable_message(self) -> str:
        return (
            "Google Gemini is currently unavailable. If you want to use Ollama instead, "
            "install it from https://ollama.com/download, start the app with `ollama serve`, "
            "then run `ollama pull llama3.2` and `ollama pull nomic-embed-text`. After that, set "
            "`LLM_PROVIDER=ollama` and restart the app."
        )

    def _execute_request(self, client, *, method: str, model: str, messages=None, texts=None, **kwargs):
        if method == "chat":
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs,
            )
            return (response.choices[0].message.content or "").strip()

        response = client.embeddings.create(model=model, input=texts, **kwargs)
        ordered = sorted(response.data, key=lambda item: item.index)
        return [item.embedding for item in ordered]

    def _try_ollama(self, *, method: str, model: str, messages=None, texts=None, **kwargs):
        try:
            result = self._execute_request(self.ollama_client, method=method, model=model, messages=messages, texts=texts, **kwargs)
            self.ollama_available = True
            return result
        except Exception:
            self.ollama_available = False
            raise

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.4, max_tokens: int = 700) -> str:
        if self.provider == "ollama":
            return self._try_ollama(
                method="chat",
                model=self.chat_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                extra_body={"keep_alive": settings.ollama_keep_alive},
            )

        if self.provider == "gemini":
            if self.client is None:
                return self._try_ollama(
                    method="chat",
                    model=self.chat_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    extra_body={"keep_alive": settings.ollama_keep_alive},
                )
            try:
                return self._execute_request(
                    self.client,
                    method="chat",
                    model=self.chat_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except Exception:
                try:
                    return self._try_ollama(
                        method="chat",
                        model=settings.ollama_chat_model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        extra_body={"keep_alive": settings.ollama_keep_alive},
                    )
                except Exception as exc:
                    raise RuntimeError(self.unavailable_message()) from exc

        response = self._execute_request(
            self.client,
            method="chat",
            model=self.chat_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self.provider == "ollama":
            return self._try_ollama(
                method="embed",
                model=self.embed_model,
                texts=texts,
                extra_body={"keep_alive": settings.ollama_keep_alive},
            )

        if self.provider == "gemini":
            if self.client is None:
                return self._try_ollama(
                    method="embed",
                    model=settings.ollama_embed_model,
                    texts=texts,
                    extra_body={"keep_alive": settings.ollama_keep_alive},
                )
            try:
                return self._execute_request(
                    self.client,
                    method="embed",
                    model=self.embed_model,
                    texts=texts,
                )
            except Exception:
                try:
                    return self._try_ollama(
                        method="embed",
                        model=settings.ollama_embed_model,
                        texts=texts,
                        extra_body={"keep_alive": settings.ollama_keep_alive},
                    )
                except Exception as exc:
                    raise RuntimeError(self.unavailable_message()) from exc

        response = self._execute_request(
            self.client,
            method="embed",
            model=self.embed_model,
            texts=texts,
        )
        return response


llm = LLMProvider()
