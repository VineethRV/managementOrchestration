# Conventional Baseline: Single-Agent Orchestration

This directory implements the **conventional baseline** for the comparative study of organizational management styles on agent orchestration. This baseline represents a simple, single-agent approach where one agent handles all phases of software development sequentially.

## Overview

The conventional baseline serves as the **control condition** against which multi-agent management styles (Top-Down, Bottom-Up, Kaizen) are compared. This approach mimics traditional single-agent systems where one autonomous agent performs all tasks from requirements gathering to code implementation.

## Architecture

### Single-Agent Workflow

```
┌─────────────────────────────────────────────────────────┐
│              SINGLE AGENT (Sequential)                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. Requirements Gathering                              │
│     ↓                                                    │
│  2. Application Design (Frontend + Backend)             │
│     ↓                                                    │
│  3. Project Scaffolding Generation                      │
│     ↓                                                    │
│  4. Code Implementation                                 │
│     ├── Frontend Pages (one by one)                    │
│     └── Backend Endpoints (one by one)                 │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Key Characteristics

- **Single Agent**: One LLM agent handles all tasks
- **Sequential Processing**: Tasks are performed one after another
- **No Coordination**: No inter-agent communication or coordination
- **No Hierarchy**: Flat structure with no management layers
- **No Parallelization**: All work done sequentially

## Files

- `single_agent.py` - Main orchestrator implementing all phases with a single agent
- `requirements.txt` - Python dependencies for the orchestration script
- `README.md` - This file

## Setup

### Prerequisites

- Python 3.8+
- Node.js and npm (for React project generation)
- Groq API key (get one at https://console.groq.com/)

### Environment Setup

1. **Create a `.env` file** in the `Conventional` directory:

```bash
cd Conventional
cp .env.example .env
```

2. **Edit `.env` file** and add your Groq API key:

```bash
GROQ_API_KEY=your_actual_api_key_here
```

**How to get your Groq API key:**
- Go to https://console.groq.com/
- Sign up or log in
- Navigate to API Keys section
- Create a new API key
- Copy the key (starts with `gsk_...`)
- Paste it into your `.env` file

**Example `.env` file:**
```
GROQ_API_KEY=gsk_1234567890abcdefghijklmnopqrstuvwxyz
```

⚠️ **Important:** Never commit your `.env` file to version control. The `.env.example` file is safe to commit as it doesn't contain real keys.

### Installation

```bash
cd Conventional

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Running the Conventional Baseline

```bash
# Make sure virtual environment is activated
python single_agent.py
```

The script will:
1. Interactively gather requirements from the user
2. Design the complete application (frontend + backend)
3. Generate React and Flask project scaffolding
4. Implement all frontend pages and backend endpoints sequentially
5. Track and save metrics for comparison

### Metrics Tracked

The baseline tracks the following metrics (matching the paper format):

- **Tokens consumed during conversation**: LLM tokens for requirements/design phases
- **Tokens consumed during coding**: LLM tokens for code generation
- **Total Tokens**: Sum of conversation + coding tokens
- **Features implemented**: Number of features successfully implemented (out of requested)
- **False interpretations**: Features incorrectly interpreted
- **Total bugs encountered**:
  - **Logical errors**: Errors in program logic
  - **Syntactic errors**: Code syntax errors
- **Lines of code modified during debugging**: Lines changed to fix bugs
- **Lines of code generated**: Total lines produced
- **Duration**: Total execution time

Metrics are saved to `logs/conventional_metrics_<timestamp>.json`

### Experiment Mode (Non-Interactive)

For reproducible experiments with a fixed specification:

```python
from single_agent import run_experiment

# Run with a specification file
run_experiment("specification.json")

# Or run with direct parameters
run_experiment(
    description="A username management application that allows users to...",
    features=["Add new usernames", "Check availability", "List all usernames"]
)
```

The specification JSON file should have this format:
```json
{
    "detailed_description": "Full description of the application...",
    "features": ["Feature 1", "Feature 2", "Feature 3"]
}
```

## Comparison with Other Approaches

### vs. Top-Down Management

- **Top-Down**: Hierarchical decomposition with specialized agents (Requirements → Technical Leads → Implementation Agents)
- **Conventional**: Single agent does everything sequentially

### vs. Bottom-Up Management

- **Bottom-Up**: Decentralized teams with collaborative refinement
- **Conventional**: No team structure, single agent

### vs. Kaizen

- **Kaizen**: Continuous improvement with PDCA cycles and quality circles
- **Conventional**: Single pass, no iterative refinement

## Experimental Design

This baseline is used in comparative experiments where:

1. **Same Task**: All approaches (Conventional, Top-Down, Bottom-Up, Kaizen) are given identical requirements
2. **Same Metrics**: All approaches are measured on the same metrics (tokens, bugs, features, LOC)
3. **Same Environment**: All approaches use the same LLM models and project structure

## Expected Characteristics

Based on theoretical predictions:

- **Efficiency**: May be slower due to sequential processing
- **Quality**: May have more errors due to lack of peer review
- **Token Usage**: May be lower due to no inter-agent communication overhead
- **Simplicity**: Easier to reason about, fewer moving parts

## Output Structure

```
Conventional/
├── logs/
│   ├── conventional_requirements_<timestamp>.log
│   ├── conventional_design_<timestamp>.log
│   ├── conventional_design_<timestamp>.json
│   ├── conventional_implementation_<timestamp>.log
│   └── conventional_metrics_<timestamp>.json
├── frontend/              # Generated React project
├── backend/               # Generated Flask project
└── single_agent.py
```

## Notes

- This implementation reuses the `project_generator.py` from the Top-Down directory for consistency
- All metrics are tracked automatically during execution
- The agent uses the same LLM model (`llama-3.3-70b-versatile`) as other approaches for fair comparison

