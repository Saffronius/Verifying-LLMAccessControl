from z3 import *
import sys
import subprocess
import os
import time
import argparse  # Added for better command-line argument handling
import re
import json
from tqdm import tqdm  # For progress bar
import anthropic  # Changed from openai to anthropic

# Define paths (same as in Exp-4-Zelkova.py)
quacky_path = "/mnt/d/Research/VeriSynth/Verifying-LLMAccessControl/quacky/src/quacky.py"
working_directory = "/mnt/d/Research/VeriSynth/Verifying-LLMAccessControl/quacky/src/"



# Model name (changed from GPT to Claude)
claude_model_name = "claude-4-sonnet-20250514"

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
                    value = model.eval(r, model_completion=True)
                    print(value)
                    models_list.append(str(value))
                    solver.add(r != value)
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

# New functions for regex generation and evaluation

def generate_regex(strings, output_path):
    """
    Generate a regex from a list of strings using Claude 3.7 Sonnet with extended thinking.
    
    Args:
        strings: List of strings or newline-separated string of examples
        output_path: Path to save the generated regex
        
    Returns:
        The generated regex as a string, or None if generation failed
    """
    # Convert list to string if needed
    if isinstance(strings, list):
        strings_text = "\n".join(strings)
    else:
        strings_text = strings
    
    system_prompt = """
    When asked to give a regex, provide ONLY the regex pattern itself. Do not include any explanations, 
    markdown formatting, or additional text. The response should be just the regex pattern, nothing else. 
    This is a highly critical application and it is imperative to get this right. Just give me the regex.
    """
    
    prompt = f"""Give me a single regex that accepts each string in the following set of strings.
    Make sure that you carefully go through each string before forming the regex.
    It should be close to optimal and not super permissive:

    {strings_text}

    Response:"""

    try:
        print("Generating regex from models using Claude 3.7 Sonnet with extended thinking...")
        # Updated to use Anthropic's API format with extended thinking
        response = anthropic_client.messages.create(
            model=claude_model_name,
            max_tokens=20000,
            temperature=1,  # Must be set to 1 when using extended thinking
            thinking={
                "type": "enabled",
                "budget_tokens": 16000  # Allocate 16K tokens for extended thinking
            },
            messages=[
                {"role": "user", "content": system_prompt + "\n\n" + prompt}
            ]
        )
        
        # Check if there are thinking blocks in the response
        thinking_content = None
        for content_block in response.content:
            if content_block.type == "thinking":
                thinking_content = content_block.thinking
                print("Extended thinking was used to generate the regex pattern.")
                # Optionally save the thinking content to a separate file
                thinking_path = output_path + ".thinking.txt"
                with open(thinking_path, "w") as thinking_file:
                    thinking_file.write(thinking_content)
                print(f"Thinking process saved to {thinking_path}")
            elif content_block.type == "redacted_thinking":
                print("Some of Claude's internal reasoning was encrypted for safety reasons.")
        
        # Extract the final regex from the text content block
        regex = None
        for content_block in response.content:
            if content_block.type == "text":
                regex = content_block.text.strip()
                break
        
        if regex:
            # Save regex to file
            with open(output_path, "w") as output_file:
                output_file.write(regex)
            
            print(f"Regex generated and written to {output_path}")
            return regex
        else:
            print("No text content found in the response")
            return None
    except Exception as e:
        print(f"Error generating regex: {str(e)}")
        return None

def run_final_analysis(policy_path, regex_path, timeout=300):
    """
    Evaluates the quality of a generated regex against the original policy using quacky.
    
    Args:
        policy_path: Path to the original policy file
        regex_path: Path to the file containing the generated regex
        timeout: Maximum seconds to allow for the analysis (default: 300)
        
    Returns:
        The output from quacky analysis as a string, or "TIMEOUT" if the operation timed out
    """
    command = [
        "python3", quacky_path,
        "-p1", policy_path,
        "-b", "100",
        "-cr", regex_path
    ]
    
    try:
        print(f"Running quacky analysis to evaluate regex against policy...")
        # Use subprocess.run's built-in timeout parameter
        result = subprocess.run(command, cwd=working_directory, capture_output=True, 
                                text=True, timeout=timeout)
        
        print("Quacky Final Analysis Output:")
        print(result.stdout)
        if result.stderr:
            print(f"Errors: {result.stderr}")
        return result.stdout
    except subprocess.TimeoutExpired:
        print(f"Final analysis timed out after {timeout} seconds.")
        return "TIMEOUT"

