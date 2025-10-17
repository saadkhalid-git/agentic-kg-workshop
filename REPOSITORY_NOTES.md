# Agentic Knowledge Graph Workshop - Repository Notes

## Overview
This repository demonstrates how to build knowledge graphs using **multi-agent workflows** with Google's Agent Development Kit (ADK) and Neo4j. It provides a complete workflow from defining user intent through schema design to actual graph construction, leveraging AI agents at each step.

## Architecture

### Core Technology Stack
- **Google ADK**: Agent orchestration framework
- **OpenAI GPT-5**: LLM for agent intelligence
- **Neo4j**: Graph database for knowledge graph storage
- **Neo4j GraphRAG**: Library for graph construction and entity extraction
- **Python**: Primary programming language

### Key Components

#### 1. Infrastructure Layer (`notebooks/`)

**Helper Modules:**
- `helper.py`: ADK wrapper utilities
  - `AgentCaller`: Simplifies agent interaction
  - `make_agent_caller()`: Factory for creating agent execution environments
  - Session management and event handling

- `neo4j_for_adk.py`: Neo4j integration
  - `Neo4jForADK`: ADK-compatible Neo4j wrapper
  - Automatic connection management via environment variables
  - Result transformation to ADK format
  - Query execution with parameter safety

- `tools.py`: Reusable tool definitions
  - `get_approved_user_goal()`: Retrieve user intent from state
  - `get_approved_files()`: Access approved file list
  - `sample_file()`: Read file samples for analysis
  - `clear_neo4j_data()`: Database reset utilities
  - `drop_neo4j_indexes()`: Index management

#### 2. Data Layer (`data/`)

**Structured Data (CSV):**
- `products.csv`: Product catalog
- `assemblies.csv`: Product assembly information
- `parts.csv`: Component parts data
- `suppliers.csv`: Supplier information
- `part_supplier_mapping.csv`: Part-supplier relationships

**Unstructured Data (Markdown):**
- `product_reviews/`: Customer review documents
  - Individual markdown files for each product
  - Used for NLP-based entity extraction

## Workflow Pipeline

### Phase 1: Introduction to ADK (Notebook 1)
**Purpose**: Learn ADK fundamentals

**Key Concepts:**
1. **Basic Agent Creation**
   - Agents with tools, models, instructions
   - Tool definition with docstrings for LLM understanding
   - Query parameterization to prevent injection

2. **Multi-Agent Teams**
   - Root agents with sub-agents
   - Automatic delegation based on agent descriptions
   - Specialized agents for specific tasks

3. **Session State Management**
   - `ToolContext` for state access in tools
   - Persistent memory across conversation turns
   - State initialization and manipulation

**Example Agents:**
- `hello_agent`: Basic greeting agent
- `greeting_subagent` & `farewell_subagent`: Specialized sub-agents
- `friendly_agent_team`: Coordinator with delegation

### Phase 2: User Intent (Notebook 2)
**Purpose**: Establish the goal for knowledge graph construction

**Agent**: `user_intent_agent`
- **Input**: User conversation
- **Output**: `approved_user_goal` (kind_of_graph + description)
- **Tools**:
  - `set_perceived_user_goal()`: Record agent's understanding
  - `approve_perceived_user_goal()`: User confirmation

**Workflow:**
1. Agent engages user in conversation
2. Clarifies the type and purpose of the graph
3. Records perceived goal
4. Obtains user approval
5. Saves to session state

### Phase 3: File Suggestions (Notebook 3)
**Purpose**: Select relevant files for graph construction

**Agent**: `file_suggestion_agent`
- **Input**: `approved_user_goal`
- **Output**: `approved_files` list
- **Tools**:
  - `list_available_files()`: Discover available data
  - `sample_file()`: Inspect file contents
  - `set_suggested_files()`: Propose file list
  - `approve_suggested_files()`: User confirmation

**Workflow:**
1. Agent analyzes available files
2. Samples content to assess relevance
3. Proposes files aligned with user goal
4. Obtains user approval

### Phase 4: Schema Proposal (Notebook 4)
**Purpose**: Design the knowledge graph schema

**Multi-Agent Architecture:**
1. **Schema Proposal Agent** (`schema_proposal_agent`)
   - Analyzes files to identify nodes vs relationships
   - Verifies unique identifiers
   - Creates construction rules

2. **Schema Critic Agent** (`schema_critic_agent`)
   - Reviews proposed schema
   - Validates against user goal
   - Provides feedback or approval

3. **Refinement Loop** (`schema_refinement_loop`)
   - Orchestrates proposal-critique cycle
   - Uses `LoopAgent` with max iterations
   - `CheckStatusAndEscalate` for loop control

4. **Coordinator** (`schema_proposal_coordinator`)
   - Manages user interaction
   - Wraps refinement loop as tool
   - Handles final approval

