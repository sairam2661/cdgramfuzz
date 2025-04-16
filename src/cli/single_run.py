import os
import sys
import argparse
import time
from typing import Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.cli.generate_seeds import generate_seeds
from cdgramfuzz.src.mutation.afl_runner import run_afl, run_afl_tmin

def run_pipeline(
    config_path: str,
    target_binary: str,
    output_dir: Optional[str] = None,
    seed_count: int = 10,
    timeout_mins: int = 10,
    top_k: int = 5,
    afl_binary: str = "afl-fuzz",
    afl_tmin_binary: str = "afl-tmin"
):
    """
    Run a single run from start to finish.
    Args:
        config_path: Path to CDGramFuzz configuration
        target_binary: Path to target binary for fuzzing
        output_dir: Base output directory
        seed_count: Number of seeds to generate
        timeout_mins: AFL++ timeout in minutes
        top_k: Number of top test cases to minimize
        afl_binary: Path to AFL++ binary
        afl_tmin_binary: Path to AFL-tmin binary
    """
    if not output_dir:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_dir = f"cdgramfuzz_run_{timestamp}"
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"CDGramFuzz Pipeline starting in {output_dir}")
    pipeline_start = time.time()
    
    # Step 1: Generate seeds
    print("\n=== Step 1: Generating Seeds ===")
    seeds_dir = generate_seeds(config_path, seed_count, output_dir)
    
    # Step 2: Run AFL++
    print("\n=== Step 2: Running AFL++ ===")
    afl_output_dir = os.path.join(output_dir, "afl_output")
    afl_output_dir = run_afl(
        seeds_dir,
        target_binary,
        afl_output_dir,
        timeout_mins,
        afl_binary
    )
    
    # Step 3: Run AFL-tmin
    print("\n=== Step 3: Minimizing Test Cases ===")
    minimized_files = run_afl_tmin(
        afl_output_dir,
        target_binary,
        top_k,
        afl_tmin_binary
    )
    
    pipeline_end = time.time()
    print(f"\nCDGramFuzz pipeline completed in {(pipeline_end - pipeline_start) / 60:.2f} minutes")
    print(f"Output directory: {output_dir}")
    print(f"Generated {seed_count} seeds")
    print(f"Minimized {len(minimized_files)} test cases")
    
    # Print paths to minimized files
    if minimized_files:
        print("\nMinimized test cases:")
        for i, file_path in enumerate(minimized_files):
            print(f"  {i+1}. {file_path}")
    
    return output_dir, seeds_dir, afl_output_dir, minimized_files

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run full CDGramFuzz pipeline")
    parser.add_argument("--config", type=str, required=True, help="Path to CDGramFuzz configuration")
    parser.add_argument("--target-binary", type=str, required=True, help="Path to target binary for fuzzing")
    parser.add_argument("--output-dir", type=str, help="Base output directory")
    parser.add_argument("--seed-count", type=int, default=10, help="Number of seeds to generate")
    parser.add_argument("--timeout", type=int, default=10, help="AFL++ timeout in minutes")
    parser.add_argument("--top-k", type=int, default=5, help="Number of top test cases to minimize")
    parser.add_argument("--afl-binary", type=str, default="afl-fuzz", help="Path to AFL++ binary")
    parser.add_argument("--afl-tmin-binary", type=str, default="afl-tmin", help="Path to AFL-tmin binary")
    
    args = parser.parse_args()
    
    run_pipeline(
        args.config,
        args.target_binary,
        args.output_dir,
        args.seed_count,
        args.timeout,
        args.top_k,
        args.afl_binary,
        args.afl_tmin_binary
    )