# Experiments - Usage Guide

This guide provides comprehensive instructions for running experiments on LLM-synthesized access control policy verification.

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Experiments Description](#experiments-description)
4. [Running Instructions](#running-instructions)
5. [Output Files](#output-files)
6. [Common Workflows](#common-workflows)
7. [Troubleshooting](#troubleshooting)

## Overview

We present a framework for verifying and analyzing access control policies synthesized by Large Language Models (LLMs). The experiments evaluate:
- Policy generation accuracy and semantic equivalence
- Resource summarization through regex synthesis
- Factors affecting summarization quality
- Fine-tuning approaches for improved performance

## Prerequisites

### 1. Environment Setup
```bash
# Python 3.8+ required
python --version

# Install dependencies
pip install -r requirements.txt
```

### 2. Required Dependencies
```bash
pip install pandas openai anthropic tqdm scikit-learn
```

### 3. API Keys Configuration
Create a `.env` or `llms.env` file in the experiment directory:
```
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key
```

### 4. External Tools

#### Quacky Installation
```bash
# Clone and install Quacky
git clone https://github.com/vlab-cs-ucsb/quacky
cd quacky
# Follow installation instructions in the repository
```

#### ABC (Automata-Based Counter) Installation
```bash
# Clone and install ABC
git clone https://github.com/vlab-cs-ucsb/ABC
cd ABC
./configure
make
```

Ensure both tools are in your PATH or update the paths in experiment scripts.

## Experiments Description

### Experiment 1: Policy Generation and Comparison
**Purpose**: Evaluates LLM's ability to generate semantically equivalent policies from descriptions.

**Process**:
1. Load original policy from Dataset
2. Generate natural language description using a language model
3. Synthesize new policy from description
4. Compare permissiveness using Quacky
5. Generate distinguishing request strings
6. Synthesize regex patterns for differences

### Experiment 2: Resource Summarization
**Purpose**: Tests Verisynth's ability to generate concise regex patterns summarizing allowed resources.

**Process**:
1. Load policy and generate sample allowed strings
2. Synthesize regex using a SOTA LLM.
3. Compare regex coverage vs original policy
4. Measure accuracy using Jaccard similarity

### Experiment 3: Multi-Size Sample Analysis
**Purpose**: Investigates how sample size affects regex synthesis quality.

**Sample Sizes**: [50, 100, 250, 500, 1000, 1500, 2000, 3000]

**Process**:
1. For each sample size, generate allowed strings
2. Synthesize regex using a SOTA LLM
3. Measure coverage accuracy across different sizes
4. Identify optimal sample size for synthesis

### Simplification Experiment
**Purpose**: Simplifies complex DFA-generated regex patterns into human-readable forms.

**Process**:
1. Generate regex from DFA using Quacky
2. Simplify using a SOTA LLM
3. Compare simplified vs original regex coverage

### Fine-tuning Experiments
**Purpose**: Improves regex synthesis through model fine-tuning.

**Components**:
- Dataset generation for fine-tuning
- Fine-tuning job submission to OpenAI
- Evaluation of fine-tuned model performance

## Running Instructions

### Quick Start - Run All Experiments
```bash
# Navigate to main experiment directory
cd Prev-Experiments/Verifying-LLMAccessControl/

# Run experiments in order
python Exp-1/Exp-1.py
python Exp-2/Exp-2.py
python Exp-3/Exp-3.py
python Simplification-Exp/simplify.py
```

### Experiment 1: Policy Generation and Comparison
```bash
cd Exp-1/

# Ensure environment variables are set
export ANTHROPIC_API_KEY="your_key"
export OPENAI_API_KEY="your_key"

# Run the experiment
python3 Exp-1.py

# The script will process policies from Dataset/
# Progress is saved in single_policy_dual_progress.json
```

### Experiment 2: Resource Summarization
```bash
cd Exp-2/

# Run the experiment
python3 Exp-2.py

# Interactive prompt will ask:
# "How many policies to process? (Enter -1 for all remaining): "
# Enter desired number or -1

# Results saved to:
# - multi-string.csv (raw results)
# - Exp-2.csv (processed results)
```

### Experiment 3: Multi-Size Analysis
```bash
cd Exp-3/

# Run the experiment
python3 Exp-3.py

# Interactive prompt for number of policies
# Processes multiple sample sizes per policy

# Monitor progress in:
# - progress.json
# - policy_analysis.log
```

### Simplification Experiment
```bash
cd Simplification-Exp/

# Run simplification
python3 simplify.py

# Results saved to:
# - simplify.csv
# - regex_simplifier.log
```

### Fine-tuning Workflow
```bash
cd Fine-tuning/

# Step 1: Generate fine-tuning dataset
python3 fine-tuning-dataset.py

# Step 2: Submit fine-tuning job
python3 fine_tuning_job.py

# Step 3: Evaluate fine-tuned model
python3 ftv1.py
```

## Output Files

### Experiment 1 Outputs
| File | Description |
|------|-------------|
| `single_policy_dual_analysis.csv` | Comparison results for each policy pair |
| `single_policy_dual_progress.json` | Resume checkpoint |
| `single_policy_dual_analysis.log` | Detailed execution logs |

### Experiment 2 Outputs
| File | Description |
|------|-------------|
| `multi-string.csv` | Raw regex synthesis results |
| `Exp-2.csv` | Processed results with metrics |
| `Exp-2_with_policy_numbers.csv` | Results with policy identifiers |
| `progress.json` | Resume checkpoint |

### Experiment 3 Outputs
| File | Description |
|------|-------------|
| `multi-string.csv` | Results for each policy-size combination |
| `policy_analysis.log` | Detailed processing logs |
| `progress.json` | Resume checkpoint |

## Common Workflows

### 1. Complete Policy Analysis Pipeline
```bash
# Start with policy generation comparison
cd Exp-1/ && python3 Exp-1.py

# Analyze resource summarization
cd ../Exp-2/ && python3 Exp-2.py

# Investigate sample size effects
cd ../Exp-3/ && python3 Exp-3.py

# Simplify complex regex patterns
cd ../Simplification-Exp/ && python3 simplify.py
```

### 2. Resume Interrupted Experiments
All experiments support checkpointing:
```bash
# Simply re-run the same command
python3 Exp-1.py  # Will resume from progress.json
```

### 3. Process Specific Policies
```bash
# For Exp-2 and Exp-3, use interactive prompt
python3 Exp-2.py
# Enter: 5  # Process next 5 policies
```

### 4. Add Custom Policies
```bash
# Add new policy files to Dataset/ directory
# Name them as: {number}.json (e.g., 41.json, 42.json)
# Re-run experiments - they'll process new policies
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Quacky Path Not Found
```bash
# Update quacky_path in experiment scripts:
quacky_path = "/path/to/your/quacky/src/quacky.py"
```

#### 2. API Rate Limits
```python
# Add delays in experiment scripts:
import time
time.sleep(1)  # Add between API calls
```

#### 3. Memory Issues
```bash
# Reduce batch size in experiments
# In Exp-1.py, Exp-2.py, modify:
batch_size = "50"  # Instead of "100"
```

#### 4. Missing Dependencies
```bash
# Ensure all required packages installed:
pip install --upgrade pandas anthropic openai tqdm
```

#### 5. Resume After Failure
```bash
# Check progress files:
cat Exp-1/single_policy_dual_progress.json
cat Exp-2/progress.json
cat Exp-3/progress.json

# Experiments will auto-resume from last checkpoint
```

### Debug Mode
Enable detailed logging:
```python
# In experiment scripts, set:
logging.basicConfig(level=logging.DEBUG)
```

### Verify Setup
```bash
# Test Quacky installation
python quacky/src/quacky.py --help

# Test API keys
python -c "import os; print('Keys set:', 'ANTHROPIC_API_KEY' in os.environ)"
```

## Performance Tips

1. **Parallel Processing**: Run different experiments in separate terminals
2. **Caching**: Results are cached in CSV files - reuse for analysis
3. **Batch Processing**: Use interactive prompts to process policies in batches
4. **Checkpointing**: Leverage progress.json files to handle interruptions

