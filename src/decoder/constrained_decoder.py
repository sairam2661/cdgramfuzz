import torch
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
import llguidance
import huggingface_hub
from transformers import AutoModelForCausalLM

from ..utils.config import CDGramFuzzConfig
from .grammar_loader import GrammarLoader

class ConstrainedDecoder:
    """Core implementation of grammar-constrained decoding"""
    
    def __init__(self, config: CDGramFuzzConfig, grammar_loader: Optional[GrammarLoader] = None):
        """
        Initialize the constrained decoder
        
        Args:
            config: Configuration for the decoder
            grammar_loader: Grammar loader instance (optional)
        """
        self.config = config
        self.grammar_loader = grammar_loader or GrammarLoader()
        
        # Setup device
        self.device = torch.device(config.device if torch.cuda.is_available() and config.device == "cuda" else "cpu")
        
        # Load the tokenizer
        self._initialize_tokenizer()
        
        # Load the model
        self._initialize_model()
        
        # Load the grammar
        self._initialize_interpreter()
        
    def _initialize_tokenizer(self):
        """Initialize the tokenizer"""
        tok_name = huggingface_hub.hf_hub_download(self.config.model_name, "tokenizer.json")
        with open(tok_name, "r") as f:
            text = f.read()
        
        # Create LLGuidance tokenizer
        self.tokenizer = llguidance.LLTokenizer(text, n_vocab=32064)  # May need to make n_vocab configurable
    
    def _initialize_model(self):
        """Initialize the language model"""
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.model_name,
            torch_dtype=torch.float16,
            device_map="auto"
        )
    
    def _initialize_interpreter(self):
        """Initialize the grammar interpreter"""
        grammar_str = self.grammar_loader.load_grammar(self.config.grammar_path)
        formatted_grammar = self.grammar_loader.format_for_interpreter(grammar_str)
        
        self.interpreter = llguidance.LLInterpreter(
            self.tokenizer,
            formatted_grammar,
            enable_ff_tokens=self.config.enable_ff_tokens,
            enable_backtrack=self.config.enable_backtrack,
            log_level=self.config.log_level,
        )
    
    def generate(self, prompt: str, max_length: Optional[int] = None) -> str:
        """
        Generate text constrained by the grammar
        
        Args:
            prompt: Input prompt
            max_length: Maximum length of generated text
            
        Returns:
            Generated text
        """
        max_length = max_length or self.config.max_length
        
        # Create a deep copy of the interpreter for this generation
        ll_interpreter = self.interpreter.deep_copy()
        
        # Tokenize the prompt
        input_ids = self.tokenizer.tokenize_str(prompt)
        processed_prompt = ll_interpreter.process_prompt(input_ids)
        generated_tokens = processed_prompt.copy()
        current_length = len(generated_tokens)
        
        # Generate tokens
        while current_length < max_length:
            mask_bytes, json_str = ll_interpreter.compute_mask()
            
            if mask_bytes is None:
                break
            
            mask = np.frombuffer(mask_bytes, dtype=np.uint8)
            mask = mask.astype(bool)
                
            # Get model's next token predictions
            inputs = torch.tensor([generated_tokens], device=self.device)
            with torch.no_grad():
                logits = self.model(inputs).logits[:, -1, :]
    
            logits[0][~mask] = float('-inf')
            
            probs = torch.softmax(logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1).item()
            
            num_to_remove, tokens_to_add = ll_interpreter.commit_token(next_token)
            
            if num_to_remove > 0:
                generated_tokens = generated_tokens[:-num_to_remove]
            generated_tokens.extend(tokens_to_add)
            current_length = len(generated_tokens)
    
            # Check if generation should stop
            if ll_interpreter.has_pending_stop():
                break
                
        # Extract generated text (remove the prompt)
        generated_text = self.tokenizer.decode_str(generated_tokens[(len(input_ids)):])
        return generated_text