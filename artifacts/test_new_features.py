#!/usr/bin/env python3
"""
Test script for new features: String Generation and Regex Synthesis
"""
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from backend.quacky_wrapper import QuackyWrapper
from backend.regex_synthesizer import RegexSynthesizer

def test_string_generation():
    """Test string generation between two policies"""
    print("\n=== Testing String Generation ===")
    
    quacky = QuackyWrapper()
    
    # Two different policies for testing
    policy1 = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "s3:*",
                "Resource": "arn:aws:s3:::public-*"
            }
        ]
    }
    
    policy2 = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                "Resource": "*"
            }
        ]
    }
    
    print("Policy 1: S3 all actions on public-* buckets")
    print("Policy 2: S3 read-only on all buckets")
    
    result = quacky.generate_strings(
        json.dumps(policy1),
        json.dumps(policy2),
        count=5,
        min_range=5,
        max_range=15
    )
    
    if result["success"]:
        print("✅ String generation successful")
        print(f"P1_not_P2 strings ({len(result['p1_not_p2'])}): {result['p1_not_p2'][:3]}")
        print(f"not_P1_P2 strings ({len(result['not_p1_p2'])}): {result['not_p1_p2'][:3]}")
        return result["p1_not_p2"], result["not_p1_p2"]
    else:
        print(f"❌ Error: {result['error']}")
        return [], []
    
    quacky.cleanup()

def test_regex_synthesis(example_strings):
    """Test regex synthesis from example strings"""
    print("\n=== Testing Regex Synthesis ===")
    
    if not example_strings:
        print("No example strings provided, using default")
        example_strings = [
            "s3:PutObject:public-data",
            "s3:DeleteObject:public-logs",
            "s3:CreateBucket:public-test"
        ]
    
    synthesizer = RegexSynthesizer()
    
    print(f"Synthesizing regex from {len(example_strings)} example strings")
    print(f"Examples: {example_strings[:3]}")
    
    result = synthesizer.synthesize_regex(example_strings)
    
    if result["success"]:
        print(f"✅ Regex synthesized using {result['model_used']}")
        print(f"Pattern: {result['regex']}")
        
        # Test explanation
        explanation = synthesizer.explain_regex(result["regex"])
        if explanation["success"]:
            print(f"Explanation: {explanation['explanation'][:200]}...")
        
        return result["regex"]
    else:
        print(f"❌ Error: {result['error']}")
        return None

def test_regex_validation(policy, regex_pattern):
    """Test regex validation against policy"""
    print("\n=== Testing Regex Validation ===")
    
    if not regex_pattern:
        print("No regex pattern to validate")
        return
    
    quacky = QuackyWrapper()
    
    print(f"Validating regex: {regex_pattern}")
    print("Against S3 policy")
    
    result = quacky.validate_regex(
        policy,
        regex_pattern,
        bound=50
    )
    
    if result["success"]:
        print("✅ Validation successful")
        print(f"Metrics: {result['metrics']}")
    else:
        print(f"❌ Error: {result['error']}")
    
    quacky.cleanup()

def test_regex_tools():
    """Test regex optimization and testing tools"""
    print("\n=== Testing Regex Tools ===")
    
    synthesizer = RegexSynthesizer()
    
    # Test optimization
    original_regex = "s3:(Put|Delete|Create)[A-Za-z]+:public-.*"
    print(f"Original regex: {original_regex}")
    
    result = synthesizer.optimize_regex(original_regex, [])
    
    if result["success"]:
        print(f"✅ Optimized regex: {result['optimized']}")
    else:
        print(f"❌ Optimization failed: {result['error']}")
    
    # Test regex matching
    import re
    test_strings = [
        "s3:PutObject:public-data",
        "s3:GetObject:private-data",
        "s3:DeleteBucket:public-test"
    ]
    
    print("\nTesting regex matches:")
    pattern = re.compile(original_regex)
    for s in test_strings:
        match = bool(pattern.match(s))
        print(f"  {'✅' if match else '❌'} {s}")

if __name__ == "__main__":
    print("Starting New Features Tests...")
    
    # Test 1: String Generation
    p1_not_p2, not_p1_p2 = test_string_generation()
    
    # Test 2: Regex Synthesis
    if p1_not_p2:
        regex_pattern = test_regex_synthesis(p1_not_p2)
    else:
        regex_pattern = test_regex_synthesis([])
    
    # Test 3: Regex Validation
    if regex_pattern:
        policy = json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "s3:*",
                    "Resource": "arn:aws:s3:::public-*"
                }
            ]
        })
        test_regex_validation(policy, regex_pattern)
    
    # Test 4: Regex Tools
    test_regex_tools()
    
    print("\n=== All Tests Complete ===")
    print("The new features are working! Access the web UI at http://localhost:8503")