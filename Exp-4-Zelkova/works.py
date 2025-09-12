from z3 import *
import sys
import subprocess
import os
import time
import argparse  # Added for better command-line argument handling
import re
import json
from tqdm import tqdm  # For progress bar

def generate_smt_file(policy_path, smt_output_path):
    """Generate SMT file from policy using quacky"""
    quacky_path = "/mnt/d/Research/VeriSynth/Verifying-LLMAccessControl/quacky/src/quacky.py"
    working_directory = "/mnt/d/Research/VeriSynth/Verifying-LLMAccessControl/quacky/src/"
    
    print(f"Generating SMT file from policy {policy_path}...")
    
    # Command to generate SMT file using quacky
    smt_gen_command = [
        "python3", quacky_path,
        "--smt-lib",  # Use this flag for Z3-compatible SMT generation
        "-p1", policy_path,
        "-b", "100"
    ]
    
    try:
        result = subprocess.run(smt_gen_command, cwd=working_directory, 
                          capture_output=True, text=True, timeout=300)
        
        if result.stderr:
            print(f"Warning: {result.stderr}")
            
        if not os.path.exists(smt_output_path):
            print(f"Error: SMT file {smt_output_path} was not created")
            return False
        
        print(f"Successfully generated SMT file: {smt_output_path}")
        return True
    except Exception as e:
        print(f"Error generating SMT file: {str(e)}")
        return False

