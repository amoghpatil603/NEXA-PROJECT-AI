import sys
import os
import time
import torch
from pathlib import Path

PROJECT_ROOT = "/content/NEXA-PROJECT-AI"
sys.path.append(PROJECT_ROOT)
sys.path.append(os.path.join(PROJECT_ROOT, "nexa-model"))

from nexa.inference.model_loader import NexaModelLoader
from nexa.inference.generator import NexaGenerator
from tokenizer.bpe_tokenizer import NexaBPETokenizer

def run_chat():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt_path = os.path.join(PROJECT_ROOT, "checkpoints/nexa_final.pt")
    tok_path = os.path.join(PROJECT_ROOT, "nexa-model/tokenizer/production/tokenizer.json")

    try:
        tokenizer = NexaBPETokenizer.load(tok_path)
        model, config = NexaModelLoader.load(ckpt_path, device=device)
        generator = NexaGenerator(model, tokenizer, device=device)
    except Exception as e:
        print(f"\u274c Initialization Error: {e}")
        return

    print("\n=== NEXA INTERACTIVE CHAT ===")
    print("Type /exit to quit, /help for commands.\n")

    history = []

    while True:
        user_input = input("User: ").strip()
        if not user_input: continue
        
        if user_input == "/exit": break
        if user_input == "/clear":
            history = []
            print("History cleared.")
            continue

        start_time = time.time()
        print("NEXA: ", end="", flush=True)
        
        token_count = 0
        for token_text in generator.generate(user_input, max_new_tokens=100):
            print(token_text, end="", flush=True)
            token_count += 1
        
        elapsed = time.time() - start_time
        print(f"\n\n[Stats: {token_count} tokens | {elapsed:.2f}s | {token_count/elapsed:.1f} tok/s]")

if __name__ == "__main__":
    run_chat()
