import os
import json
from typing import Dict, Any, Optional

class GrammarLoader:
    """Handles loading and formatting of grammar files for constrained decoding"""
    
    def __init__(self, grammar_dir: str = None):
        """
        Initialize the grammar loader
        
        Args:
            grammar_dir: Directory containing grammar files (optional)
        """
        self.grammar_dir = grammar_dir
        
    def load_grammar(self, grammar_path: str) -> str:
        """
        Load grammar content from file
        
        Args:
            grammar_path: Path to grammar file
            
        Returns:
            Grammar content as string
        """
        with open(grammar_path, 'r') as f:
            return f.read()
    
    def format_for_interpreter(self, grammar_str: str) -> str:
        """
        Format grammar string for LLInterpreter
        
        Args:
            grammar_str: Grammar content
            
        Returns:
            Formatted grammar JSON string
        """
        return json.dumps({"grammars": [{"lark_grammar": grammar_str}]})
    
    def get_grammar_path(self, grammar_name: str) -> str:
        """
        Get full path to grammar file
        
        Args:
            grammar_name: Name of grammar file (e.g., 'xml.lark')
            
        Returns:
            Full path to grammar file
        """
        if self.grammar_dir is None:
            raise ValueError("Grammar directory not specified")
        
        return os.path.join(self.grammar_dir, grammar_name)