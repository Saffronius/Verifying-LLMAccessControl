import subprocess
import pandas as pd
import os
import openai
import json
import logging
from tqdm import tqdm
import signal
import re
import time


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("policy_analysis.log"), logging.StreamHandler()])

# Initialize OpenAI client with api key

model_id = "ft:gpt-4o-mini-2024-07-18:personal::A5b7jUfX"

# Define paths
policy_folder = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/Prev-Experiments/Verifying-LLMAccessControl/Dataset"
quacky_base_path = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/CPCA/quacky/src"
quacky_path = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/CPCA/quacky/src/quacky.py"
working_directory = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/CPCA/quacky/src/"
response_file_path = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/CPCA/quacky/src/response.txt"
result_table_path = "Exp-3/multi-string.csv"
generated_policy_path = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/CPCA/quacky/src/gen_pol.json"
p1_not_p2_models_path = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/CPCA/quacky/src/P1_not_P2.models"
progress_file_path = "Exp-3/progress.json"

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def read_policy_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def generate_strings(policy_path, size):
    command = [
        "python3", quacky_path,
        "-p1", policy_path,
        "-b", "100",
        "-m", str(size),
        "-m1", "20",
        "-m2", "100"
    ]
    
    result = subprocess.run(command, cwd=working_directory, capture_output=True, text=True)
    logging.info("Getting strings:")
    if result.stderr:
        logging.error(f"Errors: {result.stderr}")
    
    with open(p1_not_p2_models_path, 'r') as file:
        strings = file.read()
    
    return strings

def generate_regex(strings):
    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": "When asked to give a regex, provide ONLY the regex pattern itself. Do not include any explanations, markdown formatting, or additional text. The response should be just the regex pattern, nothing else. This is a highly critical application and it is imperative to get this right. Just give the regex."},
                {"role": "user", "content": f"Give me a single regex that accepts each string in the following set of strings. Make sure that you carefully go through each string before forming the regex. It should be close to optimal and not super permissive:\n\n{strings}"}
            ],
            max_tokens=1000
        )
        regex = response.choices[0].message.content.strip()
        
        with open(response_file_path, "w") as output_file:
            output_file.write(regex)
        
        logging.info(f"Regex generated and written to {response_file_path}")
        return regex
    except openai.OpenAIError as e:
        logging.error(f"OpenAI API error: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error in regex generation: {str(e)}")
        return None

def timeout_handler(signum, frame):
    raise TimeoutError("Analysis took too long")

def run_final_analysis(policy_path, timeout=300):  # 5 minutes timeout
    command = [
        "python3", quacky_path,
        "-p1", policy_path,
        "-b", "100",
        "-cr", response_file_path
    ]
    
    # Setting up a timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)
    
    try:
        result = subprocess.run(command, cwd=working_directory, capture_output=True, text=True)
        # Cancel alarm
        signal.alarm(0)
        
        logging.info("Quacky Final Analysis Output:")
        logging.info(result.stdout)
        if result.stderr:
            logging.error(f"Errors: {result.stderr}")
        return result.stdout
    except TimeoutError:
        logging.error(f"Final analysis for policy {policy_path} timed out after {timeout} seconds.")
        return "TIMEOUT"
    finally:
        #Ensure the alarm is canceled even if an exception occurs
        signal.alarm(0)

def process_policy_with_retry(policy_path, sizes):
    for attempt in range(MAX_RETRIES):
        try:
            return process_policy(policy_path, sizes)
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                logging.warning(f"Error processing policy {policy_path}. Retrying in {RETRY_DELAY} seconds. Error: {str(e)}")
                time.sleep(RETRY_DELAY)
            else:
                logging.error(f"Failed to process policy {policy_path} after {MAX_RETRIES} attempts. Error: {str(e)}")
                return {
                    "model_name": model_id,
                    "Original Policy": "",
                    "Results": [],
                    "Errors": f"Failed after {MAX_RETRIES} attempts: {str(e)}"
                }

