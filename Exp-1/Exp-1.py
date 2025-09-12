import subprocess
import pandas as pd
import os
import openai
import json
import logging
from tqdm import tqdm
import time
from functools import wraps
import z3
from dotenv import load_dotenv
import re
import sys
from z3 import Solver, String, Or, sat

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("single_policy_dual_analysis.log"), logging.StreamHandler()])

# Set up Grok client with API Key
# Grok (uses OpenAI-compatible API)
grok_client = openai.OpenAI(
    api_key=os.getenv('GROK_API_KEY'),
    base_url="https://api.x.ai/v1"
)

grok_model_name = "grok-3"

# Define paths - Updated with correct paths
policy_folder = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/Prev-Experiments/Verifying-LLMAccessControl/Dataset"
quacky_base_path = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/CPCA/quacky/src"
quacky_py_path = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/CPCA/quacky/src/quacky.py"
working_directory = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/CPCA/quacky/src/"
response_file_path = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/CPCA/quacky/src/response.txt"
response2_file_path = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/CPCA/quacky/src/response2.txt"
result_table_path = "Exp-1/single_policy_dual_analysis.json"
generated_policy_path = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/CPCA/quacky/src/gen_pol.json"
smt_output_1_path = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/CPCA/quacky/src/output_1.smt2"
smt_output_2_path = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/CPCA/quacky/src/output_2.smt2"
progress_file_path = "Exp-1/single_policy_dual_progress.json"
results_list_path = "Exp-1/single_policy_dual_analysis.json"

def read_policy_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def retry(max_attempts=3, delay=5):
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

