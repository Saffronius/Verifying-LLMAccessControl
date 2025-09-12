# Large Language Model Synthesized Access Control Policy Verification

## Overview

This repository contains the code and experimental artifacts for verifying LLM-synthesized access control policies. Our research explores techniques for generating, analyzing, and verifying access control policies using large language models, with a focus on AWS IAM policies and formal verification methods.

## Research Approach

Our methodology combines:
- **Natural Language Processing**: Converting policy descriptions to formal specifications
- **Formal Verification**: Using SMT solvers and model counting for policy analysis
- **Quantitative Analysis**: Measuring policy permissiveness and semantic equivalence
- **Pattern Synthesis**: Generating regex patterns from example strings

We evaluate state-of-the-art language models on their ability to:
1. Generate syntactically and semantically correct policies
2. Comprehend and explain existing policies
3. Synthesize patterns that capture policy resource constraints
4. Maintain semantic equivalence across transformations

## Repository Structure

```
Verifying-LLMAccessControl/
├── artifacts/              # Interactive Streamlit demo with Docker deployment
│   ├── app.py             # Main web interface
│   ├── backend/           # Core logic and wrappers
│   ├── quacky/            # Modified Quacky tool (bundled)
│   ├── docker-compose.yml # Easy deployment configuration
│   └── REVIEWER_QUICKSTART.md
│
├── CPCA/                   # Core Policy Comprehension Assessment framework
│   ├── cpca.py            # Main experiment runner
│   ├── quacky/            # Quantitative analysis tool
│   └── experiment_results/ # Experimental data
│
├── Exp-1/                  # Policy Generation and Comparison
│   ├── Exp-1.py           # Dual policy analysis
│   └── README.md          # Experiment details
│
├── Exp-2/                  # Resource Summarization 
│   ├── Exp-2.py           # Regex synthesis from policies
│   ├── results/           # Evaluation metrics
│   └── tests/             # Test cases
│
├── Exp-3/                  # Factors Affecting Summarization
│   ├── Exp-3.py           # Multi-string analysis
│   └── multi-string.csv   # Results data
│
├── Exp-4-Zelkova/         # Zelkova-based Verification
│   ├── Exp-4-Zelkova.py   # Z3 model enumeration
│   ├── z3_model_enum.py   # SMT solving utilities
│   └── results/           # Verification outputs
│
├── regex/                  # Regex Generation Results
│   └── *.csv              # Pattern synthesis evaluations
│
├── Dataset/               # AWS IAM Policy Dataset
├── Fine-tuning/           # Model Fine-tuning Experiments
└── Simplification-Exp/    # Policy Simplification Studies
```

## Quick Start with Docker (Recommended)

The `artifacts/` directory contains a fully dockerized demo:

```bash
cd artifacts/
cp .env.example .env  # Add your API keys
docker-compose up -d
# Access at http://localhost:8501
```

See [artifacts/DOCKER_README.md](artifacts/DOCKER_README.md) for detailed instructions.

## Prerequisites for Local Setup

- Python 3.8+
- API keys for LLM services (at least one required)
- ABC (Automata-Based model Counter)
- Quacky (Quantitative Access Control Permissiveness Analyzer)

## Installation

1. Clone this repository

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up API keys:
   Create `.env` file with your keys:
   ```
   ANTHROPIC_API_KEY=your_key
   OPENAI_API_KEY=your_key
   GOOGLE_API_KEY=your_key
   ```

4. Install ABC solver:
   ```bash
   git clone https://github.com/vlab-cs-ucsb/ABC.git
   cd ABC && mkdir build && cd build
   cmake .. && make && sudo make install
   ```

5. Install Quacky (included in CPCA directory with modifications)

## Experiments

### Experiment 1: Policy Generation and Comparison
Evaluates LLM capabilities in generating and comparing access control policies.
```bash
cd Exp-1/
python Exp-1.py
```

### Experiment 2: Resource Summarization
Tests the ability to generate concise regex patterns that summarize policy resources.
```bash
cd Exp-2/
python Exp-2.py
```

### Experiment 3: Factors Affecting Summarization Accuracy
Investigates how various factors (string count, complexity) affect pattern synthesis accuracy.
```bash
cd Exp-3/
python Exp-3.py
```

### Experiment 4: Zelkova-based Verification
Uses Z3 theorem prover for formal policy verification and model enumeration.
```bash
cd Exp-4-Zelkova/
python Exp-4-Zelkova.py
```

### CPCA: Comprehensive Policy Analysis
Full experimental framework for policy comprehension assessment.
```bash
cd CPCA/
python cpca.py --models <model_name> --policy-dir <path> --output-dir results
```

## Key Features

- **Policy Generation**: Natural language to AWS IAM policy conversion
- **Quantitative Comparison**: SMT-based policy space analysis
- **Pattern Synthesis**: Regex generation from example strings
- **Formal Verification**: Using ABC and Z3 solvers
- **Interactive Demo**: Web-based interface for all features

## Technical Components

- **Quacky**: Translates policies to SMT-LIB format for model counting
- **ABC Solver**: Performs efficient model counting for policy analysis
- **Z3 Theorem Prover**: Used for formal verification in Exp-4
- **Streamlit Interface**: User-friendly web demo in artifacts/

## Data

The `Dataset/` folder contains AWS IAM policies used in experiments. To use your own:
1. Place policies in JSON format in the Dataset folder
2. Update experiment scripts to point to your data
3. Results will be saved in CSV format in respective experiment folders

## Replication Notes

Due to the non-deterministic nature of language models, exact result replication may vary. However, the techniques and trends should be consistent. The bundled Quacky in `artifacts/` and `CPCA/` includes necessary modifications for our experiments.

## Citation

If you use this code or our findings in your research, please cite:
```
[Citation information will be added upon publication]
```

## License

MIT License

## Contact

For questions about the experiments or techniques, please open an issue on GitHub.
