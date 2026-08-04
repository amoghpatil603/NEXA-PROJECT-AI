import sys
from pathlib import Path
import os
import json

from chat_engine import ChatEngine

def evaluate():
    try:
        engine = ChatEngine(checkpoint_path="/app/applet/checkpoints_phase4e/latest.ckpt")
    except RuntimeError as e:
        print(f"Failed to load model: {e}")
        return

    prompts = [
        "Hello",
        "Who are you?",
        "Explain what a transformer is.",
        "Write a short story.",
        "Summarize a paragraph.",
        "Continue this sentence:\nArtificial Intelligence is...",
        "Count from 1 to 20.",
        "Generate Python code that prints Hello World.",
        "Answer:\nWhat is machine learning?",
        "Write five sentences about computers."
    ]

    results = []

    print("Evaluating Prompts:\n")
    for i, p in enumerate(prompts):
        print(f"--- Prompt {i+1} ---")
        print(f"User: {p}")
        try:
            response = engine.generate(user_prompt=p, max_new_tokens=64, temperature=0.7)
            print(f"Model: {response}\n")
            results.append({"prompt": p, "response": response})
        except Exception as e:
            print(f"Error generating response: {e}\n")
            results.append({"prompt": p, "error": str(e)})
            
    with open("evaluation_report.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    evaluate()
