import re

with open('server.ts', 'r') as f:
    content = f.read()

new_get_python = """  let _cachedPythonBin: string | null = null;
  function getPythonBin(): string {
    if (_cachedPythonBin) return _cachedPythonBin;
    const { spawnSync } = require("child_process");
    const checkPaths = [
      process.env.VIRTUAL_ENV ? path.join(process.env.VIRTUAL_ENV, "bin", "python") : null,
      path.join(process.cwd(), ".venv", "bin", "python"),
      path.join(process.cwd(), "venv", "bin", "python"),
      "python3",
      "python"
    ].filter(Boolean) as string[];

    for (const p of checkPaths) {
      try {
        const res = spawnSync(p, ["--version"]);
        if (res.status === 0) {
          _cachedPythonBin = p;
          return p;
        }
      } catch (e) {
        continue;
      }
    }
    _cachedPythonBin = "python3";
    return "python3";
  }"""

content = re.sub(r'  function getPythonBin\(\): string \{.*?\n  \}', new_get_python, content, flags=re.DOTALL)

with open('server.ts', 'w') as f:
    f.write(content)

