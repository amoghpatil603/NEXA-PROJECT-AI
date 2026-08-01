from typing import Dict, Any, List, Optional
import importlib
import inspect

class NexaTool:
    """Base class for all NEXA Tools"""
    name: str = ""
    description: str = ""
    arguments: Dict[str, str] = {}
    requires_permission: bool = False

    def execute(self, **kwargs) -> Any:
        raise NotImplementedError("Tools must implement execute()")

class ToolRegistry:
    _tools: Dict[str, NexaTool] = {}

    @classmethod
    def register(cls, tool_class):
        tool_instance = tool_class()
        cls._tools[tool_instance.name] = tool_instance
        return tool_class

    @classmethod
    def get_tool(cls, name: str) -> Optional[NexaTool]:
        return cls._tools.get(name)

    @classmethod
    def list_tools(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "arguments": t.arguments,
                "permissions": t.requires_permission
            } for t in cls._tools.values()
        ]
