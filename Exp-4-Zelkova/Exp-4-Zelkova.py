import subprocess
import pandas as pd
import os
import anthropic
import json
import logging
from tqdm import tqdm
import time
from functools import wraps
import signal
import re
from z3 import * # Import Z3 library
import argparse  # Add this import at the top with the other imports
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("regex_comparison_experiment.log"), logging.StreamHandler()])

# API Setup



# Model name
claude_model_name = "claude-4-sonnet-20250514"

# Define paths
policy_folder = "/mnt/d/Research/VeriSynth/Verifying-LLMAccessControl/Dataset"
quacky_path = "/mnt/d/Research/VeriSynth/Verifying-LLMAccessControl/quacky/src/quacky.py"
working_directory = "/mnt/d/Research/VeriSynth/Verifying-LLMAccessControl/quacky/src/"

# Updated result paths to Exp-4-Zelkova directory
results_path = "/mnt/d/Research/VeriSynth/Verifying-LLMAccessControl/Exp-4-Zelkova/regex_comparison_results.csv"
progress_file_path = "/mnt/d/Research/VeriSynth/Verifying-LLMAccessControl/Exp-4-Zelkova/regex_comparison_progress.json"
z3_models_path = "/mnt/d/Research/VeriSynth/Verifying-LLMAccessControl/Exp-4-Zelkova/z3_models.txt"

# Use this path for the SMT file produced by quacky
smt_output_path = "/mnt/d/Research/VeriSynth/Verifying-LLMAccessControl/quacky/src/output_1.smt2"

# Paths for both approaches
r1_strings_path = "/mnt/d/Research/VeriSynth/Verifying-LLMAccessControl/quacky/src/P1_not_P2.models"
r1_regex_path = "/mnt/d/Research/VeriSynth/Verifying-LLMAccessControl/Exp-4-Zelkova/r1_regex.txt"
r2_regex_path = "/mnt/d/Research/VeriSynth/Verifying-LLMAccessControl/Exp-4-Zelkova/r2_regex.txt"

def solve_smt_file(smt_filename, max_models=1000):
    """
    Processes an SMT formula file using Z3 solver to find satisfying models.
    
    This function is an exact copy from z3_model_enum.py to ensure identical behavior.
    
    Args:
        smt_filename: Path to the SMT-LIB format file containing the formula
        max_models: Maximum number of models to enumerate (default: 1000)
        
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
            logging.info("Formula is satisfiable! Enumerating models:")
            
            while models_found < max_models:
                # Get the current model
                model = solver.model()
                models_found += 1
                
                # Try to get the resource string
                try:
                    r = String('resource')
                    resource_value = str(model[r])
                    logging.info(f"Model {models_found}: {resource_value}")
                    models_list.append(resource_value)
                    solver.add(r != model[r])
                except Exception as e:
                    logging.error(f"Error extracting resource value: {e}")
                    break
                
                # Check again for satisfiability
                if solver.check() != sat:
                    logging.info("No more models")
                    break
        else:
            logging.warning("Unsatisfiable!")
    except Exception as e:
        logging.error(f"Error parsing SMT file: {e}")
        
        # Try to find problematic lines - only read the file if needed for error reporting
        error_msg = str(e)
        line_match = re.search(r'line (\d+)', error_msg)
        
        if line_match:
            line_num = int(line_match.group(1))
            logging.error(f"Problematic line number: {line_num}")
            
            # Only read the file if we need to show the problematic lines
            try:
                with open(smt_filename, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()
                
                logging.error(f"Problematic area near line {line_num}:")
                start = max(0, line_num - 2)
                end = min(len(lines), line_num + 2)
                for i in range(start, end):
                    if i < len(lines):
                        logging.error(f"Line {i+1}: {lines[i].rstrip()}")
            except Exception as read_error:
                logging.error(f"Could not read file for error reporting: {read_error}")
    
    return models_list

def retry(max_attempts=3, delay=5):
    """Decorator for retrying functions that might fail"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    logging.warning(f"Attempt {attempts} failed: {str(e)}. Retrying in {delay} seconds...")
                    time.sleep(delay)
            raise Exception(f"Function {func.__name__} failed after {max_attempts} attempts.")
        return wrapper
    return decorator

