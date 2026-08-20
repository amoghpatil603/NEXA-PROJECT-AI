from typing import List, Optional
from .interfaces import GenerationConfig, GenerationRequest, GenerationResult, InferenceEngine
from backend.nexa.inference.generator import NexaGenerator

class NexaInferenceEngine(InferenceEngine):
    def __init__(self, model, tokenizer, device: str = 'cpu', pad_token_id: int = 0, eos_token_id: int = 6):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self.pad_token_id = pad_token_id
        self.eos_token_id = eos_token_id
        self.generator = NexaGenerator(model, tokenizer, device=device)

    def generate(self, request: GenerationRequest) -> GenerationResult:
        results = self.generate_batch([request])
        return results[0]

    def generate_batch(self, requests: List[GenerationRequest]) -> List[GenerationResult]:
        if not isinstance(requests, list):
            raise TypeError("requests must be a list of GenerationRequest")
        if len(requests) == 0:
            return []

        results = []
        for req in requests:
            if not isinstance(req, GenerationRequest):
                raise TypeError("Each item in requests must be a GenerationRequest")
            
            cfg = req.config or GenerationConfig()
            
            # Deterministic temperature
            temp = cfg.temperature if cfg.do_sample else 0.0
            
            tokens = []
            for token_str in self.generator.generate(
                prompt=req.prompt,
                max_new_tokens=cfg.max_new_tokens,
                temperature=temp,
                top_k=cfg.top_k,
                top_p=cfg.top_p,
                repetition_penalty=cfg.repetition_penalty,
                use_cache=True
            ):
                tokens.append(token_str)
                
            full_text = "".join(tokens)
            results.append(GenerationResult(
                text=full_text,
                tokens_generated=len(tokens),
                finish_reason="stop" if (tokens and "<EOS>" in tokens[-1]) else "length"
            ))
            
        return results
