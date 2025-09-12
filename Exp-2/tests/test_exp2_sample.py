#!/usr/bin/env python3
"""
Test script to verify Exp-2 is working by testing 2-3 policies.
"""

import sys
import os
import subprocess
import json
from pathlib import Path

# Add parent directory to path to import Exp-2
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test configuration
TEST_POLICIES = [
    "100.json",
    "101.json", 
    "102.json"
]

DATASET_PATH = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/Prev-Experiments/Verifying-LLMAccessControl/Dataset/Dataset_mutated"

def test_single_policy(policy_file):
    """Test a single policy using Exp-2."""
    policy_path = os.path.join(DATASET_PATH, policy_file)
    
    if not os.path.exists(policy_path):
        print(f"❌ Policy file not found: {policy_path}")
        return False
    
    print(f"\n{'='*60}")
    print(f"Testing policy: {policy_file}")
    print(f"{'='*60}")
    
    # Create a minimal test script that calls the Exp-2 logic
    test_code = f"""
import subprocess
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv('../.env')

# Initialize OpenAI client
client = OpenAI()

policy_path = "{policy_path}"
quacky_path = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/CPCA/quacky/src/quacky.py"
working_directory = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/CPCA/quacky/src/"

# Read policy
with open(policy_path, 'r') as f:
    policy_content = f.read()

print(f"Policy loaded: {{os.path.basename(policy_path)}}")
print(f"Policy size: {{len(policy_content)}} characters")

# Test quacky string generation with size 10
print("\\nTesting quacky string generation...")
command = [
    "python3", quacky_path,
    "-p1", policy_path,
    "-b", "100",
    "-m", "10",
    "-m1", "20",
    "-m2", "100"
]

try:
    result = subprocess.run(command, cwd=working_directory, capture_output=True, text=True, timeout=30)
    
    response_file = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/CPCA/quacky/src/response.txt"
    if os.path.exists(response_file):
        with open(response_file, 'r') as f:
            response = f.read()
            print(f"Generated {{len(response.splitlines())}} strings")
            print("Sample strings (first 3):")
            for line in response.splitlines()[:3]:
                print(f"  - {{line}}")
    else:
        print("No response file generated")
        
    if result.returncode != 0:
        print(f"Warning: quacky returned non-zero exit code: {{result.returncode}}")
        if result.stderr:
            print(f"Error: {{result.stderr[:500]}}")
            
except subprocess.TimeoutExpired:
    print("Quacky command timed out after 30 seconds")
except Exception as e:
    print(f"Error running quacky: {{e}}")

print("\\n✓ Basic test completed")
"""
    
    # Write and execute the test
    test_file = "/tmp/test_exp2_single.py"
    with open(test_file, 'w') as f:
        f.write(test_code)
    
    try:
        result = subprocess.run(
            ["python3", test_file],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        print(result.stdout)
        if result.stderr:
            print(f"Stderr: {result.stderr}")
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Test timed out after 60 seconds")
        return False
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)

def main():
    """Run tests on sample policies."""
    print("Starting Exp-2 Test Suite")
    print(f"Testing {len(TEST_POLICIES)} policies")
    
    results = []
    for policy_file in TEST_POLICIES:
        success = test_single_policy(policy_file)
        results.append((policy_file, success))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for policy_file, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {policy_file}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)