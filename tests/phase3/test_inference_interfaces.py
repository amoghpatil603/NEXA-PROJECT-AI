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

        # Valid request
        req = GenerationRequest(prompt="Write a poem")
        self.assertEqual(req.prompt, "Write a poem")
        self.assertIsNotNone(req.config)

if __name__ == "__main__":
    unittest.main()
