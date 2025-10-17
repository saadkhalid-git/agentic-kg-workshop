# Dynamic Knowledge Graph Pipeline

A fully automated pipeline that **dynamically generates plans** based on data analysis, mimicking the notebook workflow but without human intervention.

## Key Difference: Dynamic vs Hardcoded

### Original Pipeline (`run_pipeline.py`)
- Uses **hardcoded** construction plans and entity types
- Configuration defined in `config.py`
- Same plan for every run

### Dynamic Pipeline (`run_dynamic_pipeline.py`)
- **Analyzes data** to determine goals
- **Selects files** based on relevance
- **Generates schema** from file structure
- Plans stored as JSON for transparency

## How It Works

The dynamic pipeline uses specialized agents that mimic the notebook workflow:

### 1. Intent Agent (`intent_agent.py`)
- Analyzes available CSV and text files
- Determines the knowledge graph goal automatically
- Identifies domain (supply chain, customer analytics, etc.)
- Saves goal to `generated_plans/approved_user_goal.json`

### 2. File Selection Agent (`file_selection_agent.py`)
- Evaluates each file's relevance to the goal
- Scores files based on content and headers
- Selects files above threshold (default 0.3)
- Saves selection to `generated_plans/approved_files.json`

### 3. Schema Agent (`schema_agent.py`)
- Analyzes CSV structure (headers, ID columns, foreign keys)
- Identifies node vs relationship tables
- Infers relationships from foreign keys
- Generates construction plan dynamically
- Saves to `generated_plans/construction_plan.json` and `extraction_plan.json`

### 4-6. Execution Agents
Same as original pipeline, but use the dynamically generated plans.

## Usage

### Quick Demo
```bash
cd automated_pipeline
python run_dynamic_pipeline.py --demo
```

This will:
1. Analyze your data files
2. Generate all plans dynamically
3. Build a small graph (3 text files)
4. Save plans to `generated_plans/`

### Full Pipeline
```bash
python run_dynamic_pipeline.py
```

### Force Plan Regeneration
```bash
python run_dynamic_pipeline.py --regenerate
```

### View Generated Plans
```bash
python run_dynamic_pipeline.py --view-plans
```

### Use Custom Data
```bash
python run_dynamic_pipeline.py --data-dir /path/to/your/data
```

## Generated Plans

After running, check the `generated_plans/` directory:

### `approved_user_goal.json`
```json
{
  "kind_of_graph": "supply chain analysis",
  "description": "A comprehensive graph connecting Product, Supplier, Part, Assembly...",
  "primary_entities": ["Product", "Supplier", "Part"],
  "content_sources": ["customer reviews"],
  "expected_insights": ["quality issues, customer satisfaction"]
}
```

### `approved_files.json`
```json
{
  "approved_csv_files": ["products.csv", "suppliers.csv", ...],
  "approved_text_files": ["product_reviews/uppsala_sofa_reviews.md", ...],
  "csv_analysis": [
    {
      "file": "products.csv",
      "score": 0.8,
      "reason": "Contains entity 'Product'; Has ID columns"
    }
  ]
}
```

### `construction_plan.json`
```json
{
  "Product": {
    "construction_type": "node",
    "source_file": "products.csv",
    "label": "Product",
    "unique_column_name": "product_id",
    "properties": ["product_name", "price", "description"]
  },
  "SUPPLIED_BY": {
    "construction_type": "relationship",
    "source_file": "part_supplier_mapping.csv",
    "relationship_type": "SUPPLIED_BY",
    "from_node_label": "Part",
    "from_node_column": "part_id",
    "to_node_label": "Supplier",
    "to_node_column": "supplier_id"
  }
}
```

### `extraction_plan.json`
```json
{
  "entity_types": ["Product", "Issue", "Feature", "User"],
  "fact_types": {
    "has_issue": {
      "subject_label": "Product",
      "predicate_label": "has_issue",
      "object_label": "Issue"
    }
  }
}
```

## How Plans Are Generated

### Goal Determination
- Scans filenames for domain indicators (product, supplier, customer, etc.)
- Identifies primary entities from CSV files
- Detects content types from text files (reviews, reports, etc.)
- Combines into coherent goal description

### File Selection
- Scores each file for relevance:
  - Filename matches (+0.3)
  - Header columns match entities (+0.2)
  - Contains ID columns (+0.2)
  - Relationship indicators (+0.3)
- Selects files scoring >= threshold

### Schema Generation
- For each CSV:
  - Identifies unique ID columns
  - Detects foreign keys
  - Determines if node or relationship table
- Infers relationships from:
  - Dedicated mapping files
  - Foreign key references
  - Naming patterns

### Entity Extraction Planning
- Uses domain entities from CSV analysis
- Adds text-specific entities based on file types:
  - Reviews → Issue, Feature, User, Rating
  - Reports → Metric, Trend, Finding
  - Logs → Event, Error, System
- Creates fact types for relationships

## Advantages of Dynamic Pipeline

### Flexibility
- Works with any data structure
- No need to modify config for new datasets
- Adapts to available files

### Transparency
- All decisions saved as JSON
- Can review why files were selected
- Schema generation logic visible

### Reusability
- Generated plans can be reused
- Can be modified and re-run
- Serves as documentation

### Learning
- Shows how agents analyze data
- Demonstrates schema inference
- Educational for understanding KG construction

## Customization

### Adjust Selection Threshold
In `file_selection_agent.py`:
```python
threshold: float = 0.3  # Lower = more files selected
```

### Modify Goal Analysis
In `intent_agent.py`, add domain indicators:
```python
if "healthcare" in filename:
    analysis["domain_indicators"].append("healthcare")
```

### Enhance Schema Detection
In `schema_agent.py`, add patterns:
```python
if "diagnosis" in fk_base:
    rel_type = "DIAGNOSED_WITH"
```

## Comparison with Notebooks

| Feature | Notebooks | Dynamic Pipeline |
|---------|-----------|-----------------|
| Goal Setting | Human decides | Agent analyzes data |
| File Selection | Human reviews samples | Agent scores relevance |
| Schema Design | Human designs + critic | Agent infers from structure |
| Approval | Required at each step | Automatic (saved as JSON) |
| Reproducibility | Manual process | JSON plans ensure consistency |

## Tips

1. **First Run**: Use `--demo` to test with limited data
2. **Debugging**: Check generated JSONs to understand decisions
3. **Custom Data**: Ensure CSV files have clear ID columns
4. **Text Files**: Use descriptive filenames (e.g., "product_reviews.md")
5. **Regenerate**: Use `--regenerate` when data structure changes

## Example Workflow

```bash
# 1. Test with demo
python run_dynamic_pipeline.py --demo

# 2. View generated plans
python run_dynamic_pipeline.py --view-plans

# 3. Run full pipeline
python run_dynamic_pipeline.py

# 4. Save detailed results
python run_dynamic_pipeline.py --output results.json --show-plans

# 5. Use existing plans (no regeneration)
python run_dynamic_pipeline.py --no-reset
```

## Troubleshooting

### No Files Selected
- Lower the threshold in file_selection_agent.py
- Check file naming and structure
- Review `approved_files.json` for scoring details

### Wrong Schema Generated
- Check ID column detection in schema_agent.py
- Verify foreign key naming conventions
- Use `--regenerate` to force new analysis

### Plans Not Updating
- Use `--regenerate` flag
- Delete `generated_plans/*.json` manually
- Check file modification times