def process_policy(policy_path, sizes):
    errors = []
    original_policy = ""
    results = []

    try:
        original_policy = read_policy_file(policy_path)
    except Exception as e:
        raise Exception(f"Error reading policy file: {str(e)}")

    for size in sizes:
        regex = ""
        exp2_raw_output = ""
        size_errors = []

        try:
            strings = generate_strings(policy_path, size)
            if not strings:
                raise Exception("Failed to generate strings")

            regex = generate_regex(strings)
            if not regex:
                raise Exception("Failed to generate regex")

            exp2_raw_output = run_final_analysis(policy_path)
            if exp2_raw_output == "TIMEOUT":
                raise Exception("Final analysis timed out")

        except Exception as e:
            raise Exception(f"Error processing size {size}: {str(e)}")

        results.append({
            "Size": size,
            "Regex from llm": regex,
            "Experiment 2_Analysis": exp2_raw_output,
            "Errors": "; ".join(size_errors) if size_errors else ""
        })

    return {
        "model_name": model_id,
        "Original Policy": original_policy,
        "Results": results,
        "Errors": "; ".join(errors) if errors else ""
    }

def get_progress():
    if os.path.exists(progress_file_path):
        with open(progress_file_path, 'r') as f:
            return json.load(f)
    return {"last_processed": 0}

def update_progress(last_processed):
    with open(progress_file_path, 'w') as f:
        json.dump({"last_processed": last_processed}, f)

if __name__ == "__main__":
    def sort_key(filename):
        match = re.search(r'(\d+)', filename)
        return int(match.group(1)) if match else 0

    policy_files = sorted([f for f in os.listdir(policy_folder) if f.endswith('.json')], key=sort_key)
    total_policies = len(policy_files)
    
    sizes = [50, 100, 250, 500, 1000, 1500, 2000, 3000]

    while True:
        try:
            num_policies = int(input(f"Enter the number of policies to process (1-{total_policies}) or -1 for all remaining policies: "))
            if num_policies == -1 or (1 <= num_policies <= total_policies):
                break
            else:
                print(f"Please enter a number between 1 and {total_policies}, or -1 for all remaining policies.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

    progress = get_progress()
    start_index = progress["last_processed"]

    start_index = max(0, min(start_index, total_policies - 1))

    print(f"Starting from policy number {start_index + 1}")

    required_columns = [
        "model_name", "Original Policy", "Size", "Regex from llm", "Experiment 2_Analysis", "Errors"
    ]

    if not os.path.exists(result_table_path) or os.stat(result_table_path).st_size == 0:
        result_table = pd.DataFrame(columns=required_columns)
    else:
        try:
            result_table = pd.read_csv(result_table_path)
            if result_table.empty or not all(col in result_table.columns for col in required_columns):
                result_table = pd.DataFrame(columns=required_columns)
        except pd.errors.EmptyDataError:
            result_table = pd.DataFrame(columns=required_columns)
        
        for column in set(required_columns) - set(result_table.columns):
            result_table[column] = ""

    end_index = total_policies if num_policies == -1 else min(start_index + num_policies, total_policies)

    for i in tqdm(range(start_index, end_index), desc="Processing policies"):
        if i < total_policies:
            policy_file = policy_files[i]
            policy_path = os.path.join(policy_folder, policy_file)
            logging.info(f"\nProcessing policy: {policy_file}")
            
            new_entries = process_policy_with_retry(policy_path, sizes)
            
            for result in new_entries["Results"]:
                entry = {
                    "model_name": new_entries["model_name"],
                    "Original Policy": new_entries["Original Policy"],
                    "Size": result["Size"],
                    "Regex from llm": result["Regex from llm"],
                    "Experiment 2_Analysis": result["Experiment 2_Analysis"],
                    "Errors": result["Errors"] if result["Errors"] else new_entries["Errors"]
                }
                result_table = pd.concat([result_table, pd.DataFrame([entry])], ignore_index=True)
            
            result_table.to_csv(result_table_path, index=False)
            logging.info(f"Results table updated and saved to {result_table_path}")
            update_progress(i + 1)
        else:
            logging.warning(f"Index {i} is out of range. Stopping processing.")
            break

    logging.info("\nProcessing complete. Final results table saved to: " + result_table_path)
    print(f"Processed {end_index - start_index} policies. Next run will start from policy number {min(end_index + 1, total_policies)}")
