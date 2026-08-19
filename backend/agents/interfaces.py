from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from enum import Enum

class AgentState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

@dataclass
class AgentTask:
    task_id: str
    task_type: str
    description: str
    priority: int = 1

    def __post_init__(self):
        if not isinstance(self.task_id, str) or not self.task_id.strip():
            raise ValueError("task_id must be a non-empty string")
        if not isinstance(self.task_type, str) or not self.task_type.strip():
            raise ValueError("task_type must be a non-empty string")
        if not isinstance(self.description, str) or not self.description.strip():
            raise ValueError("description must be a non-empty string")
        if not isinstance(self.priority, int) or self.priority < 1:
            raise ValueError("priority must be an integer >= 1")

@dataclass
class ToolAction:
    tool_name: str
    arguments: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.tool_name, str) or not self.tool_name.strip():
            raise ValueError("tool_name must be a non-empty string")
        if not isinstance(self.arguments, dict):
            raise ValueError("arguments must be a dictionary")

@dataclass
class VerificationResult:
    is_verified: bool
    notes: str = ""

    def __post_init__(self):
        if not isinstance(self.is_verified, bool):
            raise ValueError("is_verified must be a boolean")
        if not isinstance(self.notes, str):
            raise ValueError("notes must be a string")

@dataclass
class PlanStep:
    step_id: str
    action: ToolAction
    status: AgentState = AgentState.PENDING
    dependencies: List[str] = field(default_factory=list)
    verification: Optional[VerificationResult] = None

    def __post_init__(self):
        if not isinstance(self.step_id, str) or not self.step_id.strip():
            raise ValueError("step_id must be a non-empty string")
        if not isinstance(self.action, ToolAction):
            raise ValueError("action must be a ToolAction instance")
        if not isinstance(self.status, AgentState):
            if isinstance(self.status, str):
                self.status = AgentState(self.status)
            else:
                raise ValueError("status must be a valid AgentState")
        if not isinstance(self.dependencies, list):
            raise ValueError("dependencies must be a list")
        if self.verification is not None and not isinstance(self.verification, VerificationResult):
            raise ValueError("verification must be a VerificationResult instance")

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlanStep":
        d = data.copy()
        d["action"] = ToolAction(**d["action"])
        d["status"] = AgentState(d["status"])
        if d.get("verification") is not None:
            d["verification"] = VerificationResult(**d["verification"])
        return cls(**d)
