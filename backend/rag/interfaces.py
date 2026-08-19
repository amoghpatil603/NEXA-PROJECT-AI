from dataclasses import dataclass, field, asdict
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

@dataclass
class Document:
    document_id: str
    text: str
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.document_id, str) or not self.document_id.strip():
            raise ValueError("document_id must be a non-empty string")
        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError("text must be a non-empty string")
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("source must be a non-empty string")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary")

@dataclass
class DocumentChunk:
    chunk_id: str
    document_id: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.chunk_id, str) or not self.chunk_id.strip():
            raise ValueError("chunk_id must be a non-empty string")
        if not isinstance(self.document_id, str) or not self.document_id.strip():
            raise ValueError("document_id must be a non-empty string")
        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError("text must be a non-empty string")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary")

@dataclass
class RetrievalResult:
    chunk: DocumentChunk
    score: float
    citation: str

    def __post_init__(self):
        if not isinstance(self.chunk, DocumentChunk):
            raise ValueError("chunk must be a DocumentChunk instance")
        if not isinstance(self.score, (int, float)):
            raise ValueError("score must be a float or integer")
        if not isinstance(self.citation, str) or not self.citation.strip():
            raise ValueError("citation must be a non-empty string")

class Retriever(ABC):
    @abstractmethod
    def retrieve(self, query: str, limit: int = 5) -> List[RetrievalResult]:
        """Retrieve relevant document chunks for a query."""
        pass
