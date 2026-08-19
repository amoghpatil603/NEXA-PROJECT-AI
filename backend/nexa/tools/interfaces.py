from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import re

class ToolError(Exception):
    pass

@dataclass
class ToolDefinition:
    name: str
    description: str
    arguments_schema: Dict[str, str] # e.g. {"param1": "str", "param2": "int"}
    timeout: float = 30.0
    requires_permission: bool = False

    def __post_init__(self):
        if not isinstance(self.name, str) or not re.match(r"^[a-zA-Z0-9_-]+$", self.name):
            raise ValueError("Tool name must be alphanumeric and non-empty (underscores and hyphens allowed)")
        if not isinstance(self.description, str) or not self.description.strip():
            raise ValueError("Tool description must be a non-empty string")
        if not isinstance(self.arguments_schema, dict):
            raise ValueError("arguments_schema must be a dictionary")
        if not isinstance(self.timeout, (int, float)) or self.timeout <= 0.0:
            raise ValueError("timeout must be a float > 0")
        if not isinstance(self.requires_permission, bool):
            raise ValueError("requires_permission must be a boolean")

@dataclass
class ToolRequest:
    tool_name: str
    arguments: Dict[str, Any]

    def __post_init__(self):
        if not isinstance(self.tool_name, str) or not self.tool_name.strip():
            raise ValueError("tool_name must be a non-empty string")
        if not isinstance(self.arguments, dict):
            raise ValueError("arguments must be a dictionary")

@dataclass
class ToolResult:
    status: str  # 'success' or 'error'
    output: Any

    def __post_init__(self):
        if self.status not in ('success', 'error'):
            raise ValueError("status must be 'success' or 'error'")

class ToolRegistryInterface(ABC):
    @abstractmethod
    def register_tool(self, tool: ToolDefinition) -> None:
        """Register a tool definition."""
        pass

    @abstractmethod
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Retrieve a tool definition by name."""
        pass

    @abstractmethod
    def execute_tool(self, request: ToolRequest, user_role: str) -> ToolResult:
        """Execute a tool matching request with role validation."""
        pass
