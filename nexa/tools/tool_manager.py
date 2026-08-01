import time
import logging
from .registry import ToolRegistry
from .parser import ToolParser

class ToolManager:
    def __init__(self):
        self.registry = ToolRegistry()
        self.parser = ToolParser()
        self.logger = logging.getLogger("NexaTools")

    def handle_inference_output(self, output: str):
        call = self.parser.parse_call(output)
        if not call:
            return None

        tool = self.registry.get_tool(call['name'])
        if not tool:
            return f"Error: Tool '{call['name']}' not found."

        # Permission Check Mock (UI will handle actual prompt)
        if tool.requires_permission:
            return "PENDING_PERMISSION"

        start_time = time.time()
        try:
            result = tool.execute(**call['args'])
            elapsed = time.time() - start_time
            self.logger.info(f"Executed {tool.name} in {elapsed:.4f}s")
            return result
        except Exception as e:
            return f"Execution failed: {str(e)}"
