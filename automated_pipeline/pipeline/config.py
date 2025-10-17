"""
Configuration for Automated Knowledge Graph Pipeline
Defines all settings, file paths, and parameters for the automated workflow
"""

import os
from typing import Dict, List, Any


class PipelineConfig:
    """Configuration for the automated knowledge graph pipeline."""

    # Pipeline Metadata
    PIPELINE_NAME = "Supply Chain Knowledge Graph Pipeline"
    VERSION = "1.0.0"

    # User Goal (Automated - No Human Intervention)
    USER_GOAL = {
        "kind_of_graph": "supply chain analysis",
        "description": (
            "A multi-level bill of materials for manufactured products with quality tracking. "
            "Includes supplier dependencies, component relationships, and customer feedback analysis "
            "for root cause analysis and supply chain optimization."
        )
    }

    # CSV Files for Domain Graph
    CSV_FILES = [
        "products.csv",
        "assemblies.csv",
        "parts.csv",
        "part_supplier_mapping.csv",
        "suppliers.csv"
    ]

    # Markdown Files for Subject Graph
    MARKDOWN_FILES = [
        "product_reviews/gothenburg_table_reviews.md",
        "product_reviews/helsingborg_dresser_reviews.md",
        "product_reviews/jonkoping_coffee_table_reviews.md",
        "product_reviews/linkoping_bed_reviews.md",
        "product_reviews/malmo_desk_reviews.md",
        "product_reviews/norrkoping_nightstand_reviews.md",
        "product_reviews/orebro_lamp_reviews.md",
        "product_reviews/stockholm_chair_reviews.md",
        "product_reviews/uppsala_sofa_reviews.md",
        "product_reviews/vasteras_bookshelf_reviews.md"
    ]

    # Domain Graph Construction Plan
    CONSTRUCTION_PLAN = {
        "Product": {
            "construction_type": "node",
            "source_file": "products.csv",
            "label": "Product",
            "unique_column_name": "product_id",
            "properties": ["product_name", "price", "description"]
        },
        "Assembly": {
            "construction_type": "node",
            "source_file": "assemblies.csv",
            "label": "Assembly",
            "unique_column_name": "assembly_id",
            "properties": ["assembly_name", "quantity", "product_id"]
        },
        "Part": {
            "construction_type": "node",
            "source_file": "parts.csv",
            "label": "Part",
            "unique_column_name": "part_id",
            "properties": ["part_name", "quantity", "assembly_id"]
        },
        "Supplier": {
            "construction_type": "node",
            "source_file": "suppliers.csv",
            "label": "Supplier",
            "unique_column_name": "supplier_id",
            "properties": ["name", "specialty", "city", "country", "website", "contact_email"]
        },
        "CONTAINS": {
            "construction_type": "relationship",
            "source_file": "assemblies.csv",
            "relationship_type": "CONTAINS",
            "from_node_label": "Product",
            "from_node_column": "product_id",
            "to_node_label": "Assembly",
            "to_node_column": "assembly_id",
            "properties": ["quantity"]
        },
        "IS_PART_OF": {
            "construction_type": "relationship",
            "source_file": "parts.csv",
            "relationship_type": "IS_PART_OF",
            "from_node_label": "Part",
            "from_node_column": "part_id",
            "to_node_label": "Assembly",
            "to_node_column": "assembly_id",
            "properties": ["quantity"]
        },
        "SUPPLIED_BY": {
            "construction_type": "relationship",
            "source_file": "part_supplier_mapping.csv",
            "relationship_type": "SUPPLIED_BY",
            "from_node_label": "Part",
            "from_node_column": "part_id",
            "to_node_label": "Supplier",
            "to_node_column": "supplier_id",
            "properties": ["lead_time_days", "unit_cost", "minimum_order_quantity", "preferred_supplier"]
        }
    }

    # Entity Types for Unstructured Data Extraction
    ENTITY_TYPES = ['Product', 'Issue', 'Feature', 'User', 'Location', 'Quality']

    # Fact Types for Relationship Extraction
    FACT_TYPES = {
        'has_issue': {
            'subject_label': 'Product',
            'predicate_label': 'has_issue',
            'object_label': 'Issue'
        },
        'includes_feature': {
            'subject_label': 'Product',
            'predicate_label': 'includes_feature',
            'object_label': 'Feature'
        },
        'used_in_location': {
            'subject_label': 'Product',
            'predicate_label': 'used_in_location',
            'object_label': 'Location'
        },
        'reviewed_by': {
            'subject_label': 'Product',
            'predicate_label': 'reviewed_by',
            'object_label': 'User'
        },
        'has_quality': {
            'subject_label': 'Product',
            'predicate_label': 'has_quality',
            'object_label': 'Quality'
        }
    }

    # Entity Resolution Parameters
    SIMILARITY_THRESHOLD = 0.6  # Jaro-Winkler similarity threshold (lowered for better matching)
    ENTITY_TYPES_TO_RESOLVE = ['Product', 'Supplier', 'Part', 'Assembly']

    # LLM Configuration
    LLM_MODEL = "gpt-4o"
    EMBEDDING_MODEL = "text-embedding-3-large"
    TEMPERATURE = 0  # For consistency

    # Neo4j Batch Processing
    BATCH_SIZE = 1000

    # Text Processing
    TEXT_CHUNK_DELIMITER = "---"
    MAX_SAMPLE_LINES = 100

    # Pipeline Execution Options
    RESET_GRAPH_BEFORE_RUN = True
    CREATE_INDEXES = True
    VERBOSE_OUTPUT = True
    LIMIT_FILES = None  # Set to number to limit files processed (for testing)

    # Sample Queries for Testing
    SAMPLE_QUERIES = [
        "Which suppliers provide parts for the Uppsala Sofa?",
        "What quality issues are mentioned in product reviews?",
        "List all products and their prices",
        "Find suppliers located in Sweden",
        "What assembly problems do customers report?",
        "Which parts have multiple supplier options?",
        "What features do customers appreciate most?",
        "Find single points of failure in the supply chain",
        "Which products have the most quality complaints?",
        "What are the lead times for critical components?"
    ]

    @classmethod
    def get_data_directory(cls) -> str:
        """Get the absolute path to the data directory."""
        # Go up from automated_pipeline/pipeline to root, then to data
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        return os.path.join(project_root, "data")

    @classmethod
    def get_neo4j_import_dir(cls) -> str:
        """Get the Neo4j import directory from environment or default."""
        import_dir = os.getenv("NEO4J_IMPORT_DIR")
        if not import_dir:
            # Try to get from helper module
            try:
                from notebooks.helper import get_neo4j_import_dir
                import_dir = get_neo4j_import_dir()
            except:
                pass
        return import_dir or cls.get_data_directory()

    @classmethod
    def validate_environment(cls) -> Dict[str, bool]:
        """Validate that all required environment variables are set."""
        validation = {
            "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
            "NEO4J_URI": bool(os.getenv("NEO4J_URI")),
            "NEO4J_USERNAME": bool(os.getenv("NEO4J_USERNAME")),
            "NEO4J_PASSWORD": bool(os.getenv("NEO4J_PASSWORD")),
        }

        # Optional but recommended
        validation["NEO4J_IMPORT_DIR"] = bool(os.getenv("NEO4J_IMPORT_DIR"))

        return validation

    @classmethod
    def print_config(cls) -> None:
        """Print the current configuration."""
        print("\n" + "="*60)
        print("PIPELINE CONFIGURATION")
        print("="*60)
        print(f"\nPipeline: {cls.PIPELINE_NAME} v{cls.VERSION}")
        print(f"\nGoal: {cls.USER_GOAL['kind_of_graph']}")
        print(f"Description: {cls.USER_GOAL['description'][:100]}...")
        print(f"\nData Sources:")
        print(f"  CSV Files: {len(cls.CSV_FILES)}")
        print(f"  Markdown Files: {len(cls.MARKDOWN_FILES)}")
        print(f"\nEntity Types: {', '.join(cls.ENTITY_TYPES)}")
        print(f"Fact Types: {', '.join(cls.FACT_TYPES.keys())}")
        print(f"\nParameters:")
        print(f"  Similarity Threshold: {cls.SIMILARITY_THRESHOLD}")
        print(f"  Batch Size: {cls.BATCH_SIZE}")
        print(f"  LLM Model: {cls.LLM_MODEL}")
        print(f"  Temperature: {cls.TEMPERATURE}")

        # Environment validation
        print(f"\nEnvironment Check:")
        validation = cls.validate_environment()
        for key, is_set in validation.items():
            status = "✅" if is_set else "❌"
            print(f"  {status} {key}")

        print("="*60 + "\n")