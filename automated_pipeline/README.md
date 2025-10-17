# Automated Knowledge Graph Pipeline

An automated, production-ready pipeline for constructing knowledge graphs from mixed data sources (CSV and text) without human intervention.

## Overview

This pipeline automates the entire knowledge graph construction process demonstrated in the workshop notebooks. It:

1. **Builds a Domain Graph** from structured CSV files (products, suppliers, parts, assemblies)
2. **Extracts a Subject Graph** from unstructured text (product reviews)
3. **Resolves Entities** between the two graphs using fuzzy matching
4. **Creates Indexes** for efficient querying and search

All without requiring human approval or intervention!

## Architecture

```
automated_pipeline/
├── agents/                      # Specialized agents for each task
│   ├── structured_agent.py      # CSV data import
│   ├── unstructured_agent.py    # Text extraction with LLMs
│   └── linkage_agent.py         # Entity resolution
├── pipeline/
│   ├── config.py                # All configuration settings
│   └── builder.py               # Main orchestrator
└── run_pipeline.py              # Entry point script
```

## Prerequisites

1. **Neo4j Database** running locally with APOC and GenAI plugins
2. **OpenAI API Key** for text extraction
3. **Python 3.9+** with virtual environment
4. **Data files** in the `data/` directory

## Setup

1. **Install dependencies** (from project root):
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment** (`.env` file):
   ```
   OPENAI_API_KEY=sk-...
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your_password
   NEO4J_IMPORT_DIR=/path/to/neo4j/import
   ```

3. **Copy data files** to Neo4j import directory:
   ```bash
   cp -r data/* $NEO4J_IMPORT_DIR/
   ```

## Usage

### Quick Start - Demo Mode

Run a quick demo with limited data (3 review files):
```bash
cd automated_pipeline
python run_pipeline.py --demo
```

### Full Pipeline

Run the complete pipeline with all data:
```bash
python run_pipeline.py
```

### Command Line Options

```bash
python run_pipeline.py [OPTIONS]

Options:
  --demo          Run demo mode with limited data
  --no-reset      Don't reset the graph before building
  --limit N       Limit to N markdown files
  --test          Run test queries after building
  --output FILE   Save results to JSON file
  --quiet         Reduce output verbosity
  --config        Show configuration and exit
```

### Examples

```bash
# Run without resetting existing graph
python run_pipeline.py --no-reset

# Process only 5 review files
python run_pipeline.py --limit 5

# Save detailed results
python run_pipeline.py --output results.json

# Run with test queries
python run_pipeline.py --test
```

## Pipeline Phases

### Phase 1: Domain Graph Construction
- Imports CSV files: products, suppliers, parts, assemblies
- Creates nodes with uniqueness constraints
- Establishes relationships: CONTAINS, IS_PART_OF, SUPPLIED_BY
- Batch processing (1000 rows per transaction)

### Phase 2: Subject Graph Construction
- Processes markdown review files
- Extracts entities: Product, Issue, Feature, User, Location
- Creates relationships: HAS_ISSUE, INCLUDES_FEATURE, REVIEWED_BY
- Generates embeddings for semantic search
- Creates text indexes

### Phase 3: Entity Resolution
- Links entities between graphs
- Uses Jaro-Winkler similarity (threshold: 0.8)
- Creates CORRESPONDS_TO relationships
- Handles Product, Supplier, Part, Assembly types

## Configuration

Edit `pipeline/config.py` to customize:

- **Entity Types**: Types to extract from text
- **Fact Types**: Relationships to extract
- **Similarity Threshold**: For entity matching (0-1)
- **File Lists**: CSV and markdown files to process
- **LLM Settings**: Model and temperature
- **Batch Size**: For Neo4j transactions

## Output

The pipeline provides:
- Real-time progress updates
- Statistics for each phase
- Final graph metrics (nodes, relationships)
- Execution time
- Detailed JSON results (with --output)

Example output:
```
PHASE 1: DOMAIN GRAPH CONSTRUCTION
✅ Nodes created: Product, Assembly, Part, Supplier
✅ Relationships created: CONTAINS, IS_PART_OF, SUPPLIED_BY

PHASE 2: SUBJECT GRAPH CONSTRUCTION
✅ Files processed: 10
📊 Entity Statistics:
  Product: 45 entities
  Issue: 23 entities
  Feature: 67 entities

PHASE 3: ENTITY RESOLUTION
✅ Total relationships created: 38
📊 Resolution by Type:
  Product: 10 correspondences

Final Graph Statistics:
  Total Nodes: 2,456
  Total Relationships: 3,789

Execution time: 45.23 seconds
```

## Testing

After building, test with sample queries:
```bash
python run_pipeline.py --test
```

Or use the Jupyter notebooks to explore the graph:
```python
from notebooks.neo4j_for_adk import graphdb

# Query the graph
result = graphdb.send_query("""
    MATCH (p:Product)-[:SUPPLIED_BY]->(s:Supplier)
    RETURN p.product_name, s.name
    LIMIT 10
""")
```

## Troubleshooting

### Environment Issues
- Verify all environment variables are set: `python run_pipeline.py --config`
- Check Neo4j is running: `neo4j status`
- Confirm data files exist in import directory

### Memory Issues
- Reduce batch size in config.py
- Process fewer files with `--limit`
- Increase Neo4j heap memory

### LLM Errors
- Check OpenAI API key is valid
- Verify API quota/limits
- Try with temperature=0 for consistency

## Extending the Pipeline

To add new data sources or entity types:

1. **Add Entity Types** in `config.py`:
   ```python
   ENTITY_TYPES = [..., 'NewType']
   ```

2. **Define Fact Types**:
   ```python
   FACT_TYPES['new_relationship'] = {
       'subject_label': 'Product',
       'predicate_label': 'new_relationship',
       'object_label': 'NewType'
   }
   ```

3. **Add Files** to process:
   ```python
   MARKDOWN_FILES.append('new_data/file.md')
   ```

## Performance

Typical execution times (MacBook Pro M1):
- Demo mode (3 files): ~30 seconds
- Full pipeline (10 files): ~2 minutes
- With 50 review files: ~8 minutes

Graph sizes:
- Demo: ~500 nodes, ~800 relationships
- Full: ~2,500 nodes, ~4,000 relationships

## Comparison with Workshop Notebooks

| Feature | Workshop Notebooks | Automated Pipeline |
|---------|-------------------|-------------------|
| Human Approval | Required at each step | None required |
| Execution | Interactive, cell-by-cell | Single command |
| Configuration | In notebook cells | Centralized config file |
| Error Handling | Manual intervention | Automatic logging |
| Reproducibility | Variable | Consistent |
| Speed | Slower (human delays) | Fast (no pauses) |

## License

Part of the Agentic Knowledge Graph Workshop.

## Support

For issues or questions:
1. Check the `learnings.md` file for detailed documentation
2. Review `track.json` for system capabilities
3. Examine execution logs in the output
4. Run in demo mode first to verify setup