def solve_smt_file(smt_filename, max_models=10):
    """
    Processes an SMT formula file using Z3 solver to find satisfying models.
    
    Args:
        smt_filename: Path to the SMT-LIB format file containing the formula
        max_models: Maximum number of models to enumerate (default: 10)
        
    Returns:
        List of strings representing different values for the 'resource' variable
        that satisfy the policy constraints
    """
    # Create solver instance
    solver = Solver()
    models_list = []
    
    try:
        # Load SMT file directly from disk (no need to read it in Python)
        solver.from_file(smt_filename)
        
        # Check if the formula is satisfiable
        if solver.check() == sat:
            models_found = 0
            print("Formula is satisfiable! Enumerating models:")
            
            while models_found < max_models:
                # Get the current model
                model = solver.model()
                models_found += 1
                
                # Try to get the resource string
                try:
                    r = String('resource')
                    resource_value = str(model[r])
                    print(f"Model {models_found}: {resource_value}")
                    models_list.append(resource_value)
                    solver.add(r != model[r])
                except Exception as e:
                    print(f"Error extracting resource value: {e}")
                    break
                
                # Check again for satisfiability
                if solver.check() != sat:
                    print("No more models")
                    break
        else:
            print("Unsatisfiable!")
    except Exception as e:
        print(f"Error parsing SMT file: {e}")
        
        # Try to find problematic lines - only read the file if needed for error reporting
        error_msg = str(e)
        line_match = re.search(r'line (\d+)', error_msg)
        
        if line_match:
            line_num = int(line_match.group(1))
            print(f"Problematic line number: {line_num}")
            
            # Only read the file if we need to show the problematic lines
            try:
                with open(smt_filename, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()
                
                print(f"Problematic area near line {line_num}:")
                start = max(0, line_num - 2)
                end = min(len(lines), line_num + 2)
                for i in range(start, end):
                    if i < len(lines):
                        print(f"Line {i+1}: {lines[i].rstrip()}")
            except Exception as read_error:
                print(f"Could not read file for error reporting: {read_error}")
    
    return models_list

def process_all_policies(dataset_dir, output_dir, max_models=100, start_from=0, end_at=None):
    """
    Process all policy files in the dataset directory.
    
    Args:
        dataset_dir: Path to the directory containing policy JSON files
        output_dir: Path to the directory where results will be saved
        max_models: Maximum number of models to enumerate per policy
        start_from: Policy number to start from (inclusive)
        end_at: Policy number to end at (inclusive), or None to process all
        
    Returns:
        Dictionary mapping policy numbers to success/failure status and model counts
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all policy files
    policy_files = sorted([f for f in os.listdir(dataset_dir) if f.endswith('.json')], 
                         key=lambda x: int(x.split('.')[0]))
    
    # Filter by start and end policy numbers
    policy_files = [f for f in policy_files if int(f.split('.')[0]) >= start_from]
    if end_at is not None:
        policy_files = [f for f in policy_files if int(f.split('.')[0]) <= end_at]
    
    results = {}
    
    print(f"Processing {len(policy_files)} policies from {dataset_dir}...")
    
    # IMPORTANT: The default SMT file path that quacky uses
    default_smt_path = "/mnt/d/Research/VeriSynth/Verifying-LLMAccessControl/quacky/src/output_1.smt2"
    
    # Process each policy file
    for policy_file in tqdm(policy_files, desc="Processing policies"):
        policy_number = policy_file.split('.')[0]
        policy_path = os.path.join(dataset_dir, policy_file)
        
        print(f"\n\n{'='*80}\nProcessing policy {policy_number}: {policy_path}\n{'='*80}")
        
        # Define output paths for this policy
        models_output_path = os.path.join(output_dir, f"policy_{policy_number}_models.txt")
        
        policy_result = {
            "policy_number": policy_number,
            "policy_path": policy_path,
            "models_path": models_output_path,
            "success": False,
            "models_count": 0,
            "error": None
        }
        
        try:
            # Generate SMT file - ALWAYS use the default SMT path
            if not generate_smt_file(policy_path, default_smt_path):
                policy_result["error"] = "Failed to generate SMT file"
                results[policy_number] = policy_result
                continue
            
            # Wait a moment for file to be fully written
            time.sleep(1)
            
            # Solve the SMT file - use the default SMT path
            print(f"\nEnumerating models for policy {policy_number}:")
            models = solve_smt_file(default_smt_path, max_models=max_models)
            
            if models:
                # Save models to file
                with open(models_output_path, 'w') as f:
                    for model in models:
                        f.write(f"{model}\n")
                
                policy_result["success"] = True
                policy_result["models_count"] = len(models)
                print(f"Successfully generated {len(models)} models for policy {policy_number}")
            else:
                policy_result["error"] = "No models found"
                print(f"No models found for policy {policy_number}")
        
        except Exception as e:
            policy_result["error"] = str(e)
            print(f"Error processing policy {policy_number}: {str(e)}")
        
        results[policy_number] = policy_result
        
        # Save results after each policy (in case of interruption)
        with open(os.path.join(output_dir, "processing_results.json"), 'w') as f:
            json.dump(results, f, indent=2)
    
    print(f"\nProcessing complete. Results saved to {os.path.join(output_dir, 'processing_results.json')}")
    
    # Print summary
    success_count = sum(1 for r in results.values() if r["success"])
    print(f"\nSummary: Successfully processed {success_count} out of {len(results)} policies")
    
    return results

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Generate and solve SMT formulas from policies')
    parser.add_argument('policy_path', nargs='?', 
                        default="/mnt/d/Research/VeriSynth/Verifying-LLMAccessControl/Dataset/1.json",
                        help='Path to the policy JSON file')
    parser.add_argument('--use-existing-smt', action='store_true', 
                        help='Use existing SMT file without regenerating')
    parser.add_argument('--max-models', type=int, default=100,
                        help='Maximum number of models to enumerate')
    parser.add_argument('--process-all', action='store_true',
                        help='Process all policy files in the Dataset directory')
    parser.add_argument('--output-dir', type=str,
                        default="/mnt/d/Research/VeriSynth/Verifying-LLMAccessControl/Exp-4-Zelkova/results",
                        help='Directory to save results when processing all policies')
    parser.add_argument('--start-from', type=int, default=0,
                        help='Policy number to start from (inclusive)')
    parser.add_argument('--end-at', type=int, default=None,
                        help='Policy number to end at (inclusive)')
    args = parser.parse_args()
    
    if args.process_all:
        # Process all policies
        dataset_dir = "/mnt/d/Research/VeriSynth/Verifying-LLMAccessControl/Dataset"
        process_all_policies(
            dataset_dir=dataset_dir,
            output_dir=args.output_dir,
            max_models=args.max_models,
            start_from=args.start_from,
            end_at=args.end_at
        )
    else:
        # Process a single policy (original functionality)
        # SMT file path
        smt_output_path = "/mnt/d/Research/VeriSynth/Verifying-LLMAccessControl/quacky/src/output_1.smt2"
        
        # Check if we need to generate a new SMT file
        if args.use_existing_smt:
            print(f"Using existing SMT file: {smt_output_path}")
            if not os.path.exists(smt_output_path):
                print(f"ERROR: SMT file does not exist at {smt_output_path}")
                sys.exit(1)
        else:
            # Generate SMT file
            if not generate_smt_file(args.policy_path, smt_output_path):
                print("Failed to generate SMT file. Cannot proceed with model enumeration.")
                sys.exit(1)
        
        
            # Wait a moment for file to be fully written
            time.sleep(1)
        
        # Solve the SMT file
        print("\nEnumerating models from the SMT file:")
        solve_smt_file(smt_output_path, max_models=args.max_models)