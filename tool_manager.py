from typing import Dict, Any
from tool_registry import ToolRegistry

class ToolManager:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any], require_approval: bool = False):
        tool = self.registry.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool {tool_name} not found")
        
        if tool.permission_level == "Confirmation Required" and require_approval:
            return {"status": "pending_approval", "tool": tool_name, "parameters": parameters}
            
        if tool.permission_level == "Blocked":
            return {"status": "error", "message": "Tool execution blocked by security policy"}
            
        try:
            result = tool.execute(**parameters)
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}
