import json

class AgentPlanner:
    def __init__(self, tool_manager):
        self.tool_manager = tool_manager

    def plan_execution(self, prompt: str, available_tools: list):
        # Placeholder for intent detection and tool selection
        # Returns a sequence of tool calls
        return []

    def execute_plan(self, plan: list):
        results = []
        for step in plan:
            result = self.tool_manager.execute_tool(step['tool'], step['parameters'])
            results.append(result)
            if result['status'] == 'error':
                break
        return results
