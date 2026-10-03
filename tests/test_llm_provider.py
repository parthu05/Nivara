import unittest

from app.llm.provider import LLMProvider


class FakeGeminiClient:
    class _Chat:
        class _Completions:
            @staticmethod
            def create(**kwargs):
                raise RuntimeError("Gemini unavailable")

        completions = _Completions

    chat = _Chat()

    class _Embeddings:
        @staticmethod
        def create(**kwargs):
            raise RuntimeError("Gemini embedding failed")

    embeddings = _Embeddings()


class FakeOllamaClient:
    class _Chat:
        class _Completions:
            @staticmethod
            def create(**kwargs):
                class Resp:
                    choices = [type("Choice", (), {"message": type("Message", (), {"content": "Local fallback reply"})()})]

                return Resp()

        completions = _Completions

    chat = _Chat()

    class _Embeddings:
        @staticmethod
        def create(**kwargs):
            class Data:
                index = 0
                embedding = [0.1, 0.2]

            class Resp:
                data = [Data()]

            return Resp()

    embeddings = _Embeddings()


class LLMProviderFallbackTests(unittest.TestCase):
    def test_chat_falls_back_to_ollama_when_gemini_is_unavailable(self):
        provider = LLMProvider()
        provider.provider = "gemini"
        provider.client = FakeGeminiClient()
        provider.ollama_client = FakeOllamaClient()
        provider.ollama_available = True

        response = provider.chat([{"role": "user", "content": "hello"}])

        self.assertEqual(response, "Local fallback reply")

    def test_user_friendly_error_mentions_ollama_setup_steps(self):
        provider = LLMProvider()
        provider.provider = "gemini"
        provider.ollama_available = False

        message = provider.unavailable_message()

        self.assertIn("Gemini", message)
        self.assertIn("Ollama", message)
        self.assertIn("ollama.com/download", message)


if __name__ == "__main__":
    unittest.main()