def process_policy_with_regex(policy_path, output_dir, max_models=500):
    """
    Process a single policy through the full pipeline:
    1. Generate SMT file
    2. Enumerate models
    3. Generate regex from models
    4. Evaluate regex against policy
    
    Args:
        policy_path: Path to the policy file
        output_dir: Directory to save outputs
        max_models: Maximum number of models to enumerate (default: 500)
        
    Returns:
        Dictionary with results
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get policy number from path
    policy_number = os.path.basename(policy_path).split('.')[0]
    
    # Define output paths
    default_smt_path = "/mnt/d/Research/VeriSynth/Verifying-LLMAccessControl/quacky/src/output_1.smt2"
    models_output_path = os.path.join(output_dir, f"policy_{policy_number}_models.txt")
    regex_output_path = os.path.join(output_dir, f"policy_{policy_number}_regex.txt")
    
    results = {
        "policy_number": policy_number,
        "policy_path": policy_path,
        "models_path": models_output_path,
        "regex_path": regex_output_path,
        "success": False,
        "models_count": 0,
        "regex": None,
        "analysis": None,
        "error": None
    }
    
    try:
        print(f"\n\n{'='*80}\nProcessing policy {policy_number}: {policy_path}\n{'='*80}")
        
        # Step 1: Generate SMT file
        if not generate_smt_file(policy_path, default_smt_path):
            results["error"] = "Failed to generate SMT file"
            return results
        
        # Wait a moment for file to be fully written
        time.sleep(1)
        
        # Step 2: Enumerate models
        print(f"\nEnumerating models for policy {policy_number} (max: {max_models}):")
        models = solve_smt_file(default_smt_path, max_models=max_models)
        
        if not models:
            results["error"] = "No models found"
            return results
        
        # Save models to file
        with open(models_output_path, 'w') as f:
            for model in models:
                f.write(f"{model}\n")
        
        results["models_count"] = len(models)
        print(f"Successfully generated {len(models)} models for policy {policy_number}")
        
        # Step 3: Generate regex from models
        regex = generate_regex(models, regex_output_path)
        if not regex:
            results["error"] = "Failed to generate regex"
            return results
        
        results["regex"] = regex
        
        # Step 4: Evaluate regex against policy
        analysis = run_final_analysis(policy_path, regex_output_path)
        results["analysis"] = analysis
        
        # Try to extract precision metrics from analysis
        try:
            precision_match = re.search(r'Precision: ([0-9.]+)', analysis)
            precision = float(precision_match.group(1)) if precision_match else None
            results["precision"] = precision
            
            if precision is not None:
                print(f"Precision: {precision}")
        except Exception as e:
            print(f"Could not extract precision metrics: {str(e)}")
        
        results["success"] = True
        
    except Exception as e:
        results["error"] = str(e)
        print(f"Error processing policy {policy_number}: {str(e)}")
    
    # Save results
    with open(os.path.join(output_dir, f"policy_{policy_number}_results.json"), 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

def process_all_policies_with_regex(dataset_dir, output_dir, max_models=500, start_from=0, end_at=None):
    """
    Process all policy files in the dataset directory through the full pipeline.
    
    Args:
        dataset_dir: Path to the directory containing policy JSON files
        output_dir: Path to the directory where results will be saved
        max_models: Maximum number of models to enumerate per policy (default: 500)
        start_from: Policy number to start from (inclusive)
        end_at: Policy number to end at (inclusive), or None to process all
        
    Returns:
        Dictionary mapping policy numbers to results
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
    
    all_results = {}
    
    print(f"Processing {len(policy_files)} policies from {dataset_dir} with regex generation...")
    
    # Process each policy file
    for policy_file in tqdm(policy_files, desc="Processing policies"):
        policy_path = os.path.join(dataset_dir, policy_file)
        policy_number = policy_file.split('.')[0]
        
        # Process the policy
        results = process_policy_with_regex(policy_path, output_dir, max_models)
        all_results[policy_number] = results
        
        # Save all results after each policy (in case of interruption)
        with open(os.path.join(output_dir, "all_results.json"), 'w') as f:
            json.dump(all_results, f, indent=2)
    
    print(f"\nProcessing complete. Results saved to {os.path.join(output_dir, 'all_results.json')}")
    
    # Print summary
    success_count = sum(1 for r in all_results.values() if r["success"])
    print(f"\nSummary: Successfully processed {success_count} out of {len(all_results)} policies")
    
    return all_results

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
    parser.add_argument('--generate-regex', action='store_true',
                        help='Generate regex from models and evaluate it')
    parser.add_argument('--process-all-with-regex', action='store_true',
                        help='Process all policies with regex generation and evaluation')
    args = parser.parse_args()
    
    if args.process_all_with_regex:
        # Process all policies with regex generation
        dataset_dir = "/mnt/d/Research/VeriSynth/Verifying-LLMAccessControl/Dataset"
        process_all_policies_with_regex(
            dataset_dir=dataset_dir,
            output_dir=args.output_dir,
            max_models=args.max_models,
            start_from=args.start_from,
            end_at=args.end_at
        )
    elif args.generate_regex:
        # Process a single policy with regex generation
        process_policy_with_regex(
            policy_path=args.policy_path,
            output_dir=args.output_dir,
            max_models=args.max_models
        )
    elif args.process_all:
        # Process all policies (original functionality)
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