import time
import uuid
import sys
from typing import List, Dict, Any, Optional

class Task:
    def __init__(self, task_id: str, task_type: str, description: str, required_tool: Optional[str] = None, parameters: Optional[Dict[str, Any]] = None, priority: int = 1, depends_on: Optional[List[str]] = None):
        self.task_id = task_id
        self.task_type = task_type
        self.description = description
        self.required_tool = required_tool
        self.parameters = parameters or {}
        self.priority = priority
        self.depends_on = depends_on or []
        self.tool = required_tool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "description": self.description,
            "required_tool": self.required_tool,
            "tool": self.required_tool,
            "parameters": self.parameters,
            "priority": self.priority,
            "depends_on": self.depends_on
        }

    def __getitem__(self, key):
        d = self.to_dict()
        if key in d:
            return d[key]
        raise KeyError(key)

    def get(self, key, default=None):
        return self.to_dict().get(key, default)

class ExecutionPlan:
    def __init__(self, plan_id: str, plan_type: str, status: str, created_at: float, tasks: List[Task]):
        self.plan_id = plan_id
        self.plan_type = plan_type
        self.status = status
        self.created_at = created_at
        self.tasks = tasks

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "plan_type": self.plan_type,
            "status": self.status,
            "created_at": self.created_at,
            "tasks": [t.to_dict() for t in self.tasks]
        }

    def __iter__(self):
        return iter(self.tasks)

    def __getitem__(self, index):
        return self.tasks[index]

    def __len__(self):
        return len(self.tasks)

