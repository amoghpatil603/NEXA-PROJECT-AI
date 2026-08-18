from nexa.tools.tool_manager import ToolManager
from nexa.inference.context_engine import ContextEngine

class NEXAInferenceBridge:
    """Bridges Inference, Memory, and Tool Calling logic"""
    def __init__(self, tool_manager: ToolManager, context_engine: ContextEngine):
        self.tools = tool_manager
        self.context = context_engine

    def process_step(self, user_input, model_output):
        # 1. Check for tool calls in LLM output
        tool_call = self.tools.parser.parse_call(model_output)
        if not tool_call:
            return {"status": "DONE", "output": model_output}

        tool = self.tools.registry.get_tool(tool_call['name'])
        if not tool:
            return {"status": "ERROR", "message": f"Tool {tool_call['name']} not found"}

        # 2. Safety Intercept for high-risk actions
        if tool.requires_permission:
            return {"status": "NEED_USER_APPROVAL", "tool_call": tool_call}
            
        # 3. Execution
        result = self.tools.handle_inference_output(model_output)
        
        # 4. Context Re-injection for final response
        enhanced_prompt = f"Tool Call: {tool_call['name']}\nResult: {result}\nUser requested: {user_input}"
        return {"status": "CONTINUE", "prompt": enhanced_prompt}
