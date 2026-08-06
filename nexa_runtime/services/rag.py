class RAGService:
    """Standard interface for Retrieval Augmented Generation."""
    def __init__(self, vector_db=None):
        self.vector_db = vector_db

    def query(self, text, top_k=3):
        # Interface for vector search
        return [f"Retrieved context for: {text[:20]}"]
