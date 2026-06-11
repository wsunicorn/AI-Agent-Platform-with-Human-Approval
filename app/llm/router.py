"""Model router: maps task purposes to providers with fallback chains."""

from __future__ import annotations

from enum import StrEnum

import structlog

from app.core.config import get_settings
from app.llm.gemini import GeminiProvider
from app.llm.ollama import OllamaProvider
from app.llm.provider import (
    EmbeddingRequest,
    EmbeddingResponse,
    LLMProvider,
    LLMRequest,
    LLMResponse,
    TokenUsageTracker,
)
from app.llm.redactor import PIIRedactor, RedactionResult

logger = structlog.get_logger(__name__)


class TaskPurpose(StrEnum):
    """Task purposes that map to specific model configurations."""

    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    DRAFTING = "drafting"
    ROUTING = "routing"
    QUALITY = "quality"
    EMBEDDING = "embedding"
    RERANKING = "reranking"
    DEFAULT = "default"


# Maps task purposes to ordered fallback chains of (provider_name, model_name).
_DEFAULT_ROUTING: dict[TaskPurpose, list[tuple[str, str]]] = {
    TaskPurpose.CLASSIFICATION: [
        ("gemini", "gemini-3.1-flash-lite"),
        ("ollama", "gemma3:4b"),
        ("ollama", "qwen2.5:3b"),
    ],
    TaskPurpose.EXTRACTION: [
        ("gemini", "gemini-3.1-flash-lite"),
        ("ollama", "gemma3:4b"),
        ("ollama", "qwen2.5:3b"),
    ],
    TaskPurpose.DRAFTING: [
        ("gemini", "gemini-3.1-flash-lite"),
        ("ollama", "qwen3:8b"),
        ("ollama", "gemma3:4b"),
    ],
    TaskPurpose.ROUTING: [
        ("gemini", "gemini-3.1-flash-lite"),
        ("ollama", "qwen2.5:3b"),
    ],
    TaskPurpose.QUALITY: [
        ("gemini", "gemini-3.5-flash"),
        ("gemini", "gemini-3.1-flash-lite"),
        ("ollama", "qwen3:8b"),
    ],
    TaskPurpose.EMBEDDING: [
        ("ollama", "nomic-embed-text-v2-moe"),
    ],
    TaskPurpose.RERANKING: [
        ("gemini", "gemini-3.1-flash-lite"),
        ("ollama", "gemma3:4b"),
    ],
    TaskPurpose.DEFAULT: [
        ("gemini", "gemini-3.1-flash-lite"),
        ("ollama", "gemma3:4b"),
    ],
}


class ModelRouter:
    """Routes LLM requests to the appropriate provider with fallback."""

    def __init__(self) -> None:
        settings = get_settings()
        self._providers: dict[str, LLMProvider] = {}
        self._tracker = TokenUsageTracker()
        self._redactor = PIIRedactor()

        # Initialize Gemini if API key is available.
        if settings.gemini_api_key:
            self._providers["gemini"] = GeminiProvider(
                api_key=settings.gemini_api_key,
            )
            logger.info("gemini_provider_initialized")
        else:
            logger.warning("gemini_provider_skipped", reason="no API key")

        # Initialize Ollama (always available for local models).
        self._providers["ollama"] = OllamaProvider(
            base_url=settings.ollama_base_url,
        )
        logger.info("ollama_provider_initialized", base_url=settings.ollama_base_url)

    def get_provider(self, provider_name: str) -> LLMProvider | None:
        """Get a specific provider by name."""
        return self._providers.get(provider_name)

    def _get_chain(self, purpose: TaskPurpose) -> list[tuple[str, str]]:
        """Get the fallback chain for a given task purpose."""
        return _DEFAULT_ROUTING.get(purpose, _DEFAULT_ROUTING[TaskPurpose.DEFAULT])

    async def complete(
        self,
        request: LLMRequest,
        purpose: TaskPurpose = TaskPurpose.DEFAULT,
        redact_pii: bool = True,
    ) -> LLMResponse:
        """Complete an LLM request with automatic routing and fallback.

        If a model is specified in the request, it uses that directly.
        Otherwise, it routes by purpose through the fallback chain.
        """
        chain = self._get_chain(purpose)

        errors: list[str] = []
        for provider_name, model_name in chain:
            provider = self._providers.get(provider_name)
            if provider is None:
                continue

            # Apply PII redaction for hosted providers.
            actual_request = request.model_copy()
            actual_request.model = model_name
            redaction_result: RedactionResult | None = None

            if redact_pii and provider_name != "ollama":
                for i, msg in enumerate(actual_request.messages):
                    result = self._redactor.redact(msg.content)
                    if result.redaction_count > 0:
                        actual_request.messages[i].content = result.redacted_text
                        redaction_result = result
                if actual_request.system_prompt:
                    result = self._redactor.redact(actual_request.system_prompt)
                    if result.redaction_count > 0:
                        actual_request.system_prompt = result.redacted_text

            try:
                response = await provider.complete(actual_request)
                self._tracker.record(response)
                logger.info(
                    "llm_complete_success",
                    provider=provider_name,
                    model=model_name,
                    purpose=purpose,
                    tokens=response.total_tokens,
                    latency_ms=round(response.latency_ms, 1),
                )
                return response
            except Exception as exc:
                error_msg = f"{provider_name}/{model_name}: {exc}"
                errors.append(error_msg)
                logger.warning(
                    "llm_provider_failed",
                    provider=provider_name,
                    model=model_name,
                    error=str(exc),
                )
                continue

        raise RuntimeError(
            f"All LLM providers failed for purpose={purpose}. "
            f"Errors: {'; '.join(errors)}"
        )

    async def complete_json(
        self,
        request: LLMRequest,
        purpose: TaskPurpose = TaskPurpose.DEFAULT,
        redact_pii: bool = True,
    ) -> dict:
        """Complete an LLM request and parse the result as JSON."""
        import json

        if request.response_format is None:
            request.response_format = {"type": "json_object"}

        response = await self.complete(
            request, purpose=purpose, redact_pii=redact_pii
        )

        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            return json.loads(content.strip())

    async def embed(
        self,
        texts: list[str],
        purpose: TaskPurpose = TaskPurpose.EMBEDDING,
    ) -> EmbeddingResponse:
        """Generate embeddings using the configured embedding provider."""
        chain = self._get_chain(purpose)

        for provider_name, model_name in chain:
            provider = self._providers.get(provider_name)
            if provider is None:
                continue

            try:
                response = await provider.embed(
                    EmbeddingRequest(texts=texts, model=model_name)
                )
                self._tracker.record(response)
                logger.info(
                    "embedding_success",
                    provider=provider_name,
                    model=model_name,
                    count=len(texts),
                    latency_ms=round(response.latency_ms, 1),
                )
                return response
            except Exception as exc:
                logger.warning(
                    "embedding_provider_failed",
                    provider=provider_name,
                    model=model_name,
                    error=str(exc),
                )
                continue

        raise RuntimeError("All embedding providers failed.")

    def get_usage_stats(self) -> dict:
        """Return token usage statistics."""
        return self._tracker.get_stats()

    async def health(self) -> dict[str, bool]:
        """Check health of all providers."""
        result = {}
        for name, provider in self._providers.items():
            result[name] = await provider.health_check()
        return result


# Module-level singleton.
_router: ModelRouter | None = None


def get_model_router() -> ModelRouter:
    """Get or create the singleton ModelRouter."""
    global _router
    if _router is None:
        _router = ModelRouter()
    return _router


def reset_model_router() -> None:
    """Reset the singleton (for testing)."""
    global _router
    _router = None
