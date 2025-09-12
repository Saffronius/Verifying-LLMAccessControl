# Single-Policy Multi-Size Regex Synthesis & Coverage Analysis Experiment

## Abstract

This experiment investigates how well an LLM (OpenAI GPT-4o Mini) can synthesize precise regular expressions from example request strings across multiple sample sizes, and then quantitatively assesses the regex's coverage compared to the original policy using **Quacky**'s model counting. By varying the number of sample strings, we explore the tradeoff between sample size and regex quality.

## 1. Introduction

Regular expressions are often used to compactly describe sets of allowed cloud resource requests (e.g., AWS ARNs). This experiment asks: given increasingly large samples of allowed requests from a single policy, can an LLM infer a concise, accurate regex—and how does that regex's permissiveness compare to the policy's true coverage?

## 2. Background

### 2.1 Access Control Policies

Cloud providers (AWS, Azure, GCP) expose JSON‐based IAM policies that specify which principals can perform which actions on which resources. These policies can be formally analyzed by translating them into logical constraints.

### 2.2 Model Counting & Regex Synthesis

- **Quacky**: Converts policies (and regexes) into SMT‐LIB 2 formulas and uses the ABC solver to count satisfying assignments, yielding a quantitative permissiveness metric.  
- **Regex Synthesis**: An LLM is prompted with example requests to propose a single regex intended to match exactly those strings, minimizing over‐generalization.

## 3. Experimental Setup

- **Language**: Python 3.8+ with:
  - `pandas`, `openai`, `tqdm`, `logging`, `signal`, `re`, `subprocess`, `json`, `os`, `time`
- **LLM Endpoint**: OpenAI GPT-4o Mini (`OPENAI_API_KEY`) for regex synthesis.
- **Tool Path**: `quacky/src/quacky.py` (requires executable SMT-LIB toolchain & ABC solver).
- **Data Folder**: `Dataset/` contains original policy JSON files (`0.json`, `1.json`, …).
- **Interactive Prompt**: On launch, the script asks how many policies to process this session (or `-1` for all remaining).

## 4. Workflow

1. **Initialize**: Create or load `Exp-3/multi-string.csv` and `Exp-3/progress.json` for checkpointing.
2. **Prompt User**: Enter the number of policies to process (or `-1` for all).
3. **Iterate Policies** (from saved `start_index` to `end_index`):
   1. **For Each Sample Size** in `[50, 100, 250, 500, 1000, 1500, 2000, 3000]`:
      1. Run Quacky to generate a sample of allowed request strings (`P1_not_P2.models`).
      2. Prompt GPT-4o Mini to synthesize a single regex matching those strings; save to `response.txt`.
      3. Run Quacky with the regex (`-cr`) to count how many assignments the regex accepts vs. the original policy.
      4. Append an entry `{model_name, original_policy, size, regex, raw_analysis, errors}` to `multi-string.csv`.
   2. Update `progress.json` to resume after the last completed policy.
4. **Finish**: Print summary of policies processed and next start index.

## 5. Outputs

| File                              | Description                                                            |
|-----------------------------------|------------------------------------------------------------------------|
| `Exp-3/multi-string.csv`          | Raw results: one row per policy‐size pair (regex + raw analysis).      |
| `Exp-3/progress.json`             | Checkpointing: last processed policy index.                            |
| `policy_analysis.log`             | Detailed logs from the script and Quacky runs.                         |
| `quacky/src/P1_not_P2.models`     | Sample strings allowed by the original policy for each run.            |
| `quacky/src/response.txt`         | Regex synthesized by the LLM for the latest sample.                    |

## 6. Getting Started

### Prerequisites

```bash
pip install pandas openai tqdm
# Ensure Quacky dependencies: SMT-LIB toolchain & ABC solver installed and on PATH
export OPENAI_API_KEY="your_openai_key"
```

### Running the Experiment

```bash
cd Exp-3
python3 Exp-3.py
```

- **Prompt**: Input the number of policies to process or `-1` to process all remaining.
- **Resume**: Rerun at any time; the script will pick up from `progress.json`.

## 7. Directory Structure

```
Exp-3/
├── Dataset/                    # Original policy JSON files
├── quacky/                     # Quacky tool & temporary outputs
├── Exp-3.py                    # Experiment orchestration script
├── multi-string.csv            # Raw results per policy-size sample
├── progress.json               # Resume checkpoint
├── policy_analysis.log         # Log file of processing steps
└── README.md                   # This experiment description
```

---

*This document outlines the Single-Policy Multi-Size Regex Synthesis & Coverage Analysis experiment, integrating LLM-driven regex inference with formal model counting to evaluate regex vs. policy coverage across sample sizes.* 