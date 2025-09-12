# Single-Policy Multi-String Analysis Experiment

## Abstract

This experiment evaluates the feasibility of synthesizing minimal regular expressions from example request strings of a single cloud access control policy, and then quantitatively assessing the policy's permissiveness against the synthesized regex using **Quacky**. We generate a corpus of strings allowed by the policy, prompt an LLM to propose a tight regex, and compare the coverage of the regex to the original policy via model counting.

## 1. Introduction

Regex patterns are often used to succinctly describe sets of allowed requests for cloud resources (e.g., AWS ARN patterns). This experiment explores how well an LLM (Claude-3.5 Sonnet) can synthesize a precise regex from a sample of allowed request strings, and then uses a formal model-counting tool (Quacky + ABC solver) to compare the regex's coverage against the policy itself.

## 2. Background

### 2.1 Access Control Policies

Cloud platforms like AWS, Azure, and GCP expose JSON-based IAM policies that specify which actions and resources are allowed or denied. These policies can be translated into logical constraints for automated analysis.

### 2.2 Model Counting & Regex Synthesis

- **Quacky**: Transforms policies into SMT-LIB 2 formulas and uses the ABC solver to count satisfying assignments, giving a numeric measure of permissiveness.  
- **Regex Synthesis**: Given a set of example strings (e.g., ARNs), an LLM can propose a condensed regex intended to match exactly those strings without over-generalizing.

## 3. Experimental Setup

- **Language**: Python 3.8+ with:
  - `pandas` (data handling)
  - `anthropic` (LLM API)
  - `tqdm`, `logging`, `signal`, `re`, `subprocess`, `json`, `os`, `time`
- **LLM Endpoint**: Claude-3.5 Sonnet (`ANTHROPIC_API_KEY`) for regex synthesis.
- **Tool Path**: `quacky/src/quacky.py` (requires executable SMT-LIB toolchain & ABC).
- **Data Folder**: `Dataset/` contains policy JSON files (`0.json`, `1.json`, …).
- **Interactive Prompt**: On launch, the script asks how many policies to process in this session (or `-1` for all remaining).

## 4. Workflow

1. **Initialize**: Read or create `Exp-2/multi-string.csv` and `Exp-2/progress.json` to resume progress.
2. **Select Range**: User inputs number of policies to process; script computes `start_index` from saved progress.
3. **For Each Policy**:
   1. **Load Policy JSON** from `Dataset/{n}.json`.
   2. **Generate Sample Strings**: Run Quacky with `-p1` only to emit `quacky/src/P1_not_P2.models`, a set of strings satisfying the policy.
   3. **Synthesize Regex**: Prompt Claude-3.5 to produce a single, tight regex matching all sample strings. Save it to `quacky/src/response.txt`.
   4. **Final Analysis**: Run Quacky again with `-p1` and the regex (`-cr`) to count models accepted by the regex vs. the policy.
   5. **Record Entry**: Append `{model_name, original_policy, size, regex, raw_analysis, errors}` to `multi-string.csv` and update `progress.json`.
4. **CSV Post-Processing**:
   1. Load `multi-string.csv` and parse the raw analysis text via regular expressions into structured metrics (e.g., counts, Jaccard indices).
   2. Emit a cleaned, human-friendly table as `Exp-2/Exp-2.csv`.

## 5. Outputs

| File                        | Description                                                          |
|-----------------------------|----------------------------------------------------------------------|
| `Exp-2/multi-string.csv`    | Raw experiment log per policy: regex, raw Quacky analysis, errors.  |
| `Exp-2/progress.json`       | Resume checkpoint: last processed index.                             |
| `Exp-2/Exp-2.csv`           | Post-processed table with parsed metrics (counts, coverage, etc.).  |
| `quacky/src/response.txt`   | Synthesized regex from LLM.                                          |
| `quacky/src/P1_not_P2.models` | Sample strings allowed by the original policy.                      |

## 6. Getting Started

### Prerequisites

```bash
pip install pandas anthropic tqdm
# Ensure `quacky.py` dependencies: SMT-LIB toolchain & ABC solver installed and on PATH
export ANTHROPIC_API_KEY="your_anthropic_key"
```

### Running the Experiment

```bash
cd Exp-2
python3 Exp-2.py
```

- **Prompt**: Enter the number of policies to process or `-1` to process all remaining.
- **Resume**: Rerun the script; it will pick up from `Exp-2/progress.json`.

## 7. Directory Structure

```
Exp-2/
├── Dataset/               # Original policy JSON files
├── quacky/                # Quacky tool & temporary outputs
├── Exp-2.py               # Experiment orchestration script
├── multi-string.csv       # Raw experiment results (regex + analysis)
├── progress.json          # Resume checkpoint
├── Exp-2.csv              # Final parsed results table
└── README.md              # This experiment description
```

---

*This document summarizes the Single-Policy Multi-String Analysis experiment, integrating LLM-driven regex synthesis with formal model counting to quantify regex vs. policy coverage.* 