class MemoryManager:
    """Handles conversation history and context window truncation."""
    def __init__(self, max_tokens=2048):
        self.history = []
        self.max_tokens = max_tokens

    def add_message(self, role, content):
        self.history.append({"role": role, "content": content})

    def get_context(self):
        return " ".join([m['content'] for m in self.history])

    def clear(self):
        self.history = []
