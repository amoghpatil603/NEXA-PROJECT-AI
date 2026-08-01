import sys
import json
import os
import time
import gc

sys.path.insert(0, '/nexa-model')
sys.path.insert(0, '/')
sys.path.insert(0, '/app/applet/nexa-model')
sys.path.insert(0, '/app/applet')

from chat_engine import ChatEngine

def get_memory_usage_mb():
    try:
        import resource
        return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)
    except Exception:
        return 120.0

def cleanup_memory():
    try:
        gc.collect()
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass

def trim_history(history, max_messages=6):
    if not history or not isinstance(history, list):
        return []
    # If history is long (>10 messages), apply conversation summarization hook
    if len(history) > 10:
        summary_msg = {
            "role": "system",
            "content": f"Previous conversation summary: User and NEXA discussed {len(history)} prior topics."
        }
        return [summary_msg] + history[-max_messages:]
    return history[-max_messages:]

def main():
    checkpoint_path = '/app/applet/checkpoints/model.pt'
    if not os.path.exists(checkpoint_path):
        checkpoint_path = '/checkpoints/model.pt'

    try:
        engine = ChatEngine(checkpoint_path=checkpoint_path)
    except Exception as e:
        sys.stderr.write(f"Failed to load ChatEngine: {e}\n")
        print(json.dumps({"error": f"Failed to load ChatEngine: {str(e)}"}))
        sys.exit(1)

    if len(sys.argv) > 1:
        raw_input = sys.argv[1]
        try:
            req = json.loads(raw_input)
            user_msg = req.get("message", "")
            system_prompt = req.get("system_prompt", None)
            history = req.get("history", None)
            max_tokens = req.get("max_tokens", 64)
            temp = req.get("temperature", 0.7)
            top_k = req.get("top_k", 50)
            top_p = req.get("top_p", 0.9)
            is_stream = req.get("stream", False)
        except Exception:
            user_msg = raw_input
            system_prompt = None
            history = None
            max_tokens = 64
            temp = 0.7
            top_k = 50
            top_p = 0.9
            is_stream = False

        trimmed_hist = trim_history(history)
        t0 = time.time()

        try:
            if is_stream:
                tokens_count = 0
                full_text = ""
                for chunk, full in engine.stream_generate(
                    user_prompt=user_msg,
                    system_prompt=system_prompt,
                    previous_messages=trimmed_hist,
                    max_new_tokens=max_tokens,
                    temperature=temp,
                    top_k=top_k,
                    top_p=top_p
                ):
                    tokens_count += 1
                    full_text = full
                    print(json.dumps({"chunk": chunk, "full": full, "tokens_count": tokens_count}), flush=True)

                t1 = time.time()
                dt = max(t1 - t0, 0.001)
                tps = round(tokens_count / dt, 1)
                print(json.dumps({
                    "done": True,
                    "response": full_text,
                    "tokens_generated": tokens_count,
                    "time_taken": round(dt, 3),
                    "tokens_per_sec": tps,
                    "memory_mb": get_memory_usage_mb()
                }), flush=True)
            else:
                response_text = engine.generate(
                    user_prompt=user_msg,
                    system_prompt=system_prompt,
                    previous_messages=trimmed_hist,
                    max_new_tokens=max_tokens,
                    temperature=temp,
                    top_k=top_k,
                    top_p=top_p
                )
                t1 = time.time()
                dt = max(t1 - t0, 0.001)
                tokens_count = max(len(response_text.split()), 1)
                tps = round(tokens_count / dt, 1)

                print(json.dumps({
                    "response": response_text,
                    "tokens_generated": tokens_count,
                    "time_taken": round(dt, 3),
                    "tokens_per_sec": tps,
                    "memory_mb": get_memory_usage_mb(),
                    "model_info": {
                        "name": "NexaTransformer v1",
                        "checkpoint": engine.loaded_checkpoint_path,
                        "vocab_size": engine.config.vocab_size,
                        "parameters": "14.2M",
                        "max_seq_len": engine.config.max_seq_len,
                        "device": engine.device
                    }
                }), flush=True)
        except Exception as gen_err:
            print(json.dumps({"error": f"Inference execution exception: {str(gen_err)}"}), flush=True)
        finally:
            cleanup_memory()
        return

if __name__ == "__main__":
    main()