**Key Tools:**
- `propose_node_construction()`: Define node extraction rules
- `propose_relationship_construction()`: Define relationship rules
- `search_file()`: Validate column existence
- `remove_*_construction()`: Schema refinement

**Output**: `approved_construction_plan` with detailed rules for each file

### Phase 5: Knowledge Graph Construction (Notebook 5)
**Purpose**: Build the actual knowledge graph

**Two-Part Construction:**

#### Part A: Structured Data (CSV → Domain Graph)
- Direct rule-based import using construction plan
- Node creation with uniqueness constraints
- Relationship creation with property mapping

#### Part B: Unstructured Data (Markdown → Subject Graph)
- **NER Agent** (`ner_schema_agent`): Identifies entity types
- **Fact Agent** (`relevant_fact_agent`): Defines relationship types
- Entity extraction from text
- Fact triple extraction (subject-predicate-object)

### Phase 6: Platform Implementation (Notebooks 8.1 & 8.2)
**Purpose**: Complete knowledge graph with all components

#### Notebook 8.1: Domain Graph Construction
**Tools:**
- `create_uniqueness_constraint()`: Database constraints
- `load_nodes_from_csv()`: Batch node import
- `import_relationships()`: Relationship creation
- `construct_domain_graph()`: Complete pipeline

**Process:**
1. Create constraints for data integrity
2. Import all node types
3. Import all relationships
4. Validate construction

#### Notebook 8.2: Lexical & Subject Graph Construction
**Advanced Features:**

1. **Custom Components:**
   - `RegexTextSplitter`: Markdown chunking
   - `MarkdownDataLoader`: Document processing
   - Contextualized extraction prompts

2. **Neo4j GraphRAG Integration:**
   - `SimpleKGPipeline`: Entity extraction pipeline
   - OpenAI embeddings for chunks
   - Schema-guided extraction

3. **Entity Resolution:**
   - Key correlation between graphs
   - Fuzzy matching with rapidfuzz
   - Jaro-Winkler distance for value similarity
   - `CORRESPONDS_TO` relationships

**Final Graph Structure:**
- **Domain Graph**: Structured business data
- **Lexical Graph**: Document chunks with embeddings
- **Subject Graph**: Extracted entities and relationships
- **Connections**: Entity resolution links

## Key Design Patterns

### 1. Human-in-the-Loop
- Agent proposes, human approves
- Structured state management
- Clear separation of working memory vs specifications

### 2. Critic Pattern
- Proposal agent creates initial solution
- Critic agent evaluates and provides feedback
- Refinement loop until satisfactory

### 3. Tool Composition
- Small, focused tools
- Clear documentation for LLM understanding
- State-aware tools via `ToolContext`

### 4. Progressive Workflow
- Each phase builds on previous results
- State accumulation through workflow
- Clear input/output contracts

### 5. Delegation Architecture
- Root agents coordinate
- Sub-agents specialize
- Automatic routing based on descriptions

## Running the Workshop

### Prerequisites
1. Python environment with virtual environment
2. Neo4j database with APOC and GenAI plugins
3. OpenAI API key
4. Environment variables configured

### Execution Order
1. **Setup**: Configure environment and test connections
2. **Notebook 0**: Reset Neo4j (optional)
3. **Notebook 1**: Learn ADK basics
4. **Notebook 2**: Define user intent
5. **Notebook 3**: Select files
6. **Notebook 4**: Design schema
7. **Notebook 5**: Initial construction concepts
8. **Notebook 8.1**: Build domain graph
9. **Notebook 8.2**: Add lexical/subject graphs

### Key Configuration Files
- `.env`: Environment variables (API keys, Neo4j credentials)
- `requirements.txt`: Python dependencies
- `CLAUDE.md`: Project documentation for AI assistants

## Best Practices Demonstrated

1. **Agent Design**
   - Clear, specific instructions
   - Comprehensive tool documentation
   - Appropriate model selection

2. **State Management**
   - Explicit state keys
   - Separation of concerns (working vs approved)
   - State persistence across turns

3. **Error Handling**
   - Tool validation before execution
   - Graceful error messages
   - Retry mechanisms in loops

4. **Graph Construction**
   - Schema-first approach
   - Constraint enforcement
   - Batch processing for performance

5. **Entity Resolution**
   - Multiple similarity metrics
   - Configurable thresholds
   - Relationship tracking

## Advanced Topics Covered

- **Multi-agent orchestration** with delegation
- **Schema refinement loops** with critic agents
- **Contextualized prompts** for better extraction
- **Custom data loaders** for specific formats
- **Entity resolution** across graph components
- **Fuzzy matching** for imperfect data
- **Vector embeddings** for semantic search

## Future Extensions

Potential improvements and extensions:
1. Additional data format support (JSON, XML, PDF)
2. More sophisticated entity resolution algorithms
3. Graph validation and quality metrics
4. Query generation agents
5. Graph visualization tools
6. Production deployment considerations