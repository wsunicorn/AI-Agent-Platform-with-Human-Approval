"""Abstract LLM provider interface and shared types."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class LLMMessage(BaseModel):
    """A single message in a conversation."""

    role: str = "user"
    content: str = ""


class LLMRequest(BaseModel):
    """Unified request to any LLM provider."""

    messages: list[LLMMessage]
    model: str
    temperature: float = 0.3
    max_tokens: int = 2048
    response_format: dict[str, Any] | None = None
    system_prompt: str | None = None
    stop: list[str] | None = None


class LLMResponse(BaseModel):
    """Unified response from any LLM provider."""

    content: str = ""
    model: str = ""
    provider: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    finish_reason: str = ""
    raw: dict[str, Any] = Field(default_factory=dict)


class EmbeddingRequest(BaseModel):
    """Request for embedding generation."""

    texts: list[str]
    model: str


class EmbeddingResponse(BaseModel):
    """Response with embedding vectors."""

    embeddings: list[list[float]]
    model: str
    provider: str
    dimensions: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    provider_name: str = "base"

    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Generate a completion from the LLM."""
        ...

    async def complete_json(self, request: LLMRequest) -> dict[str, Any]:
        """Generate a JSON completion. Parses the response content as JSON."""
        import json

        if request.response_format is None:
            request.response_format = {"type": "json_object"}
        response = await self.complete(request)
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            # Try to extract JSON from the response.
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            return json.loads(content.strip())

    @abstractmethod
    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embeddings for the given texts."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is available."""
        ...

    @staticmethod
    def _now_ms() -> float:
        return time.monotonic() * 1000


class TokenUsageTracker:
    """Tracks cumulative token usage and latency per model."""

    def __init__(self) -> None:
        self._usage: dict[str, dict[str, float]] = {}

    def record(self, response: LLMResponse | EmbeddingResponse) -> None:
        model = response.model
        if model not in self._usage:
            self._usage[model] = {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "total_latency_ms": 0,
                "call_count": 0,
            }
        stats = self._usage[model]
        if isinstance(response, LLMResponse):
            stats["input_tokens"] += response.input_tokens
            stats["output_tokens"] += response.output_tokens
        stats["total_tokens"] += response.total_tokens
        stats["total_latency_ms"] += response.latency_ms
        stats["call_count"] += 1

    def get_stats(self) -> dict[str, dict[str, float]]:
        return dict(self._usage)

    def reset(self) -> None:
        self._usage.clear()
