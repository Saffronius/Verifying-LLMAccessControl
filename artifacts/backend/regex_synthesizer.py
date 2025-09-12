"""
Regex Synthesizer - Generate regex patterns from example strings using LLMs
"""
import os
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RegexSynthesizer:
    def __init__(self, use_reasoning=True, model_preference="best"):
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.use_reasoning = use_reasoning
        
        # Initialize the appropriate client based on available keys
        self.client = None
        self.model = None
        
        # Model options with latest 2025 models optimized for pattern recognition
        self.model_options = {
            "anthropic": {
                "best": "claude-opus-4.1-20250805",  # Claude Opus 4.1 - 72.5% on SWE-bench
                "reasoning": "claude-sonnet-4-20250523",  # Claude Sonnet 4 - Hybrid reasoning with tool use
                "fast": "claude-3.7-sonnet-20250224",  # Claude 3.7 - Step-by-step reasoning
                "legacy": "claude-3-5-sonnet-20241022"
            },
            "openai": {
                "best": "gpt-5",  # GPT-5 - 74.9% SWE-bench, 94.6% AIME, unified system
                "reasoning": "o3-pro",  # O3-Pro - Deep reasoning for complex patterns
                "fast": "gpt-5-mini",  # GPT-5 mini - Efficient pattern matching
                "ultra-fast": "gpt-5-nano",  # GPT-5 nano - Fastest for simple patterns
                "legacy": "o4-mini"
            }
        }
        
        if self.anthropic_key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.anthropic_key)
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
                # For regex tasks, prefer reasoning model if available
                if self.use_reasoning and "reasoning" in self.model_options["openai"]:
                    self.model = self.model_options["openai"]["reasoning"]
                elif model_preference in self.model_options["openai"]:
                    self.model = self.model_options["openai"][model_preference]
                else:
                    self.model = self.model_options["openai"]["best"]
                self.provider = "openai"
            except ImportError:
                pass
    
    def synthesize_regex(self, example_strings: List[str]) -> Dict:
        """
        Synthesize a regex pattern that matches all provided example strings
        """
        if not self.client:
            return {
                "success": False,
                "error": "No LLM API key configured",
                "regex": None
            }
        
        if not example_strings:
            return {
                "success": False,
                "error": "No example strings provided",
                "regex": None
            }
        
        # Format strings for prompt - use up to 500 strings for better pattern detection
        max_strings_for_synthesis = 500
        strings_to_use = example_strings[:max_strings_for_synthesis]
        strings_text = "\n".join(strings_to_use)
        
        # Use reasoning-enhanced prompt for complex pattern synthesis
        if self.use_reasoning and len(strings_to_use) > 50:
            prompt = f"""Analyze these {len(strings_to_use)} example strings to identify common patterns and synthesize a precise regular expression.

Step 1: Identify common patterns in the strings (prefixes, suffixes, character sets, repetitions)
Step 2: Determine the minimal regex that matches ALL examples
Step 3: Optimize the regex for readability and efficiency

IMPORTANT: After your analysis, output ONLY the final regex pattern on the last line, with no quotes or markdown.

Example strings:
{strings_text}

Analyze the patterns and provide the regex:"""
        else:
            prompt = f"""Generate a single regular expression that matches ALL of the following strings exactly.
The regex should be as specific as possible while matching all examples.

IMPORTANT: Return ONLY the regex pattern itself, with no explanation, no markdown, no quotes.

Example strings ({len(strings_to_use)} strings):
{strings_text}

Regex pattern:"""
        
        try:
            if self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=500,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2
                )
                regex_pattern = response.content[0].text.strip()
            else:  # OpenAI
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a regex expert. Generate only the regex pattern, no explanations."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2
                )
                regex_pattern = response.choices[0].message.content.strip()
            
            # For reasoning models, extract the final regex from the response
            if self.use_reasoning and len(strings_to_use) > 50:
                # Extract the last non-empty line which should be the regex
                lines = regex_pattern.strip().split('\n')
                regex_pattern = lines[-1].strip() if lines else regex_pattern
            
            # Clean up the regex (remove quotes if present)
            regex_pattern = regex_pattern.strip('"\'`')
            
            return {
                "success": True,
                "regex": regex_pattern,
                "model_used": self.model,
                "num_examples": len(example_strings),
                "num_used_for_synthesis": len(strings_to_use),
                "used_reasoning": self.use_reasoning and len(strings_to_use) > 50
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "regex": None
            }
    
    def explain_regex(self, regex_pattern: str) -> Dict:
        """
        Generate a human-readable explanation of a regex pattern
        """
        if not self.client:
            return {
                "success": False,
                "error": "No LLM API key configured",
                "explanation": None
            }
        
        prompt = f"""Explain this regular expression in simple terms. 
Describe what it matches and any special patterns or constraints.

Regex: {regex_pattern}

Provide a clear, concise explanation:"""
        
        try:
            if self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=500,
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
    
    def optimize_regex(self, regex_pattern: str, example_strings: List[str]) -> Dict:
        """
        Optimize a regex pattern to be more efficient or readable
        """
        if not self.client:
            return {
                "success": False,
                "error": "No LLM API key configured",
                "optimized": None
            }
        
        # Use more strings for optimization context
        max_strings_for_optimization = 100
        strings_sample = "\n".join(example_strings[:max_strings_for_optimization])
        
        prompt = f"""Optimize this regex pattern to be more efficient and readable while still matching the same strings.

Current regex: {regex_pattern}

Sample strings it should match:
{strings_sample}

Return ONLY the optimized regex pattern:"""
        
        try:
            if self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=500,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2
                )
                optimized = response.content[0].text.strip()
            else:  # OpenAI
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a regex optimization expert."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2
                )
                optimized = response.choices[0].message.content.strip()
            
            # Clean up
            optimized = optimized.strip('"\'`')
            
            return {
                "success": True,
                "optimized": optimized,
                "original": regex_pattern
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "optimized": None
            }