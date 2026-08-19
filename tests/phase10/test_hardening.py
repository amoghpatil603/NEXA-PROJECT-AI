import unittest
from pathlib import Path
from backend.utils.terminal_tools import ExecuteCommandTool

class TestHardening(unittest.TestCase):
    def test_python_compile_checks(self):
        import py_compile
        workspace_root = Path(__file__).resolve().parent.parent.parent
        backend_dir = workspace_root / "backend"
        tests_dir = workspace_root / "tests"
        
        py_files = list(backend_dir.glob("**/*.py")) + list(tests_dir.glob("**/*.py"))
        for f in py_files:
            try:
                py_compile.compile(str(f), doraise=True)
            except py_compile.PyCompileError as e:
                self.fail(f"Compilation failed for {f}: {e}")

    def test_execute_command_restricted_operators(self):
        tool = ExecuteCommandTool()
        
        bad_commands = [
            "echo Hello; rm -rf /",
            "echo Hello && ls",
            "cat file.txt | grep text",
            "echo `whoami`"
        ]
        for cmd in bad_commands:
            res = tool.execute(cmd)
            self.assertIn("error", res)
            self.assertIn("restricted shell operator", res["error"])

    def test_execute_command_restricted_binaries(self):
        tool = ExecuteCommandTool()
        
        bad_commands = [
            "rm -rf /app",
            "chmod +x script.py",
            "chown root script.py"
        ]
        for cmd in bad_commands:
            res = tool.execute(cmd)
            self.assertIn("error", res)
            self.assertIn("blocked", res["error"])

if __name__ == "__main__":
    unittest.main()
