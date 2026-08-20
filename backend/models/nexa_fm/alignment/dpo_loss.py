import torch
import torch.nn.functional as F
from typing import Tuple

def compute_logprobs(logits: torch.Tensor, labels: torch.Tensor, ignore_index: int = -100) -> torch.Tensor:
    """
    Computes sequence log-probabilities given model logits and target labels.
    Masked tokens (labels == ignore_index) are excluded from the sum.
    """
    # Shift logits and labels for causal next-token prediction
    shift_logits = logits[..., :-1, :].contiguous()
    shift_labels = labels[..., 1:].contiguous()

    log_probs = F.log_softmax(shift_logits, dim=-1)
    
    # Gather log-probs for actual target tokens
    # Mask out ignore_index tokens for gather
    mask = (shift_labels != ignore_index)
    safe_labels = shift_labels.clone()
    safe_labels[~mask] = 0

    per_token_logprobs = torch.gather(log_probs, dim=-1, index=safe_labels.unsqueeze(-1)).squeeze(-1)
    masked_logprobs = per_token_logprobs * mask.float()
    return masked_logprobs.sum(dim=-1)

def compute_dpo_loss(
    policy_chosen_logps: torch.Tensor,
    policy_rejected_logps: torch.Tensor,
    reference_chosen_logps: torch.Tensor,
    reference_rejected_logps: torch.Tensor,
    beta: float = 0.1
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Computes Direct Preference Optimization (DPO) loss.
    Loss = -E[log sigmoid(beta * ((log pi(y_w|x) - log ref(y_w|x)) - (log pi(y_l|x) - log ref(y_l|x))))]
    """
    pi_logratios = policy_chosen_logps - policy_rejected_logps
    ref_logratios = reference_chosen_logps - reference_rejected_logps

    logits = beta * (pi_logratios - ref_logratios)
    loss = -F.logsigmoid(logits).mean()

    chosen_rewards = beta * (policy_chosen_logps - reference_chosen_logps).detach()
    rejected_rewards = beta * (policy_rejected_logps - reference_rejected_logps).detach()

    return loss, chosen_rewards, rejected_rewards
