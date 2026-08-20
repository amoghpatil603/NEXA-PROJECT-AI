import uuid
from typing import Dict, Any, List, Optional, Type
from backend.agents.interfaces import AgentState, AgentTask
from backend.agents.multi_agent_system import BaseAgent, AgentMessage

class SharedTaskState:
    def __init__(self, task_id: Optional[str] = None, initial_context: Optional[Dict[str, Any]] = None):
        self.task_id = task_id or str(uuid.uuid4())
        self.state: AgentState = AgentState.PENDING
        self.context: Dict[str, Any] = initial_context.copy() if initial_context else {}
        self.history: List[Dict[str, Any]] = []
        self.error: Optional[str] = None

    def update_context(self, updates: Dict[str, Any]):
        if isinstance(updates, dict):
            self.context.update(updates)

    def record_step(self, agent_id: str, action: str, result: Dict[str, Any], status: str):
        self.history.append({
            "agent_id": agent_id,
            "action": action,
            "result": result,
            "status": status
        })

    def fail(self, error_message: str):
        self.state = AgentState.FAILED
        self.error = error_message

    def complete(self):
        if self.state != AgentState.FAILED:
            self.state = AgentState.COMPLETED

class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._capabilities: Dict[str, List[str]] = {}

    def register(self, agent: BaseAgent, capabilities: Optional[List[str]] = None):
        if not isinstance(agent, BaseAgent):
            raise TypeError("agent must be an instance of BaseAgent")
        agent_id = agent.agent_id
        self._agents[agent_id] = agent
        self._capabilities[agent_id] = capabilities or [agent_id.lower()]

    def unregister(self, agent_id: str):
        self._agents.pop(agent_id, None)
        self._capabilities.pop(agent_id, None)

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        return self._agents.get(agent_id)

    def find_agent_for_task(self, task_type: str) -> Optional[BaseAgent]:
        # 1. Direct match by agent_id
        if task_type in self._agents:
            return self._agents[task_type]
        
        # 2. Match by capabilities
        task_lower = task_type.lower()
        for agent_id, caps in self._capabilities.items():
            if any(task_lower == c.lower() or task_lower in c.lower() for c in caps):
                return self._agents[agent_id]
        return None

    def list_agents(self) -> List[str]:
        return list(self._agents.keys())

class MultiAgentCoordinator:
    def __init__(self, registry: Optional[AgentRegistry] = None):
        self.registry = registry or AgentRegistry()

    def route_task(
        self,
        task: AgentTask,
        shared_state: Optional[SharedTaskState] = None
    ) -> SharedTaskState:
        state = shared_state or SharedTaskState(task_id=task.task_id)
        state.state = AgentState.RUNNING

        agent = self.registry.find_agent_for_task(task.task_type)
        if not agent:
            state.fail(f"No agent registered for task_type: '{task.task_type}'")
            return state

        message = AgentMessage(
            sender="Coordinator",
            receiver=agent.agent_id,
            task_id=task.task_id,
            status="PENDING",
            payload={"task": task.description, "context": state.context}
        )

        try:
            response = agent.process(message)
            if response.status == "FAILED":
                state.fail(response.payload.get("error", f"Agent {agent.agent_id} failed processing"))
                state.record_step(agent.agent_id, task.description, response.payload, "FAILED")
            else:
                state.update_context(response.payload)
                state.record_step(agent.agent_id, task.description, response.payload, "SUCCESS")
                state.complete()
        except Exception as e:
            state.fail(f"Agent {agent.agent_id} raised an unhandled exception: {str(e)}")
            state.record_step(agent.agent_id, task.description, {"error": str(e)}, "EXCEPTION")

        return state

    def execute_handoff(
        self,
        task_a: AgentTask,
        task_b: AgentTask,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> SharedTaskState:
        state = SharedTaskState(task_id=task_a.task_id, initial_context=initial_context)
        
        # Step 1: Run Task A
        state = self.route_task(task_a, shared_state=state)
        if state.state == AgentState.FAILED:
            # Propagate failure immediately without executing downstream task
            return state

        # Step 2: Hand off output/context to Task B
        state.state = AgentState.RUNNING
        state = self.route_task(task_b, shared_state=state)
        return state

    def execute_pipeline(
        self,
        tasks: List[AgentTask],
        initial_context: Optional[Dict[str, Any]] = None
    ) -> SharedTaskState:
        state = SharedTaskState(initial_context=initial_context)
        for task in tasks:
            state = self.route_task(task, shared_state=state)
            if state.state == AgentState.FAILED:
                break
        return state