@retry(max_attempts=3, delay=5)
def get_policy_description(policy_content):
    prompt = f"""Please provide a clear, comprehensive natural language explanation of what this AWS IAM policy allows or denies in a manner that allows the reconstruction of this policy.
Don't respond with your thought process at all. Make sure you only respond with the relevant explanation and nothing else. And make sure that the explanation is still in natural language otherwise it kinda defeats the purpose.

Policy:
{policy_content}
"""
    
    try:
        response = grok_client.chat.completions.create(
            model=grok_model_name,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=1
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error calling Grok API for policy description: {str(e)}")
        return ""

@retry(max_attempts=3, delay=5)
def generate_new_policy(description):
    prompt = f"""Based on this explanation, generate a complete AWS IAM policy in JSON format.
Only output valid JSON, no other text.

Explanation:
{description}
"""
    
    try:
        response = grok_client.chat.completions.create(
            model=grok_model_name,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=1
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error calling Grok API for policy generation: {str(e)}")
        return ""

def save_generated_policy(policy_content, file_path):
    try:
        with open(file_path, 'w') as file:
            json.dump(json.loads(policy_content), file, indent=2)
        logging.info(f"Generated policy saved to: {file_path}")
    except json.JSONDecodeError:
        logging.error("Generated policy is not valid JSON. Saving as plain text.")
        with open(file_path, 'w') as file:
            file.write(policy_content)

def generate_smt_formulas(original_policy_path, generated_policy_path):
    """Generate SMT formulas using quacky for policy comparison"""
    command = [
        "python3", quacky_py_path,
        "-p1", original_policy_path,
        "-p2", generated_policy_path,
        "-b", "100"
    ]
    
    result = subprocess.run(command, cwd=working_directory, capture_output=True, text=True)
    logging.info("Generating SMT formulas:")
    logging.info(result.stdout)
    if result.stderr:
        logging.error(f"Errors: {result.stderr}")
    
    # Check if SMT files were generated
    smt1_exists = os.path.exists(smt_output_1_path)
    smt2_exists = os.path.exists(smt_output_2_path)
    
    logging.info(f"SMT file 1 (P1 && ~P2) exists: {smt1_exists}")
    logging.info(f"SMT file 2 (~P1 && P2) exists: {smt2_exists}")
    
    return result.returncode == 0 and smt1_exists and smt2_exists

def z3_get_models(smt_file_path, num_models=1000):
    """Use Z3 to get models from SMT formula using solver.from_string()"""
    try:
        logging.info(f"Generating {num_models} models from {smt_file_path} using solver.from_string()")
        
        with open(smt_file_path, 'r') as f:
            smt_formula_str = f.read()

        # It's possible that quacky's output still contains constructs that 
        # solver.from_string() might struggle with if they are non-standard SMT-LIB v2.
        # If errors persist, we might need a light pre-processing here.
        # For now, let's try direct parsing.

        solver = Solver() # Use z3.Solver() for clarity if z3 is imported directly
        solver.from_string(smt_formula_str)
        
        models = []
        
        for i in range(num_models):
            if solver.check() == sat: # Use z3.sat for clarity
                model = solver.model()
                models.append(model) # Store the Z3 model object directly for now
                                     # Conversion to string can happen later if needed or kept as is.
                
                # Create constraint to exclude the current model to find a new one.
                # This is a standard way to enumerate multiple models.
                constraints = []
                for d in model.decls():
                    # Ensure we only try to create constraints for variables present in the model
                    # and that their interpretation is a constant value.
                    if model[d] is not None: # Check if the declaration has a value in the model
                        # For uninterpreted sorts or functions, model[d] might be complex.
                        # We are interested in variables that have simple values.
                        # Assuming Action, Resource, Principal are String constants based on SMT output.
                        # Adjust based on actual variable types if this causes issues.
                        try:
                            constraints.append(d() != model[d])
                        except Exception as e:
                            logging.warning(f"Could not create exclusion constraint for {d.name()}: {e}")                            
                
                if not constraints:
                    logging.warning(f"No constraints generated for model {i+1} in {smt_file_path}, cannot find diverse models. Breaking.")
                    break # Avoid infinite loop if no new constraints can be added

                solver.add(Or(constraints))
            else:
                logging.warning(f"No more models available after {i} models for {smt_file_path}")
                break
        
        # Convert Z3 models to JSON string representation
        json_models = []
        for model_obj in models:
            model_dict = {}
            for decl in model_obj.decls():
                model_dict[str(decl.name())] = str(model_obj[decl])
            json_models.append(json.dumps(model_dict, sort_keys=True))

        logging.info(f"Generated {len(json_models)} models from {smt_file_path}")
        return json_models
        
    except Exception as e:
        # Log the full Z3 error if it occurs during from_string or check/model
        logging.error(f"Error generating models from {smt_file_path}: {str(e)}")
        if hasattr(e, 'stdout') and e.stdout:
            logging.error(f"Z3 stdout: {e.stdout.decode() if isinstance(e.stdout, bytes) else e.stdout}")
        if hasattr(e, 'stderr') and e.stderr:
            logging.error(f"Z3 stderr: {e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr}")
        return []

def models_to_strings(models):
    """Convert Z3 models to string format for LLM processing"""
    strings = []
    for i, model in enumerate(models):
        # Create a readable string representation
        model_line = f"Model_{i}: {model}"
        strings.append(model_line)
    
    return "\n".join(strings)

@retry(max_attempts=3, delay=5)
def generate_regex_from_models(models, response_file_path):
    """Generate regex from Z3 models using Grok-3"""
    if not models:
        logging.warning("No models provided for regex generation")
        return None
        
    model_strings = models_to_strings(models)

    system_prompt = """
    When asked to give a regex, provide ONLY the regex pattern itself. Do not include any explanations, markdown formatting, or additional text. The response should be just the regex pattern, nothing else. This is a highly critical application and it is imperative to get this right. Just give me the regex.
    """
    prompt = f"Give me a single regex that characterizes the pattern in the following set of Z3 model strings. The regex should capture the essential structure and be reasonably general but not overly permissive:\n\n{model_strings}\n\nResponse:"

    try:
        response = grok_client.chat.completions.create(
            model=grok_model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=1
        )
        regex = response.choices[0].message.content.strip()
        regex = regex.replace("^", "").replace("$", "").strip()
        
        with open(response_file_path, "w") as output_file:
            output_file.write(regex)
        
        logging.info(f"Regex generated and written to {response_file_path}")
        return regex
    except Exception as e:
        logging.error(f"Error calling Grok API for regex generation: {str(e)}")
        return None

@retry(max_attempts=3, delay=5)
def run_final_analysis(original_policy_path, generated_policy_path):
    command = [
        "python3", quacky_py_path,
        "-p1", original_policy_path,
        "-p2", generated_policy_path,
        "-b", "100",
        "-cr", response_file_path,
        "-cr2", response2_file_path
    ]
    
    result = subprocess.run(command, cwd=working_directory, capture_output=True, text=True)
    logging.info("Quacky Final Analysis Output:")
    logging.info(result.stdout)
    if result.stderr:
        logging.error(f"Errors: {result.stderr}")
    return result.stdout

def get_progress():
    # Ensure the directory for the progress file exists
    os.makedirs(os.path.dirname(progress_file_path), exist_ok=True)
    if os.path.exists(progress_file_path):
        try:
            with open(progress_file_path, 'r') as f:
                content = json.load(f)
                # Basic validation
                if isinstance(content, dict) and "last_processed" in content and isinstance(content["last_processed"], int):
                    return content
                else:
                    logging.warning(f"Progress file {progress_file_path} has invalid format. Resetting.")
                    return {"last_processed": 0} # Reset if format is bad
        except json.JSONDecodeError:
            logging.warning(f"Could not decode JSON from progress file {progress_file_path}. Resetting.")
            return {"last_processed": 0} # Reset if corrupted
    return {"last_processed": 0}

def update_progress(last_processed):
    # Ensure the directory for the progress file exists
    os.makedirs(os.path.dirname(progress_file_path), exist_ok=True)
    with open(progress_file_path, 'w') as f:
        json.dump({"last_processed": last_processed}, f)
    logging.info(f"Progress updated to: {last_processed}")

def load_results():
    """Load existing results from JSON file"""
    # Ensure the directory for the results file exists
    os.makedirs(os.path.dirname(results_list_path), exist_ok=True) # Changed from result_table_path
    if os.path.exists(results_list_path):
        try:
            with open(results_list_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logging.warning(f"Could not decode JSON from results file {results_list_path}. Returning empty list.")
            return [] # Return empty if corrupted, so we don't lose all results
    return []

def save_results(results_list):
    """Save results list to JSON file"""
    # Ensure the directory for the results file exists
    os.makedirs(os.path.dirname(results_list_path), exist_ok=True) # Changed from result_table_path
    with open(results_list_path, 'w') as f:
        json.dump(results_list, f, indent=2)
    logging.info(f"Results saved to {results_list_path}")

@retry(max_attempts=3, delay=10)
def process_policy(policy_path):
    start_time = time.time()
    original_policy = read_policy_file(policy_path)
    policy_description = get_policy_description(original_policy)
    logging.info(f"Policy Description:\n{policy_description}")
    
    new_policy = generate_new_policy(policy_description)
    logging.info("Generated Policy:")
    logging.info(new_policy)
    
    save_generated_policy(new_policy, generated_policy_path)
    
    # Generate SMT formulas using quacky
    if not generate_smt_formulas(policy_path, generated_policy_path):
        raise Exception("Failed to generate SMT formulas.")
    
    # Use Z3 to get models from SMT formulas
    models_p1_not_p2 = z3_get_models(smt_output_1_path, num_models=1000)
    models_not_p1_p2 = z3_get_models(smt_output_2_path, num_models=1000)
    
    # Generate regex from Z3 models
    regex1 = generate_regex_from_models(models_p1_not_p2, response_file_path)
    regex2 = generate_regex_from_models(models_not_p1_p2, response2_file_path)
    
    if not regex1 or not regex2:
        raise Exception("Failed to generate one or both regexes from Z3 models.")
    
    final_analysis = run_final_analysis(policy_path, generated_policy_path)
    
    end_time = time.time()
    total_processing_time = end_time - start_time
    
    return {
        "model_name": grok_model_name,
        "Original Policy": original_policy,
        "Generated Policy": new_policy,
        "Policy Description": policy_description,
        "Z3 Models (P1_not_P2)": len(models_p1_not_p2),
        "Z3 Models (not_P1_P2)": len(models_not_p1_p2),
        "Regex from llm (P1_not_P2)": regex1,
        "Regex from llm (not_P1_P2)": regex2,
        "Final Analysis": final_analysis,
        "Total Processing Time (seconds)": total_processing_time
    }

if __name__ == "__main__":
    # Ensure the main Exp-1 directory exists for outputs relative to script location or CWD
    # This is crucial if result_table_path and progress_file_path are relative like "Exp-1/file.json"
    # os.makedirs("Exp-1", exist_ok=True) # This might be too broad if paths are absolute.
                                        # The per-function os.makedirs is safer.

    policy_files = sorted([f for f in os.listdir(policy_folder) if f.endswith('.json')], key=lambda x: int(x.split('.')[0]))[:41]  # Sort and limit to 0-40

    progress = get_progress()
    start_index = progress["last_processed"]

    print(f"Starting from policy number {start_index}")
    
    results_list = load_results()
    existing_policy_numbers = {result.get("Policy Number") for result in results_list if "Policy Number" in result}

    for i in tqdm(range(start_index, len(policy_files)), desc="Processing policies"):
        policy_file = policy_files[i]
        policy_path = os.path.join(policy_folder, policy_file)
        policy_number = policy_file.split('.')[0]
        
        if policy_file == "0.json":
            logging.info(f"Skipping policy file: {policy_file} as per request.")
            if i == start_index:
                 update_progress(i + 1)
            continue

        logging.info(f"\nProcessing policy: {policy_file}")
        
        if policy_number in existing_policy_numbers:
            logging.info(f"Policy {policy_number} already processed and found in results, skipping...")
            if i == start_index:
                update_progress(i + 1)
            continue
        
        try:
            new_entry = process_policy(policy_path)
            new_entry["Policy Number"] = policy_number
            new_entry["Processing Timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
            results_list.append(new_entry)
            save_results(results_list)
            logging.info(f"Results updated and saved to {results_list_path}")
            update_progress(i + 1)
        except Exception as e:
            logging.error(f"Failed to process policy after multiple attempts: {policy_file}. Error: {str(e)}")
            error_entry = {
                "Policy Number": policy_number,
                "model_name": grok_model_name,
                "Status": "Failed",
                "Error": str(e),
                "Processing Timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            results_list.append(error_entry)
            save_results(results_list)
            update_progress(i + 1)
            continue

    logging.info("\nProcessing complete. Final results saved to: " + results_list_path)
    print(f"Processed policies. Results saved to: {results_list_path}")
