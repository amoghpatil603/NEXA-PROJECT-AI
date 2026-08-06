from backend.rag.vector_store import VectorStore
from typing import List, Dict, Any

class RetrievalService:
    def __init__(self):
        self.store = VectorStore()

    def retrieve(self, query: str, top_k: int = 5, token_budget: int = 2000) -> List[Dict[str, Any]]:
        results = self.store.search_chunks(query, top_k=top_k)
        
        context_chunks = []
        current_tokens = 0
        
        for res in results:
            approx_tokens = len(res['content']) // 4
            if current_tokens + approx_tokens <= token_budget:
                context_chunks.append(res)
                current_tokens += approx_tokens
            else:
                break
                
        return context_chunks

    def build_prompt_context(self, chunks: List[Dict[str, Any]]) -> str:
        context_str = "Context:\n"
        for i, chunk in enumerate(chunks):
            context_str += f"--- Document Snippet {i+1} ---\n{chunk['content']}\n\n"
        return context_str
