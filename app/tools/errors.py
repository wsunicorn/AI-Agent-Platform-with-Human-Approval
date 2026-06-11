class ToolRegistryError(RuntimeError):
    pass


class ToolNotRegisteredError(ToolRegistryError):
    def __init__(self, tool_name: str) -> None:
        super().__init__(f"Tool is not registered: {tool_name}")
        self.tool_name = tool_name


class DuplicateToolError(ToolRegistryError):
    def __init__(self, tool_name: str) -> None:
        super().__init__(f"Tool is already registered: {tool_name}")
        self.tool_name = tool_name


class ToolExecutionError(RuntimeError):
    pass


class ToolBlockedError(ToolExecutionError):
    pass


class ToolApprovalRequiredError(ToolExecutionError):
    pass
