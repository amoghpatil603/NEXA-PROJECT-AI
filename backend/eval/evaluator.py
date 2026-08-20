import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from .interfaces import EvaluationCase, EvaluationResult, MetricResult, BenchmarkDefinition

class ExactMatchMetric:
    @staticmethod
    def compute(expected: str, actual: str) -> float:
        return 1.0 if expected.strip().lower() == actual.strip().lower() else 0.0

class SubstringMetric:
    @staticmethod
    def compute(expected: str, actual: str) -> float:
        return 1.0 if expected.strip().lower() in actual.strip().lower() else 0.0

class EvaluationRunner:
    """
    Executes benchmark suites against language models or inference generation callables.
    Produces structured evaluation summaries and persisted JSON benchmark reports.
    """
    def __init__(self, metrics: Optional[Dict[str, Callable[[str, str], float]]] = None):
        self.metrics = metrics or {
            "exact_match": ExactMatchMetric.compute,
            "substring_match": SubstringMetric.compute
        }

    def evaluate_case(
        self,
        case: EvaluationCase,
        generate_fn: Callable[[str], str]
    ) -> EvaluationResult:
        actual_output = generate_fn(case.input)
        em_score = self.metrics["exact_match"](case.expected_output, actual_output)
        
        failure_reason = None
        if em_score < 1.0:
            failure_reason = f"Expected '{case.expected_output}', got '{actual_output}'"

        return EvaluationResult(
            case_id=case.case_id,
            input=case.input,
            expected_output=case.expected_output,
            actual_output=actual_output,
            score=em_score,
            failure_reason=failure_reason
        )

    def run_benchmark(
        self,
        benchmark: BenchmarkDefinition,
        generate_fn: Callable[[str], str]
    ) -> Dict[str, Any]:
        results: List[EvaluationResult] = []
        total_score = 0.0

        for case in benchmark.cases:
            res = self.evaluate_case(case, generate_fn)
            results.append(res)
            total_score += res.score

        num_cases = len(benchmark.cases)
        accuracy = (total_score / num_cases) if num_cases > 0 else 0.0

        summary = {
            "benchmark_name": benchmark.benchmark_name,
            "description": benchmark.description,
            "total_cases": num_cases,
            "passed_cases": sum(1 for r in results if r.score == 1.0),
            "failed_cases": sum(1 for r in results if r.score < 1.0),
            "mean_accuracy": accuracy,
            "results": [
                {
                    "case_id": r.case_id,
                    "input": r.input,
                    "expected": r.expected_output,
                    "actual": r.actual_output,
                    "score": r.score,
                    "failure_reason": r.failure_reason
                }
                for r in results
            ]
        }
        return summary

    def save_report(self, summary: Dict[str, Any], output_path: str):
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
