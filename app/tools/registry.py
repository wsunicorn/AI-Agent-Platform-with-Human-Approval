import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Generic, TypeVar, cast

from pydantic import BaseModel

from app.models import Sensitivity
from app.tools.errors import DuplicateToolError, ToolNotRegisteredError

InputModel = TypeVar("InputModel", bound=BaseModel)
OutputModel = TypeVar("OutputModel", bound=BaseModel)
ToolReturn = BaseModel | dict[str, Any]
ToolHandler = Callable[[InputModel], ToolReturn | Awaitable[ToolReturn]]


@dataclass(frozen=True)
class ToolDefinition(Generic[InputModel, OutputModel]):
    name: str
    description: str
    input_model: type[InputModel]
    output_model: type[OutputModel]
    handler: ToolHandler[InputModel]
    sensitivity: Sensitivity = Sensitivity.SAFE
    timeout_seconds: float | None = None
    max_attempts: int | None = None
    retry_backoff_seconds: float | None = None
    risk_reason: str | None = None

    def validate_input(self, payload: dict[str, Any]) -> InputModel:
        return self.input_model.model_validate(payload)

    def validate_output(self, payload: ToolReturn) -> OutputModel:
        if isinstance(payload, self.output_model):
            return payload
        return self.output_model.model_validate(payload)

    async def call(self, payload: InputModel) -> ToolReturn:
        result = self.handler(payload)
        if inspect.isawaitable(result):
            return await result
        return cast(ToolReturn, result)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition[Any, Any]] = {}

    def register(self, definition: ToolDefinition[Any, Any]) -> ToolDefinition[Any, Any]:
        if definition.name in self._tools:
            raise DuplicateToolError(definition.name)

        self._tools[definition.name] = definition
        return definition

    def decorator(
        self,
        *,
        name: str,
        description: str,
        input_model: type[InputModel],
        output_model: type[OutputModel],
        sensitivity: Sensitivity = Sensitivity.SAFE,
        timeout_seconds: float | None = None,
        max_attempts: int | None = None,
        retry_backoff_seconds: float | None = None,
        risk_reason: str | None = None,
    ) -> Callable[[ToolHandler[InputModel]], ToolHandler[InputModel]]:
        def wrap(handler: ToolHandler[InputModel]) -> ToolHandler[InputModel]:
            self.register(
                ToolDefinition(
                    name=name,
                    description=description,
                    input_model=input_model,
                    output_model=output_model,
                    handler=handler,
                    sensitivity=sensitivity,
                    timeout_seconds=timeout_seconds,
                    max_attempts=max_attempts,
                    retry_backoff_seconds=retry_backoff_seconds,
                    risk_reason=risk_reason,
                )
            )
            return handler

        return wrap

    def get(self, tool_name: str) -> ToolDefinition[Any, Any]:
        try:
            return self._tools[tool_name]
        except KeyError as error:
            raise ToolNotRegisteredError(tool_name) from error

    def maybe_get(self, tool_name: str) -> ToolDefinition[Any, Any] | None:
        return self._tools.get(tool_name)

    def list(self) -> list[ToolDefinition[Any, Any]]:
        return sorted(self._tools.values(), key=lambda tool: tool.name)


tool_registry = ToolRegistry()
