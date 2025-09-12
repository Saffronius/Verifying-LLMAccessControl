#!/usr/bin/env python3
"""
Test script to run Exp-2.py on the first 5 policies
"""

import sys
import os
import json
import logging
import pandas as pd
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now import the Exp-2 module
import importlib.util
spec = importlib.util.spec_from_file_location("exp2", "../Exp-2.py")
exp2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exp2)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_first_5_policies():
    """Test the first 5 policies from the dataset"""
    
    # Get list of policy files
    policy_folder = exp2.policy_folder
    
    # Check if folder exists
    if not os.path.exists(policy_folder):
        logging.error(f"Policy folder not found: {policy_folder}")
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
        logging.error("No policy files found in the dataset folder")
        return
        
    # Take first 5 policies
    policies_to_test = policy_files[:5]
    logging.info(f"Testing {len(policies_to_test)} policies:")
    for p in policies_to_test:
        logging.info(f"  - {p}")
    
    # Results storage
    results = []
    size = 100  # Use smaller size for testing
    
    # Process each policy
    for i, policy_file in enumerate(policies_to_test, 1):
        policy_path = os.path.join(policy_folder, policy_file)
        logging.info(f"\n[{i}/5] Processing: {policy_file}")
        
        try:
            # Read policy
            logging.info("  Reading policy file...")
            original_policy = exp2.read_policy_file(policy_path)
            
            # Generate strings
            logging.info(f"  Generating {size} strings from policy...")
            strings = exp2.generate_strings(policy_path, size)
            
            if not strings:
                logging.error("  Failed to generate strings")
                results.append({
                    "policy": policy_file,
                    "status": "Failed",
                    "error": "String generation failed"
                })
                continue
            
            # Count strings
            string_lines = [s for s in strings.strip().split('\n') if s]
            logging.info(f"  Generated {len(string_lines)} unique strings")
            
            # Generate regex
            logging.info("  Generating regex pattern...")
            regex = exp2.generate_regex(strings)
            
            if not regex:
                logging.error("  Failed to generate regex")
                results.append({
                    "policy": policy_file,
                    "status": "Failed", 
                    "error": "Regex generation failed"
                })
                continue
            
            logging.info(f"  Generated regex: {regex[:100]}..." if len(regex) > 100 else f"  Generated regex: {regex}")
            
            # Run final analysis
            logging.info("  Running final analysis with quacky...")
            analysis_output = exp2.run_final_analysis(policy_path)
            
            if analysis_output:
                logging.info("  ✓ Analysis completed successfully")
                
                # Extract key metrics
                import re
                sat_match = re.search(r'satisfiability:\s*(\w+)', analysis_output)
                baseline_match = re.search(r'Baseline Regex Count\s*:\s*(\d+)', analysis_output)
                synth_match = re.search(r'Synthesized Regex Count\s*:\s*(\d+)', analysis_output)
                
                results.append({
                    "policy": policy_file,
                    "status": "Success",
                    "strings_generated": len(string_lines),
                    "regex_length": len(regex),
                    "satisfiability": sat_match.group(1) if sat_match else "unknown",
                    "baseline_count": baseline_match.group(1) if baseline_match else "N/A",
                    "synthesized_count": synth_match.group(1) if synth_match else "N/A"
                })
            else:
                logging.error("  Analysis failed")
                results.append({
                    "policy": policy_file,
                    "status": "Failed",
                    "error": "Analysis failed"
                })
                
        except Exception as e:
            logging.error(f"  Error processing policy: {str(e)}")
            results.append({
                "policy": policy_file,
                "status": "Error",
                "error": str(e)
            })
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    success_count = sum(1 for r in results if r.get("status") == "Success")
    print(f"Total policies tested: {len(results)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(results) - success_count}")
    
    print("\nDetailed Results:")
    for r in results:
        print(f"\n{r['policy']}:")
        print(f"  Status: {r.get('status')}")
        if r.get('status') == 'Success':
            print(f"  Strings generated: {r.get('strings_generated')}")
            print(f"  Regex length: {r.get('regex_length')}")
            print(f"  Satisfiability: {r.get('satisfiability')}")
            print(f"  Baseline count: {r.get('baseline_count')}")
            print(f"  Synthesized count: {r.get('synthesized_count')}")
        else:
            print(f"  Error: {r.get('error')}")
    
    # Save results to CSV
    output_file = "test_5_policies_results.csv"
    df = pd.DataFrame(results)
    df.to_csv(output_file, index=False)
    print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    print("Starting test of first 5 policies...")
    print("This will test the complete pipeline: policy → strings → regex → analysis")
    print("-" * 60)
    test_first_5_policies()