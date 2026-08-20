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

    def test_multi_agent_coordination_runtime(self):
        from backend.agents.coordination import AgentRegistry, MultiAgentCoordinator, SharedTaskState
        from backend.agents.multi_agent_system import BaseAgent, AgentMessage

        class MockResearchAgent(BaseAgent):
            def __init__(self):
                super().__init__("ResearchAgent")

            def process(self, message: AgentMessage) -> AgentMessage:
                return AgentMessage(
                    sender=self.agent_id,
                    receiver=message.sender,
                    task_id=message.task_id,
                    status="SUCCESS",
                    payload={"research_data": f"Facts about {message.payload.get('task')}"}
                )

        class MockCodingAgent(BaseAgent):
            def __init__(self):
                super().__init__("CodingAgent")

            def process(self, message: AgentMessage) -> AgentMessage:
                context = message.payload.get("context", {})
                research = context.get("research_data", "no research")
                return AgentMessage(
                    sender=self.agent_id,
                    receiver=message.sender,
                    task_id=message.task_id,
                    status="SUCCESS",
                    payload={"code": f"# Implementation based on {research}"}
                )

        class FailingAgent(BaseAgent):
            def __init__(self):
                super().__init__("FailingAgent")

            def process(self, message: AgentMessage) -> AgentMessage:
                return AgentMessage(
                    sender=self.agent_id,
                    receiver=message.sender,
                    task_id=message.task_id,
                    status="FAILED",
                    payload={"error": "Database query timed out"}
                )

        # 1. Two agents registered
        registry = AgentRegistry()
        research_agent = MockResearchAgent()
        coding_agent = MockCodingAgent()
        failing_agent = FailingAgent()

        registry.register(research_agent, capabilities=["research", "search", "facts"])
        registry.register(coding_agent, capabilities=["coding", "python", "code_generation"])
        registry.register(failing_agent, capabilities=["unstable"])

        self.assertEqual(len(registry.list_agents()), 3)
        self.assertEqual(registry.get_agent("ResearchAgent"), research_agent)
        self.assertEqual(registry.get_agent("CodingAgent"), coding_agent)

        coordinator = MultiAgentCoordinator(registry)

        # 2. Task routed to correct agent & 3. Agent result returned
        task_research = AgentTask(task_id="t1", task_type="research", description="quantum physics")
        state1 = coordinator.route_task(task_research)
        self.assertEqual(state1.state, AgentState.COMPLETED)
        self.assertIn("research_data", state1.context)
        self.assertIn("quantum physics", state1.context["research_data"])
        self.assertEqual(len(state1.history), 1)
        self.assertEqual(state1.history[0]["agent_id"], "ResearchAgent")

        # 4. Agent failure propagates
        task_failing = AgentTask(task_id="t-fail", task_type="unstable", description="bad task")
        state_fail = coordinator.route_task(task_failing)
        self.assertEqual(state_fail.state, AgentState.FAILED)
        self.assertIn("Database query timed out", state_fail.error)

        # 5. Multi-step task state remains consistent (handoff pipeline)
        task_step1 = AgentTask(task_id="p1", task_type="research", description="sorting algorithms")
        task_step2 = AgentTask(task_id="p2", task_type="coding", description="write sorting code")

        state_handoff = coordinator.execute_handoff(task_step1, task_step2)
        self.assertEqual(state_handoff.state, AgentState.COMPLETED)
        self.assertIn("research_data", state_handoff.context)
        self.assertIn("code", state_handoff.context)
        self.assertIn("sorting algorithms", state_handoff.context["code"])
        self.assertEqual(len(state_handoff.history), 2)
        self.assertEqual(state_handoff.history[0]["agent_id"], "ResearchAgent")
        self.assertEqual(state_handoff.history[1]["agent_id"], "CodingAgent")

        # Failure in handoff stops pipeline
        state_fail_handoff = coordinator.execute_handoff(task_failing, task_step2)
        self.assertEqual(state_fail_handoff.state, AgentState.FAILED)
        self.assertEqual(len(state_fail_handoff.history), 1)

    def test_agent_planner_coordinator_integration(self):
        from backend.agents.agent_planner import AgentPlanner, Task, ExecutionPlan
        from backend.agents.coordination import AgentRegistry, MultiAgentCoordinator
        from backend.agents.multi_agent_system import BaseAgent, AgentMessage
        from backend.agents.interfaces import AgentState

        class MockRagAgent(BaseAgent):
            def __init__(self):
                super().__init__("RagAgent")

            def process(self, message: AgentMessage) -> AgentMessage:
                return AgentMessage(
                    sender=self.agent_id,
                    receiver=message.sender,
                    task_id=message.task_id,
                    status="SUCCESS",
                    payload={"documents": ["NEXA architecture doc", "API guidelines"]}
                )

        class FailingAgent(BaseAgent):
            def __init__(self):
                super().__init__("BrokenAgent")

            def process(self, message: AgentMessage) -> AgentMessage:
                return AgentMessage(
                    sender=self.agent_id,
                    receiver=message.sender,
                    task_id=message.task_id,
                    status="FAILED",
                    payload={"error": "Remote agent unreachable"}
                )

        registry = AgentRegistry()
        rag_agent = MockRagAgent()
        failing_agent = FailingAgent()
        registry.register(rag_agent, capabilities=["rag_search", "documentation"])
        registry.register(failing_agent, capabilities=["broken_task"])

        coordinator = MultiAgentCoordinator(registry)
        planner = AgentPlanner(coordinator=coordinator)

        # 1. Real planner path -> plan execution -> coordinator -> registered agent -> result
        plan = planner.plan_execution("search documentation for README.md")
        self.assertEqual(plan.tasks[0].task_type, "rag_search")

        results = planner.execute_plan(plan)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "success")
        self.assertIn("documents", results[0]["result"])
        self.assertIn("NEXA architecture doc", results[0]["result"]["documents"])

        # 2. Direct route_to_coordinator integration
        state = planner.route_to_coordinator("documentation", "find API guidelines")
        self.assertEqual(state.state, AgentState.COMPLETED)
        self.assertIn("documents", state.context)

        # 3. Failure propagation through planner execution
        fail_task = Task(task_id="t_err", task_type="broken_task", description="fail now")
        fail_plan = ExecutionPlan(plan_id="p_fail", plan_type="test", status="pending", created_at=0.0, tasks=[fail_task])
        fail_results = planner.execute_plan(fail_plan)
        self.assertEqual(len(fail_results), 1)
        self.assertEqual(fail_results[0]["status"], "error")
        self.assertIn("Remote agent unreachable", fail_results[0]["message"])

    def test_invalid_plan_step(self):
        from backend.agents.interfaces import ToolAction, PlanStep
        action = ToolAction(tool_name="tool", arguments={})
        with self.assertRaises(ValueError):
            PlanStep(step_id="", action=action)
        with self.assertRaises(ValueError):
            PlanStep(step_id="s", action=None)
        with self.assertRaises(ValueError):
            PlanStep(step_id="s", action=action, status="invalid_status")

if __name__ == "__main__":
    unittest.main()
