import re

with open("api_chat_runner.py", "r") as f:
    content = f.read()

content = content.replace(
    "from chat_engine import ChatEngine",
    "from chat_engine import ChatEngine\nfrom execution_engine import ExecutionEngine"
)

content = content.replace(
    "engine = ChatEngine(checkpoint_path=checkpoint_path)",
    "engine = ChatEngine(checkpoint_path=checkpoint_path)\n        exec_engine = ExecutionEngine()"
)

# Replace stream generate block
stream_block_old = """
                for chunk, full in engine.stream_generate(
                    user_prompt=user_msg,
                    system_prompt=system_prompt,
                    previous_messages=trimmed_hist,
                    max_new_tokens=max_tokens,
                    temperature=temp,
                    top_k=top_k,
                    top_p=top_p
                ):
"""

stream_block_new = """
                context = exec_engine.process_request(user_msg, trimmed_hist, system_prompt)
                
                for chunk, full in engine.stream_generate(
                    user_prompt=context['user_prompt'],
                    system_prompt=context['system_prompt'],
                    previous_messages=context['previous_messages'],
                    max_new_tokens=max_tokens,
                    temperature=temp,
                    top_k=top_k,
                    top_p=top_p
                ):
"""
content = content.replace(stream_block_old, stream_block_new)

# Replace standard generate block
gen_block_old = """
                response_text = engine.generate(
                    user_prompt=user_msg,
                    system_prompt=system_prompt,
                    previous_messages=trimmed_hist,
                    max_new_tokens=max_tokens,
                    temperature=temp,
                    top_k=top_k,
                    top_p=top_p
                )
"""

gen_block_new = """
                context = exec_engine.process_request(user_msg, trimmed_hist, system_prompt)
                
                response_text = engine.generate(
                    user_prompt=context['user_prompt'],
                    system_prompt=context['system_prompt'],
                    previous_messages=context['previous_messages'],
                    max_new_tokens=max_tokens,
                    temperature=temp,
                    top_k=top_k,
                    top_p=top_p
                )
                
                # Automatically store assistant responses
                if response_text and len(response_text) > 20:
                    exec_engine.memory_engine.create_memory("assistant_response", response_text)
"""
content = content.replace(gen_block_old, gen_block_new)

with open("api_chat_runner.py", "w") as f:
    f.write(content)

print("Patched api_chat_runner.py")
