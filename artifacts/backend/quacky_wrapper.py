"""
Wrapper for Quacky tool - provides Python interface to quacky commands
"""
import subprocess
import json
import os
import re
import tempfile
import time
import hashlib
from pathlib import Path
from typing import Dict, Optional, Tuple, List

# Path to quacky executable - auto-detect based on environment
def get_quacky_paths():
    """Detect quacky path based on environment (Docker or local)"""
    # Check if running in Docker
    if os.environ.get('QUACKY_DOCKER') == '1':
        quacky_path = os.environ.get('QUACKY_PATH', '/opt/VerifyingLLMGeneratedPolicies/CPCA/quacky/src/quacky.py')
        working_dir = os.path.dirname(quacky_path)
    else:
        # Local development paths
        quacky_path = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/CPCA/quacky/src/quacky.py"
        working_dir = "/home/ash/Desktop/VerifyingLLMGeneratedPolicies/CPCA/quacky/src"
    
    # Verify quacky exists
    if not os.path.exists(quacky_path):
        # Try alternative paths
        alt_paths = [
            "/opt/quacky/src/quacky.py",
            "./quacky/src/quacky.py",
            "../CPCA/quacky/src/quacky.py",
            "../../CPCA/quacky/src/quacky.py",
        ]
        for alt in alt_paths:
            if os.path.exists(alt):
                quacky_path = os.path.abspath(alt)
                working_dir = os.path.dirname(quacky_path)
                break
    
    return quacky_path, working_dir

QUACKY_PATH, QUACKY_WORKING_DIR = get_quacky_paths()

