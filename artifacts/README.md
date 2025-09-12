# Quacky Pipeline Demo

An interactive web interface for demonstrating the Quacky policy analysis pipeline. This artifact provides a user-friendly way to generate, compare, and analyze AWS IAM access control policies using formal verification methods.

## Features

### ✅ Implemented
- **Policy Generation from Natural Language** - Convert plain English descriptions to AWS IAM policies
- **Policy Comparison** - Quantitative analysis of policy differences using SMT solving
- **Interactive Web UI** - Streamlit-based interface for easy interaction

### 🚧 Coming Soon
- **String Generation** - Generate example requests that distinguish policies
- **Regex Synthesis** - Create patterns from example strings
- **Validation & Analysis** - Comprehensive regex validation against policies

## Docker Deployment (Recommended for Reviewers)

For the easiest setup, use Docker:

```bash
# 1. Set up API keys
cp .env.example .env
# Edit .env and add your API keys

# 2. Build and run with Docker Compose
docker-compose up -d

# 3. Access the application
# Open http://localhost:8501 in your browser
```

See [DOCKER_README.md](DOCKER_README.md) for detailed Docker instructions.

## Quick Start (Local Installation)

### Prerequisites
- Python 3.8+
- ABC solver installed and in PATH
- Quacky tool (already included in the parent repository)

### Installation

1. **Install dependencies:**
```bash
cd artifacts
pip install -r requirements.txt
```

2. **Set up API keys:**
```bash
cp .env.example .env
# Edit .env and add your API keys:
# - ANTHROPIC_API_KEY for Claude
# - OPENAI_API_KEY for GPT models
```

3. **Run the application:**
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Usage Guide

### Policy Generation
1. Navigate to "Policy Generation" in the sidebar
2. Enter a natural language description of your desired policy
3. Click "Generate Policy" to create an AWS IAM policy
4. Review and download the generated JSON

### Policy Comparison
1. Navigate to "Policy Comparison"
2. Input two policies (paste JSON, upload files, or use generated)
3. Set the analysis bound (higher = more accurate but slower)
4. Click "Compare Policies" to run quantitative analysis
5. Review metrics: satisfiability, solve time, request space size

### Example Descriptions
- "Allow all EC2 actions in us-west-2 region only"
- "Grant read-only access to S3 buckets starting with 'public-'"
- "Allow Lambda function management but deny deletion"
- "Grant full DynamoDB access except for table deletion"

## Architecture

```
artifacts/
├── app.py                      # Main Streamlit application
├── backend/
│   ├── quacky_wrapper.py      # Python interface to quacky tool
│   └── policy_generator.py    # LLM integration for NL→Policy
├── examples/
│   └── sample_policies/       # Example AWS IAM policies
└── requirements.txt           # Python dependencies
```

## How It Works

1. **Natural Language → Policy**: Uses LLMs (Claude/GPT) to generate valid AWS IAM policies from descriptions
2. **Policy → SMT Formula**: Quacky translates policies to SMT-LIB format
3. **SMT Analysis**: ABC solver performs model counting to quantify policy space
4. **Comparison**: Identifies requests allowed by one policy but not another
5. **Metrics**: Provides precise measurements of policy permissiveness

## Troubleshooting

### "No LLM API key configured"
- Ensure you have set either `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in the `.env` file

### "ABC solver not found"
- Install ABC and ensure it's in your PATH
- Check with: `which abc`

### "Quacky not found"
- The quacky tool should be at: `/home/ash/Desktop/VerifyingLLMGeneratedPolicies/CPCA/quacky/src/quacky.py`
- Ensure the path in `backend/quacky_wrapper.py` is correct

## Technical Details

- **Frontend**: Streamlit for rapid prototyping and interactive UI
- **Backend**: Python subprocess management for quacky integration
- **Analysis**: SMT-LIB 2.0 format with ABC solver for model counting
- **LLM Integration**: Anthropic Claude or OpenAI GPT for natural language processing

## Contributing

To extend this demo:
1. Add new features in `app.py`
2. Extend backend capabilities in `backend/`
3. Add more example policies in `examples/`
4. Update this README with new features

## Citation

If you use this tool in your research, please cite:
```
[Quacky: Quantitative Analysis of Access Control Policies]
```

## License

This demo is part of the VerifyingLLMGeneratedPolicies research project.