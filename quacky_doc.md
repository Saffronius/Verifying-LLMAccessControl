# Quacky Documentation

## Overview
Quacky is a policy verification tool that uses the ABC (Automata Based Counter) solver to analyze and compare access control policies. It translates policies into SMT-LIB format and performs model counting and string generation for policy analysis.

## Command Line Usage

### Basic Syntax
```bash
python3 quacky.py [options]
```

### Core Parameters

#### Policy Inputs
- `-p1 <path>` - Path to the first (original) policy JSON file (required)
- `-p2 <path>` - Path to the second (generated) policy JSON file (optional, for comparison)

#### Bounds and Limits
- `-b <value>` - Bound value for ABC solver (default: 100)
- `--bound <value>` - Alternative syntax for bound value

#### Output Control
- `-o <prefix>` - Output file prefix for SMT formulas (default: "output")
  - Creates `output_1.smt2` for policy 1
  - Creates `output_2.smt2` for policy 2 (if provided)

#### Model Generation
- `-m <count>` - Number of random models to generate
- `--models <count>` - Alternative syntax for model count
- `--minrange <value>` - Minimum range for model generation (default: 1)
- `--maxrange <value>` - Maximum range for model generation (default: 10)
- Output: Models are saved to `P1_not_P2.models` (strings allowed by P1 but not P2)
- Output: `not_P1_P2.models` contains strings allowed by P2 but not P1

#### Regex Operations
- `--print-regex` or `-pr` - Print the regex generated from the DFA
- `--compare-regex <file>` or `-cr <file>` - Compare a regex file against policy results
  - File should contain a single regex pattern
  - Used to validate if a regex matches the policy's accepted strings

#### Analysis Options
- `--count-variable` - Count models per variable (principal, action, resource)
- `--variable` - Enable variable-specific counting
- `--verbose` or `-v` - Enable verbose output showing ABC solver details

### Common Usage Patterns

#### Experiment 1: Policy Comparison with Regex Synthesis
```bash
# Step 1: Generate SMT formulas and compare policies
python3 quacky.py -p1 original.json -p2 generated.json -o output

# Step 2: Generate example strings that differ between policies
python3 quacky.py -p1 original.json -p2 generated.json -b 100 -m 10 --minrange 1 --maxrange 10

# Step 3: Validate regex patterns against policies
python3 quacky.py -p1 original.json -p2 generated.json -b 100 -cr response.txt
```

#### Experiment 2 & 3: Single Policy Analysis with Regex
```bash
# Step 1: Generate sample strings from a single policy
python3 quacky.py -p1 policy.json -b 100 -m <size>

# Step 2: Compare synthesized regex against policy
python3 quacky.py -p1 policy.json -b 100 -cr response.txt
```

## Output Files

### Generated Files
- `output_1.smt2` - SMT-LIB formula for policy 1
- `output_2.smt2` - SMT-LIB formula for policy 2 (if -p2 provided)
- `P1_not_P2.models` - Strings accepted by P1 but not P2
- `not_P1_P2.models` - Strings accepted by P2 but not P1
- `response.txt` - Regex pattern (created by LLM, used with -cr)
- `response2.txt` - Second regex pattern (for not_P1_P2 strings)

### Output Format
The tool outputs:
1. Policy comparison status ("Policy 1 ⇏ Policy 2" or "Policy 1")
2. Solve time in milliseconds
3. Satisfiability result (sat/unsat)
4. Count time (if counting enabled)
5. Log of request count: `lg(requests)` 
6. ABC command used (when comparing regex)
7. Baseline regex count (when using -cr)

## Integration with ABC Solver

Quacky internally calls the ABC solver with commands like:
```bash
abc -bs 100 -v 0 -i output_1.smt2 --precise --count-tuple [additional options]
```

Additional ABC options used:
- `--count-variable principal,action,resource` - Count per variable
- `--get-num-random-models <n> <min> <max> resource <file>` - Generate random models
- `--print-regex resource` - Generate regex from DFA
- `--compare-regex resource <file>` - Compare against provided regex

## Error Handling

The tool will raise exceptions for:
- Invalid policy JSON files
- ABC solver failures
- Missing required arguments
- Regex comparison errors

Error details are logged including:
- ABC stdout/stderr output
- SMT formula contents
- Input policy contents
- Regex pattern contents

## Dependencies

- Python 3.x
- ABC solver (must be in PATH)
- SMT-LIB toolchain
- Required Python modules:
  - `frontend` (policy validation)
  - `translator` (SMT translation)
  - `utilities` (helper functions)
  - `utils.Shell` (command execution)

## Typical Workflow

1. **Policy Generation**: LLM generates a new policy from original
2. **String Generation**: Quacky generates example strings showing differences
3. **Regex Synthesis**: LLM creates regex patterns matching the strings
4. **Validation**: Quacky validates regex coverage against policies
5. **Analysis**: Results show model counts and coverage metrics