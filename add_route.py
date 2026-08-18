import sys

with open("server.ts", "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'app.get("/api/health"' in line:
        insert_idx = i
        break

upload_route = """
  app.post("/api/upload", upload.single("file"), (req, res) => {
    if (!req.file) {
      return res.status(400).json({ error: "No file uploaded" });
    }
    
    // rename file to its original name and extension if needed
    // or just pass the path
    const filePath = req.file.path;
    const originalName = req.file.originalname;
    const destPath = path.join(process.cwd(), "uploads", originalName);
    
    // simple rename
    try {
      if (!fs.existsSync(path.join(process.cwd(), "uploads"))) {
        fs.mkdirSync(path.join(process.cwd(), "uploads"));
      }
      fs.renameSync(filePath, destPath);
    } catch (e) {
      // ignore
    }

    const py = getPythonBin();
    const runner = spawn(py, ["upload_runner.py", destPath], {
      cwd: process.cwd(),
      env: { ...process.env, PYTHONUNBUFFERED: "1" }
    });

    let output = "";
    runner.stdout.on("data", (data) => output += data.toString());
    runner.stderr.on("data", (data) => output += data.toString());

    runner.on("close", (code) => {
      try {
        // Try to parse the last JSON object in output
        const lines = output.trim().split("\\n");
        const lastLine = lines[lines.length - 1];
        const result = JSON.parse(lastLine);
        if (code === 0) {
           res.json(result);
        } else {
           res.status(500).json({ error: result.error || "Upload failed", details: output });
        }
      } catch (e) {
        res.status(500).json({ error: "Failed to parse runner output", output });
      }
    });
  });
"""

lines.insert(insert_idx, upload_route)

with open("server.ts", "w") as f:
    f.writelines(lines)
