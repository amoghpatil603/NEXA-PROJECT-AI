import subprocess
from backend.utils.filesystem_tools import BaseTool

class ExecuteCommandTool(BaseTool):
    def __init__(self):
        super().__init__("execute_command", "Execute a terminal command", "Confirmation Required")

    def execute(self, command, timeout=30):
        if not isinstance(command, str):
            return {"error": "Command must be a string"}

        # Security check: prevent command separators and redirections
        for operator in [";", "&&", "||", "|", "`", "$(", ">", "<", "\n"]:
            if operator in command:
                return {"error": f"Security restriction: command contains restricted shell operator '{operator}'"}

        # Security check: prevent directory traversal
        if ".." in command:
            return {"error": "Security restriction: command contains directory traversal sequence '..'"}

        parts = command.strip().split()
        if not parts:
            return {"error": "Empty command"}

        # Restrict dangerous binaries
        dangerous_commands = {"rm", "mv", "chmod", "chown", "dd", "format", "mkfs", "sh", "bash"}
        if parts[0] in dangerous_commands:
            return {"error": f"Security restriction: execution of command '{parts[0]}' is blocked"}

        try:
            # Execute command directly without a shell (shell=False) to avoid injection vulnerabilities
            result = subprocess.run(parts, shell=False, capture_output=True, text=True, timeout=timeout)
            return {"stdout": result.stdout, "stderr": result.stderr, "exit_code": result.returncode}
        except subprocess.TimeoutExpired:
            return {"error": "Command execution timed out"}
        except Exception as e:
            return {"error": f"Command execution failed: {str(e)}"}
