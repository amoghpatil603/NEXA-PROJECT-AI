import unittest
import json
from backend.eval.interfaces import EvaluationCase, EvaluationResult, MetricResult, BenchmarkDefinition

class TestEvalScaffold(unittest.TestCase):
    def test_valid_eval_case(self):
        case = EvaluationCase(
            case_id="case-1",
            input="Translate to French: Hello",
            expected_output="Bonjour",
            metadata={"difficulty": "easy"}
        )
        self.assertEqual(case.case_id, "case-1")
        self.assertEqual(case.expected_output, "Bonjour")

        with self.assertRaises(ValueError):
            EvaluationCase(case_id="", input="in", expected_output="out")

    def test_eval_result_score_validation(self):
        res = EvaluationResult(
            case_id="case-1",
            input="Translate to French: Hello",
            expected_output="Bonjour",
            actual_output="Bonjour",
            score=1.0,
            failure_reason=None
        )
        self.assertEqual(res.score, 1.0)
        self.assertIsNone(res.failure_reason)

        # Invalid score validation checks
        with self.assertRaises(ValueError):
            EvaluationResult(
                case_id="case-1",
                input="Translate to French: Hello",
                expected_output="Bonjour",
                actual_output="Bonjour",
                score=1.5
            )
        with self.assertRaises(ValueError):
            EvaluationResult(
                case_id="case-1",
                input="Translate to French: Hello",
                expected_output="Bonjour",
                actual_output="Bonjour",
                score=-0.1
            )

    def test_deterministic_metric_evaluation(self):
        case = EvaluationCase(
            case_id="c1",
            input="What is 2+2?",
            expected_output="4"
        )
        
        def calculate_exact_match(case_item: EvaluationCase, actual: str) -> EvaluationResult:
            expected = case_item.expected_output.strip().lower()
            got = actual.strip().lower()
            score = 1.0 if expected == got else 0.0
            reason = None if score == 1.0 else f"Expected '{expected}', got '{got}'"
            return EvaluationResult(
                case_id=case_item.case_id,
                input=case_item.input,
                expected_output=case_item.expected_output,
                actual_output=actual,
                score=score,
                failure_reason=reason
            )

        res_pass = calculate_exact_match(case, "4")
        self.assertEqual(res_pass.score, 1.0)
        self.assertIsNone(res_pass.failure_reason)

        res_fail = calculate_exact_match(case, "five")
        self.assertEqual(res_fail.score, 0.0)
        self.assertEqual(res_fail.failure_reason, "Expected '4', got 'five'")

    def test_benchmark_definition(self):
        cases = [
            EvaluationCase(case_id="c1", input="in1", expected_output="out1"),
            EvaluationCase(case_id="c2", input="in2", expected_output="out2")
        ]
        benchmark = BenchmarkDefinition(
            benchmark_name="Translation Benchmark",
            description="Tests translation capability",
            cases=cases
        )
        self.assertEqual(benchmark.benchmark_name, "Translation Benchmark")
        self.assertEqual(len(benchmark.cases), 2)

    def test_eval_case_serialization_and_missing_output(self):
        with self.assertRaises(ValueError):
            EvaluationCase(case_id="case-1", input="in", expected_output=None)
        with self.assertRaises(ValueError):
            EvaluationCase(case_id="case-1", input="in", expected_output=123)

        case = EvaluationCase(
            case_id="c1",
            input="in1",
            expected_output="out1",
            metadata={"priority": "high"}
        )
        from dataclasses import asdict
        d = asdict(case)
        self.assertEqual(d["case_id"], "c1")
        self.assertEqual(d["metadata"]["priority"], "high")

        case2 = EvaluationCase(**d)
        self.assertEqual(case2.case_id, case.case_id)
        self.assertEqual(case2.expected_output, case.expected_output)

    def test_evaluation_runner_execution(self):
        from backend.eval.evaluator import EvaluationRunner
        import tempfile
        import os
        
        benchmark = BenchmarkDefinition(
            benchmark_name="Arithmetic Benchmark",
            description="Simple arithmetic evaluation",
            cases=[
                EvaluationCase(case_id="q1", input="2+2", expected_output="4"),
                EvaluationCase(case_id="q2", input="3*3", expected_output="9"),
                EvaluationCase(case_id="q3", input="5-1", expected_output="4")
            ]
        )

        def mock_model(prompt: str) -> str:
            if prompt == "2+2": return "4"
            if prompt == "3*3": return "9"
            return "unknown" # q3 fails

        runner = EvaluationRunner()
        summary = runner.run_benchmark(benchmark, mock_model)
        
        self.assertEqual(summary["total_cases"], 3)
        self.assertEqual(summary["passed_cases"], 2)
        self.assertEqual(summary["failed_cases"], 1)
        self.assertAlmostEqual(summary["mean_accuracy"], 2/3, places=2)

        # Test report saving
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            report_path = tf.name

        try:
            runner.save_report(summary, report_path)
            self.assertTrue(os.path.exists(report_path))
            with open(report_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            self.assertEqual(loaded["benchmark_name"], "Arithmetic Benchmark")
        finally:
            if os.path.exists(report_path):
                os.unlink(report_path)

    def test_run_eval_cli_parser_and_suites(self):
        from scripts.run_eval import build_parser, load_benchmark
        parser = build_parser()
        args = parser.parse_args(["--benchmark", "gsm8k", "--dry-run"])
        self.assertEqual(args.benchmark, "gsm8k")
        self.assertTrue(args.dry_run)

        bench_gsm8k = load_benchmark("gsm8k")
        self.assertEqual(bench_gsm8k.benchmark_name, "gsm8k")
        self.assertGreater(len(bench_gsm8k.cases), 0)

        bench_all = load_benchmark("all")
        self.assertEqual(bench_all.benchmark_name, "all")
        self.assertGreater(len(bench_all.cases), 3)

if __name__ == "__main__":
    unittest.main()

