import unittest
from agent_planner import AgentPlanner, ExecutionPlan, Task
from tool_registry import ToolRegistry
from tool_manager import ToolManager

class TestProductionPlanner(unittest.TestCase):
    def setUp(self):
        self.registry = ToolRegistry()
        self.tool_manager = ToolManager(self.registry)
        self.planner = AgentPlanner(self.tool_manager)

    def test_simple_chat_intent(self):
        plan = self.planner.plan_execution("Hello", [])
        self.assertEqual(plan.plan_type, "NORMAL_CHAT")
        self.assertGreater(len(plan.tasks), 0)
        self.assertIsNotNone(plan.plan_id)

    def test_memory_store_intent(self):
        plan = self.planner.plan_execution("Remember my birthday is March 15", [])
        self.assertEqual(plan.plan_type, "MEMORY_STORE")
        self.assertEqual(plan.tasks[0].required_tool, "memory_store")

    def test_memory_recall_intent(self):
        plan = self.planner.plan_execution("When is my birthday?", [])
        self.assertEqual(plan.plan_type, "MEMORY_RECALL")
        self.assertEqual(plan.tasks[0].required_tool, "memory_recall")

    def test_rag_search_intent(self):
        plan = self.planner.plan_execution("Summarize README.md", [])
        self.assertEqual(plan.plan_type, "RAG_SEARCH")
        self.assertEqual(plan.tasks[0].required_tool, "rag_search")

    def test_filesystem_intent(self):
        plan = self.planner.plan_execution("Create hello.py", [])
        self.assertEqual(plan.plan_type, "FILESYSTEM")
        self.assertEqual(plan.tasks[0].required_tool, "write_file")

    def test_python_intent(self):
        plan = self.planner.plan_execution("Run hello.py", [])
        self.assertEqual(plan.plan_type, "PYTHON")
        self.assertEqual(plan.tasks[0].required_tool, "execute_python")

    def test_terminal_intent(self):
        plan = self.planner.plan_execution("Execute ls -la", [])
        self.assertEqual(plan.plan_type, "TERMINAL")
        self.assertEqual(plan.tasks[0].required_tool, "execute_command")

    def test_multi_step_intent(self):
        plan = self.planner.plan_execution("Create hello.py then execute it", [])
        self.assertEqual(plan.plan_type, "MULTI_STEP")
        self.assertGreaterEqual(len(plan.tasks), 2)
        task2 = plan.tasks[1]
        self.assertIn("task_1", task2.depends_on)

    def test_unknown_prompt_fallback(self):
        plan = self.planner.plan_execution("Xyzzy qux random gibberish 12345", [])
        self.assertEqual(plan.plan_type, "NORMAL_CHAT")
        self.assertGreater(len(plan.tasks), 0)

    def test_never_empty_plan(self):
        plan = self.planner.plan_execution("", [])
        self.assertIsNotNone(plan)
        self.assertGreater(len(plan.tasks), 0)

    def test_performance_metrics(self):
        self.planner.plan_execution("Test prompt for metrics", [])
        metrics = self.planner.get_performance_metrics()
        self.assertIn("planning_latency_ms", metrics)
        self.assertIn("memory_consumption_bytes", metrics)
        self.assertIn("average_plan_size", metrics)
        self.assertGreater(metrics["total_plans_generated"], 0)

if __name__ == "__main__":
    unittest.main()
