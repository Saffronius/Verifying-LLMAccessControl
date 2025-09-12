#!/usr/bin/env python3
"""
Experiment 0: Comprehensive Policy Comprehension Assessment
Implements the 7-step workflow from the paper for multiple LLMs
"""

import os
import json
import hashlib
import random
import subprocess
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
import pandas as pd
from tqdm import tqdm
import re

# LLM clients
import openai
from anthropic import Anthropic
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from dotenv import load_dotenv

load_dotenv()

@dataclass
class ExperimentConfig:
    """Configuration for the experiment"""
    policy_dir: str
    quacky_base_path: str
    quacky_py_path: str
    output_dir: str = "experiment_results"
    results_file: str = "experiment_0_results.json"
    checkpoint_file: str = "experiment_checkpoint.json"  # Will be per-model: experiment_checkpoint_{model}.json
    num_test_requests: int = 20  # 10 allow + 10 deny
    batch_size: str = "100"
    run_from_scratch: bool = False  # New option to ignore checkpoints

@dataclass
class PolicyResult:
    """Results for a single policy-LLM combination"""
    policy_file: str
    llm_model: str
    timestamp: str
    results: Dict[str, Any]
    error: Optional[str] = None

class LLMClient:
    """Unified client for multiple LLMs"""
    
    def __init__(self):
        # Initialize all LLM clients
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.anthropic_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
        # Grok (uses OpenAI-compatible API)
        self.grok_client = openai.OpenAI(
            api_key=os.getenv('GROK_API_KEY'),
            base_url="https://api.x.ai/v1"
        )
        
        # DeepSeek (uses OpenAI-compatible API)  
        self.deepseek_client = openai.OpenAI(
            api_key=os.getenv('DEEPSEEK_API_KEY'),
            base_url="https://api.deepseek.com"
        )
        
        # Google Gemini - using standard import for now
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        
        # Sentence transformer for similarity scoring - force CPU to avoid CUDA issues
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
    
    def call_llm(self, model: str, prompt: str, max_retries: int = 3) -> str:
        """Call the specified LLM with retry logic"""
        
        for attempt in range(max_retries):
            try:
                if model == "o4-mini":
                    response = self.openai_client.responses.create(
                        model="o4-mini",
                        input=[
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        text={
                            "format": {
                                "type": "text"
                            }
                        },
                        reasoning={
                            "effort": "low"
                        },
                        tools=[],
                        store=True
                    )
                    return response.output_text
                
                elif model == "gpt-4.1-nano":
                    response = self.openai_client.chat.completions.create(
                        model="gpt-4.1-nano",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.1
                    )
                    return response.choices[0].message.content
                
                elif model == "claude-3.7-sonnet":
                    # Generate message without extended thinking
                    response = self.anthropic_client.messages.create(
                        model="claude-3-7-sonnet-20250219",
                        max_tokens=12000,
                        temperature=0.1,
                        messages=[{"role": "user", "content": prompt}],
                        thinking={"type": "disabled"}
                    )
                    # Extract text from content blocks, skipping non-text
                    text_output = ''
                    content_blocks = response.content or []
                    for block in content_blocks:
                        # block may be an object with .text or a dict
                        if hasattr(block, 'text'):
                            text_output += block.text
                        elif isinstance(block, dict) and block.get('type') == 'text':
                            text_output += block.get('text', '')
                    # Fallback: if no blocks, try string content
                    if not text_output:
                        try:
                            text_output = response.content if isinstance(response.content, str) else ''
                        except:
                            text_output = ''
                    # Strip and remove code fences if present
                    text = text_output.strip()
                    if text.startswith('```'):
                        lines = text.split('\n')
                        # drop fences
                        if lines and lines[0].startswith('```'):
                            lines = lines[1:]
                        if lines and lines[-1].startswith('```'):
                            lines = lines[:-1]
                        text = '\n'.join(lines)
                    return text
                
                elif model == "claude-3.5-sonnet":
                    response = self.anthropic_client.messages.create(
                        model="claude-3-5-sonnet-20240620",
                        max_tokens=8192,
                        temperature=0.1,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    # Extract text from content blocks, skipping non-text
                    text_output = ''
                    content_blocks = response.content or []
                    for block in content_blocks:
                        # block may be an object with .text or a dict
                        if hasattr(block, 'text'):
                            text_output += block.text
                        elif isinstance(block, dict) and block.get('type') == 'text':
                            text_output += block.get('text', '')
                    # Fallback: if no blocks, try string content
                    if not text_output:
                        try:
                            text_output = response.content if isinstance(response.content, str) else ''
                        except:
                            text_output = ''
                    # Strip and remove code fences if present
                    text = text_output.strip()
                    if text.startswith('```'):
                        lines = text.split('\n')
                        # drop fences
                        if lines and lines[0].startswith('```'):
                            lines = lines[1:]
                        if lines and lines[-1].startswith('```'):
                            lines = lines[:-1]
                        text = '\n'.join(lines)
                    return text
                
                elif model == "grok-3":
                    response = self.grok_client.chat.completions.create(
                        model="grok-3",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=1
                    )
                    return response.choices[0].message.content
                
                elif model == "deepseek-chat":
                    response = self.deepseek_client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.1,
                        stream=False
                    )
                    return response.choices[0].message.content
                
                elif model == "gemini-2.5-flash":
                    # Using standard genai API for now until new client API is available
                    model_instance = genai.GenerativeModel('gemini-2.0-flash-exp')
                    response = model_instance.generate_content(
                        prompt,
                        generation_config=genai.GenerationConfig(temperature=1)
                    )
                    return response.text
                
                else:
                    raise ValueError(f"Unknown model: {model}")
                    
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for {model}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise e

class RequestGenerator:
    """Generates test requests for policies"""
    
    def __init__(self):
        # Common AWS actions by service for violation generation
        self.aws_actions = {
            's3': ['s3:GetObject', 's3:PutObject', 's3:DeleteObject', 's3:ListBucket', 
                   's3:CreateBucket', 's3:DeleteBucket', 's3:GetBucketLocation',
                   's3:GetObjectVersion', 's3:DeleteObjectVersion'],
            'ec2': ['ec2:DescribeInstances', 'ec2:StartInstances', 'ec2:StopInstances',
                    'ec2:TerminateInstances', 'ec2:CreateSnapshot', 'ec2:DeleteSnapshot'],
            'iam': ['iam:CreateUser', 'iam:DeleteUser', 'iam:AttachUserPolicy',
                    'iam:CreateRole', 'iam:DeleteRole', 'iam:ListUsers']
        }
    
    def extract_policy_components(self, policy: Dict) -> Dict[str, List[str]]:
        """Extract principals, actions, and resources from policy"""
        principals, actions, resources = set(), set(), set()
        
        for statement in policy.get('Statement', []):
            # Extract principals
            principal = statement.get('Principal', [])
            if isinstance(principal, str):
                principals.add(principal)
            elif isinstance(principal, list):
                principals.update(principal)
            elif isinstance(principal, dict):
                for key, values in principal.items():
                    if isinstance(values, list):
                        principals.update(values)
                    else:
                        principals.add(values)
            
            # Extract actions
            action = statement.get('Action', [])
            if isinstance(action, str):
                actions.add(action)
            elif isinstance(action, list):
                actions.update(action)
            
            # Extract resources
            resource = statement.get('Resource', [])  
            if isinstance(resource, str):
                resources.add(resource)
            elif isinstance(resource, list):
                resources.update(resource)
        
        # If no principals found (common in IAM policies), generate defaults
        if not principals:
            principals = {
                'arn:aws:iam::123456789012:user/testuser',
                'arn:aws:iam::123456789012:role/testrole',
                'arn:aws:iam::123456789012:user/adminuser'
            }
        
        return {
            'principals': list(principals),
            'actions': list(actions), 
            'resources': list(resources)
        }
    
    def generate_allow_requests(self, components: Dict[str, List[str]], seed: str) -> List[Dict]:
        """Generate requests that should be allowed by the policy"""
        random.seed(seed)
        requests = []
        
        # Generate valid combinations - now guaranteed to have principals
        for i in range(10):
            if components['actions'] and components['resources']:
                requests.append({
                    'principal': random.choice(components['principals']),
                    'action': random.choice(components['actions']),
                    'resource': random.choice(components['resources'])
                })
        
        return requests[:10]  # Ensure exactly 10
    
    def generate_deny_requests(self, components: Dict[str, List[str]], seed: str) -> List[Dict]:
        """Generate requests that should be denied by the policy"""
        random.seed(seed + "_deny")  # Different seed for deny requests
        requests = []
        
        # Detect primary service
        service = 's3'  # Default to s3
        if components['actions']:
            first_action = components['actions'][0]
            if ':' in first_action:
                service = first_action.split(':')[0]
        
        # Get forbidden actions (actions not in policy)
        all_service_actions = self.aws_actions.get(service, self.aws_actions['s3'])
        forbidden_actions = [a for a in all_service_actions if a not in components['actions']]
        
        # 1. Principal violations (3 requests) - use unauthorized principals
        unauthorized_principals = [
            'arn:aws:iam::999999999999:user/unauthorized',
            'arn:aws:iam::123456789012:user/blocked',
            'arn:aws:iam::123456789012:role/deniedaccess'
        ]
        
        for i in range(3):
            if components['actions'] and components['resources']:
                requests.append({
                    'principal': unauthorized_principals[i % len(unauthorized_principals)],
                    'action': random.choice(components['actions']),
                    'resource': random.choice(components['resources'])
                })
        
        # 2. Action violations (4 requests)
        for i in range(4):
            if forbidden_actions and components['resources']:
                requests.append({
                    'principal': random.choice(components['principals']),
                    'action': random.choice(forbidden_actions),
                    'resource': random.choice(components['resources'])
                })
        
        # 3. Resource violations (3 requests)
        for i in range(3):
            if components['actions']:
                # Modify resource ARN
                if components['resources']:
                    original_resource = random.choice(components['resources'])
                    if 'arn:aws:s3:::' in original_resource:
                        modified_resource = original_resource.replace('my-bucket', 'unauthorized-bucket')
                        if modified_resource == original_resource:  # If no replacement happened
                            modified_resource = original_resource.replace('bucket', 'forbidden-bucket')
                    elif 'arn:aws:ec2:' in original_resource:
                        # For EC2 resources, change instance ID
                        modified_resource = original_resource.replace('instance/', 'instance/i-unauthorized')
                    else:
                        modified_resource = original_resource + '-denied'
                else:
                    # If no resources in policy, use generic unauthorized resource
                    modified_resource = 'arn:aws:' + service + ':::unauthorized-resource'
                
                requests.append({
                    'principal': random.choice(components['principals']),
                    'action': random.choice(components['actions']),
                    'resource': modified_resource
                })
        
        return requests[:10]  # Ensure exactly 10
    
    def generate_test_requests(self, policy: Dict, policy_file: str) -> Tuple[List[Dict], List[Dict]]:
        """Generate both allow and deny test requests"""
        components = self.extract_policy_components(policy)
        seed = hashlib.md5(policy_file.encode()).hexdigest()[:8]
        
        allow_requests = self.generate_allow_requests(components, seed)
        deny_requests = self.generate_deny_requests(components, seed)
        
        return allow_requests, deny_requests

class QuackyRunner:
    """Interface to run Quacky for policy comparison"""
    
    def __init__(self, config: ExperimentConfig):
        self.quacky_py_path = config.quacky_py_path
        self.quacky_base_path = config.quacky_base_path
        self.batch_size = config.batch_size
    
    def compare_policies(self, policy1_path: str, policy2_path: str) -> Dict[str, Any]:
        """Compare two policies using Quacky"""
        try:
            # Use absolute paths so Quacky can open files regardless of cwd
            abs_p1 = str(Path(policy1_path).resolve())
            abs_p2 = str(Path(policy2_path).resolve())
            command = [
                "python3", self.quacky_py_path,
                "-p1", abs_p1,
                "-p2", abs_p2,
                "-b", self.batch_size
            ]
            
            result = subprocess.run(
                command,
                cwd=self.quacky_base_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                # Parse Quacky output to extract semantic equivalence info
                output = result.stdout
                return {
                    'semantic_equivalent': 'equivalent' in output.lower(),
                    'quacky_output': output.strip(),
                    'exit_code': result.returncode
                }
            else:
                return {
                    'semantic_equivalent': False,
                    'quacky_output': result.stderr or f"Failed with code {result.returncode}",
                    'exit_code': result.returncode
                }
                
        except Exception as e:
            return {
                'semantic_equivalent': False,
                'quacky_output': f"Error running Quacky: {str(e)}",
                'exit_code': -1
            }

class ExperimentRunner:
    """Main experiment runner implementing the 7-step workflow"""
    
    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.llm_client = LLMClient()
        self.request_generator = RequestGenerator()
        self.quacky_runner = QuackyRunner(config)
        
        # Create output directory
        Path(config.output_dir).mkdir(exist_ok=True)
        
        # LLM models to test
        self.models = [
            "grok-3",
            "claude-3.7-sonnet", 
            "claude-3.5-sonnet",
            "o4-mini",
            "gpt-4.1-nano",
            "deepseek-chat",
            "gemini-2.5-flash"
        ]
    
    def load_checkpoint(self, model: str) -> Dict[str, Any]:
        """Load checkpoint for a specific model to resume from where we left off"""
        if self.config.run_from_scratch:
            print(f"🔄 Running from scratch for {model} (ignoring checkpoints)")
            return {'completed': [], 'results': []}
            
        checkpoint_file = f"experiment_checkpoint_{model}.json"
        checkpoint_path = Path(self.config.output_dir) / checkpoint_file
        if checkpoint_path.exists():
            with open(checkpoint_path, 'r') as f:
                checkpoint = json.load(f)
                print(f"📂 Loaded checkpoint for {model}: {len(checkpoint.get('completed', []))} experiments completed")
                return checkpoint
        else:
            print(f"📝 No checkpoint found for {model}, starting fresh")
            return {'completed': [], 'results': []}
    
    def save_checkpoint(self, model: str, checkpoint_data: Dict[str, Any]):
        """Save checkpoint for a specific model"""
        checkpoint_file = f"experiment_checkpoint_{model}.json"
        checkpoint_path = Path(self.config.output_dir) / checkpoint_file
        with open(checkpoint_path, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""
        embeddings = self.llm_client.sentence_model.encode([text1, text2])
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return float(similarity)
    
    def run_single_experiment(self, policy_file: str, model: str) -> PolicyResult:
        """Run the 7-step experiment for a single policy-model combination"""
        
        try:
            # Load policy
            policy_path = Path(self.config.policy_dir) / policy_file
            with open(policy_path, 'r') as f:
                policy = json.load(f)
            
            policy_json_str = json.dumps(policy, indent=2)
            
            results = {}
            
            # Step 1: Original Explanation Generation
            explanation_prompt = f"""
            Please provide a clear, comprehensive natural language explanation of what this AWS IAM policy allows or denies in a manner that allows the reconstruction of this policy.
            Don't respond with your thought process at all. Make sure you only respond with the relevant explanation and nothing else. And make sure that the explanation is still in natural language otherwise it kinda defeats the purpose.

            Policy:
            {policy_json_str}
            """
            
            original_explanation = self.llm_client.call_llm(model, explanation_prompt)
            results['original_explanation'] = original_explanation
            
            # Step 2: Request Outcome Prediction
            allow_requests, deny_requests = self.request_generator.generate_test_requests(policy, policy_file)
            all_requests = allow_requests + deny_requests
            expected_outcomes = ['Allow'] * 10 + ['Deny'] * 10
            
            prediction_prompt = f"""
            Given this AWS IAM policy:
            {policy_json_str}
            
            For each of the following requests, predict whether the policy would Allow or Deny access.
            Respond with exactly one word per line: either "Allow" or "Deny".
            
            Requests:
            """
            
            for i, req in enumerate(all_requests, 1):
                prediction_prompt += f"{i}. Principal: {req['principal']}, Action: {req['action']}, Resource: {req['resource']}\n"
            
            predictions_response = self.llm_client.call_llm(model, prediction_prompt)
            
            # Parse predictions
            predicted_outcomes = []
            for line in predictions_response.split('\n'):
                line = line.strip()
                if 'allow' in line.lower():
                    predicted_outcomes.append('Allow')
                elif 'deny' in line.lower():
                    predicted_outcomes.append('Deny')
            
            # Calculate accuracy
            correct_predictions = sum(1 for pred, exp in zip(predicted_outcomes, expected_outcomes) if pred == exp)
            request_accuracy = correct_predictions / len(expected_outcomes) if expected_outcomes else 0
            
            results['request_predictions'] = {
                'requests': all_requests,
                'expected': expected_outcomes,
                'predicted': predicted_outcomes,
                'accuracy': request_accuracy
            }
            
            # Step 3: Policy Reconstruction
            reconstruction_prompt = f"""
            Based on this explanation, generate a complete AWS IAM policy in JSON format.
            Only output valid JSON, no other text.
            
            Explanation:
            {original_explanation}
            """
            
            reconstructed_policy_str = self.llm_client.call_llm(model, reconstruction_prompt)
            
            # Create paths for reconstructed policy and raw response
            temp_reconstructed_path = Path(self.config.output_dir) / f"reconstructed_{model}_{policy_file}"
            raw_response_path = Path(self.config.output_dir) / f"raw_response_{model}_{policy_file}.txt"
            
            # Save the raw response
            with open(raw_response_path, 'w') as f:
                f.write(reconstructed_policy_str)
            
            # Try to parse reconstructed policy
            try:
                # Check if the response is wrapped in markdown code blocks
                policy_to_parse = reconstructed_policy_str
                if policy_to_parse.strip().startswith("```"):
                    # Extract content between code fences
                    lines = policy_to_parse.strip().split('\n')
                    if lines and lines[0].startswith("```"):
                        lines = lines[1:]  # Remove opening fence
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]  # Remove closing fence
                    policy_to_parse = '\n'.join(lines)
                    
                    # If a language specifier was included (like ```json), remove it
                    if policy_to_parse.strip().startswith("json"):
                        policy_to_parse = policy_to_parse.strip()[4:].strip()
                        
                # Save the processed content for debugging
                processed_response_path = Path(self.config.output_dir) / f"processed_response_{model}_{policy_file}.txt"
                with open(processed_response_path, 'w') as f:
                    f.write(policy_to_parse)
                
                reconstructed_policy = json.loads(policy_to_parse)
                results['reconstructed_policy'] = reconstructed_policy
                
                # Save reconstructed policy to file for Quacky comparison
                with open(temp_reconstructed_path, 'w') as f:
                    json.dump(reconstructed_policy, f, indent=2)
                
                # Verify file was created successfully
                if temp_reconstructed_path.exists():
                    # Step 5: Semantic Equivalence Check (using Quacky)
                    quacky_result = self.quacky_runner.compare_policies(str(policy_path), str(temp_reconstructed_path))
                    results['semantic_equivalence'] = quacky_result
                else:
                    results['semantic_equivalence'] = {
                        'semantic_equivalent': False,
                        'quacky_output': f'Failed to create temp file: {temp_reconstructed_path}',
                        'exit_code': -1
                    }
                
                # Keep the temp files instead of deleting them
                # temp_reconstructed_path.unlink(missing_ok=True)
                
            except json.JSONDecodeError as e:
                results['reconstructed_policy'] = None
                results['semantic_equivalence'] = {
                    'semantic_equivalent': False,
                    'quacky_output': f'Failed to parse reconstructed policy JSON: {str(e)}',
                    'exit_code': -1
                }
            
            # Step 4: Reconstructed Explanation Generation
            if results.get('reconstructed_policy'):
                recon_explanation_prompt = f"""
                Please provide a clear, comprehensive natural language explanation of what this AWS IAM policy allows or denies in a manner that allows the reconstruction of this policy.
                Don't respond with your thought process at all. Make sure you only respond with the relevant explanation and nothing else. And make sure that the explanation is still in natural language otherwise it kinda defeats the purpose.
                
                Policy:
                {json.dumps(results['reconstructed_policy'], indent=2)}
                """
                
                reconstructed_explanation = self.llm_client.call_llm(model, recon_explanation_prompt)
                results['reconstructed_explanation'] = reconstructed_explanation
                
                # Step 6: Explanation Consistency Analysis
                consistency_score = self.calculate_similarity(original_explanation, reconstructed_explanation)
                results['explanation_consistency'] = consistency_score
            else:
                results['reconstructed_explanation'] = None
                results['explanation_consistency'] = 0.0
            
            return PolicyResult(
                policy_file=policy_file,
                llm_model=model,
                timestamp=datetime.now().isoformat(),
                results=results
            )
            
        except Exception as e:
            return PolicyResult(
                policy_file=policy_file,
                llm_model=model,
                timestamp=datetime.now().isoformat(),
                results={},
                error=str(e)
            )
    
    def run_experiment(self):
        """Run the complete experiment for all policies and models"""
        # Get all policy files
        policy_files = [f for f in os.listdir(self.config.policy_dir) if f.endswith('.json')]
        policy_files.sort()
        
        print(f"Found {len(policy_files)} policy files")
        print(f"Testing {len(self.models)} LLM models")
        print(f"Total experiments: {len(policy_files) * len(self.models)}")
        
        # Collect all results from all models
        all_model_results = []
        
        # Run experiments
        for model in self.models:
            print(f"\n{'='*60}")
            print(f"Processing model: {model}")
            print(f"{'='*60}")
            
            # Load checkpoint for this model
            checkpoint = self.load_checkpoint(model)
            completed_experiments = set(checkpoint['completed'])
            model_results = checkpoint['results']
            
            model_progress = tqdm(policy_files, desc=f"{model} policies")
            
            for policy_file in model_progress:
                experiment_id = f"{model}::{policy_file}"
                
                # Skip if already completed
                if experiment_id in completed_experiments:
                    model_progress.set_postfix(status="SKIPPED")
                    continue
                
                model_progress.set_postfix(status="RUNNING")
                
                # Run single experiment
                result = self.run_single_experiment(policy_file, model)
                
                # Add to results
                model_results.append(result.__dict__)
                completed_experiments.add(experiment_id)
                
                # Update checkpoint for this model
                checkpoint['completed'] = list(completed_experiments)
                checkpoint['results'] = model_results
                self.save_checkpoint(model, checkpoint)
                
                if result.error:
                    model_progress.set_postfix(status=f"ERROR: {result.error[:30]}")
                else:
                    accuracy = result.results.get('request_predictions', {}).get('accuracy', 0)
                    model_progress.set_postfix(status=f"OK (acc: {accuracy:.2f})")
            
            # Add this model's results to the global collection
            all_model_results.extend(model_results)
            print(f"✅ {model} complete: {len(model_results)} experiments")
        
        # Save combined final results
        results_path = Path(self.config.output_dir) / self.config.results_file
        with open(results_path, 'w') as f:
            json.dump(all_model_results, f, indent=2)
        
        print(f"\n🎉 Experiment complete! Results saved to: {results_path}")
        print(f"Total experiments completed: {len(all_model_results)}")
        print(f"📁 Individual checkpoints saved as: experiment_checkpoint_{{model}}.json")

def main():
    """Main function to run the experiment"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Comprehensive Policy Comprehension Assessment')
    parser.add_argument('--from-scratch', action='store_true', 
                       help='Run all experiments from scratch, ignoring existing checkpoints')
    parser.add_argument('--models', nargs='+', 
                       choices=['grok-3', 'claude-3.7-sonnet', 'claude-3.5-sonnet', 'o4-mini', 'gpt-4.1-nano', 'deepseek-chat', 'gemini-2.5-flash'],
                       help='Specify which models to run (default: all models)')
    parser.add_argument('--policy-dir', type=str,
                       help='Override the policy directory path')
    parser.add_argument('--output-dir', type=str, default='experiment_results',
                       help='Output directory for results and checkpoints')
    
    args = parser.parse_args()
    
    # Configuration - UPDATE THESE PATHS
    config = ExperimentConfig(
        policy_dir=args.policy_dir or "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/Prev-Experiments/Verifying-LLMAccessControl/Dataset",
        quacky_base_path="/home/ash/Documents/Verifying-LLMAccessControl/Exp-1/quacky/src",
        quacky_py_path="/home/ash/Documents/Verifying-LLMAccessControl/Exp-1/quacky/src/quacky.py",
        output_dir=args.output_dir,
        run_from_scratch=args.from_scratch
    )
    
    # Validate paths
    if not Path(config.policy_dir).exists():
        print(f"❌ Policy directory not found: {config.policy_dir}")
        print("Please update the policy_dir in the config or use --policy-dir")
        return
    
    if not Path(config.quacky_py_path).exists():
        print(f"❌ Quacky script not found: {config.quacky_py_path}")
        print("Please update the quacky_py_path in the config")
        return
    
    # Check API keys
    required_keys = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY', 'GROK_API_KEY', 'DEEPSEEK_API_KEY']
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    
    if missing_keys:
        print(f"❌ Missing API keys: {missing_keys}")
        print("Please add them to your .env file")
        return
    
    print("🚀 Starting Experiment 0: Policy Comprehension Assessment")
    print(f"Policy directory: {config.policy_dir}")
    print(f"Output directory: {config.output_dir}")
    if config.run_from_scratch:
        print("🔄 Running from scratch (ignoring checkpoints)")
    
    # Run experiment
    runner = ExperimentRunner(config)
    
    # Override models if specified
    if args.models:
        runner.models = args.models
        print(f"🎯 Running selected models: {args.models}")
    
    runner.run_experiment()

if __name__ == "__main__":
    main()