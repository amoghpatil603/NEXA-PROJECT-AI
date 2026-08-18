import re

with open("api_chat_runner.py", "r") as f:
    content = f.read()

stream_save_old = """
                t1 = time.time()
                dt = max(t1 - t0, 0.001)
                tps = round(tokens_count / dt, 1)
"""

stream_save_new = """
                # Automatically store assistant responses
                if full_text and len(full_text) > 20:
                    exec_engine.memory_engine.create_memory("assistant_response", full_text)
                    
                t1 = time.time()
                dt = max(t1 - t0, 0.001)
                tps = round(tokens_count / dt, 1)
"""
content = content.replace(stream_save_old, stream_save_new)

with open("api_chat_runner.py", "w") as f:
    f.write(content)

print("Patched api_chat_runner.py for stream memory")
