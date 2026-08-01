with open("run_phase5b5_verification.py", "r") as f:
    content = f.read()

import re
# Find the loop
old_loop = """    for idx in range(100):
        body_str, latency = http_post("/api/chat", {
            "message": f"Stress prompt #{idx+1}: Verify local stability and tensor cleanup.",
            "max_tokens": 20,
            "temperature": 0.7
        })
        prompt_latencies.append(latency)
        try:
            r = json.loads(body_str)
            if "response" in r:
                consecutive_success += 1
        except Exception:
            pass"""

new_loop = """    for idx in range(100):
        try:
            body_str, latency = http_post("/api/chat", {
                "message": f"Stress prompt #{idx+1}: Verify local stability and tensor cleanup.",
                "max_tokens": 20,
                "temperature": 0.7
            })
            prompt_latencies.append(latency)
            r = json.loads(body_str)
            if "response" in r:
                consecutive_success += 1
        except Exception as e:
            print(f"Exception at prompt {idx+1}: {e}")"""

content = content.replace(old_loop, new_loop)

# Also fix the final stats to handle empty list
old_stats = """    avg_latency = round(sum(prompt_latencies) / len(prompt_latencies), 3)
    min_latency = min(prompt_latencies)
    max_latency = max(prompt_latencies)"""

new_stats = """    avg_latency = round(sum(prompt_latencies) / len(prompt_latencies), 3) if prompt_latencies else 0
    min_latency = min(prompt_latencies) if prompt_latencies else 0
    max_latency = max(prompt_latencies) if prompt_latencies else 0"""

content = content.replace(old_stats, new_stats)

with open("run_phase5b5_verification.py", "w") as f:
    f.write(content)

print("File patched")
