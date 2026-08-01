import torch
from nexa.memory.memory_manager import MemoryManager

class ContextEngine:
    """
    Orchestrates memory retrieval and injection for inference.
    """
    def __init__(self, memory_manager: MemoryManager):
        self.mem = memory_manager

    def retrieve_context(self, query: str, max_results: int = 3):
        """Search across multiple memory layers."""
        results = []
        # Search across known layers where we stored test data
        for layer in ['long_term', 'projects', 'session']:
            hits = self.mem.search_memory(query, layer=layer)
            if hits:
                results.extend(hits)
        
        if not results:
            return ""

        context_header = "\n### RELEVANT CONTEXT FROM MEMORY ###\n"
        context_body = "\n".join([f"- {str(r)}" for r in results[:max_results]])
        return f"{context_header}{context_body}\n### END CONTEXT ###\n"

    def prepare_inference_prompt(self, user_input: str):
        """Main entry point for prompt injection used by the verification script."""
        context = self.retrieve_context(user_input)
        if context:
            return f"{context}\nUser: {user_input}"
        return user_input

    def inject_context(self, user_prompt, session_id='default'):
        """Alias for prepare_inference_prompt to ensure compatibility with all scripts."""
        return self.prepare_inference_prompt(user_prompt)