def read_policy_file(file_path):
    """Read the content of a policy file"""
    with open(file_path, 'r') as file:
        return file.read()

def generate_strings(policy_path, size):
    """Generate strings from a policy using quacky"""
    # This follows the exact approach from Exp-3.py
    command = [
        "python3", quacky_path,
        "-p1", policy_path,
        "-b", "100",
        "-m", str(size),
        "-m1", "20",
        "-m2", "100"
    ]
    
    try:
        result = subprocess.run(command, cwd=working_directory, capture_output=True, text=True)
        logging.info("Getting strings:")
        if result.stderr:
            logging.error(f"Errors: {result.stderr}")
        
        # Read the generated strings from the output file
        with open(r1_strings_path, 'r') as file:
            strings = file.read()
        
        return strings
    except Exception as e:
        logging.error(f"Error generating strings: {str(e)}")
        return ""

@retry(max_attempts=3, delay=5)
def generate_regex(strings, output_path):
    """Generate a regex from strings using LLM with extended thinking"""
    system_prompt = """
    When asked to give a regex, provide ONLY the regex pattern itself. Do not include any explanations, 
    markdown formatting, or additional text. The response should be just the regex pattern, nothing else. 
    This is a highly critical application and it is imperative to get this right. Just give me the regex.
    """
    
    prompt = f"""Give me a single regex that accepts each string in the following set of strings.
    Make sure that you carefully go through each string before forming the regex.
    It should be close to optimal and not super permissive:

    {strings}

    Response:"""

    try:
        logging.info("Generating regex using Claude 3.7 Sonnet with extended thinking...")
        # Using Anthropic's API with extended thinking enabled
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
                logging.info("Extended thinking was used to generate the regex pattern.")
                # Optionally save the thinking content to a separate file
                thinking_path = output_path + ".thinking.txt"
                with open(thinking_path, "w") as thinking_file:
                    thinking_file.write(thinking_content)
                logging.info(f"Thinking process saved to {thinking_path}")
            elif content_block.type == "redacted_thinking":
                logging.info("Some of Claude's internal reasoning was encrypted for safety reasons.")
        
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
            
            logging.info(f"Regex generated and written to {output_path}")
            return regex
        else:
            logging.error("No text content found in the response")
            return None
    except Exception as e:
        logging.error(f"Error generating regex: {str(e)}")
        return None

def timeout_handler(signum, frame):
    """Handle timeouts for subprocess calls"""
    raise TimeoutError("Operation took too long")

