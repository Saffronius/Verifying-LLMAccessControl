"""
Policy Generator - Generate AWS IAM policies from natural language descriptions
"""
import json
import os
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class PolicyGenerator:
    def __init__(self, use_reasoning=True, model_preference="best"):
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.default_model = os.getenv("DEFAULT_MODEL", "claude-3-sonnet")
        self.use_reasoning = use_reasoning
        
        # Initialize the appropriate client based on available keys
        self.client = None
        self.model = None
        
        # Model options with latest 2025 models
        self.model_options = {
            "anthropic": {
                "best": "claude-opus-4.1-20250805",  # Claude Opus 4.1 - Best for coding and complex tasks
                "reasoning": "claude-sonnet-4-20250523",  # Claude Sonnet 4 with hybrid reasoning
                "fast": "claude-3.7-sonnet-20250224",  # Claude 3.7 Sonnet - Good balance
                "legacy": "claude-3-5-sonnet-20241022"
            },
            "openai": {
                "best": "gpt-5",  # GPT-5 - 94.6% AIME 2025, 74.9% SWE-bench, unified system
                "reasoning": "o3-pro",  # O3-Pro - Most intelligent reasoning model
                "fast": "gpt-5-mini",  # GPT-5 mini - Fast, efficient, available to all
                "ultra-fast": "gpt-5-nano",  # GPT-5 nano - Cheapest and fastest
                "legacy": "o4-mini"
            }
        }
        
        if self.anthropic_key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.anthropic_key)
                # Try to use the preferred model, fallback to best
                if model_preference in self.model_options["anthropic"]:
                    self.model = self.model_options["anthropic"][model_preference]
                else:
                    self.model = self.model_options["anthropic"]["best"]
                self.provider = "anthropic"
            except ImportError:
                pass
        
        if not self.client and self.openai_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.openai_key)
                # Try to use the preferred model, fallback to best
                if model_preference in self.model_options["openai"]:
                    self.model = self.model_options["openai"][model_preference]
                else:
                    self.model = self.model_options["openai"]["best"]
                self.provider = "openai"
            except ImportError:
                pass
    
    def generate_policy_from_nl(self, description: str) -> Dict:
        """
        Generate an AWS IAM policy from a natural language description
        """
        if not self.client:
            return {
                "success": False,
                "error": "No LLM API key configured. Please set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env file",
                "policy": None
            }
        
        prompt = f"""Generate a complete AWS IAM policy in JSON format based on this description:

{description}

Requirements:
1. Output ONLY valid JSON - no markdown, no explanations
2. Follow AWS IAM policy schema exactly
3. Include "Version": "2012-10-17"
4. Include proper "Statement" array with Effect, Action, Resource fields
5. Be specific about actions and resources based on the description

Output the JSON policy only:"""
        
        try:
            if self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )
                policy_text = response.content[0].text.strip()
            else:  # OpenAI
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an AWS IAM policy expert. Generate only valid JSON policies."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )
                policy_text = response.choices[0].message.content.strip()
            
            # Clean up the response (remove markdown if present)
            policy_text = self._clean_json_response(policy_text)
            
            # Validate JSON
            policy_json = json.loads(policy_text)
            
            # Validate AWS policy structure
            if not self._validate_aws_policy_structure(policy_json):
                return {
                    "success": False,
                    "error": "Generated policy does not have valid AWS IAM structure",
                    "policy": policy_text
                }
            
            return {
                "success": True,
                "policy": json.dumps(policy_json, indent=2),
                "policy_json": policy_json,
                "model_used": self.model
            }
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Generated policy is not valid JSON: {str(e)}",
                "policy": policy_text if 'policy_text' in locals() else None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error generating policy: {str(e)}",
                "policy": None
            }
    
    def explain_policy(self, policy: str) -> Dict:
        """
        Generate a natural language explanation of an AWS IAM policy
        """
        if not self.client:
            return {
                "success": False,
                "error": "No LLM API key configured",
                "explanation": None
            }
        
        prompt = f"""Explain this AWS IAM policy in simple, clear language. 
Describe what permissions it grants and any conditions or restrictions:

{policy}

Provide a concise explanation:"""
        
        try:
            if self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1000,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )
                explanation = response.content[0].text.strip()
            else:  # OpenAI
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )
                explanation = response.choices[0].message.content.strip()
            
            return {
                "success": True,
                "explanation": explanation
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "explanation": None
            }
    
    def _clean_json_response(self, text: str) -> str:
        """Remove markdown code blocks if present"""
        # Remove ```json and ``` markers
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        
        if text.endswith("```"):
            text = text[:-3]
        
        return text.strip()
    
    def _validate_aws_policy_structure(self, policy: Dict) -> bool:
        """Validate that the policy has proper AWS IAM structure"""
        # Check for required top-level fields
        if "Statement" not in policy:
            return False
        
        if not isinstance(policy["Statement"], list):
            return False
        
        # Check each statement
        for statement in policy["Statement"]:
            if "Effect" not in statement:
                return False
            if statement["Effect"] not in ["Allow", "Deny"]:
                return False
            if "Action" not in statement and "NotAction" not in statement:
                return False
            if "Resource" not in statement and "NotResource" not in statement:
                return False
        
        return True