import os
import sys
import argparse
import subprocess
import time
import signal
from typing import Optional, List, Tuple

def run_afl(
    seeds_dir: str,
    target_binary: str,
    output_dir: str,
    timeout_mins: int = 10,
    afl_binary: str = "afl-fuzz",
    dictionary_path: Optional[str] = None,
    memory_limit: str = "none"
):
    """
    Run AFL++ fuzzing on the target binary using generated seeds
    
    Args:
        seeds_dir: Directory containing seed files
        target_binary: Path to the target binary to fuzz
        output_dir: Directory to save AFL++ output
        timeout_mins: Timeout in minutes
        afl_binary: Path to AFL++ binary
        dictionary_path: Path to AFL dictionary file (optional)
        memory_limit: Memory limit for AFL (none, 50M, etc.)
        
    Returns:
        Tuple of (output_dir, success_flag)
    """
    # Make sure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Base AFL command
    command = [
        afl_binary,
        "-i", seeds_dir,
        "-o", output_dir,
        "-m", memory_limit,
        "-t", "1000"  # 1 second timeout per execution
    ]
    
    # Add dictionary if provided
    if dictionary_path:
        command.extend(["-x", dictionary_path])
    
    # Add timeout
    if timeout_mins > 0:
        command.extend(["-V", str(timeout_mins * 60)])  # Convert to seconds
    
    # Add target
    command.extend(["--", target_binary, "@@"])  # @@ will be replaced with input file
    
    print(f"Running AFL++: {' '.join(command)}")
    print(f"Fuzzing for {timeout_mins} minutes...")
    
    try:
        # Start AFL process
        start_time = time.time()
        process = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Create a new process group
        )
        
        # Wait for timeout
        if timeout_mins > 0:
            try:
                process.wait(timeout=timeout_mins * 60)
            except subprocess.TimeoutExpired:
                print(f"AFL++ reached the timeout of {timeout_mins} minutes, terminating...")
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                process.wait()
        else:
            # If no timeout, just wait for process to complete
            process.wait()
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print(f"AFL++ fuzzing completed in {elapsed_time / 60:.2f} minutes")
        
        # Check for crashes/hangs
        crashes_dir = os.path.join(output_dir, "crashes")
        hangs_dir = os.path.join(output_dir, "hangs")
        queue_dir = os.path.join(output_dir, "queue")
        
        num_crashes = len(os.listdir(crashes_dir)) if os.path.exists(crashes_dir) else 0
        num_hangs = len(os.listdir(hangs_dir)) if os.path.exists(hangs_dir) else 0
        num_queue = len(os.listdir(queue_dir)) if os.path.exists(queue_dir) else 0
        
        print(f"Results:")
        print(f"  - Queue entries: {num_queue}")
        print(f"  - Crashes found: {num_crashes}")
        print(f"  - Hangs detected: {num_hangs}")
        
        return output_dir, True
        
    except Exception as e:
        print(f"Error running AFL++: {e}")
        return output_dir, False

