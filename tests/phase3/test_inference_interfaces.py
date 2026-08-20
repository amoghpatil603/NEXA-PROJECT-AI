import unittest
from nexa_runtime.engine import GenerationConfig, GenerationRequest, GenerationResult

class TestInferenceInterfaces(unittest.TestCase):
    def test_valid_config(self):
        config = GenerationConfig(
            max_new_tokens=256,
            temperature=0.8,
            top_k=40,
            top_p=0.95,
            repetition_penalty=1.1,
            do_sample=True,
            seed=123
        )
        self.assertEqual(config.max_new_tokens, 256)
        self.assertEqual(config.temperature, 0.8)
        self.assertEqual(config.top_k, 40)
        self.assertEqual(config.top_p, 0.95)
        self.assertEqual(config.repetition_penalty, 1.1)
        self.assertTrue(config.do_sample)
        self.assertEqual(config.seed, 123)

    def test_invalid_max_new_tokens(self):
        with self.assertRaises(ValueError):
            GenerationConfig(max_new_tokens=0)
        with self.assertRaises(ValueError):
            GenerationConfig(max_new_tokens=-10)
        with self.assertRaises(ValueError):
            GenerationConfig(max_new_tokens="100")

    def test_invalid_temperature(self):
        with self.assertRaises(ValueError):
            GenerationConfig(temperature=-0.1)
        with self.assertRaises(ValueError):
            GenerationConfig(temperature=2.5)
        with self.assertRaises(ValueError):
            GenerationConfig(temperature="hot")

    def test_invalid_top_k(self):
        with self.assertRaises(ValueError):
            GenerationConfig(top_k=-1)
        with self.assertRaises(ValueError):
            GenerationConfig(top_k="top")

    def test_invalid_top_p(self):
        with self.assertRaises(ValueError):
            GenerationConfig(top_p=-0.05)
        with self.assertRaises(ValueError):
            GenerationConfig(top_p=1.05)
        with self.assertRaises(ValueError):
            GenerationConfig(top_p="high")

    def test_invalid_repetition_penalty(self):
        with self.assertRaises(ValueError):
            GenerationConfig(repetition_penalty=0.9)
        with self.assertRaises(ValueError):
            GenerationConfig(repetition_penalty=-1.5)
        with self.assertRaises(ValueError):
            GenerationConfig(repetition_penalty="none")

    def test_generation_request_validation(self):
        # Empty prompt should raise ValueError
        with self.assertRaises(ValueError):
            GenerationRequest(prompt="")
        with self.assertRaises(ValueError):
            GenerationRequest(prompt="   ")
        with self.assertRaises(ValueError):
            GenerationRequest(prompt=1234)

    def test_kv_cache_generation_and_shape_consistency(self):
        import torch
        from backend.models.model.config import NexaConfig
        from backend.models.model.transformer import NexaTransformer
        from backend.nexa.inference.generator import NexaGenerator

        torch.manual_seed(42)
        config = NexaConfig(vocab_size=100, max_seq_len=64, d_model=32, n_layers=2, n_heads=4, d_ff=64)
        model = NexaTransformer(config)
        model.eval()

        # Dummy tokenizer for deterministic test
        class DummyTokenizer:
            def encode(self, text):
                return [10, 20, 30]
            def decode(self, ids):
                return " ".join(str(i) for i in ids)

        tokenizer = DummyTokenizer()
        generator = NexaGenerator(model, tokenizer, device='cpu')

        # 1. No-cache greedy generation produces reference output
        torch.manual_seed(100)
        tokens_no_cache = list(generator.generate("hello", max_new_tokens=6, temperature=0.0, use_cache=False))

        # 2. Cache-enabled greedy generation produces identical tokens
        torch.manual_seed(100)
        tokens_with_cache = list(generator.generate("hello", max_new_tokens=6, temperature=0.0, use_cache=True))

        self.assertEqual(tokens_no_cache, tokens_with_cache)
        self.assertEqual(len(tokens_with_cache), 6)

        # 3. Cache resets correctly and does not leak state across generations
        torch.manual_seed(100)
        tokens_run2 = list(generator.generate("hello", max_new_tokens=6, temperature=0.0, use_cache=True))
        self.assertEqual(tokens_with_cache, tokens_run2)

        # 4. Cache handles one-token incremental decode & shape consistency
        input_ids = torch.tensor([[10, 20, 30]], dtype=torch.long)
        logits1, past_kv = model(input_ids, use_cache=True)
        self.assertIsNotNone(past_kv)
        self.assertEqual(len(past_kv), config.n_layers)

        # Check shape of past_kv: (k, v) where each is [B, n_heads, seq_len, head_dim]
        head_dim = config.d_model // config.n_heads
        for layer_k, layer_v in past_kv:
            self.assertEqual(layer_k.shape, (1, config.n_heads, 3, head_dim))
            self.assertEqual(layer_v.shape, (1, config.n_heads, 3, head_dim))

        # Incremental single token forward
        next_token = torch.tensor([[40]], dtype=torch.long)
        logits2, past_kv2 = model(next_token, past_key_values=past_kv, use_cache=True)
        self.assertEqual(len(past_kv2), config.n_layers)
        for layer_k, layer_v in past_kv2:
            self.assertEqual(layer_k.shape, (1, config.n_heads, 4, head_dim))
            self.assertEqual(layer_v.shape, (1, config.n_heads, 4, head_dim))

        # Compare logits of 4-token full sequence without cache vs 1-token decode with cache
        full_seq = torch.tensor([[10, 20, 30, 40]], dtype=torch.long)
        logits_full, _ = model(full_seq, use_cache=False)
        self.assertTrue(torch.allclose(logits2, logits_full[:, [-1], :], atol=1e-5))

if __name__ == "__main__":
    unittest.main()
