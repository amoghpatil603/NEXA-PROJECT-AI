from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional

@dataclass
class EvaluationCase:
    case_id: str
    input: str
    expected_output: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.case_id, str) or not self.case_id.strip():
            raise ValueError("case_id must be a non-empty string")
        if not isinstance(self.input, str):
            raise ValueError("input must be a string")
        if not isinstance(self.expected_output, str):
            raise ValueError("expected_output must be a string")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary")

@dataclass
class EvaluationResult:
    case_id: str
    input: str
    expected_output: str
    actual_output: str
    score: float
    failure_reason: Optional[str] = None

    def __post_init__(self):
        if not isinstance(self.case_id, str) or not self.case_id.strip():
            raise ValueError("case_id must be a non-empty string")
        if not isinstance(self.input, str):
            raise ValueError("input must be a string")
        if not isinstance(self.expected_output, str):
            raise ValueError("expected_output must be a string")
        if not isinstance(self.actual_output, str):
            raise ValueError("actual_output must be a string")
        if not isinstance(self.score, (int, float)) or not (0.0 <= self.score <= 1.0):
            raise ValueError("score must be a float between 0.0 and 1.0")
        if self.failure_reason is not None and not isinstance(self.failure_reason, str):
            raise ValueError("failure_reason must be a string if provided")

@dataclass
class MetricResult:
    metric_name: str
    score: float
    details: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.metric_name, str) or not self.metric_name.strip():
            raise ValueError("metric_name must be a non-empty string")
        if not isinstance(self.score, (int, float)):
            raise ValueError("score must be a float or integer")
        if not isinstance(self.details, dict):
            raise ValueError("details must be a dictionary")

@dataclass
class BenchmarkDefinition:
    benchmark_name: str
    description: str
    cases: List[EvaluationCase] = field(default_factory=list)

    def __post_init__(self):
        if not isinstance(self.benchmark_name, str) or not self.benchmark_name.strip():
            raise ValueError("benchmark_name must be a non-empty string")
        if not isinstance(self.description, str) or not self.description.strip():
            raise ValueError("description must be a non-empty string")
        if not isinstance(self.cases, list):
            raise ValueError("cases must be a list of EvaluationCase")
        for case in self.cases:
            if not isinstance(case, EvaluationCase):
                raise ValueError("all cases must be EvaluationCase instances")
