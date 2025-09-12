#!/usr/bin/env python3
"""
Test script to run Exp-2.py on the first policy with 500 strings
Shows complete output including analysis results
"""

import sys
import os
import logging

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Exp-2 module
import importlib.util
spec = importlib.util.spec_from_file_location("exp2", "../Exp-2.py")
exp2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exp2)

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def run_single_policy_test():
    """Run the complete pipeline on the first policy with 500 strings"""
    
    print("="*80)
    print("TESTING EXP-2.PY ON FIRST POLICY WITH 500 STRINGS")
    print("="*80)
    
    # Get the first policy
    policy_folder = exp2.policy_folder
    
    # Check if folder exists
    if not os.path.exists(policy_folder):
        print(f"ERROR: Policy folder not found: {policy_folder}")
        return
    
    # Get sorted list of policy files
    import re
    def sort_key(filename):
        match = re.search(r'(\d+)', filename)
        if match:
            return int(match.group(1))
        return 0
    
    policy_files = sorted(
        [f for f in os.listdir(policy_folder) if f.endswith('.json')], 
        key=sort_key
    )
    
    if len(policy_files) == 0:
        print("ERROR: No policy files found in the dataset folder")
        return
    
    # Take first policy
    policy_file = policy_files[0]
    policy_path = os.path.join(policy_folder, policy_file)
    
    print(f"\nPolicy file: {policy_file}")
    print(f"Full path: {policy_path}")
    print("-"*80)
    
    # Parameters
    size = 500  # Generate 500 strings as requested
    
    try:
        # Step 1: Read the policy
        print("\n[STEP 1] Reading policy file...")
        original_policy = exp2.read_policy_file(policy_path)
        print(f"Policy content (first 500 chars):")
        print(original_policy[:500])
        if len(original_policy) > 500:
            print("...")
        print("-"*80)
        
        # Step 2: Generate strings
        print(f"\n[STEP 2] Generating {size} strings from policy...")
        strings = exp2.generate_strings(policy_path, size)
        
        if not strings:
            print("ERROR: Failed to generate strings")
            return
        
        string_lines = [s for s in strings.strip().split('\n') if s]
        print(f"Successfully generated {len(string_lines)} strings")
        print("\nFirst 10 strings:")
        for i, s in enumerate(string_lines[:10], 1):
            print(f"  {i}. {s}")
        if len(string_lines) > 10:
            print(f"  ... ({len(string_lines)-10} more strings)")
        print("-"*80)
        
        # Step 3: Generate regex
        print("\n[STEP 3] Generating regex pattern using GPT-5...")
        print("(This may take a moment...)")
        regex = exp2.generate_regex(strings)
        
        if not regex:
            print("ERROR: Failed to generate regex")
            return
        
        print(f"\nGenerated regex pattern:")
        print(f"  {regex}")
        print(f"  Length: {len(regex)} characters")
        print("-"*80)
        
        # Step 4: Run final analysis
        print("\n[STEP 4] Running final analysis with Quacky...")
        analysis_output = exp2.run_final_analysis(policy_path)
        
        if not analysis_output:
            print("ERROR: Analysis failed")
            return
        
        print("\n" + "="*80)
        print("QUACKY ANALYSIS OUTPUT:")
        print("="*80)
        print(analysis_output)
        print("="*80)
        
        # Parse and display key metrics
        print("\n[SUMMARY] Key Metrics:")
        import re
        
        # Extract metrics using regex
        metrics = {
            'Satisfiability': re.search(r'satisfiability:\s*(\w+)', analysis_output),
            'Solve Time (ms)': re.search(r'Solve Time \(ms\):\s*([\d.]+)', analysis_output),
            'Count Time (ms)': re.search(r'Count Time \(ms\):\s*([\d.]+)', analysis_output),
            'lg(requests)': re.search(r'lg\(requests\):\s*([\d.]+)', analysis_output),
            'Baseline Regex Count': re.search(r'Baseline Regex Count\s*:\s*(\d+)', analysis_output),
            'Synthesized Regex Count': re.search(r'Synthesized Regex Count\s*:\s*(\d+)', analysis_output),
            'Jaccard Similarity': re.search(r'similarity1\s*:\s*([\d.]+)', analysis_output),
            'Regex from DFA length': re.search(r'length_regex_from_dfa\s*:\s*(\d+)', analysis_output),
            'Regex from LLM length': re.search(r'length_regex_from_llm\s*:\s*(\d+)', analysis_output),
        }
        
        for metric, match in metrics.items():
            if match:
                print(f"  {metric}: {match.group(1)}")
            else:
                print(f"  {metric}: Not found")
        
        print("\n" + "="*80)
        print("TEST COMPLETED SUCCESSFULLY!")
        print("="*80)
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_single_policy_test()