class QuackyWrapper:
    def __init__(self, debug=False):
        self.quacky_path, self.working_dir = get_quacky_paths()
        self.temp_dir = tempfile.mkdtemp(prefix="quacky_artifact_")
        self.debug = debug
        self.execution_log = []
        
    def validate_policy(self, policy_content: str) -> Tuple[bool, str]:
        """Validate if the policy is valid JSON and has required structure"""
        try:
            policy = json.loads(policy_content)
            if "Statement" not in policy:
                return False, "Policy must contain 'Statement' field"
            return True, "Valid policy"
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}"
    
    def save_policy_to_file(self, policy_content: str, filename: str) -> str:
        """Save policy to a temporary file and return the path"""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w') as f:
            if isinstance(policy_content, dict):
                json.dump(policy_content, f, indent=2)
            else:
                f.write(policy_content)
        return filepath
    
    def compare_policies(self, policy1: str, policy2: str, bound: int = 100) -> Dict:
        """
        Compare two policies using quacky
        Returns analysis results including satisfiability and model counts
        """
        # Save policies to temp files
        p1_path = self.save_policy_to_file(policy1, "policy1.json")
        p2_path = self.save_policy_to_file(policy2, "policy2.json")
        
        # Run quacky comparison
        cmd = [
            "python3", self.quacky_path,
            "-p1", p1_path,
            "-p2", p2_path,
            "-b", str(bound)
        ]
        
        # Log execution details
        execution_id = hashlib.md5(f"{time.time()}{policy1}{policy2}".encode()).hexdigest()[:8]
        start_time = time.time()
        
        if self.debug:
            print(f"[DEBUG] Executing quacky comparison (ID: {execution_id})")
            print(f"[DEBUG] Command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            execution_time = time.time() - start_time
            
            # Parse output
            output = result.stdout
            error = result.stderr
            
            # Log execution
            self.execution_log.append({
                "id": execution_id,
                "operation": "compare_policies",
                "time": execution_time,
                "command": " ".join(cmd),
                "success": result.returncode == 0
            })
            
            if self.debug:
                print(f"[DEBUG] Execution completed in {execution_time:.3f}s")
                print(f"[DEBUG] Output length: {len(output)} chars")
            
            # Extract key metrics from output
            metrics = self._parse_quacky_output(output)
            
            return {
                "success": result.returncode == 0,
                "output": output,
                "error": error,
                "metrics": metrics,
                "command": " ".join(cmd)
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Quacky execution timed out after 60 seconds",
                "metrics": {}
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "metrics": {}
            }
    
    def generate_strings(self, policy1: str, policy2: Optional[str] = None, 
                        count: int = 10, min_range: int = 1, max_range: int = 10) -> Dict:
        """
        Generate example strings that differentiate between policies
        Returns P1_not_P2 and not_P1_P2 model strings
        """
        p1_path = self.save_policy_to_file(policy1, "policy1.json")
        
        cmd = [
            "python3", self.quacky_path,
            "-p1", p1_path,
            "-b", "100",
            "-m", str(count),
            "--minrange", str(min_range),
            "--maxrange", str(max_range)
        ]
        
        if policy2:
            p2_path = self.save_policy_to_file(policy2, "policy2.json")
            cmd.extend(["-p2", p2_path])
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Read generated model files
            p1_not_p2_path = os.path.join(self.working_dir, "P1_not_P2.models")
            not_p1_p2_path = os.path.join(self.working_dir, "not_P1_P2.models")
            
            p1_not_p2_strings = []
            not_p1_p2_strings = []
            
            if os.path.exists(p1_not_p2_path):
                with open(p1_not_p2_path, 'r') as f:
                    p1_not_p2_strings = f.read().strip().split('\n')
            
            if os.path.exists(not_p1_p2_path):
                with open(not_p1_p2_path, 'r') as f:
                    not_p1_p2_strings = f.read().strip().split('\n')
            
            return {
                "success": result.returncode == 0,
                "p1_not_p2": p1_not_p2_strings,
                "not_p1_p2": not_p1_p2_strings,
                "output": result.stdout,
                "error": result.stderr
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "p1_not_p2": [],
                "not_p1_p2": []
            }
    
    def validate_regex(self, policy: str, regex_pattern: str, bound: int = 100) -> Dict:
        """
        Validate a regex pattern against a policy
        Returns coverage metrics and automata-generated regex
        """
        p_path = self.save_policy_to_file(policy, "policy.json")
        
        # Save regex to file
        regex_path = os.path.join(self.temp_dir, "regex.txt")
        with open(regex_path, 'w') as f:
            f.write(regex_pattern)
        
        cmd = [
            "python3", self.quacky_path,
            "-p1", p_path,
            "-b", str(bound),
            "-cr", regex_path,
            "-pr"  # Add flag to print regex from DFA
        ]
        
        # Log execution details
        execution_id = hashlib.md5(f"{time.time()}{policy}{regex_pattern}".encode()).hexdigest()[:8]
        start_time = time.time()
        
        if self.debug:
            print(f"[DEBUG] Executing regex validation (ID: {execution_id})")
            print(f"[DEBUG] Command: {' '.join(cmd)}")
            print(f"[DEBUG] Regex pattern: {regex_pattern[:50]}...")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            execution_time = time.time() - start_time
            
            # Log execution
            self.execution_log.append({
                "id": execution_id,
                "operation": "validate_regex",
                "time": execution_time,
                "command": " ".join(cmd),
                "success": result.returncode == 0
            })
            
            if self.debug:
                print(f"[DEBUG] Execution completed in {execution_time:.3f}s")
                print(f"[DEBUG] Output length: {len(result.stdout)} chars")
            
            # Parse validation results with enhanced metrics
            metrics = self._parse_regex_validation_enhanced(result.stdout)
            
            return {
                "success": result.returncode == 0,
                "metrics": metrics,
                "output": result.stdout,
                "error": result.stderr
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "metrics": {}
            }
    
    def _parse_quacky_output(self, output: str) -> Dict:
        """Parse quacky output to extract metrics"""
        metrics = {}
        
        # Extract satisfiability
        if "satisfiability:" in output:
            sat_match = re.search(r"satisfiability:\s+(\w+)", output)
            if sat_match:
                metrics["satisfiability"] = sat_match.group(1)
        
        # Extract solve time
        if "Solve Time (ms):" in output:
            time_match = re.search(r"Solve Time \(ms\):\s+([\d.]+)", output)
            if time_match:
                metrics["solve_time_ms"] = float(time_match.group(1))
        
        # Extract log of requests
        if "lg(requests):" in output:
            lg_match = re.search(r"lg\(requests\):\s+([\d.]+)", output)
            if lg_match:
                metrics["log_requests"] = float(lg_match.group(1))
        
        # Extract count time
        if "Count Time (ms):" in output:
            count_match = re.search(r"Count Time \(ms\):\s+([\d.]+)", output)
            if count_match:
                metrics["count_time_ms"] = float(count_match.group(1))
        
        return metrics
    
    def _parse_regex_validation(self, output: str) -> Dict:
        """Parse regex validation output"""
        metrics = {}
        
        # Extract baseline regex count
        if "Baseline Regex Count" in output:
            count_match = re.search(r"Baseline Regex Count\s*:\s*([\d\w]+)", output)
            if count_match:
                metrics["regex_count"] = count_match.group(1)
        
        # Extract ABC command used
        if "abc -bs" in output:
            abc_match = re.search(r"(abc -bs.*)", output)
            if abc_match:
                metrics["abc_command"] = abc_match.group(1)
        
        return metrics
    
    def _parse_regex_validation_enhanced(self, output: str) -> Dict:
        """Parse enhanced regex validation output including DFA regex and similarity metrics"""
        metrics = {}
        
        # Extract baseline regex count
        if "Baseline Regex Count" in output:
            count_match = re.search(r"Baseline Regex Count\s*:\s*([\d\w]+)", output)
            if count_match:
                metrics["baseline_regex"] = count_match.group(1)
        
        # Extract synthesized regex count
        if "Synthesized Regex Count" in output:
            count_match = re.search(r"Synthesized Regex Count\s*:\s*([\d\w]+)", output)
            if count_match:
                metrics["synthesized_regex"] = count_match.group(1)
        
        # Extract regex from DFA (non-simplified)
        if "regex_from_dfa" in output:
            dfa_match = re.search(r"regex_from_dfa\s*:\s*(.+?)(?:\n|$)", output)
            if dfa_match:
                metrics["regex_from_dfa"] = dfa_match.group(1).strip()
        
        # Extract regex from LLM (simplified)
        if "regex_from_llm" in output:
            llm_match = re.search(r"regex_from_llm\s*:\s*(.+?)(?:\n|$)", output)
            if llm_match:
                metrics["regex_from_llm"] = llm_match.group(1).strip()
        
        # Extract operation counts
        if "ops_regex_from_dfa" in output:
            ops_dfa_match = re.search(r"ops_regex_from_dfa\s*:\s*(\d+)", output)
            if ops_dfa_match:
                metrics["ops_regex_from_dfa"] = int(ops_dfa_match.group(1))
        
        if "ops_regex_from_llm" in output:
            ops_llm_match = re.search(r"ops_regex_from_llm\s*:\s*(\d+)", output)
            if ops_llm_match:
                metrics["ops_regex_from_llm"] = int(ops_llm_match.group(1))
        
        # Extract length metrics
        if "length_regex_from_dfa" in output:
            len_dfa_match = re.search(r"length_regex_from_dfa\s*:\s*(\d+)", output)
            if len_dfa_match:
                metrics["length_regex_from_dfa"] = int(len_dfa_match.group(1))
        
        if "length_regex_from_llm" in output:
            len_llm_match = re.search(r"length_regex_from_llm\s*:\s*(\d+)", output)
            if len_llm_match:
                metrics["length_regex_from_llm"] = int(len_llm_match.group(1))
        
        # Extract Jaccard similarity metrics
        if "jaccard_numerator" in output:
            num_match = re.search(r"jaccard_numerator\s*:\s*(\d+)", output)
            if num_match:
                metrics["jaccard_numerator"] = int(num_match.group(1))
        
        if "jaccard_denominator" in output:
            denom_match = re.search(r"jaccard_denominator\s*:\s*(\d+)", output)
            if denom_match:
                metrics["jaccard_denominator"] = int(denom_match.group(1))
        
        # Calculate similarity if we have both numerator and denominator
        if "jaccard_numerator" in metrics and "jaccard_denominator" in metrics:
            if metrics["jaccard_denominator"] > 0:
                metrics["jaccard_similarity"] = round(
                    metrics["jaccard_numerator"] / metrics["jaccard_denominator"], 4
                )
            else:
                metrics["jaccard_similarity"] = 0.0
        
        # Calculate simplification metrics
        if "length_regex_from_dfa" in metrics and "length_regex_from_llm" in metrics:
            if metrics["length_regex_from_dfa"] > 0:
                metrics["length_reduction_pct"] = round(
                    (1 - metrics["length_regex_from_llm"] / metrics["length_regex_from_dfa"]) * 100, 2
                )
        
        if "ops_regex_from_dfa" in metrics and "ops_regex_from_llm" in metrics:
            if metrics["ops_regex_from_dfa"] > 0:
                metrics["ops_reduction_pct"] = round(
                    (1 - metrics["ops_regex_from_llm"] / metrics["ops_regex_from_dfa"]) * 100, 2
                )
        
        # Extract ABC command used
        if "abc -bs" in output:
            abc_match = re.search(r"(abc -bs.*)", output)
            if abc_match:
                metrics["abc_command"] = abc_match.group(1)
        
        return metrics
    
    def get_execution_history(self):
        """Get the history of quacky executions"""
        return self.execution_log
    
    def cleanup(self):
        """Clean up temporary files"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)