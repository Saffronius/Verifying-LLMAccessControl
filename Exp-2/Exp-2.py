import subprocess
import pandas as pd
import os
from openai import OpenAI
import json
import logging
from tqdm import tqdm
import re
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the OpenAI client
client = OpenAI()

# Use GPT-5 with medium reasoning effort for regex synthesis
model_name = "gpt-5"


policy_folder = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/Prev-Experiments/Verifying-LLMAccessControl/Dataset/Dataset_mutated"
quacky_base_path = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/quacky/src"
quacky_path = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/quacky/src/quacky.py"
working_directory = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/quacky/src/"
response_file_path = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/quacky/src/response.txt"
result_table_path = "Exp-2/multi-string.csv"
generated_policy_path = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/quacky/src/gen_pol.json"
p1_not_p2_models_path = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/quacky/src/P1_not_P2.models"
progress_file_path = "Exp-2/progress.json"

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
    developer_prompt = """
Output only the regex pattern (no quotes, no prose).

Constraints (safe for DFA/ABC-style tooling):
- Do NOT use ^ or $, \\A \\Z \\z \\G.
- Do NOT use any (?...) constructs at all:
  non-capturing (?: ), lookarounds (?=, ?!, ?<=, ?<!), inline flags (?i),
  atomic (?>), conditionals, named groups, or backreferences \\1..\\9.
- Do NOT use lazy quantifiers (*?, +?, ??, {m,n}?).
- Match substrings; do not add boundaries.
- Do NOT invent rules about '/', spaces, or extensions unless forced by examples.
- Keep it specific; prefer bounded {m,n} and tight positive classes.
"""
    user_prompt = (
        "Give a single regex that matches ALL of these strings (substring semantics). "
        "Return ONLY the regex pattern, nothing else:\n\n" + strings
    )

    try:
        response = client.responses.create(
            model=model_name,
            input=[
                {"role": "developer", "content": developer_prompt},
                {"role": "user", "content": user_prompt}
            ],
            reasoning={
                "effort": "medium"  # Use medium reasoning effort
            },
            max_output_tokens=5000  # Balanced for reasoning through 1000 strings
        )
        
        # Extract text from the nested response structure (as per official GPT-5 docs)
        regex = ""
        if hasattr(response, 'output') and response.output:
            for item in response.output:
                if hasattr(item, "content"):
                    for content in item.content:
                        if hasattr(content, "text"):
                            regex += content.text
        
        regex = regex.strip()
        
        with open(response_file_path, "w") as output_file:
            output_file.write(regex)
        
        logging.info(f"Regex generated and written to {response_file_path}")
        return regex
    except Exception as e:
        logging.error(f"Error calling Anthropic API for regex generation: {str(e)}")
        return None

def run_final_analysis(policy_path):
    command = [
        "python3", quacky_path,
        "-p1", policy_path,
        "-b", "100",
        "-cr", response_file_path
    ]

    try:
        result = subprocess.run(command, cwd=working_directory, capture_output=True, text=True)

        if result.returncode != 0 or "FATAL ERROR FROM ABC" in result.stderr:
            raise Exception("Quacky analysis failed")

        logging.info("Quacky Final Analysis Output:")
        logging.info(result.stdout)
        if result.stderr:
            logging.error(f"Errors: {result.stderr}")
        return result.stdout
    except Exception as e:
        logging.error(f"Error in final analysis: {str(e)}")
        return None


