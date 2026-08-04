from typing import List, Dict, Any, Optional
from agent_planner import AgentPlanner
from memory_engine import MemoryEngine
from rag_engine import RAGEngine
from tool_manager import ToolManager
from tool_registry import ToolRegistry
from context_engine import ContextEngine

class ExecutionEngine:
    def __init__(self):
        self.registry = ToolRegistry()
        self.tool_manager = ToolManager(self.registry)
        self.planner = AgentPlanner(self.tool_manager)
        self.memory_engine = MemoryEngine()
        self.rag_engine = RAGEngine()
        self.context_engine = ContextEngine()
        
    def process_request(self, user_message: str, history: List[Dict[str, str]] = None, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        # 1. Store user message in memory (basic heuristic)
        if len(user_message) > 10:
            self.memory_engine.create_memory("user_fact", user_message)
            
        # 2. Retrieve relevant memories
        memories = self.memory_engine.search_memory(user_message)
        
        # 3. Retrieve RAG Knowledge
        rag_chunks = []
        try:
            rag_chunks = self.rag_engine.store.search_chunks(user_message, top_k=3)
        except Exception:
            pass
            
        # 4. Plan and Execute Tools
        available_tools = self.registry.list_tools()
        plan = self.planner.plan_execution(user_message, available_tools)
        tool_results = self.planner.execute_plan(plan)
        
        # 5. Build Context
        context = self.context_engine.build_context(
            user_message=user_message,
            system_prompt=system_prompt,
            history=history,
            memories=memories,
            rag_chunks=rag_chunks,
            tool_results=tool_results
        )
        
        return context
