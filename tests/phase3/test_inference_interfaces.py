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

    def test_kv_cache_sliding_window_context_limits(self):
        import torch
        from backend.models.model.config import NexaConfig
        from backend.models.model.transformer import NexaTransformer
        from backend.nexa.inference.generator import NexaGenerator

        # Tiny model with small max_seq_len = 8
        torch.manual_seed(42)
        config = NexaConfig(vocab_size=50, max_seq_len=8, d_model=16, n_layers=2, n_heads=2, d_ff=32)
        model = NexaTransformer(config)
        model.eval()

        class MockTokenizer:
            def encode(self, text):
                return [5, 10, 15]
            def decode(self, ids):
                return "".join(f"[{i}]" for i in ids)

        tokenizer = MockTokenizer()
        generator = NexaGenerator(model, tokenizer, device='cpu')

        # 1. Equality below context limit
        torch.manual_seed(99)
        tokens_no_cache = list(generator.generate("prompt", max_new_tokens=4, temperature=0.0, use_cache=False))
        torch.manual_seed(99)
        tokens_cache = list(generator.generate("prompt", max_new_tokens=4, temperature=0.0, use_cache=True))
        self.assertEqual(tokens_no_cache, tokens_cache)

        # 2. Generation beyond context limit (prompt len 3 + 12 generated tokens = 15 > max_seq_len 8)
        # Verify it generates successfully without raising any shape or index error
        torch.manual_seed(99)
        tokens_extended = list(generator.generate("prompt", max_new_tokens=12, temperature=0.0, use_cache=True))
        self.assertEqual(len(tokens_extended), 12)

        # 3. Cache length never exceeds max_seq_len=8 at any step
        input_ids = torch.tensor([[5, 10, 15]], dtype=torch.long)
        _, past_kv = model(input_ids, use_cache=True)
        for step in range(15):
            next_tok = torch.tensor([[step % 50]], dtype=torch.long)
            _, past_kv = model(next_tok, past_key_values=past_kv, use_cache=True)
            for k, v in past_kv:
                self.assertLessEqual(k.size(-2), config.max_seq_len)
                self.assertLessEqual(v.size(-2), config.max_seq_len)

        # 4. Cache reset between requests
        torch.manual_seed(99)
        run_a = list(generator.generate("prompt", max_new_tokens=5, temperature=0.0, use_cache=True))
        torch.manual_seed(99)
        run_b = list(generator.generate("prompt", max_new_tokens=5, temperature=0.0, use_cache=True))
        self.assertEqual(run_a, run_b)

    def test_batched_inference(self):
        import torch
        from backend.models.model.config import NexaConfig
        from backend.models.model.transformer import NexaTransformer
        from nexa_runtime.engine import NexaInferenceEngine, GenerationConfig, GenerationRequest

        torch.manual_seed(42)
        config = NexaConfig(vocab_size=100, max_seq_len=64, d_model=32, n_layers=2, n_heads=4, d_ff=64)
        model = NexaTransformer(config)
        model.eval()

        # Track input batch sizes to prove tensor reached model with B=2
        forward_batch_shapes = []
        def hook_fn(module, input_tensor, output):
            # input_tensor is a tuple (idx, ...)
            if isinstance(input_tensor, tuple) and len(input_tensor) > 0 and isinstance(input_tensor[0], torch.Tensor):
                forward_batch_shapes.append(input_tensor[0].shape)

        hook_handle = model.register_forward_hook(hook_fn)

        class MockTokenizer:
            def encode(self, text):
                if text == "short":
                    return [10, 20]
                elif text == "longer prompt here":
                    return [10, 20, 30, 40, 50]
                elif text == "eos prompt":
                    return [6] # Token that triggers EOS
                return [15, 25, 35]

            def decode(self, ids):
                return "".join(f"[{i}]" for i in ids if i != 0)

        tokenizer = MockTokenizer()
        engine = NexaInferenceEngine(model, tokenizer, device='cpu')

        cfg_greedy = GenerationConfig(max_new_tokens=5, do_sample=False)
        req_a = GenerationRequest(prompt="short", config=cfg_greedy)
        req_b = GenerationRequest(prompt="longer prompt here", config=cfg_greedy)

        # 1. batch_size = 1 works identically to single generation
        forward_batch_shapes.clear()
        single_res_a = engine.generate(req_a)
        self.assertTrue(any(s[0] == 1 for s in forward_batch_shapes), "Proof B=1 reached model")

        # 2. batch_size = 2 actually enters model with B=2
        forward_batch_shapes.clear()
        batch_res = engine.generate_batch([req_a, req_b])
        self.assertEqual(len(batch_res), 2)
        # PROOF: check that forward calls received tensor with shape [2, T]
        self.assertTrue(len(forward_batch_shapes) > 0)
        self.assertTrue(all(s[0] == 2 for s in forward_batch_shapes), f"Proof B=2 reached model: shapes={forward_batch_shapes}")

        # 3. Unequal prompt lengths & matching greedy outputs
        single_res_b = engine.generate(req_b)
        self.assertEqual(batch_res[0].text, single_res_a.text)
        self.assertEqual(batch_res[1].text, single_res_b.text)

        # 4. padding tokens do not corrupt generation
        self.assertNotIn("[0]", batch_res[0].text)
        self.assertNotIn("[0]", batch_res[1].text)

        # 5. request-response metadata matches 1:1
        self.assertEqual(batch_res[0].tokens_generated, 5)
        self.assertEqual(batch_res[1].tokens_generated, 5)
        self.assertEqual(batch_res[0].finish_reason, "length")
        self.assertEqual(batch_res[1].finish_reason, "length")

        # 6. EOS isolation: when one request reaches EOS earlier, other continues
        req_eos = GenerationRequest(prompt="eos prompt", config=cfg_greedy)
        req_normal = GenerationRequest(prompt="longer prompt here", config=GenerationConfig(max_new_tokens=3, do_sample=False))
        forward_batch_shapes.clear()
        mixed_batch = engine.generate_batch([req_eos, req_normal])
        self.assertEqual(len(mixed_batch), 2)
        self.assertEqual(mixed_batch[1].tokens_generated, 3)

        # 7. Empty batch handled
        self.assertEqual(engine.generate_batch([]), [])

        hook_handle.remove()

if __name__ == "__main__":
    unittest.main()
