import os
import sys
import argparse
import json
import time
from typing import Optional, List
import uuid
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.config import CDGramFuzzConfig
from src.decoder.constrained_decoder import ConstrainedDecoder
from src.decoder.grammar_loader import GrammarLoader

def generate_seeds(config_path: str, count: int = 10, output_dir: Optional[str] = None):
    """
    Generate multiple outputs using CDGramFuzz
    
    Args:
        config_path: Path to configuration file
        count: Number of outputs to generate
        output_dir: Directory to save outputs (defaults to config's output_dir)
    """
    # Load configuration
    config = CDGramFuzzConfig.from_json(config_path)
    
    # Override output directory if specified
    if output_dir:
        config.output_dir = output_dir
        
    # Make sure output directory exists
    if not config.output_dir:
        config.output_dir = "output"
    
    seeds_dir = os.path.join(config.output_dir, "seeds")
    os.makedirs(seeds_dir, exist_ok=True)
    
    # Initialize decoder
    grammar_loader = GrammarLoader()
    decoder = ConstrainedDecoder(config, grammar_loader)
    
    # Generate outputs
    print(f"Generating {count} outputs...")
    start_time = time.time()
    
    file_paths = []
    for i in range(count):
        print(f"Generating output {i+1}/{count}...")
        
        # Generate text with constrained decoding
        output = decoder.generate(config.prompt)
        
        # Create a unique filename with the specified file format
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"seed_{timestamp}_{i+1:03d}.{config.file_format}"
        filepath = os.path.join(seeds_dir, filename)
        
        # Save output
        with open(filepath, 'w') as f:
            f.write(output)
            
        file_paths.append(filepath)
        print(f"Saved to {filepath}")
    
    end_time = time.time()
    print(f"Generation completed in {end_time - start_time:.2f} seconds")
    print(f"Generated {count} outputs in {seeds_dir}")
    
    return seeds_dir, file_paths

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate multiple outputs using CDGramFuzz")
    parser.add_argument("--config", type=str, required=True, help="Path to configuration file")
    parser.add_argument("--count", type=int, default=10, help="Number of outputs to generate")
    parser.add_argument("--output-dir", type=str, help="Directory to save outputs")
    args = parser.parse_args()
    
    generate_seeds(args.config, args.count, args.output_dir)