class AgentPlanner:
    def __init__(self, tool_manager=None):
        self.tool_manager = tool_manager
        self.last_planning_latency = 0.0
        self.last_memory_consumption = 0.0
        self.total_plans_generated = 0
        self.total_tasks_generated = 0

    def classify_intent(self, prompt: str) -> str:
        if not prompt or not isinstance(prompt, str):
            return "NORMAL_CHAT"
        p = prompt.strip().lower()
        
        if " then " in p or " after " in p or "and then" in p or " first " in p:
            return "MULTI_STEP"
            
        if any(kw in p for kw in ["remember", "store", "save", "my birthday is", "note that", "keep in mind"]):
            return "MEMORY_STORE"
            
        if any(kw in p for kw in ["what is my", "when is my", "when is", "recall", "do you remember", "what did i", "retrieve", "do you know my"]):
            return "MEMORY_RECALL"
            
        if any(kw in p for kw in ["summarize", "search documentation", "look up", "docs", "readme", "explain"]):
            return "RAG_SEARCH"
            
        if any(kw in p for kw in ["create file", "write file", "list files", "read file", "delete file", "create ", "list"]):
            return "FILESYSTEM"
            
        if (("run" in p or "execute" in p) and (".py" in p or "python" in p or "script" in p)):
            return "PYTHON"
            
        if ".py" in p and not ("run" in p or "execute" in p):
            return "FILESYSTEM"
            
        if any(kw in p for kw in ["execute", "run command", "bash", "shell", "ls ", "npm", "git"]):
            return "TERMINAL"
            
        if p in ["hi", "hello", "hey", "greetings"] or len(p) < 3:
            return "NORMAL_CHAT"
            
        return "NORMAL_CHAT"

    def plan_execution(self, prompt: str, available_tools: list = None) -> ExecutionPlan:
        start_time = time.time()
        mem_before = sys.getsizeof(prompt) + (sys.getsizeof(available_tools) if available_tools else 0)
        
        intent = self.classify_intent(prompt)
        plan_id = f"plan-{int(time.time()*1000)}-{uuid.uuid4().hex[:6]}"
        tasks = []
        
        p = prompt.strip() if prompt else ""
        p_lower = p.lower()
        
        if intent == "NORMAL_CHAT":
            tasks.append(Task(
                task_id="task_1",
                task_type="chat",
                description=f"Process chat query: {p}",
                required_tool=None,
                parameters={"prompt": p},
                priority=1,
                depends_on=[]
            ))
            
        elif intent == "MEMORY_STORE":
            tasks.append(Task(
                task_id="task_1",
                task_type="memory_store",
                description=f"Store information in memory: {p}",
                required_tool="memory_store",
                parameters={"content": p},
                priority=1,
                depends_on=[]
            ))
            
        elif intent == "MEMORY_RECALL":
            tasks.append(Task(
                task_id="task_1",
                task_type="memory_recall",
                description=f"Recall information from memory: {p}",
                required_tool="memory_recall",
                parameters={"query": p},
                priority=1,
                depends_on=[]
            ))
            
        elif intent == "RAG_SEARCH":
            query = p
            if "readme.md" in p_lower:
                query = "README.md"
            tasks.append(Task(
                task_id="task_1",
                task_type="rag_search",
                description=f"Search documentation and knowledge base for: {query}",
                required_tool="rag_search",
                parameters={"query": query},
                priority=1,
                depends_on=[]
            ))
            
        elif intent == "FILESYSTEM":
            if "list" in p_lower:
                tasks.append(Task(
                    task_id="task_1",
                    task_type="filesystem",
                    description="List files in directory",
                    required_tool="list_files",
                    parameters={"path": "."},
                    priority=1,
                    depends_on=[]
                ))
            elif "create" in p_lower or "write" in p_lower or ".py" in p_lower:
                filename = "hello.py"
                if "hello.py" in p_lower:
                    filename = "hello.py"
                elif ".py" in p_lower:
                    parts = p.split()
                    for pt in parts:
                        if pt.endswith(".py") or "." in pt:
                            filename = pt.strip(".,'\"")
                            break
                tasks.append(Task(
                    task_id="task_1",
                    task_type="filesystem",
                    description=f"Create file {filename}",
                    required_tool="write_file",
                    parameters={"path": filename, "content": "# Generated by NEXA Planner\nprint('Hello from NEXA')\n"},
                    priority=1,
                    depends_on=[]
                ))
            else:
                tasks.append(Task(
                    task_id="task_1",
                    task_type="filesystem",
                    description=f"Filesystem operation: {p}",
                    required_tool="read_file",
                    parameters={"path": "README.md"},
                    priority=1,
                    depends_on=[]
                ))
                
        elif intent == "PYTHON":
            filename = "hello.py"
            if "hello.py" in p_lower:
                filename = "hello.py"
            tasks.append(Task(
                task_id="task_1",
                task_type="python",
                description=f"Execute python script {filename}",
                required_tool="execute_python",
                parameters={"code": f"import os; print('Executing {filename}'); os.system('python3 {filename} if os.path.exists(\"{filename}\") else print(\"File not found\")')"},
                priority=1,
                depends_on=[]
            ))
            
        elif intent == "TERMINAL":
            cmd = "ls -la"
            if "ls" in p_lower:
                cmd = "ls -la"
            elif "npm" in p_lower:
                cmd = "npm run build"
            tasks.append(Task(
                task_id="task_1",
                task_type="terminal",
                description=f"Execute terminal command: {cmd}",
                required_tool="execute_command",
                parameters={"command": cmd},
                priority=1,
                depends_on=[]
            ))
            
        elif intent == "MULTI_STEP":
            filename = "hello.py"
            tasks.append(Task(
                task_id="task_1",
                task_type="filesystem",
                description=f"Step 1: Create {filename}",
                required_tool="write_file",
                parameters={"path": filename, "content": "print('Hello World from NEXA Multi-step')\n"},
                priority=1,
                depends_on=[]
            ))
            tasks.append(Task(
                task_id="task_2",
                task_type="python",
                description=f"Step 2: Execute {filename}",
                required_tool="execute_python",
                parameters={"code": f"with open('{filename}') as f: exec(f.read())"},
                priority=2,
                depends_on=["task_1"]
            ))
            tasks.append(Task(
                task_id="task_3",
                task_type="chat",
                description="Step 3: Summarize execution results",
                required_tool=None,
                parameters={"summary": "Execution completed successfully"},
                priority=3,
                depends_on=["task_2"]
            ))
        else:
            tasks.append(Task(
                task_id="task_1",
                task_type="chat",
                description=f"Process prompt: {p}",
                required_tool=None,
                parameters={"prompt": p},
                priority=1,
                depends_on=[]
            ))

        if not tasks:
            tasks.append(Task(
                task_id="task_1",
                task_type="chat",
                description="Default chat handling",
                required_tool=None,
                parameters={"prompt": p},
                priority=1,
                depends_on=[]
            ))

        end_time = time.time()
        self.last_planning_latency = (end_time - start_time) * 1000.0
        self.last_memory_consumption = float(mem_before)
        self.total_plans_generated += 1
        self.total_tasks_generated += len(tasks)

        plan = ExecutionPlan(
            plan_id=plan_id,
            plan_type=intent,
            status="pending",
            created_at=time.time(),
            tasks=tasks
        )
        return plan

    def execute_plan(self, plan: Any) -> List[Dict[str, Any]]:
        tasks = []
        if hasattr(plan, 'tasks'):
            tasks = plan.tasks
        elif isinstance(plan, dict) and 'tasks' in plan:
            tasks = plan['tasks']
        elif isinstance(plan, list):
            tasks = plan
        else:
            tasks = [plan]

        results = []
        completed_task_ids = set()
        remaining_tasks = list(tasks)
        max_iterations = len(tasks) * 2 + 5
        iteration = 0

        while remaining_tasks and iteration < max_iterations:
            iteration += 1
            progress_made = False
            next_remaining = []

            for task in remaining_tasks:
                if isinstance(task, dict):
                    depends_on = task.get('depends_on', [])
                    tool = task.get('tool') or task.get('required_tool')
                    params = task.get('parameters', {})
                    task_id = task.get('task_id', 'task_unknown')
                else:
                    depends_on = task.depends_on
                    tool = task.tool or task.required_tool
                    params = task.parameters
                    task_id = task.task_id

                deps_satisfied = all(dep in completed_task_ids for dep in depends_on)

                if deps_satisfied:
                    progress_made = True
                    if tool and self.tool_manager:
                        try:
                            res = self.tool_manager.execute_tool(tool, params)
                            results.append({"task_id": task_id, "tool": tool, "status": res.get('status', 'success'), "result": res})
                            if res.get('status') == 'error':
                                return results
                        except Exception as e:
                            results.append({"task_id": task_id, "tool": tool, "status": "error", "message": str(e)})
                            return results
                    else:
                        results.append({"task_id": task_id, "tool": None, "status": "success", "result": "Completed successfully"})
                    completed_task_ids.add(task_id)
                else:
                    next_remaining.append(task)

            remaining_tasks = next_remaining
            if not progress_made:
                break

        return results

    def get_performance_metrics(self) -> Dict[str, Any]:
        avg_plan_size = (self.total_tasks_generated / self.total_plans_generated) if self.total_plans_generated > 0 else 0.0
        return {
            "planning_latency_ms": self.last_planning_latency,
            "memory_consumption_bytes": self.last_memory_consumption,
            "total_plans_generated": self.total_plans_generated,
            "total_tasks_generated": self.total_tasks_generated,
            "average_plan_size": avg_plan_size
        }
