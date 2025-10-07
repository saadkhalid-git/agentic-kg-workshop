# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **Agentic Knowledge Graph Workshop** repository that demonstrates multi-agent workflows for knowledge graph construction using Google's ADK (Agent Development Kit) and Neo4j.

## Development Environment Setup

### 1. Python Virtual Environment
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Variables
Copy `.env.template` to `.env` and configure:
- `OPENAI_API_KEY`: Required for OpenAI API access
- `NEO4J_URI`: Default is `bolt://localhost:7687`
- `NEO4J_USERNAME`: Default is `neo4j`
- `NEO4J_PASSWORD`: Your Neo4j database password
- `NEO4J_IMPORT_DIR`: Absolute path to Neo4j import directory

### 3. Neo4j Database
- Install Neo4j Desktop and create a database instance
- Enable APOC and GenAI plugins
- Configure `neo4j.conf`:
  ```
  dbms.security.procedures.unrestricted=apoc.*
  dbms.security.procedures.allowlist=apoc.*,genai.*
  ```
- Copy data files to Neo4j import directory

## Common Development Commands

### Running Jupyter Notebooks
```bash
jupyter notebook
# or
jupyter lab
```

### Working with Neo4j
```python
# Use the provided Neo4j wrapper
from notebooks.neo4j_for_adk import Neo4jForADK
neo4j_client = Neo4jForADK()
```

## Code Architecture

### Key Components

1. **Agent Framework** (`notebooks/helper.py`):
   - `AgentCaller`: Wrapper class for interacting with ADK agents
   - `make_agent_caller()`: Factory function for creating agent instances
   - Session management and event handling

2. **Neo4j Integration** (`notebooks/neo4j_for_adk.py`):
   - `Neo4jForADK`: ADK-friendly Neo4j wrapper
   - Automatic connection management using environment variables
   - Result transformation for ADK compatibility

3. **Workshop Notebooks** (in order):
   - `0-reset_neo4j.ipynb`: Database reset utilities
   - `1-intro_to_adk.ipynb`: Introduction to ADK concepts
   - `2-user_intent.ipynb`: Intent recognition workflows
   - `3-file_suggestions.ipynb`: File suggestion agent
   - `4-schema_proposal.ipynb`: Schema design agent
   - `5-kg-construction.ipynb`: Knowledge graph construction
   - `8.1-kg-construction-I-platform.ipynb`: Platform-specific KG construction (Part 1)
   - `8.2-kg-construction-II-platform.ipynb`: Platform-specific KG construction (Part 2)

### Agent Development Pattern

Agents in this project follow the Google ADK pattern:
1. Define agent with tools and prompts
2. Create runner with session service
3. Use `AgentCaller` wrapper for simplified interaction
4. Process events to get final responses

Example usage:
```python
from google.adk.agents import Agent
from notebooks.helper import make_agent_caller

# Define agent
agent = Agent(
    name="example_agent",
    tools=[...],
    system_prompt="..."
)

# Create caller
caller = await make_agent_caller(agent)

# Execute query
response = await caller.call("Your query here")
```

## Data Files

The `data/` directory contains sample datasets for knowledge graph construction exercises. These should be copied to your Neo4j import directory during setup.

## Dependencies

Key libraries:
- `google-adk`: Agent Development Kit
- `neo4j`: Neo4j Python driver
- `neo4j-graphrag`: Graph RAG utilities
- `openai`: OpenAI API client
- `spacy`: NLP utilities
- `litellm`: Multi-model LLM interface