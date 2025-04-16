import os
import sys
import argparse
import json
from typing import Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.config import CDGramFuzzConfig
from src.decoder.constrained_decoder import ConstrainedDecoder
from src.decoder.grammar_loader import GrammarLoader

def load_prompt(prompt_path: str) -> str:
    """Load prompt from file"""
    with open(prompt_path, 'r') as f:
        return f.read()

def main(config_path: Optional[str] = None):
    """
    Run the CDGramFuzz framework with the given configuration
    
    Args:
        config_path: Path to configuration file (optional)
    """
    # Define default config for XML if not provided
    if config_path:
        config = CDGramFuzzConfig.from_json(config_path)
    else:
        # Default XML example configuration
        config = CDGramFuzzConfig(
            model_name="microsoft/Phi-3.5-mini-instruct",
            grammar_path="grammars/xml.lark",
            prompt_path="prompts/xml_prompt.txt",
            max_length=2000,
            output_dir="output"
        )
    
    # Load prompt if specified by path
    if config.prompt_path and not config.prompt:
        config.prompt = load_prompt(config.prompt_path)
    
    # Initialize decoder
    grammar_loader = GrammarLoader()
    decoder = ConstrainedDecoder(config, grammar_loader)
    
    # Generate output
    print("Generating output...")
    output = decoder.generate(config.prompt)
    
    # Save output
    if config.output_dir:
        os.makedirs(config.output_dir, exist_ok=True)
        output_file = os.path.join(config.output_dir, "generated_output.txt")
        with open(output_file, 'w') as f:
            f.write(output)
        print(f"Output saved to {output_file}")
    
    # Print output
    print("\nGenerated Output:")
    print("=" * 80)
    print(output)
    print("=" * 80)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the CDGramFuzz framework")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    args = parser.parse_args()
    
    main(args.config)