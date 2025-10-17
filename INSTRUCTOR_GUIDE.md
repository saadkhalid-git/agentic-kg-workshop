# Instructor Evaluation Guide - PhD Exercise

## Expected Solution Discovery

This exercise is designed to lead PhD candidates toward discovering the need for an **intelligent knowledge graph construction pipeline with retrieval-augmented generation (RAG)** capabilities, without explicitly mentioning these technologies.

## What We're Looking For

### 1. Problem Recognition (Minimum Expectation)

Candidates should recognize that they need:
- **Automated data understanding** (not manual schema definition)
- **Entity and relationship extraction** from multiple sources
- **Some form of connected data structure** (ideally a graph)
- **Intelligent query processing** (not just keyword search)

### 2. Solution Approach (Good)

A good solution will include:
- **Multi-agent or modular architecture** for different tasks
- **Knowledge representation** that captures relationships
- **Entity resolution** to handle name variations
- **Hybrid search** combining multiple retrieval methods

### 3. Optimal Discovery (Excellent)

The best candidates will independently discover:

#### Phase 1: Dynamic Planning
- **Intent Analysis**: System that analyzes available data to understand the domain
- **File Selection**: Intelligent selection of relevant data sources
- **Schema Generation**: Automatic creation of data model from file analysis

#### Phase 2: Knowledge Construction
- **Graph Structure**: Realization that a graph database is optimal for connected queries
- **Multi-Graph Architecture**: Separate graphs for different concerns (domain, extracted, lexical)
- **Entity Resolution**: Sophisticated matching beyond exact string comparison

#### Phase 3: Intelligent Retrieval
- **RAG Pattern**: Combining retrieval with generation for answers
- **Hybrid Search**: Vector + keyword + graph traversal
- **Context Assembly**: Building relevant context from multiple sources

## Evaluation Rubric

### Architecture (40 points)

**Excellent (35-40):**
- Discovers need for graph-based knowledge representation
- Designs multi-agent or pipeline architecture
- Includes dynamic planning phase
- Separates concerns properly

**Good (25-34):**
- Creates some form of connected data structure
- Has modular design with clear components
- Handles both structured and unstructured data
- Some automation of schema discovery

**Acceptable (15-24):**
- Basic ETL pipeline with storage
- Handles CSV and text separately
- Manual or semi-manual schema definition
- Simple query interface

**Poor (0-14):**
- Hardcoded solution for specific files
- No real adaptability
- Traditional database approach only

### Implementation (40 points)

**Excellent (35-40):**
- Working graph construction from data
- LLM-based entity/relationship extraction
- Entity resolution implementation
- Retrieval-augmented answer generation

**Good (25-34):**
- Automated data ingestion
- Basic entity extraction
- Some relationship discovery
- Query answering with evidence

**Acceptable (15-24):**
- Loads CSVs and text files
- Simple keyword extraction
- Basic search functionality
- Returns relevant documents

**Poor (0-14):**
- Hardcoded for specific files
- No text processing
- SQL queries only
- No adaptability

### Innovation (20 points)

**Excellent (18-20):**
- Discovers RAG pattern independently
- Implements critic/validation loops
- Uses embeddings for semantic search
- Multi-hop reasoning capability

**Good (14-17):**
- Creative approach to entity resolution
- Interesting query decomposition
- Some semantic understanding
- Handles ambiguity well

**Acceptable (10-13):**
- Standard NLP techniques
- Basic relationship extraction
- Simple scoring mechanisms
- Reasonable assumptions

**Poor (0-9):**
- No innovation beyond basics
- Purely rule-based approach
- No handling of ambiguity
- Minimal text understanding

## Key Indicators of Understanding

### 🟢 Green Flags (They get it!)
- Mentions need for "knowledge graph" or "graph database"
- Discusses "retrieval" before generation/answering
- Implements entity resolution/disambiguation
- Creates embeddings or semantic representations
- Designs system that learns/adapts
- Separates planning from execution

### 🟡 Yellow Flags (Partial understanding)
- Uses relational database with heavy joins
- Keyword-based search only
- Manual schema mapping
- No entity resolution
- Limited text processing
- Hardcoded relationships

### 🔴 Red Flags (Missed the point)
- Completely hardcoded solution
- No text document processing
- No relationship discovery
- No adaptability to new data
- Pure SQL/traditional approach
- No use of AI/ML techniques

## Expected Technologies

Candidates who truly understand the problem will likely use:

1. **Graph Database** (Neo4j, NetworkX, or custom)
2. **LLMs** (OpenAI, Anthropic, etc.) for understanding
3. **Embeddings** for semantic search
4. **NLP Libraries** (spaCy, NLTK) for text processing
5. **Agent Framework** (LangChain, ADK, or custom)

## Interview Questions

After reviewing their solution, ask:

1. "How would your system handle 1000x more files?"
2. "What if the relationships were more implicit?"
3. "How do you ensure answer accuracy?"
4. "What happens when data contradicts itself?"
5. "How would you add reasoning capabilities?"

## Grading Guidelines

- **A+ (95-100)**: Independently invents graph RAG pipeline
- **A (90-94)**: Strong graph-based solution with retrieval
- **B+ (85-89)**: Good connected system with adaptability
- **B (80-84)**: Decent solution with some automation
- **C (70-79)**: Basic solution that technically works
- **F (<70)**: Doesn't meet core requirements

## What This Exercise Tests

1. **System Design Thinking**: Can they design complex systems?
2. **Problem Decomposition**: Do they break down the challenge?
3. **Technology Selection**: Do they choose appropriate tools?
4. **Innovation**: Can they invent solutions to novel problems?
5. **Practical Implementation**: Can they build working systems?

## Common Pitfalls to Watch For

1. **Over-engineering**: Building unnecessary complexity
2. **Under-engineering**: Missing the relationship aspect
3. **Missing Text**: Ignoring unstructured data
4. **No Adaptability**: Hardcoding everything
5. **Poor Abstraction**: Not separating concerns

## Bonus Points

Award extra credit for:
- Implementing validation loops
- Graph visualization
- Confidence scoring
- Contradiction detection
- Performance optimization
- Clean, documented code
- Creative solutions we didn't expect

## Sample Solution Outline

An ideal solution would include:

```
project/
├── agents/
│   ├── intent_analyzer.py      # Understands data and goals
│   ├── schema_generator.py     # Creates knowledge model
│   ├── entity_extractor.py     # Extracts from text
│   └── query_processor.py      # Answers questions
├── knowledge/
│   ├── graph_builder.py        # Constructs knowledge graph
│   ├── entity_resolver.py      # Resolves duplicates
│   └── relationship_finder.py  # Discovers connections
├── retrieval/
│   ├── vector_search.py        # Semantic search
│   ├── graph_search.py         # Graph traversal
│   └── hybrid_search.py        # Combines methods
└── pipeline/
    ├── orchestrator.py         # Manages workflow
    └── config.json             # Dynamic configuration
```

## Final Notes

- This exercise reveals how candidates approach **novel problems**
- We're testing **invention**, not just implementation
- The graph RAG solution should emerge **naturally** from requirements
- Best candidates will realize they're building an **intelligent system**, not just a database

Remember: We're not looking for them to use specific terminology (RAG, Knowledge Graph), but to independently discover these patterns as solutions to the problem.