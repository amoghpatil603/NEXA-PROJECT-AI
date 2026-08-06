import subprocess
from backend.utils.filesystem_tools import BaseTool

class ExecutePythonTool(BaseTool):
    def __init__(self):
        super().__init__("execute_python", "Execute python code", "Confirmation Required")

    def execute(self, code, timeout=30):
        try:
            result = subprocess.run(['python3', '-c', code], capture_output=True, text=True, timeout=timeout)
            return {"stdout": result.stdout, "stderr": result.stderr, "exit_code": result.returncode}
        except subprocess.TimeoutExpired:
            return {"error": "Python execution timed out"}
