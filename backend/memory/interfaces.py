from dataclasses import dataclass, field, asdict
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import uuid
import time

@dataclass
class MemoryItem:
    memory_id: str
    scope: str  # user/session scope
    content: str
    importance: float
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.memory_id, str) or not self.memory_id.strip():
            raise ValueError("memory_id must be a non-empty string")
        if not isinstance(self.scope, str) or not self.scope.strip():
            raise ValueError("scope must be a non-empty string")
        if not isinstance(self.content, str) or not self.content.strip():
            raise ValueError("content must be a non-empty string")
        if not isinstance(self.importance, (int, float)) or not (0.0 <= self.importance <= 10.0):
            raise ValueError("importance must be a float between 0.0 and 10.0")
        if not isinstance(self.created_at, (int, float)) or self.created_at < 0:
            raise ValueError("created_at must be a valid non-negative timestamp")
        if not isinstance(self.updated_at, (int, float)) or self.updated_at < 0:
            raise ValueError("updated_at must be a valid non-negative timestamp")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryItem":
        item_data = data.copy()
        if 'memory_id' not in item_data:
            item_data['memory_id'] = str(uuid.uuid4())
        return cls(**item_data)

@dataclass
class MemoryQuery:
    query: str
    scope: Optional[str] = None
    top_k: int = 5

    def __post_init__(self):
        if not isinstance(self.query, str) or not self.query.strip():
            raise ValueError("query must be a non-empty string")
        if self.scope is not None and (not isinstance(self.scope, str) or not self.scope.strip()):
            raise ValueError("scope must be a non-empty string if provided")
        if not isinstance(self.top_k, int) or self.top_k <= 0:
            raise ValueError("top_k must be an integer > 0")

@dataclass
class MemoryResult:
    item: MemoryItem
    score: float

    def __post_init__(self):
        if not isinstance(self.item, MemoryItem):
            raise ValueError("item must be a MemoryItem instance")
        if not isinstance(self.score, (int, float)):
            raise ValueError("score must be a float or integer")

class MemoryStore(ABC):
    @abstractmethod
    def store_memory(self, item: MemoryItem) -> None:
        """Stores a memory item."""
        pass

    @abstractmethod
    def retrieve_memories(self, query: MemoryQuery) -> List[MemoryResult]:
        """Retrieves memories matching a query."""
        pass
