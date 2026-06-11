"""Gemini LLM provider using litellm."""

from __future__ import annotations

import structlog

from app.llm.provider import (
    EmbeddingRequest,
    EmbeddingResponse,
    LLMProvider,
    LLMRequest,
    LLMResponse,
)

logger = structlog.get_logger(__name__)


class GeminiProvider(LLMProvider):
    """Google Gemini provider via litellm."""

    provider_name = "gemini"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def complete(self, request: LLMRequest) -> LLMResponse:
        import litellm

        start = self._now_ms()

        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})

        kwargs: dict = {
            "model": f"gemini/{request.model}",
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "api_key": self._api_key,
        }
        if request.response_format:
            kwargs["response_format"] = request.response_format
        if request.stop:
            kwargs["stop"] = request.stop

        try:
            response = await litellm.acompletion(**kwargs)
        except litellm.exceptions.AuthenticationError:
            logger.error("gemini_auth_failed", model=request.model)
            raise
        except litellm.exceptions.RateLimitError:
            logger.warning("gemini_rate_limited", model=request.model)
            raise
        except Exception as exc:
            logger.error("gemini_call_failed", model=request.model, error=str(exc))
            raise

        elapsed = self._now_ms() - start
        choice = response.choices[0]
        usage = response.usage or {}

        return LLMResponse(
            content=choice.message.content or "",
            model=request.model,
            provider=self.provider_name,
            input_tokens=getattr(usage, "prompt_tokens", 0),
            output_tokens=getattr(usage, "completion_tokens", 0),
            total_tokens=getattr(usage, "total_tokens", 0),
            latency_ms=elapsed,
            finish_reason=getattr(choice, "finish_reason", ""),
        )

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        import litellm

        start = self._now_ms()

        response = await litellm.aembedding(
            model=f"gemini/{request.model}",
            input=request.texts,
            api_key=self._api_key,
        )

        elapsed = self._now_ms() - start
        embeddings = [item["embedding"] for item in response.data]
        dimensions = len(embeddings[0]) if embeddings else 0

        return EmbeddingResponse(
            embeddings=embeddings,
            model=request.model,
            provider=self.provider_name,
            dimensions=dimensions,
            total_tokens=getattr(response.usage, "total_tokens", 0),
            latency_ms=elapsed,
        )

    async def health_check(self) -> bool:
        try:
            response = await self.complete(
                LLMRequest(
                    messages=[{"role": "user", "content": "ping"}],
                    model="gemini-3.1-flash-lite",
                    max_tokens=5,
                )
            )
            return bool(response.content)
        except Exception:
            return False
