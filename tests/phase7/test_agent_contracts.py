import unittest
from backend.agents.interfaces import AgentState, AgentTask, ToolAction, VerificationResult, PlanStep

class TestAgentContracts(unittest.TestCase):
    def test_agent_states(self):
        self.assertEqual(AgentState.PENDING, "pending")
        self.assertEqual(AgentState.RUNNING, "running")
        self.assertEqual(AgentState.COMPLETED, "completed")
        self.assertEqual(AgentState.FAILED, "failed")
        self.assertEqual(AgentState.BLOCKED, "blocked")

    def test_valid_agent_task(self):
        task = AgentTask(task_id="t1", task_type="code_generation", description="Write quicksort", priority=2)
        self.assertEqual(task.task_id, "t1")
        self.assertEqual(task.priority, 2)

        with self.assertRaises(ValueError):
            AgentTask(task_id="", task_type="t", description="d")
        with self.assertRaises(ValueError):
            AgentTask(task_id="id", task_type="t", description="d", priority=0)

    def test_plan_step_serialization_roundtrip(self):
        action = ToolAction(tool_name="write_file", arguments={"path": "quicksort.py", "content": "def quicksort(): pass"})
        verification = VerificationResult(is_verified=True, notes="quicksort.py compiled clean")
        
        step = PlanStep(
            step_id="step-1",
            action=action,
            status=AgentState.RUNNING,
            dependencies=["step-0"],
            verification=verification
        )

        self.assertEqual(step.status, AgentState.RUNNING)

        # Serialize
        d = step.to_dict()
        self.assertEqual(d["step_id"], "step-1")
        self.assertEqual(d["status"], "running")
        self.assertEqual(d["action"]["tool_name"], "write_file")
        self.assertTrue(d["verification"]["is_verified"])

        # Deserialize
        step2 = PlanStep.from_dict(d)
        self.assertEqual(step2.step_id, "step-1")
        self.assertEqual(step2.status, AgentState.RUNNING)
        self.assertEqual(step2.action.tool_name, "write_file")
        self.assertEqual(step2.dependencies, ["step-0"])
        self.assertTrue(step2.verification.is_verified)
        self.assertEqual(step2.verification.notes, "quicksort.py compiled clean")

    def test_invalid_plan_step(self):
        action = ToolAction(tool_name="tool", arguments={})
        with self.assertRaises(ValueError):
            PlanStep(step_id="", action=action)
        with self.assertRaises(ValueError):
            PlanStep(step_id="s", action=None)
        with self.assertRaises(ValueError):
            PlanStep(step_id="s", action=action, status="invalid_status")

if __name__ == "__main__":
    unittest.main()
