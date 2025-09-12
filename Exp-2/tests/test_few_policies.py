#!/usr/bin/env python3
"""
Simple test to run Exp-2 on just a few policies to verify it works.
"""

import sys
import os
sys.path.append('..')

# Import the actual Exp-2 code
import subprocess
import pandas as pd
from openai import OpenAI
import json
from dotenv import load_dotenv

# Load environment
load_dotenv('../.env')

# Initialize OpenAI
client = OpenAI()

# Use the same paths from Exp-2.py
policy_folder = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/Prev-Experiments/Verifying-LLMAccessControl/Dataset/Dataset_mutated"
quacky_path = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/quacky/src/quacky.py"
working_directory = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/quacky/src/"

# Test just 3 policies
test_policies = ["100.json", "101.json", "102.json"]

print("Testing Exp-2 with 3 policies...")
print(f"Policy folder: {policy_folder}")

for policy_file in test_policies:
    policy_path = os.path.join(policy_folder, policy_file)
    
    print(f"\n{'='*60}")
    print(f"Testing: {policy_file}")
    
    # Check if policy exists
    if not os.path.exists(policy_path):
        print(f"ERROR: Policy not found at {policy_path}")
        continue
    
    # Read the policy
    with open(policy_path, 'r') as f:
        policy_content = f.read()
    
    print(f"Policy loaded, size: {len(policy_content)} bytes")
    
    # Try to generate strings with quacky (small test)
    command = [
        "python3", quacky_path,
        "-p1", policy_path,
        "-b", "10",  # Small bound
        "-m", "5",   # Only 5 strings
        "-m1", "5",
        "-m2", "10"
    ]
    
    print(f"Running: {' '.join(command)}")
    
    try:
        # Run with a timeout
        result = subprocess.run(
            command, 
            cwd=working_directory, 
            capture_output=True, 
            text=True,
            timeout=10  # 10 second timeout
        )
        
        if result.returncode == 0:
            print("✓ Quacky executed successfully")
            # Check if response file was created
            response_file = os.path.join(working_directory, "response.txt")
            if os.path.exists(response_file):
                with open(response_file, 'r') as f:
                    lines = f.readlines()
                    print(f"Generated {len(lines)} test strings")
        else:
            print(f"✗ Quacky failed with return code: {result.returncode}")
            if result.stderr:
                print(f"Error: {result.stderr[:200]}")
                
    except subprocess.TimeoutExpired:
        print("✗ Quacky timed out (10s limit)")
        print("Note: This might mean ABC needs to be built or there's an issue with the policy")
    except Exception as e:
        print(f"✗ Error: {e}")

print(f"\n{'='*60}")
print("Test complete!")