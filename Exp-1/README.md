# Single-Policy Dual-Analysis Experiment

## Abstract

This experiment explores the generation and quantitative analysis of cloud access control policies using large language models (LLMs) and a formal policy permissiveness tool called **Quacky**. We compare an original policy against a newly generated variant to assess relative permissiveness, extract distinguishing request strings, synthesize minimal regex patterns, and perform a final automated analysis. Results are logged to a CSV for downstream study.

## 1. Introduction

Cloud access control policies (e.g., AWS IAM, Azure RBAC, GCP IAM) govern which principals can perform which actions on which resources. Slight changes in policy structure can have large effects on permissiveness. This experiment automates a dual‐analysis pipeline, combining the creative capabilities of LLMs with the formal rigor of model counting via Quacky to generate, compare, and analyze policy variants at scale.

## 2. Background

### 2.1 Access Control Policies
- **AWS IAM**: JSON‐based policies defining `Effect`, `Action`, and `Resource`.
- **Azure**: Role assignments and custom role definitions.
- **GCP IAM**: Similar JSON policies with roles and bindings.

### 2.2 Policy Permissiveness & Model Counting
- **Quacky** translates policies into SMT‐LIB 2 formulas.
- **ABC solver** performs model counting, yielding a quantitative measure of how permissive a policy is (more models = more permissive).

## 3. Experimental Setup

- **Language:** Python 3.8+ with `pandas`, `openai`, `anthropic`, `tqdm`, and standard libraries.
- **LLM Endpoints:**
  - **Claude-3.5 Sonnet** for policy description & generation (`ANTHROPIC_API_KEY`).
  - **GPT-4o Mini** for regex synthesis (`OPENAI_API_KEY`).
- **Tool Path:** `quacky/src/quacky.py` (must be executable, requires SMT‐LIB & ABC).
- **Data Folder:** `Dataset/` contains original policy JSON files named `0.json`, `1.json`, …

## 4. Workflow

1. **Load Original Policy** from `Dataset/{n}.json`.
2. **Describe** it via Claude to obtain a concise natural‐language summary.
3. **Generate New Policy**: feed the summary back to Claude with a "JSON‐only" system prompt.
4. **Save** the generated policy to `quacky/src/gen_pol.json`.
5. **String Generation**:
   - Run `quacky.py` to produce two sets of example requests:
     - `P1_not_P2.models`: allowed by original but denied by new.
     - `not_P1_P2.models`: vice versa.
6. **Regex Synthesis**:
   - Prompt GPT-4o Mini to derive a tight regex pattern for each string set.
   - Store patterns in `response.txt` and `response2.txt`.
7. **Final Analysis**:
   - Run `quacky.py` again with both policies and regexes to generate a detailed comparison report.
   - Capture Quacky's stdout in the experiment results.
8. **Logging & Checkpointing**:
   - Append results to `Exp-1/single_policy_dual_analysis.csv`.
   - Update `Exp-1/single_policy_dual_progress.json` to resume on failure.

## 5. Outputs

| File                                      | Description                                       |
|-------------------------------------------|---------------------------------------------------|
| `single_policy_dual_analysis.csv`         | Tabular results for each policy pair              |
| `single_policy_dual_progress.json`        | Last processed index for resuming                 |
| `quacky/src/gen_pol.json`                 | Machine‐generated policy in JSON                  |
| `quacky/src/response.txt`                 | Regex for `P1_not_P2` strings                     |
| `quacky/src/response2.txt`                | Regex for `not_P1_P2` strings                     |

## 6. Getting Started

### Prerequisites

```bash
pip install pandas openai anthropic tqdm
# Ensure `quacky.py` dependencies are installed: SMT‐LIB toolchain, ABC solver
export OPENAI_API_KEY="your_openai_key"
export ANTHROPIC_API_KEY="your_anthropic_key"
```

### Running the Experiment

```bash
cd Exp-1
python3 Exp-1.py
```

Progress is printed to console and logged. To resume after an interruption, rerun the same command; the script will pick up from the last saved index.

## 7. Directory Structure

```
Exp-1/
├── Exp-1.py                          # Orchestrates entire pipeline
├── single_policy_dual_analysis.csv   # Experiment results
├── single_policy_dual_progress.json  # Resume checkpoint
├── README.md                         # This experiment description
└── ...                               # Additional Quacky files
```

---

*This document aims to provide a clear, step‐by‐step overview of the single‐policy dual‐analysis experiment, integrating LLMs and formal model counting to rigorously evaluate policy changes.* 