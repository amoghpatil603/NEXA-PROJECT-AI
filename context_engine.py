from typing import List, Dict, Any, Optional

class ContextEngine:
    def __init__(self):
        pass

    def build_context(
        self, 
        user_message: str, 
        system_prompt: Optional[str] = None, 
        history: List[Dict[str, str]] = None, 
        memories: List[Dict[str, Any]] = None, 
        rag_chunks: List[Dict[str, Any]] = None, 
        tool_results: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Builds the final contextualized prompt.
        """
        context_parts = []
        
        if memories and len(memories) > 0:
            memory_texts = [m.get('content', '') for m in memories if m.get('content')]
            if memory_texts:
                context_parts.append("RELEVANT MEMORIES:\n" + "\n".join(f"- {m}" for m in memory_texts))
                
        if rag_chunks and len(rag_chunks) > 0:
            rag_texts = [c.get('content', '') for c in rag_chunks if c.get('content')]
            if rag_texts:
                context_parts.append("RETRIEVED KNOWLEDGE:\n" + "\n".join(f"- {r}" for r in rag_texts))
                
        if tool_results and len(tool_results) > 0:
            tool_texts = [str(r.get('result', '')) for r in tool_results if r.get('status') == 'success']
            if tool_texts:
                context_parts.append("TOOL RESULTS:\n" + "\n".join(f"- {t}" for t in tool_texts))
                
        final_system_prompt = system_prompt or "You are NEXA, an intelligent AI assistant."
        if context_parts:
            final_system_prompt += "\n\n" + "\n\n".join(context_parts)
            
        return {
            "user_prompt": user_message,
            "system_prompt": final_system_prompt,
            "previous_messages": history or []
        }
