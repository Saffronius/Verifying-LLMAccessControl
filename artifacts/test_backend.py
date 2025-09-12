#!/usr/bin/env python3
"""
Test script for Quacky Pipeline backend functionality
"""
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from backend.quacky_wrapper import QuackyWrapper
from backend.policy_generator import PolicyGenerator

def test_policy_generation():
    """Test policy generation from natural language"""
    print("\n=== Testing Policy Generation ===")
    
    generator = PolicyGenerator()
    description = "Allow all EC2 actions in us-west-2 region only"
    
    print(f"Description: {description}")
    result = generator.generate_policy_from_nl(description)
    
    if result["success"]:
        print(f"✅ Policy generated successfully using {result.get('model_used', 'LLM')}")
        print("Generated Policy:")
        print(result["policy"])
        return result["policy"]
    else:
        print(f"❌ Error: {result['error']}")
        return None

def test_policy_comparison():
    """Test policy comparison using quacky"""
    print("\n=== Testing Policy Comparison ===")
    
    # Sample policies for testing
    policy1 = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "ec2:*",
                "Resource": "*",
                "Condition": {
                    "StringEquals": {
                        "ec2:Region": "us-west-2"
                    }
                }
            }
        ]
    }
    
    policy2 = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "ec2:DescribeInstances",
                    "ec2:DescribeImages"
                ],
                "Resource": "*"
            }
        ]
    }
    
    quacky = QuackyWrapper()
    
    print("Policy 1: EC2 all actions in us-west-2")
    print("Policy 2: EC2 read-only globally")
    
    result = quacky.compare_policies(
        json.dumps(policy1),
        json.dumps(policy2),
        bound=50
    )
    
    if result["success"]:
        print("✅ Comparison successful")
        print(f"Metrics: {result['metrics']}")
        print(f"Output preview: {result['output'][:200]}...")
    else:
        print(f"❌ Error: {result['error']}")
    
    quacky.cleanup()
    return result

def test_quacky_direct():
    """Test direct quacky execution"""
    print("\n=== Testing Direct Quacky Execution ===")
    
    import subprocess
    
    # Create a simple test policy file
    test_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "s3:GetObject",
                "Resource": "arn:aws:s3:::test-bucket/*"
            }
        ]
    }
    
    with open("/tmp/test_policy.json", "w") as f:
        json.dump(test_policy, f)
    
    cmd = [
        "python3",
        "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/CPCA/quacky/src/quacky.py",
        "-p1", "/tmp/test_policy.json",
        "-b", "10"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            cwd="/home/ash/Desktop/VerifyingLLMGeneratedPolicies/CPCA/quacky/src"
        )
        
        if result.returncode == 0:
            print("✅ Quacky executed successfully")
            print(f"Output: {result.stdout[:300]}")
        else:
            print(f"❌ Quacky failed with return code {result.returncode}")
            print(f"Error: {result.stderr}")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    print("Starting Quacky Pipeline Backend Tests...")
    
    # Test 1: Direct quacky execution
    test_quacky_direct()
    
    # Test 2: Policy generation
    generated_policy = test_policy_generation()
    
    # Test 3: Policy comparison
    test_policy_comparison()
    
    print("\n=== Tests Complete ===")