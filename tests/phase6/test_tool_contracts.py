import unittest
from backend.nexa.tools.interfaces import ToolDefinition, ToolRequest, ToolResult, ToolError, ToolRegistryInterface

class MockToolRegistry(ToolRegistryInterface):
    def __init__(self):
        self.tools = {}

    def register_tool(self, tool: ToolDefinition):
        if tool.name in self.tools:
            raise ToolError(f"Duplicate tool name: {tool.name}")
        self.tools[tool.name] = tool

    def get_tool(self, name: str):
        return self.tools.get(name)

    def execute_tool(self, request: ToolRequest, user_role: str):
        tool = self.get_tool(request.tool_name)
        if not tool:
            raise ToolError(f"Unknown tool: {request.tool_name}")

        # Permission check
        if tool.requires_permission and user_role != "ADMIN":
            raise ToolError(f"Unauthorized tool request: {request.tool_name} requires ADMIN role")

        # Arguments validation
        for arg_name, arg_type in tool.arguments_schema.items():
            if arg_name not in request.arguments:
                raise ToolError(f"Missing argument: {arg_name}")
            val = request.arguments[arg_name]
            if arg_type == "int" and not isinstance(val, int):
                raise ToolError(f"Argument type mismatch: {arg_name} must be int")
            elif arg_type == "str" and not isinstance(val, str):
                raise ToolError(f"Argument type mismatch: {arg_name} must be str")

        return ToolResult(status="success", output=f"Executed {tool.name}")

class TestToolContracts(unittest.TestCase):
    def test_valid_tool_definition(self):
        tool = ToolDefinition(
            name="calculator",
            description="Add numbers",
            arguments_schema={"a": "int", "b": "int"},
            timeout=10.0,
            requires_permission=False
        )
        self.assertEqual(tool.name, "calculator")
        self.assertEqual(tool.timeout, 10.0)

    def test_invalid_tool_name(self):
        with self.assertRaises(ValueError):
            ToolDefinition("bad name!", "desc", {})
        with self.assertRaises(ValueError):
            ToolDefinition("", "desc", {})

    def test_invalid_timeout(self):
        with self.assertRaises(ValueError):
            ToolDefinition("t", "desc", {}, timeout=0.0)
        with self.assertRaises(ValueError):
            ToolDefinition("t", "desc", {}, timeout=-5.0)

    def test_registry_validations(self):
        registry = MockToolRegistry()
        calc = ToolDefinition(
            name="calculator",
            description="Add numbers",
            arguments_schema={"a": "int", "b": "int"},
            requires_permission=False
        )
        delete_files = ToolDefinition(
            name="delete_files",
            description="Delete system files",
            arguments_schema={"path": "str"},
            requires_permission=True
        )

        registry.register_tool(calc)
        registry.register_tool(delete_files)

        # 1. Duplicate tool registration check
        with self.assertRaises(ToolError):
            registry.register_tool(calc)

        # 2. Unknown tool execution check
        req_unknown = ToolRequest(tool_name="unregistered_tool", arguments={})
        with self.assertRaises(ToolError):
            registry.execute_tool(req_unknown, "ADMIN")

        # 3. Unauthorized tool request check
        req_delete = ToolRequest(tool_name="delete_files", arguments={"path": "/usr/bin"})
        with self.assertRaises(ToolError):
            registry.execute_tool(req_delete, "STANDARD_USER")

        # 4. Malformed arguments type mismatch check
        req_calc_bad_args = ToolRequest(tool_name="calculator", arguments={"a": "one", "b": 2})
        with self.assertRaises(ToolError):
            registry.execute_tool(req_calc_bad_args, "STANDARD_USER")

        # 5. Missing argument check
        req_calc_missing_args = ToolRequest(tool_name="calculator", arguments={"a": 1})
        with self.assertRaises(ToolError):
            registry.execute_tool(req_calc_missing_args, "STANDARD_USER")

        # 6. Valid execution check
        req_calc_valid = ToolRequest(tool_name="calculator", arguments={"a": 1, "b": 2})
        res = registry.execute_tool(req_calc_valid, "STANDARD_USER")
        self.assertEqual(res.status, "success")
        self.assertEqual(res.output, "Executed calculator")

if __name__ == "__main__":
    unittest.main()