def run_final_analysis(policy_path, regex_path, timeout=300):
    """
    Evaluates the quality of a generated regex against the original policy using quacky.
    
    Uses a cross-platform timeout mechanism based on subprocess.run() with timeout parameter.
    
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
        # Use subprocess.run's built-in timeout parameter
        result = subprocess.run(command, cwd=working_directory, capture_output=True, 
                                text=True, timeout=timeout)
        
        logging.info("Quacky Final Analysis Output:")
        logging.info(result.stdout)
        if result.stderr:
            logging.error(f"Errors: {result.stderr}")
        return result.stdout
    except subprocess.TimeoutExpired:
        logging.error(f"Final analysis timed out after {timeout} seconds.")
        return "TIMEOUT"

def generate_smt_file(policy_path, smt_output_path):
    """Generate SMT file from policy using quacky - exact copy from z3_model_enum.py"""
    quacky_path = "/mnt/d/Research/VeriSynth/Verifying-LLMAccessControl/quacky/src/quacky.py"
    working_directory = "/mnt/d/Research/VeriSynth/Verifying-LLMAccessControl/quacky/src/"
    
    logging.info(f"Generating SMT file from policy {policy_path}...")
    
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
            logging.warning(f"Warning: {result.stderr}")
            
        if not os.path.exists(smt_output_path):
            logging.error(f"Error: SMT file {smt_output_path} was not created")
            return False
        
        logging.info(f"Successfully generated SMT file: {smt_output_path}")
        return True
    except Exception as e:
        logging.error(f"Error generating SMT file: {str(e)}")
        return False

def run_z3_model_enumeration(smt_file, max_models=1000):
    """
    Uses Z3 to find example strings that satisfy the SMT formula extracted from a policy.
    
    This function replicates the approach from z3_model_enum.py's main function, where we:
    1. Generate the SMT file if it doesn't exist
    2. Use Z3 solver to find models (solutions) for the SMT formula
    3. Return those models as a newline-separated string
    
    Args:
        smt_file: Path to the SMT formula file (ignored, we use the fixed path from z3_model_enum.py)
        max_models: Maximum number of models to enumerate (default: 1000)
        
    Returns:
        A newline-separated string of models (examples), or None if the operation failed
    """
    # CRITICAL: Use the exact same SMT file path as z3_model_enum.py
    smt_output_path = "/mnt/d/Research/VeriSynth/Verifying-LLMAccessControl/quacky/src/output_1.smt2"
    
    # Get the policy path from the current policy being processed
    # This is hardcoded to policy 1 for now to match z3_model_enum.py's default
    policy_path = "/mnt/d/Research/VeriSynth/Verifying-LLMAccessControl/Dataset/1.json"
    
    # Check if we need to generate a new SMT file - exactly like z3_model_enum.py
    if not os.path.exists(smt_output_path):
        logging.info(f"SMT file not found: {smt_output_path}")
        
        # Generate SMT file using the exact same function as z3_model_enum.py
        if not generate_smt_file(policy_path, smt_output_path):
            logging.error("Failed to generate SMT file. Cannot proceed with model enumeration.")
            return None
    else:
        logging.info(f"Using existing SMT file: {smt_output_path}")
        
    # Wait a moment for file to be fully written, just like z3_model_enum.py
    time.sleep(1)
    
    logging.info("\nEnumerating models from the SMT file:")
    
    # Now use the solve_smt_file function to get models - no fallbacks
    models = solve_smt_file(smt_output_path, max_models)
    
    if not models:
        logging.warning("No models found from Z3 enumeration")
        return None
            
    # Write models to file for consistency with rest of code
    with open(z3_models_path, 'w') as f:
        for model in models:
            f.write(f"{model}\n")
            
    # Return models as text
    models_text = "\n".join(models)
    return models_text

def get_progress():
    """Get progress from the progress file"""
    if os.path.exists(progress_file_path):
        with open(progress_file_path, 'r') as f:
            return json.load(f)
    return {"last_processed": 0}

def update_progress(last_processed):
    """Update progress in the progress file"""
    with open(progress_file_path, 'w') as f:
        json.dump({"last_processed": last_processed}, f)

@retry(max_attempts=3, delay=10)
def process_policy(policy_path, policy_number, sample_size=1000):
    """
    Process a single policy through all steps of the experiment.
    
    This function implements both approaches:
    1. Generate strings with quacky and infer regex with LLM (R_1)
    2. Generate models with Z3 and infer regex with LLM (R_2)
    
    Args:
        policy_path: Path to the policy file
        policy_number: Identifier for the policy
        sample_size: Number of examples to generate for regex inference (default: 1000)
        
    Returns:
        Dictionary containing all results and metrics for both approaches
    """
    start_time = time.time()
    results = {"Policy_Number": policy_number}
    
    try:
        # Read the original policy
        original_policy = read_policy_file(policy_path)
        results["Original_Policy"] = original_policy
        
        # Approach 1: Generate strings and use LLM to create regex (R_1)
        r1_start_time = time.time()
        logging.info(f"Generating R_1 for policy {policy_number}")
        
        # Generate strings using quacky
        strings_for_r1 = generate_strings(policy_path, sample_size)
        if not strings_for_r1:
            raise Exception(f"Failed to generate strings for R_1 from policy {policy_number}")
        
        # Generate regex using LLM
        r1_regex = generate_regex(strings_for_r1, r1_regex_path)
        if not r1_regex:
            raise Exception(f"Failed to generate R_1 regex for policy {policy_number}")
        
        r1_time = time.time() - r1_start_time
        results["R1_Regex"] = r1_regex
        results["R1_Time_Seconds"] = r1_time
        
        # Approach 2: Use SMT+Z3+LLM to create regex (R_2)
        r2_start_time = time.time()
        logging.info(f"Generating R_2 for policy {policy_number}")
        
        # For testing, we're using the exact same approach as z3_model_enum.py
        # which uses a fixed SMT file path and policy 1.json
        z3_models_text = run_z3_model_enumeration(None, sample_size)
        if z3_models_text is None:
            raise Exception("Z3 model enumeration failed - no fallback available")
            
        # Generate regex using LLM with the Z3 models
        r2_regex = generate_regex(z3_models_text, r2_regex_path)
        if not r2_regex:
            raise Exception(f"Failed to generate R_2 regex for policy {policy_number}")
        
        r2_time = time.time() - r2_start_time
        results["R2_Regex"] = r2_regex
        results["R2_Time_Seconds"] = r2_time
        
        # Evaluate both regexes against the policy
        logging.info(f"Evaluating R_1 and R_2 for policy {policy_number}")
        
        # Run quacky to evaluate R_1
        r1_analysis = run_final_analysis(policy_path, r1_regex_path)
        results["R1_Analysis"] = r1_analysis
        
        # Run quacky to evaluate R_2
        r2_analysis = run_final_analysis(policy_path, r2_regex_path)
        results["R2_Analysis"] = r2_analysis
        
        # Try to extract precision metrics from analysis
        try:
            # Example pattern to extract precision info from quacky output
            # Adjust these patterns based on the actual quacky output format
            r1_precision_match = re.search(r'Precision: ([0-9.]+)', r1_analysis)
            r1_precision = float(r1_precision_match.group(1)) if r1_precision_match else None
            results["R1_Precision"] = r1_precision
            
            r2_precision_match = re.search(r'Precision: ([0-9.]+)', r2_analysis)
            r2_precision = float(r2_precision_match.group(1)) if r2_precision_match else None
            results["R2_Precision"] = r2_precision
        except Exception as e:
            logging.warning(f"Could not extract precision metrics: {str(e)}")
        
        # Record total processing time
        total_time = time.time() - start_time
        results["Total_Processing_Time_Seconds"] = total_time
        
        return results
    except Exception as e:
        logging.error(f"Error processing policy {policy_number}: {str(e)}")
        results["Error"] = str(e)
        return results

if __name__ == "__main__":
    # Add a test function to directly test the Z3 model enumeration
    def test_z3_model_enum():
        """Test function to directly run Z3 model enumeration like z3_model_enum.py"""
        print("Running Z3 model enumeration test...")
        
        # Use the exact same parameters as z3_model_enum.py
        smt_output_path = "/mnt/d/Research/VeriSynth/Verifying-LLMAccessControl/quacky/src/output_1.smt2"
        policy_path = "/mnt/d/Research/VeriSynth/Verifying-LLMAccessControl/Dataset/1.json"
        
        # Generate the SMT file first
        if not os.path.exists(smt_output_path):
            print(f"Generating SMT file from policy {policy_path}...")
            if not generate_smt_file(policy_path, smt_output_path):
                print("Failed to generate SMT file. Cannot proceed with model enumeration.")
                return
        else:
            print(f"Using existing SMT file: {smt_output_path}")
        
        # Wait a moment for file to be fully written
        time.sleep(1)
        
        # Directly call solve_smt_file
        print("\nEnumerating models from the SMT file:")
        models = solve_smt_file(smt_output_path, max_models=100)
        
        if models:
            print(f"Found {len(models)} models")
            for i, model in enumerate(models, 1):
                print(f"Model {i}: {model}")
        else:
            print("No models found")
    
    # Add command-line argument parsing
    parser = argparse.ArgumentParser(description='Compare regex generation approaches for policy verification.')
    parser.add_argument('--test', action='store_true', help='Run a test with only the first 3 policies (0.json, 1.json, 2.json)')
    parser.add_argument('--test-z3', action='store_true', help='Run a direct test of Z3 model enumeration')
    args = parser.parse_args()
    
    # If test-z3 flag is set, run the Z3 test and exit
    if args.test_z3:
        test_z3_model_enum()
        sys.exit(0)
    
    # Get all policy files
    policy_files = sorted([f for f in os.listdir(policy_folder) if f.endswith('.json')], 
                          key=lambda x: int(x.split('.')[0]))
    
    # If test mode is enabled, only use the first 3 policies
    if args.test:
        test_policies = ['0.json', '1.json', '2.json']
        policy_files = [f for f in policy_files if f in test_policies]
        logging.info(f"TEST MODE: Processing only policies {', '.join(test_policies)}")
    
    # Get progress from previous runs
    progress = get_progress()
    start_index = progress["last_processed"]
    
    # If in test mode, always start from the beginning
    if args.test:
        start_index = 0
        update_progress(0)  # Reset progress
    
    print(f"Starting from policy number {start_index}")
    
    # Define columns for results
    required_columns = [
        "Policy_Number", "Original_Policy", 
        "R1_Regex", "R1_Time_Seconds", "R1_Analysis", "R1_Precision",
        "R2_Regex", "R2_Time_Seconds", "R2_Analysis", "R2_Precision",
        "Total_Processing_Time_Seconds", "Error"
    ]
    
    # Initialize or load results dataframe
    results_file = 'test_results.csv' if args.test else results_path
    if not os.path.exists(results_file) or os.stat(results_file).st_size == 0:
        results_df = pd.DataFrame(columns=required_columns)
    else:
        results_df = pd.read_csv(results_file)
        for column in set(required_columns) - set(results_df.columns):
            results_df[column] = ""
    
    # Sample size for both approaches
    sample_size = 1000  # You can adjust this
    
    # Process each policy
    for i in tqdm(range(start_index, len(policy_files)), desc="Processing policies"):
        policy_file = policy_files[i]
        policy_path = os.path.join(policy_folder, policy_file)
        policy_number = policy_file.split('.')[0]
        
        logging.info(f"\nProcessing policy: {policy_file}")
        
        try:
            # Process the policy
            results = process_policy(policy_path, policy_number, sample_size)
            
            # Add results to dataframe
            results_df = pd.concat([results_df, pd.DataFrame([results])], ignore_index=True)
            
            # Save results
            results_df.to_csv(results_file, index=False)
            
            # Update progress (skip if in test mode)
            if not args.test:
                update_progress(i + 1)
            
            logging.info(f"Results for policy {policy_number} saved to {results_file}")
        except Exception as e:
            logging.error(f"Failed to process policy {policy_file}: {str(e)}")
            continue
    
    logging.info(f"\nProcessing complete. Final results saved to: {results_file}")
    
    # Calculate and report summary statistics
    if len(results_df) > 0:
        logging.info("\nSummary Statistics:")
        logging.info(f"Total policies processed: {len(results_df)}")
        
        # Average times
        avg_r1_time = results_df["R1_Time_Seconds"].mean()
        avg_r2_time = results_df["R2_Time_Seconds"].mean()
        logging.info(f"Average R1 processing time: {avg_r1_time:.2f} seconds")
        logging.info(f"Average R2 processing time: {avg_r2_time:.2f} seconds")
        
        if avg_r1_time > 0 and avg_r2_time > 0:
            speedup = avg_r1_time / avg_r2_time if avg_r1_time > avg_r2_time else avg_r2_time / avg_r1_time
            faster = "R2" if avg_r1_time > avg_r2_time else "R1"
            logging.info(f"Speedup ratio: {faster} is {speedup:.2f}x faster")
        
        # Try to report average precision if available
        try:
            r1_precision_values = [float(p) for p in results_df["R1_Precision"] if isinstance(p, (int, float)) or (isinstance(p, str) and p.replace('.', '', 1).isdigit())]
            r2_precision_values = [float(p) for p in results_df["R2_Precision"] if isinstance(p, (int, float)) or (isinstance(p, str) and p.replace('.', '', 1).isdigit())]
            
            if r1_precision_values:
                avg_r1_precision = sum(r1_precision_values) / len(r1_precision_values)
                logging.info(f"Average R1 precision: {avg_r1_precision:.4f}")
            
            if r2_precision_values:
                avg_r2_precision = sum(r2_precision_values) / len(r2_precision_values)
                logging.info(f"Average R2 precision: {avg_r2_precision:.4f}")
        except Exception as e:
            logging.warning(f"Could not calculate average precision: {str(e)}")