class ToolRegistry:
    """Manages executable tools for the agentic SDK."""
    def __init__(self):
        self.tools = {}

    def register(self, name, func):
        self.tools[name] = func

    def call(self, name, **kwargs):
        if name in self.tools:
            return self.tools[name](**kwargs)
        return f"Tool {name} not found."
