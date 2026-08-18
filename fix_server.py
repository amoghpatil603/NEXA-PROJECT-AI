import re

with open('server.ts', 'r') as f:
    content = f.read()

new_get_python = """  function getPythonBin(): string {
    const checkPaths = [
      process.env.VIRTUAL_ENV ? path.join(process.env.VIRTUAL_ENV, "bin", "python") : null,
      path.join(process.cwd(), ".venv", "bin", "python"),
      path.join(process.cwd(), "venv", "bin", "python"),
      "python3",
      "python"
    ].filter(Boolean) as string[];

    for (const p of checkPaths) {
      if (p === "python3" || p === "python") return p;
      try {
        fs.accessSync(p, fs.constants.X_OK);
        return p;
      } catch (e) {
        continue;
      }
    }
    return "python3";
  }"""

content = re.sub(r'  function getPythonBin\(\): string \{.*?\n  \}', new_get_python, content, flags=re.DOTALL)

# Now fix the child spawn error handling
spawn_code = """    const child = spawn(pythonBin, [scriptPath, task.payload], { cwd: process.cwd() });"""

new_spawn_code = """    const child = spawn(pythonBin, [scriptPath, task.payload], { cwd: process.cwd() });

    child.on("error", (err) => {
      console.error(`[SPAWN ERROR] Failed to start python:`, err);
      if (!task.res.headersSent) {
        task.res.status(500).json({
          success: false,
          error: "Failed to spawn inference process",
          details: err.message
        });
      }
      currentActiveTask = null;
      processNextQueueTask();
    });"""

content = content.replace(spawn_code, new_spawn_code)

with open('server.ts', 'w') as f:
    f.write(content)

