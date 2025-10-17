# Agentic Knowledge Graph Workshop - Learnings & Architecture

## Executive Summary
This repository demonstrates a production-grade multi-agent system for constructing knowledge graphs from mixed data sources (structured CSV and unstructured text). It uses Google's Agent Development Kit (ADK) with Neo4j to create a unified, queryable graph for supply chain analysis.

## Core Architecture: Three-Graph System

### 1. Domain Graph
- **Source**: Structured CSV files
- **Entities**: Products, Suppliers, Parts, Assemblies
- **Relationships**: CONTAINS, SUPPLIED_BY, IS_PART_OF
- **Characteristics**:
  - Strong typing with unique identifiers
  - Referential integrity through constraints
  - Batch loading for performance

### 2. Subject Graph
- **Source**: Unstructured markdown/text files (product reviews)
- **Entities**: Product mentions, Issues, Features, Users, Locations
- **Relationships**: HAS_ISSUE, INCLUDES_FEATURE, REVIEWED_BY
- **Characteristics**:
  - LLM-extracted entities
  - Schema-guided extraction
  - Fuzzy entity boundaries

### 3. Lexical Graph
- **Purpose**: Enables semantic search and RAG
- **Components**:
  - Document chunks with embeddings (3072-dim vectors)
  - Full-text indexes
  - Links to extracted entities via MENTIONED_IN relationships

## Agent Workflow Phases

### Phase 1: User Intent Recognition
- **Agent**: `user_intent_agent`
- **Pattern**: Human-in-the-loop approval
- **Tools**:
  - `set_perceived_user_goal`: Records initial understanding
  - `approve_perceived_user_goal`: Finalizes goal
- **State Management**: Separates working memory from specifications
- **Key Learning**: Structured conversations with explicit approval steps

### Phase 2: File Selection
- **Agent**: `file_suggestion_agent`
- **Intelligence**: Analyzes file content relevance to goal
- **Tools**:
  - `list_available_files`: Discovers data sources
  - `sample_file`: Examines content (100 lines max)
  - `set_suggested_files`/`approve_suggested_files`: Approval flow
- **Key Learning**: Content-aware file selection, not just name matching

### Phase 3: Schema Design (Multi-Agent)
- **Pattern**: Critic Loop with refinement
- **Agents**:
  - `schema_proposal_agent`: Generates construction rules
  - `schema_critic_agent`: Validates and provides feedback
  - `CheckStatusAndEscalate`: Controls loop termination
- **Innovation**: Self-improving through automated feedback
- **Tools**:
  - `propose_node_construction`: Defines node import rules
  - `propose_relationship_construction`: Defines edge rules
  - `search_file`: Validates unique identifiers
- **Key Learning**: Automated schema refinement reduces errors

### Phase 4: Domain Graph Construction
- **Agent**: `StructuredDataAgent`
- **Process**:
  1. Create uniqueness constraints
  2. Batch load nodes (MERGE operations)
  3. Create relationships with property mapping
- **Performance**: Transaction batches of 1000 rows
- **Key Learning**: Constraint-first approach ensures data integrity

### Phase 5: Subject Graph Construction
- **Agent**: `UnstructuredDataAgent`
- **Components**:
  - Custom `MarkdownDataLoader`: Extracts product names
  - `RegexTextSplitter`: Chunks on "---" delimiter
  - LLM extraction with schema guidance
- **Process**:
  1. Load and chunk documents
  2. Extract entities per schema
  3. Create embeddings
  4. Build text indexes
- **Key Learning**: Schema-guided extraction improves consistency

### Phase 6: Entity Resolution
- **Agent**: `EntityResolutionAgent`
- **Algorithm**: Jaro-Winkler similarity (threshold: 0.8)
- **Creates**: CORRESPONDS_TO relationships
- **Strategy**: Type-aware matching (Product→Product, etc.)
- **Key Learning**: Fuzzy matching bridges structured/unstructured divide

### Phase 7: RAG Q&A System
- **Agent**: `LangChainRAGAgent`
- **Strategies**:
  - Vector similarity search
  - Full-text search
  - Cypher query generation
  - LangGraph workflows for complex reasoning
- **Key Learning**: Multi-strategy retrieval improves answer quality

## Technical Patterns Discovered

### 1. ADK Agent Composition
```python
Agent(
    name="unique_identifier",
    model=llm,  # LLM instance
    instruction="detailed_prompt",  # Behavior specification
    tools=[functions],  # Available actions
    sub_agents=[agents]  # Delegation targets
)
```

### 2. Tool-Based State Management
- Tools access `tool_context.state` for persistence
- State carries across agent interactions
- Enables workflow continuity

