import pytest
from pydantic import BaseModel

from app.models import Sensitivity
from app.tools.errors import DuplicateToolError, ToolNotRegisteredError
from app.tools.registry import ToolDefinition, ToolRegistry


class EchoInput(BaseModel):
    text: str


class EchoOutput(BaseModel):
    text: str


def echo_tool(payload: EchoInput) -> dict[str, str]:
    return {"text": payload.text}


def test_tool_registry_registers_and_lists_tools() -> None:
    registry = ToolRegistry()
    definition = ToolDefinition(
        name="echo",
        description="Echo text.",
        input_model=EchoInput,
        output_model=EchoOutput,
        handler=echo_tool,
        sensitivity=Sensitivity.SAFE,
    )

    registry.register(definition)

    assert registry.get("echo") is definition
    assert registry.list() == [definition]


def test_tool_registry_rejects_duplicate_tools() -> None:
    registry = ToolRegistry()
    definition = ToolDefinition(
        name="echo",
        description="Echo text.",
        input_model=EchoInput,
        output_model=EchoOutput,
        handler=echo_tool,
    )

    registry.register(definition)

    with pytest.raises(DuplicateToolError):
        registry.register(definition)


def test_tool_registry_raises_for_missing_tool() -> None:
    registry = ToolRegistry()

    with pytest.raises(ToolNotRegisteredError):
        registry.get("missing")
