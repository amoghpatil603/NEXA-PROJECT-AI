from ..registry import NexaTool, ToolRegistry
import math

@ToolRegistry.register
class Calculator(NexaTool):
    name = "calculator"
    description = "Performs mathematical calculations."
    arguments = {"expression": "A string math expression (e.g. '2 + 2')"}
    requires_permission = False

    def execute(self, expression: str):
        try:
            # Safe eval alternative for limited scope
            allowed_names = {"__builtins__": None, "math": math}
            return eval(expression, allowed_names, {})
        except Exception as e:
            return f"Error: {str(e)}"
