import subprocess
import json

scenarios = [
    "Hello",
    "Remember my name is Alex.",
    "What is my name?",
    "Summarize README.md",
    "Calculate 245*38",
    "Search transformer architecture"
]

for s in scenarios:
    print(f"\n====================================================")
    print(f"Scenario: {s}")
    payload = json.dumps({"message": s, "max_tokens": 20})
    result = subprocess.run([".venv/bin/python", "api_chat_runner.py", payload], capture_output=True, text=True)
    out = result.stdout
    err = result.stderr
    print(out)
    if err:
        print("ERR:", err)
    
