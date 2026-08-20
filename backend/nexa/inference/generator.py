import torch
import torch.nn.functional as F
from .sampler import top_k_top_p_filtering

class NexaGenerator:
    def __init__(self, model, tokenizer, device='cpu'):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device

    @torch.no_grad()
    def generate(self,
                 prompt,
                 max_new_tokens=50,
                 temperature=1.0,
                 top_k=50,
                 top_p=0.9,
                 repetition_penalty=1.2,
                 use_cache=False):
        
        max_seq_len = getattr(self.model.config, 'max_seq_len', 256)
        input_ids = torch.tensor([self.tokenizer.encode(prompt)], dtype=torch.long).to(self.device)
        past_key_values = None
        
        for step in range(max_new_tokens):
            if use_cache:
                if past_key_values is None:
                    curr_input = input_ids[:, -max_seq_len:]
                else:
                    curr_input = input_ids[:, -1:]
                logits, past_key_values = self.model(curr_input, past_key_values=past_key_values, use_cache=True)
            else:
                curr_input = input_ids[:, -max_seq_len:]
                logits, _ = self.model(curr_input)

            if temperature < 1e-5:
                next_token_logits = logits[:, -1, :]
                if repetition_penalty != 1.0:
                    for token_id in set(input_ids[0].tolist()):
                        next_token_logits[0, token_id] /= repetition_penalty
                next_token = torch.argmax(next_token_logits, dim=-1, keepdim=True)
            else:
                next_token_logits = logits[:, -1, :] / (temperature if temperature > 0 else 1.0)
                if repetition_penalty != 1.0:
                    for token_id in set(input_ids[0].tolist()):
                        next_token_logits[0, token_id] /= repetition_penalty
                filtered_logits = top_k_top_p_filtering(next_token_logits, top_k=top_k, top_p=top_p)
                probs = F.softmax(filtered_logits, dim=-1)
                next_token = torch.multinomial(probs, num_samples=1)
            
            input_ids = torch.cat([input_ids, next_token], dim=-1)
            
            yield self.tokenizer.decode([next_token.item()])

            if next_token.item() == 6: # EOS_ID
                break
