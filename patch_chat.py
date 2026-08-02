import re

with open("chat_engine.py", "r") as f:
    content = f.read()

target = """        try:
            self.tokenizer = NexaBPETokenizer()
            tok_candidates = [
                (vocab_path, merges_path),
                ('/app/applet/nexa-model/tokenizer/candidates/8k/bpe_vocab.json', '/app/applet/nexa-model/tokenizer/candidates/8k/bpe_merges.txt'),
                ('/app/applet/nexa-model/tokenizer/bpe_vocab.json', '/app/applet/nexa-model/tokenizer/bpe_merges.txt'),
                ('nexa-model/tokenizer/candidates/8k/bpe_vocab.json', 'nexa-model/tokenizer/candidates/8k/bpe_merges.txt'),
                ('/nexa-model/tokenizer/candidates/8k/bpe_vocab.json', '/nexa-model/tokenizer/candidates/8k/bpe_merges.txt')
            ]
            loaded_tok = False
            for vp, mp in tok_candidates:
                if vp and mp and os.path.exists(vp) and os.path.exists(mp):
                    self.tokenizer.load(vp, mp)
                    loaded_tok = True
                    break
            if not loaded_tok:
                print("Warning: Tokenizer files not found, using default special tokens.")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize BPE Tokenizer: {e}")"""

replacement = """        try:
            tok_candidates = [
                "/app/applet/nexa-model/tokenizer/production/tokenizer.json",
                "nexa-model/tokenizer/production/tokenizer.json"
            ]
            loaded_tok = False
            for p in tok_candidates:
                if os.path.exists(p):
                    self.tokenizer = IncrementalBPETokenizer.load(p)
                    loaded_tok = True
                    print(f"Successfully loaded tokenizer from {p}")
                    break
            if not loaded_tok:
                print("Warning: Tokenizer files not found, using default special tokens.")
                self.tokenizer = IncrementalBPETokenizer(vocab_size=8000)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize BPE Tokenizer: {e}")"""

content = content.replace(target, replacement)

with open("chat_engine.py", "w") as f:
    f.write(content)
