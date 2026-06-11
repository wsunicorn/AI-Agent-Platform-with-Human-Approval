"""Ollama LLM provider using litellm."""

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


class OllamaProvider(LLMProvider):
    """Local Ollama provider via litellm."""

    provider_name = "ollama"

    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self._base_url = base_url

    async def complete(self, request: LLMRequest) -> LLMResponse:
        import litellm

        start = self._now_ms()

        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})

        kwargs: dict = {
            "model": f"ollama/{request.model}",
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "api_base": self._base_url,
        }
        if request.response_format:
            kwargs["response_format"] = request.response_format
        if request.stop:
            kwargs["stop"] = request.stop

        try:
            response = await litellm.acompletion(**kwargs)
        except litellm.exceptions.ServiceUnavailableError:
            logger.error("ollama_unavailable", base_url=self._base_url)
            raise
        except Exception as exc:
            logger.error(
                "ollama_call_failed",
                model=request.model,
                error=str(exc),
            )
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
            model=f"ollama/{request.model}",
            input=request.texts,
            api_base=self._base_url,
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
        import httpx

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False
