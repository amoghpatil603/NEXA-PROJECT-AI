import sys
import json
from pathlib import Path

from chat_engine import ChatEngine

def evaluate_checkpoint(ckpt_path, name):
    print(f"=== Evaluating {name} ({ckpt_path}) ===")
    try:
        engine = ChatEngine(checkpoint_path=ckpt_path)
    except RuntimeError as e:
        print(f"Failed to load model: {e}")
        return None

    prompts = [
        "Hello",
        "Explain what a transformer is.",
        "Count from 1 to 20.",
        "Generate Python code that prints Hello World.",
        "What is machine learning?"
    ]

    results = []
    for i, p in enumerate(prompts):
        print(f"--- Prompt {i+1}: {p} ---")
        try:
            response = engine.generate(user_prompt=p, max_new_tokens=64, temperature=0.7)
            print(f"Model: {response}\n")
            results.append({"prompt": p, "response": response})
        except Exception as e:
            print(f"Error generating response: {e}\n")
            results.append({"prompt": p, "error": str(e)})
            
    return results

def main():
    ckpts = [
        ("Phase 4e (Under-trained)", "/app/applet/checkpoints_phase4e/latest.ckpt"),
        ("Final Training (Converged)", "/app/applet/checkpoints_full/best.ckpt")
    ]
    
    all_results = {}
    for name, path in ckpts:
        if Path(path).exists():
            all_results[name] = evaluate_checkpoint(path, name)
        else:
            print(f"Checkpoint not found: {path}")

    with open("benchmark_comparison.json", "w") as f:
        json.dump(all_results, f, indent=2)

if __name__ == "__main__":
    main()
