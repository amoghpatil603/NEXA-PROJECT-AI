import subprocess
from filesystem_tools import BaseTool

class ExecuteCommandTool(BaseTool):
    def __init__(self):
        super().__init__("execute_command", "Execute a terminal command", "Confirmation Required")

    def execute(self, command, timeout=30):
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
            return {"stdout": result.stdout, "stderr": result.stderr, "exit_code": result.returncode}
        except subprocess.TimeoutExpired:
            return {"error": "Command execution timed out"}
