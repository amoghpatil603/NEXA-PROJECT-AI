import sys
import json
import os
import datetime
import hashlib
import time
from pathlib import Path

# Setup path
sys.path.append(os.path.abspath("nexa-model"))
from tokenizer.bpe_tokenizer import NexaBPETokenizer, DEFAULT_SPECIAL_TOKENS
from tokenizer.incremental_bpe import IncrementalBPETokenizer

class TokenizerPipeline:
    def __init__(self, dataset_path, output_dir, vocab_size=500):
        self.dataset_path = Path(dataset_path)
        self.output_dir = Path(output_dir)
        self.vocab_size = vocab_size
        self.tokenizer = IncrementalBPETokenizer(vocab_size=self.vocab_size, min_frequency=2, special_tokens=DEFAULT_SPECIAL_TOKENS)

    def extract_text(self):
        texts = []
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                sample = json.loads(line)
                # Combine instruction, output, chosen, rejected
                text = sample.get("instruction", "")
                if "output" in sample:
                    text += " " + sample["output"]
                if "chosen" in sample:
                    text += " " + sample["chosen"]
                if "rejected" in sample:
                    text += " " + sample["rejected"]
                texts.append(text.strip())
        return texts

    def train(self):
        print("Extracting texts from certified dataset...")
        texts = self.extract_text()
        print(f"Extracted {len(texts)} samples. Training tokenizer...")
        
        start_time = time.time()
        self.tokenizer.train(texts)
        duration = time.time() - start_time
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tokenizer.save(self.output_dir / "tokenizer.json")
        
        # Generate auxiliary artifacts
        vocab = {str(k): "".join(chr(b) for b in v) for k, v in self.tokenizer.vocab.items()}
        with open(self.output_dir / "vocab.json", "w", encoding="utf-8") as f:
            json.dump(vocab, f, indent=2)
            
        with open(self.output_dir / "merges.txt", "w", encoding="utf-8") as f:
            for m in self.tokenizer.merges:
                f.write(f"{m[0]} {m[1]}\n")
                
        with open(self.output_dir / "tokenizer_config.json", "w", encoding="utf-8") as f:
            json.dump({
                "model_type": "nexa_bpe",
                "vocab_size": len(self.tokenizer.vocab) + len(self.tokenizer.special_tokens),
                "special_tokens": self.tokenizer.special_tokens
            }, f, indent=2)
            
        return {
            "vocab_size": len(self.tokenizer.vocab) + len(self.tokenizer.special_tokens),
            "training_time": duration,
            "merges_count": len(self.tokenizer.merges)
        }
        
    def verify(self):
        test_string = "What is the capital of France? Paris."
        encoded = self.tokenizer.encode(test_string)
        decoded = self.tokenizer.decode(encoded)
        success = test_string == decoded
        
        # Test unknown/special token handling
        spec_encode = self.tokenizer.encode("<|endoftext|>")
        spec_handled = len(spec_encode) > 0
        
        return {
            "encode_decode_success": success,
            "special_token_handled": spec_handled,
            "test_string": test_string,
            "encoded_tokens": encoded,
            "decoded_string": decoded
        }

if __name__ == "__main__":
    pipeline = TokenizerPipeline("validated_dataset.jsonl", "tokenizer_v1", vocab_size=300)
    stats = pipeline.train()
    print("Training stats:", stats)
    
    verif = pipeline.verify()
    print("Verification:", verif)
    
    # Save verification for report
    with open("tokenizer_v1/stats.json", "w") as f:
        json.dump({"stats": stats, "verification": verif}, f)
