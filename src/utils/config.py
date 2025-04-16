# src/utils/config.py

import os
import json
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List

@dataclass
class CDGramFuzzConfig:
    """Configuration for CDGramFuzz framework"""
    model_name: str
    grammar_path: str
    prompt: str
    prompt_path: Optional[str] = None
    max_length: int = 1000
    device: str = "cuda"
    log_level: int = 1
    enable_backtrack: bool = False
    enable_ff_tokens: bool = False
    output_dir: Optional[str] = None
    file_format: Optional[str] = None
    
    @classmethod
    def from_json(cls, json_path: str) -> "CDGramFuzzConfig":
        """Load configuration from JSON file"""
        with open(json_path, 'r') as f:
            config_dict = json.load(f)
            
        # Handle prompt_path if present
        if 'prompt_path' in config_dict:
            prompt_path = config_dict.pop('prompt_path')
            if os.path.exists(prompt_path):
                with open(prompt_path, 'r') as f:
                    config_dict['prompt'] = f.read()
        
        return cls(**config_dict)
    
    def to_json(self, json_path: str) -> None:
        """Save configuration to JSON file"""
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, 'w') as f:
            json.dump(asdict(self), f, indent=2)