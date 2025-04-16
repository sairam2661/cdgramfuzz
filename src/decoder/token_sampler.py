# src/decoder/token_sampler.py

import torch
import numpy as np
from typing import Optional, List, Callable, Dict, Any

class TokenSampler:
    """Implements different sampling strategies for token selection"""
    
    @staticmethod
    def greedy_sampling(logits: torch.Tensor, mask: torch.Tensor) -> int:
        """
        Greedy sampling - select the token with highest probability
        
        Args:
            logits: Token prediction logits from model
            mask: Boolean mask of valid tokens according to grammar
            
        Returns:
            Selected token ID
        """
        # Apply mask
        masked_logits = logits.clone()
        masked_logits[0][~mask] = float('-inf')
        
        # Select highest probability token
        return torch.argmax(masked_logits, dim=-1).item()
    
    @staticmethod
    def temperature_sampling(logits: torch.Tensor, mask: torch.Tensor, 
                            temperature: float = 1.0) -> int:
        """
        Temperature sampling - adjust probability distribution before sampling
        
        Args:
            logits: Token prediction logits from model
            mask: Boolean mask of valid tokens according to grammar
            temperature: Temperature for sampling (higher = more random)
            
        Returns:
            Selected token ID
        """
        # Apply mask
        masked_logits = logits.clone()
        masked_logits[0][~mask] = float('-inf')
        
        # Apply temperature
        if temperature != 1.0:
            masked_logits = masked_logits / temperature
            
        # Convert to probabilities and sample
        probs = torch.softmax(masked_logits, dim=-1)
        return torch.multinomial(probs, num_samples=1).item()
    
    @staticmethod
    def top_k_sampling(logits: torch.Tensor, mask: torch.Tensor, 
                      k: int = 50, temperature: float = 1.0) -> int:
        """
        Top-k sampling - limit to k most likely tokens
        
        Args:
            logits: Token prediction logits from model
            mask: Boolean mask of valid tokens according to grammar
            k: Number of top tokens to consider
            temperature: Temperature for sampling
            
        Returns:
            Selected token ID
        """
        # Apply mask
        masked_logits = logits.clone()
        masked_logits[0][~mask] = float('-inf')
        
        # Apply temperature
        if temperature != 1.0:
            masked_logits = masked_logits / temperature
            
        # Keep only top-k tokens
        top_k_logits, top_k_indices = torch.topk(masked_logits[0], k=min(k, sum(mask).item()))
        
        # Set probabilities for non-top-k tokens to 0
        masked_probs = torch.zeros_like(masked_logits[0])
        masked_probs.scatter_(0, top_k_indices, torch.softmax(top_k_logits, dim=-1))
        
        # Sample token
        return torch.multinomial(masked_probs.unsqueeze(0), num_samples=1).item()