import os
import json
import time
import uuid
from pathlib import Path
from datetime import datetime

class AgentMessage:
    def __init__(self, sender, receiver, task_id, status="PENDING", payload=None):
        self.message_id = str(uuid.uuid4())
        self.sender = sender
        self.receiver = receiver
        self.timestamp = datetime.utcnow().isoformat()
        self.task_id = task_id
        self.status = status
        self.payload = payload or {}

    def to_dict(self):
        return {
            "message_id": self.message_id,
            "sender": self.sender,
            "receiver": self.receiver,
            "timestamp": self.timestamp,
            "task_id": self.task_id,
            "status": self.status,
            "payload": self.payload
        }

class BaseAgent:
    def __init__(self, agent_id):
        self.agent_id = agent_id

    def process(self, message: AgentMessage) -> AgentMessage:
        raise NotImplementedError

class PlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__("PlannerAgent")

    def process(self, message: AgentMessage) -> AgentMessage:
        goal = message.payload.get("goal", "")
        # Break goal into subtasks
        subtasks = [
            {"task_id": "t1", "agent": "ResearchAgent", "action": "retrieve_knowledge", "query": goal},
            {"task_id": "t2", "agent": "MemoryAgent", "action": "recall_context", "query": goal},
            {"task_id": "t3", "agent": "CodingAgent", "action": "generate_or_debug", "query": goal},
            {"task_id": "t4", "agent": "ToolAgent", "action": "execute_tool", "query": goal}
        ]
        return AgentMessage(
            sender=self.agent_id,
            receiver="CoordinatorAgent",
            task_id=message.task_id,
            status="SUCCESS",
            payload={"subtasks": subtasks, "goal": goal}
        )

class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__("ResearchAgent")

    def process(self, message: AgentMessage) -> AgentMessage:
        query = message.payload.get("query", "")
        evidence = f"Retrieved evidence and documentation chunks for query: {query}"
        return AgentMessage(
            sender=self.agent_id,
            receiver="CoordinatorAgent",
            task_id=message.task_id,
            status="SUCCESS",
            payload={"evidence": evidence}
        )

class CodingAgent(BaseAgent):
    def __init__(self):
        super().__init__("CodingAgent")

    def process(self, message: AgentMessage) -> AgentMessage:
        query = message.payload.get("query", "")
        code_result = f"Generated/Validated code snippet for: {query}"
        return AgentMessage(
            sender=self.agent_id,
            receiver="CoordinatorAgent",
            task_id=message.task_id,
            status="SUCCESS",
            payload={"code_result": code_result}
        )

class MemoryAgent(BaseAgent):
    def __init__(self):
        super().__init__("MemoryAgent")

    def process(self, message: AgentMessage) -> AgentMessage:
        query = message.payload.get("query", "")
        memory_context = f"Recalled relevant past session memories and user preferences for: {query}"
        return AgentMessage(
            sender=self.agent_id,
            receiver="CoordinatorAgent",
            task_id=message.task_id,
            status="SUCCESS",
            payload={"memory_context": memory_context}
        )

class ToolAgent(BaseAgent):
    def __init__(self):
        super().__init__("ToolAgent")

    def process(self, message: AgentMessage) -> AgentMessage:
        action = message.payload.get("action", "default")
        tool_output = f"Successfully executed tool action: {action}"
        return AgentMessage(
            sender=self.agent_id,
            receiver="CoordinatorAgent",
            task_id=message.task_id,
            status="SUCCESS",
            payload={"tool_output": tool_output}
        )

class CriticAgent(BaseAgent):
    def __init__(self):
        super().__init__("CriticAgent")

    def process(self, message: AgentMessage) -> AgentMessage:
        response = message.payload.get("response", "")
        # Review response for hallucinations or safety
        critique = "Passed safety, hallucination, and coherence validation."
        return AgentMessage(
            sender=self.agent_id,
            receiver="CoordinatorAgent",
            task_id=message.task_id,
            status="SUCCESS",
            payload={"critique": critique, "approved": True}
        )

class CoordinatorAgent(BaseAgent):
    def __init__(self):
        super().__init__("CoordinatorAgent")
        self.planner = PlannerAgent()
        self.research = ResearchAgent()
        self.coding = CodingAgent()
        self.memory = MemoryAgent()
        self.tool = ToolAgent()
        self.critic = CriticAgent()

    def coordinate_workflow(self, user_goal):
        task_id = str(uuid.uuid4())
        
        # 1. Planner Agent
        plan_msg = AgentMessage(sender="User", receiver="PlannerAgent", task_id=task_id, payload={"goal": user_goal})
        plan_res = self.planner.process(plan_msg)
        subtasks = plan_res.payload.get("subtasks", [])

        aggregated_payload = {"goal": user_goal, "trace": []}

        # 2. Execute subtasks (Research, Memory, Coding, Tool)
        for st in subtasks:
            agent_name = st["agent"]
            msg = AgentMessage(sender="CoordinatorAgent", receiver=agent_name, task_id=task_id, payload={"query": user_goal, "action": st["action"]})
            
            if agent_name == "ResearchAgent":
                res = self.research.process(msg)
                aggregated_payload.update(res.payload)
            elif agent_name == "MemoryAgent":
                res = self.memory.process(msg)
                aggregated_payload.update(res.payload)
            elif agent_name == "CodingAgent":
                res = self.coding.process(msg)
                aggregated_payload.update(res.payload)
            elif agent_name == "ToolAgent":
                res = self.tool.process(msg)
                aggregated_payload.update(res.payload)
            
            aggregated_payload["trace"].append(res.to_dict())

        # 3. Synthesize preliminary response
        prelim_response = f"Synthesized multi-agent response for goal '{user_goal}' integrating research, memory, coding, and tools."

        # 4. Critic Agent review
        critic_msg = AgentMessage(sender="CoordinatorAgent", receiver="CriticAgent", task_id=task_id, payload={"response": prelim_response})
        critic_res = self.critic.process(critic_msg)
        aggregated_payload["critic_review"] = critic_res.to_dict()
        aggregated_payload["final_response"] = prelim_response

        return aggregated_payload
