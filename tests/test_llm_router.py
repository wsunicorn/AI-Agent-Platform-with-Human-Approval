from unittest.mock import AsyncMock, patch

import pytest

from app.core.config import Settings
from app.llm.provider import LLMMessage, LLMRequest, LLMResponse
from app.llm.router import ModelRouter, TaskPurpose, reset_model_router


@pytest.fixture(autouse=True)
def cleanup_router() -> None:
    reset_model_router()
    yield
    reset_model_router()


@pytest.mark.asyncio
async def test_router_initialization_no_gemini() -> None:
    settings = Settings(gemini_api_key="", ollama_base_url="http://localhost:11434")
    with patch("app.llm.router.get_settings", return_value=settings):
        # Patching providers so we don't try to connect to Ollama health check
        with patch("app.llm.router.OllamaProvider", spec=True):
            router = ModelRouter()
            assert "gemini" not in router._providers
            assert "ollama" in router._providers


@pytest.mark.asyncio
async def test_router_initialization_with_gemini() -> None:
    settings = Settings(gemini_api_key="fake_key", ollama_base_url="http://localhost:11434")
    with patch("app.llm.router.get_settings", return_value=settings):
        with patch("app.llm.router.OllamaProvider", spec=True):
            with patch("app.llm.router.GeminiProvider", spec=True):
                router = ModelRouter()
                assert "gemini" in router._providers
                assert "ollama" in router._providers


@pytest.mark.asyncio
async def test_router_complete_fallback_chain() -> None:
    settings = Settings(gemini_api_key="fake_key")
    with patch("app.llm.router.get_settings", return_value=settings):
        gemini_mock = AsyncMock()
        ollama_mock = AsyncMock()

        # Let Gemini fail, and Ollama succeed
        gemini_mock.complete.side_effect = RuntimeError("Gemini over quota")
        ollama_mock.complete.return_value = LLMResponse(
            content="Hello from Ollama",
            model="gemma3:4b",
            prompt_tokens=10,
            completion_tokens=5,
            latency_ms=100.0,
        )

        with patch("app.llm.router.GeminiProvider", return_value=gemini_mock):
            with patch("app.llm.router.OllamaProvider", return_value=ollama_mock):
                router = ModelRouter()
                request = LLMRequest(
                    messages=[LLMMessage(role="user", content="Hi")],
                    model="default",
                )
                response = await router.complete(request, purpose=TaskPurpose.DEFAULT)

                assert response.content == "Hello from Ollama"
                gemini_mock.complete.assert_called_once()
                ollama_mock.complete.assert_called_once()


@pytest.mark.asyncio
async def test_pii_redaction() -> None:
    settings = Settings(gemini_api_key="fake_key")
    with patch("app.llm.router.get_settings", return_value=settings):
        gemini_mock = AsyncMock()
        gemini_mock.complete.return_value = LLMResponse(
            content="Sure",
            model="gemini-3.1-flash-lite",
            prompt_tokens=5,
            completion_tokens=2,
            latency_ms=50.0,
        )

        with patch("app.llm.router.GeminiProvider", return_value=gemini_mock):
            with patch("app.llm.router.OllamaProvider", spec=True):
                router = ModelRouter()
                request = LLMRequest(
                    messages=[
                        LLMMessage(
                            role="user",
                            content=(
                                "My email is test@example.com and phone is "
                                "123-456-7890."
                            ),
                        )
                    ],
                    model="default",
                )
                await router.complete(request, purpose=TaskPurpose.DEFAULT, redact_pii=True)

                # The content passed to gemini should be redacted
                called_request = gemini_mock.complete.call_args[0][0]
                assert "test@example.com" not in called_request.messages[0].content
                assert "123-456-7890" not in called_request.messages[0].content
                assert "[EMAIL_REDACTED" in called_request.messages[0].content
                assert "[PHONE_REDACTED" in called_request.messages[0].content
