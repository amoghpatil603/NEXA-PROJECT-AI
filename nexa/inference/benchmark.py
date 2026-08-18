import time
import torch
import json
from .generator import NexaGenerator
from .model_loader import NexaModelLoader
from tokenizer.bpe_tokenizer import NexaBPETokenizer

BENCHMARK_PROMPTS = [
    {"domain": "math", "prompt": "If x + 5 = 10, then x is equal to"},
    {"domain": "logic", "prompt": "All humans are mortal. Socrates is a human. Therefore, Socrates is"},
    {"domain": "coding", "prompt": "def fibonacci(n):\n    if n <= 1: return n\n    else: return"}
]

def run_benchmark(checkpoint_path, tokenizer_path, device='cpu'):
    tokenizer = NexaBPETokenizer.load(tokenizer_path)
    model, config = NexaModelLoader.load(checkpoint_path, device=device)
    generator = NexaGenerator(model, tokenizer, device=device)
    
    results = []
    print(f"--- Starting NEXA Benchmark on {device} ---")
    
    for item in BENCHMARK_PROMPTS:
        start = time.time()
        response = ""
        tokens = 0
        
        # Generate using streaming interface
        for chunk in generator.generate(item['prompt'], max_new_tokens=32):
            response += chunk
            tokens += 1
            
        elapsed = time.time() - start
        tps = tokens / elapsed if elapsed > 0 else 0
        
        results.append({
            "domain": item['domain'],
            "prompt": item['prompt'],
            "tokens_per_sec": round(tps, 2),
            "response": response.strip()
        })
        print(f"Domain: {item['domain']} | TPS: {tps:.2f}")
    
    return results

if __name__ == '__main__':
    # Default paths for production environment
    CP_PATH = '/content/NEXA-PROJECT-AI/checkpoints/ckpt_3000.pt'
    TOK_PATH = '/content/NEXA-PROJECT-AI/nexa-model/tokenizer/production/tokenizer.json'
    DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    bench_results = run_benchmark(CP_PATH, TOK_PATH, DEVICE)
    with open('/content/NEXA-PROJECT-AI/logs/benchmark_results.json', 'w') as f:
        json.dump(bench_results, f, indent=2)