### 3. Multi-Agent Patterns
- **Delegation**: Root agent routes to specialists
- **Critic Loop**: Proposal → Critique → Refine
- **Sequential Pipeline**: Phase-by-phase construction
- **Human-in-the-Loop**: Approval checkpoints

### 4. Error Handling Pattern
```python
def tool_function():
    if error_condition:
        return tool_error("message")
    return tool_success("key", data)
```

### 5. Async Agent Execution
- All agents run async for I/O efficiency
- Event-driven architecture
- `is_final_response()` marks completion

## Key Insights

### Architecture Decisions
1. **Three-graph separation**: Each optimized for its purpose
2. **Schema-first approach**: Define structure before extraction
3. **State persistence**: Session state enables complex workflows
4. **Tool abstraction**: Agents interact via well-defined interfaces

### Best Practices Learned
1. **Single Responsibility**: Each agent has ONE clear job
2. **Explicit Approvals**: Critical decisions need confirmation
3. **Defensive Validation**: Verify assumptions (unique IDs, file existence)
4. **Progressive Enhancement**: Build simple → add intelligence
5. **Composability**: Agents as reusable building blocks

### Performance Optimizations
1. **Batch Operations**: 1000-row transactions for Neo4j
2. **Constraint Indexes**: Improve MERGE performance
3. **Lazy Loading**: Sample files before full processing
4. **Parallel Extraction**: Process multiple documents concurrently

### Error Prevention
1. **Schema Validation**: Critic agent catches design flaws
2. **File Content Verification**: Check columns exist before use
3. **Type Safety**: Validate entity types in relationships
4. **Threshold Tuning**: Configurable similarity for entity resolution

## Supply Chain Use Case Analysis

### Data Model
- **Hierarchical**: Product → Assembly → Part → Supplier
- **Quality Tracking**: Reviews → Issues → Products
- **Multi-Supplier**: Parts can have multiple sources
- **Cost Analysis**: Lead times, unit costs, minimum orders

### Query Capabilities
1. **Dependency Analysis**: "What parts are in Product X?"
2. **Supplier Risk**: "Single points of failure in supply chain"
3. **Quality Tracking**: "Common issues across products"
4. **Cost Optimization**: "Alternative suppliers for expensive parts"

### Business Value
- **Root Cause Analysis**: Trace issues to specific components
- **Supplier Management**: Identify dependencies and alternatives
- **Quality Improvement**: Aggregate feedback across products
- **Risk Mitigation**: Find single-supplier vulnerabilities

## Framework Evaluation

### Strengths of ADK + Neo4j
1. **Natural Graph Modeling**: Relationships are first-class
2. **Flexible Schema**: Evolve without migrations
3. **Pattern Matching**: Cypher enables complex queries
4. **Agent Orchestration**: ADK handles complexity well
5. **State Management**: Built-in session handling

### Challenges Encountered
1. **LLM Consistency**: Extraction can vary between runs
2. **Entity Boundary**: Fuzzy edges in unstructured data
3. **Scale Considerations**: Token limits for large documents
4. **Debugging Complexity**: Multi-agent flows are harder to trace

### Mitigation Strategies
1. **Temperature = 0**: Reduce LLM variability
2. **Schema Constraints**: Guide extraction
3. **Document Chunking**: Handle large files
4. **Comprehensive Logging**: Track agent decisions

## Production Readiness Assessment

### Ready for Production
- ✅ Modular architecture
- ✅ Error handling
- ✅ State persistence
- ✅ Batch processing
- ✅ Schema validation

### Needs Enhancement
- ⚠️ Monitoring/observability
- ⚠️ Rate limiting for APIs
- ⚠️ Distributed processing
- ⚠️ Incremental updates
- ⚠️ Version control for schemas

## Future Enhancements

### Technical Improvements
1. **Streaming Processing**: Handle real-time data
2. **Distributed Agents**: Scale across machines
3. **Schema Evolution**: Automated migration strategies
4. **Active Learning**: Improve extraction from feedback
5. **Graph Analytics**: PageRank, community detection

### Business Extensions
1. **Predictive Analytics**: Forecast supply disruptions
2. **Recommendation Engine**: Suggest supplier alternatives
3. **Compliance Tracking**: Regulatory requirement mapping
4. **Cost Optimization**: Multi-objective supplier selection
5. **Quality Prediction**: Early warning for issues

## Conclusion

This workshop demonstrates that **multi-agent systems are powerful** for knowledge graph construction because they:
1. **Decompose Complexity**: Break down into manageable tasks
2. **Enable Specialization**: Each agent optimized for its role
3. **Support Iteration**: Critic loops improve quality
4. **Maintain Flexibility**: Easy to modify/extend
5. **Provide Transparency**: Decisions are traceable

The combination of Google ADK's agent orchestration with Neo4j's graph capabilities creates a robust platform for building intelligent knowledge systems that can handle both structured and unstructured data effectively.