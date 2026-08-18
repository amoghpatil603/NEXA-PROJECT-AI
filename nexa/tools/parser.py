import json
import re

class ToolParser:
    """Parses LLM output for structured tool calls like [TOOL: name ARGS: {json}]"""
    
    @staticmethod
    def parse_call(text: str):
        pattern = r"\[TOOL:\s*(?P<name>\w+)\s*ARGS:\s*(?P<args>\{.*?\})\]"
        match = re.search(pattern, text)
        if match:
            try:
                return {
                    "name": match.group("name"),
                    "args": json.loads(match.group("args"))
                }
            except json.JSONDecodeError:
                return None
        return None
