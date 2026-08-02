import urllib.request
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
    print(f"\nScenario: {s}")
    req = urllib.request.Request("http://127.0.0.1:3000/api/chat", method="POST")
    req.add_header("Content-Type", "application/json")
    data = json.dumps({"message": s, "max_tokens": 20}).encode("utf-8")
    try:
        with urllib.request.urlopen(req, data=data) as response:
            result = json.loads(response.read().decode())
            print("Response:", result.get("response", "").strip() or result)
    except Exception as e:
        print("Error:", e)