def run_afl_tmin(
    afl_output_dir: str,
    target_binary: str,
    output_dir: Optional[str] = None,
    top_k: int = 5,
    afl_tmin_binary: str = "afl-tmin"
):
    """
    Run AFL-tmin to minimize the top k test cases
    
    Args:
        afl_output_dir: Directory containing AFL++ output
        target_binary: Path to the target binary
        output_dir: Directory to save minimized files (optional)
        top_k: Number of top test cases to minimize
        afl_tmin_binary: Path to AFL-tmin binary
        
    Returns:
        List of paths to minimized test cases
    """
    # Create output directory for minimized files
    if not output_dir:
        output_dir = os.path.join(afl_output_dir, "minimized")
    os.makedirs(output_dir, exist_ok=True)
    
    # Check for crashes directory
    crashes_dir = os.path.join(afl_output_dir, "crashes")
    hangs_dir = os.path.join(afl_output_dir, "hangs")
    queue_dir = os.path.join(afl_output_dir, "queue")
    
    # Priority: crashes first, then hangs, then queue
    source_dirs = []
    if os.path.exists(crashes_dir) and os.listdir(crashes_dir):
        source_dirs.append(crashes_dir)
    if os.path.exists(hangs_dir) and os.listdir(hangs_dir):
        source_dirs.append(hangs_dir)
    if os.path.exists(queue_dir) and os.listdir(queue_dir):
        source_dirs.append(queue_dir)
    
    if not source_dirs:
        print("No test cases found in AFL output directories")
        return []
    
    # Collect all files
    all_files = []
    for source_dir in source_dirs:
        dir_type = os.path.basename(source_dir)
        for filename in os.listdir(source_dir):
            filepath = os.path.join(source_dir, filename)
            if os.path.isfile(filepath):
                # Get file stats for sorting
                stats = os.stat(filepath)
                all_files.append({
                    'path': filepath,
                    'type': dir_type,
                    'size': stats.st_size,
                    'mtime': stats.st_mtime,
                    'filename': filename
                })
    
    # Sort files: first by type (crashes first), then by modification time (newer first)
    all_files.sort(key=lambda x: (
        0 if x['type'] == 'crashes' else 1 if x['type'] == 'hangs' else 2,
        -x['mtime']
    ))
    
    # Take top k
    selected_files = all_files[:top_k]
    
    minimized_files = []
    
    for i, file_info in enumerate(selected_files):
        input_file = file_info['path']
        file_type = file_info['type']
        orig_filename = file_info['filename']
        
        print(f"Minimizing test case {i+1}/{len(selected_files)}: {input_file}")
        
        # Output file
        output_file = os.path.join(
            output_dir, 
            f"min_{file_type}_{i+1:03d}_{orig_filename}"
        )
        
        # AFL-tmin command
        command = [
            afl_tmin_binary,
            "-i", input_file,
            "-o", output_file,
            "--", target_binary, "@@"
        ]
        
        print(f"Running: {' '.join(command)}")
        
        try:
            subprocess.run(command, check=True)
            minimized_files.append(output_file)
            print(f"Minimized test case saved to {output_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error minimizing test case: {e}")
    
    print(f"Minimized {len(minimized_files)} test cases out of {len(selected_files)}")
    return minimized_files

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AFL++ fuzzing on generated inputs")
    parser.add_argument("--seeds-dir", type=str, required=True, help="Directory containing seed files")
    parser.add_argument("--target-binary", type=str, required=True, help="Path to the target binary to fuzz")
    parser.add_argument("--output-dir", type=str, default="afl_output", help="Directory to save AFL++ output")
    parser.add_argument("--timeout", type=int, default=10, help="Timeout in minutes")
    parser.add_argument("--afl-binary", type=str, default="afl-fuzz", help="Path to AFL++ binary")
    parser.add_argument("--dict", type=str, help="Path to AFL dictionary file")
    parser.add_argument("--memory-limit", type=str, default="none", help="Memory limit for AFL")
    
    parser.add_argument("--tmin", action="store_true", help="Run AFL-tmin after fuzzing")
    parser.add_argument("--top-k", type=int, default=5, help="Number of top test cases to minimize")
    parser.add_argument("--tmin-output-dir", type=str, help="Directory to save minimized files")
    
    args = parser.parse_args()
    
    # Run AFL++
    afl_output_dir, success = run_afl(
        args.seeds_dir,
        args.target_binary,
        args.output_dir,
        args.timeout,
        args.afl_binary,
        args.dict,
        args.memory_limit
    )
    
    # Run AFL-tmin if requested and fuzzing was successful
    if args.tmin and success:
        minimized_files = run_afl_tmin(
            afl_output_dir,
            args.target_binary,
            args.tmin_output_dir,
            args.top_k
        )