def process_policy(policy_path, size, max_retries=5):
    errors = []
    original_policy = ""

    try:
        original_policy = read_policy_file(policy_path)
    except Exception as e:
        errors.append(f"Error reading policy file: {str(e)}")
        return {
            "model_name": model_name,
            "Original Policy": original_policy,
            "Size": size,
            "Regex from llm": "",
            "Experiment 2_Analysis": "",
            "Errors": "; ".join(errors)
        }

    for attempt in range(max_retries):
        try:
            
            strings = generate_strings(policy_path, size)
            if not strings:
                raise Exception("Failed to generate strings")

            regex = generate_regex(strings)
            if not regex:
                raise Exception("Failed to generate regex")

            exp2_raw_output = run_final_analysis(policy_path)
            if exp2_raw_output is None:
                raise Exception("Final analysis failed")

            
            return {
                "model_name": model_name,
                "Original Policy": original_policy,
                "Size": size,
                "Regex from llm": regex,
                "Experiment 2_Analysis": exp2_raw_output,
                "Errors": ""
            }

        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_retries - 1:
                errors.append(f"Process failed after {max_retries} attempts: {str(e)}")
            else:
                time.sleep(5) 

    
    return {
        "model_name": model_name,
        "Original Policy": original_policy,
        "Size": size,
        "Regex from llm": "",
        "Experiment 2_Analysis": "",
        "Errors": "; ".join(errors)
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
        if match:
            return int(match.group(1))
        return 0  

    policy_files = sorted([f for f in os.listdir(policy_folder) if f.endswith('.json')], key=sort_key)
    total_policies = len(policy_files)
    
    size = 1000  

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
            
            new_entry = process_policy(policy_path, size, max_retries=5)
            
            result_table = pd.concat([result_table, pd.DataFrame([new_entry])], ignore_index=True)
            result_table.to_csv(result_table_path, index=False)
            logging.info(f"Results table updated and saved to {result_table_path}")
            update_progress(i + 1)
        else:
            logging.warning(f"Index {i} is out of range. Stopping processing.")
            break

    logging.info("\nProcessing complete. Final results table saved to: " + result_table_path)
    print(f"Processed {end_index - start_index} policies. Next run will start from policy number {min(end_index + 1, total_policies)}")
    
    logging.info("Starting CSV processing...")

    def parse_analysis(analysis):
        if not isinstance(analysis, str):
            return '', {}
        
        fields = {
            'Policy_Analysis': '',
            'Baseline Regex Count': None,
            'Synthesized Regex Count': None,
            'Baseline_Not_Synthesized Count': None,
            'Not_Baseline_Synthesized_Count': None,
            'regex_from_dfa': None,
            'regex_from_llm': None,
            'ops_regex_from_dfa': None,
            'ops_regex_from_llm': None,
            'length_regex_from_dfa': None,
            'length_regex_from_llm': None,
            'jaccard_numerator': None,
            'jaccard_denominator': None
        }

        policy_match = re.search(r'Policy 1.*?lg\(requests\): [\d.]+', analysis, re.DOTALL)
        if policy_match:
            fields['Policy_Analysis'] = policy_match.group(0)

        for field in fields:
            if field != 'Policy_Analysis':
                match = re.search(rf'{field}\s*:\s*(.*?)(?:\n|$)', analysis)
                if match:
                    fields[field] = match.group(1).strip()

        return fields

    df = pd.read_csv(result_table_path, encoding='utf-8')

    parsed_data = df['Experiment 2_Analysis'].apply(parse_analysis)

    for field in parsed_data.iloc[0].keys():
        df[field] = parsed_data.apply(lambda x: x[field] if isinstance(x, dict) else '')

    columns_order = ['model_name', 'Original Policy', 'Size', 'Regex from llm', 'Policy_Analysis'] + \
                    [col for col in df.columns if col not in ['model_name', 'Original Policy', 'Size', 'Regex from llm', 'Policy_Analysis', 'Experiment 2_Analysis']] + \
                    ['Errors']
    df = df[columns_order]

    processed_csv_path = os.path.join(os.path.dirname(result_table_path), 'Exp-2.csv')
    df.to_csv(processed_csv_path, index=False, encoding='utf-8')
    logging.info(f"CSV file has been processed and saved as '{processed_csv_path}'")
    print(f"Processed CSV file saved as '{processed_csv_path}'")
