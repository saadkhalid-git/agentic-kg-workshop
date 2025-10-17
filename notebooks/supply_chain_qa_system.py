"""
Supply Chain Q&A System - Main Orchestrator

This module orchestrates all agents to build a complete knowledge graph
and provide Q&A capabilities for supply chain analysis.
"""

import os
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path

# Import all agents
from structured_data_agent import StructuredDataAgent, DEFAULT_SUPPLY_CHAIN_PLAN
from unstructured_data_agent import UnstructuredDataAgent, DEFAULT_ENTITY_TYPES, DEFAULT_FACT_TYPES
from entity_resolution_agent import EntityResolutionAgent
from langchain_rag_agent import LangChainRAGAgent

# Import utilities
from neo4j_for_adk import graphdb
from tools import drop_neo4j_indexes, clear_neo4j_data
from helper import get_neo4j_import_dir


class SupplyChainQASystem:
    """
    Main orchestrator for the supply chain knowledge graph Q&A system.

    This system combines:
    - Domain graph construction from structured CSV data
    - Subject graph construction from unstructured text
    - Entity resolution between graphs
    - Multi-strategy Q&A using LangChain GraphRAG
    """

    def __init__(
        self,
        neo4j_uri: Optional[str] = None,
        neo4j_username: Optional[str] = None,
        neo4j_password: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        import_dir: Optional[str] = None
    ):
        """
        Initialize the supply chain Q&A system.

        Args:
            neo4j_uri: Neo4j connection URI (uses env if not provided)
            neo4j_username: Neo4j username (uses env if not provided)
            neo4j_password: Neo4j password (uses env if not provided)
            openai_api_key: OpenAI API key (uses env if not provided)
            import_dir: Neo4j import directory (uses env if not provided)
        """
        # Load from environment if not provided
        self.neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_username = neo4j_username or os.getenv("NEO4J_USERNAME", "neo4j")
        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD")
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.import_dir = import_dir or get_neo4j_import_dir()

        # Initialize agents
        self.structured_agent = StructuredDataAgent()
        self.unstructured_agent = UnstructuredDataAgent()
        self.resolution_agent = EntityResolutionAgent()
        self.rag_agent = LangChainRAGAgent(
            neo4j_uri=self.neo4j_uri,
            neo4j_username=self.neo4j_username,
            neo4j_password=self.neo4j_password
        )

        # Configuration
        self.construction_plan = DEFAULT_SUPPLY_CHAIN_PLAN
        self.entity_types = DEFAULT_ENTITY_TYPES
        self.fact_types = DEFAULT_FACT_TYPES

        # File lists
        self.csv_files = [
            'products.csv',
            'assemblies.csv',
            'parts.csv',
            'part_supplier_mapping.csv',
            'suppliers.csv'
        ]

        self.markdown_files = [
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

        # Workflow state
        self.graph_built = False
        self.rag_initialized = False

    def reset_graph(self, confirm: bool = False) -> Dict[str, Any]:
        """
        Reset the Neo4j graph database.

        Args:
            confirm: Safety confirmation flag

        Returns:
            Dictionary with reset status
        """
        if not confirm:
            return {
                "status": "error",
                "message": "Reset requires confirmation. Set confirm=True to proceed."
            }

        print("🔄 Resetting Neo4j graph...")

        # Drop indexes
        drop_result = drop_neo4j_indexes()
        print(f"  Indexes dropped: {drop_result['status']}")

        # Clear data
        clear_result = clear_neo4j_data()
        print(f"  Data cleared: {clear_result['status']}")

        self.graph_built = False
        self.rag_initialized = False

        return {
            "status": "success",
            "indexes_dropped": drop_result['status'],
            "data_cleared": clear_result['status']
        }

    def build_domain_graph(
        self,
        construction_plan: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build the domain graph from structured CSV files.

        Args:
            construction_plan: Optional custom construction plan

        Returns:
            Dictionary with construction results
        """
        plan = construction_plan or self.construction_plan

        print("\n📊 Building Domain Graph from CSV files...")

        # Validate construction plan
        warnings = self.structured_agent.validate_construction_plan(plan)
        if warnings:
            print("⚠️  Validation warnings:")
            for warning in warnings:
                print(f"    - {warning}")

        # Construct the graph
        results = self.structured_agent.construct_domain_graph(plan)

        print("\n✅ Domain Graph Construction Complete")
        print(f"  Nodes created: {', '.join(results['nodes_created'])}")
        print(f"  Relationships created: {', '.join(results['relationships_created'])}")

        if results.get('statistics'):
            print("\n📈 Graph Statistics:")
            for label, count in results['statistics'].get('nodes', {}).items():
                print(f"    {label}: {count} nodes")
            for rel_type, count in results['statistics'].get('relationships', {}).items():
                print(f"    {rel_type}: {count} relationships")

        return results

    async def build_subject_graph(
        self,
        markdown_files: Optional[List[str]] = None,
        entity_types: Optional[List[str]] = None,
        fact_types: Optional[Dict[str, Dict[str, str]]] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Build the subject graph from unstructured markdown files.

        Args:
            markdown_files: Optional list of markdown files to process
            entity_types: Optional list of entity types to extract
            fact_types: Optional dictionary of fact types
            limit: Optional limit on number of files to process

        Returns:
            Dictionary with extraction results
        """
        files = markdown_files or self.markdown_files
        entities = entity_types or self.entity_types
        facts = fact_types or self.fact_types

        # Apply limit if specified
        if limit:
            files = files[:limit]

        print(f"\n📄 Building Subject Graph from {len(files)} markdown files...")

        # Use local data directory instead of Neo4j import dir
        import os
        data_dir = os.path.abspath('../data')

        # Construct the subject graph
        results = await self.unstructured_agent.construct_subject_graph(
            file_paths=files,
            entity_types=entities,
            fact_types=facts,
            import_dir=data_dir
        )

        print("\n✅ Subject Graph Construction Complete")
        print(f"  Files processed: {len(results['files_processed'])}")
        print(f"  Files failed: {len(results['files_failed'])}")

        if results.get('entities_by_type'):
            print("\n📈 Entity Statistics:")
            for entity_type, count in results['entities_by_type'].items():
                print(f"    {entity_type}: {count} entities")

        print(f"  Chunks created: {results.get('chunk_count', 0)}")
        print(f"  Documents created: {results.get('document_count', 0)}")

        # Create text indexes for search
        print("\n🔍 Creating text indexes...")
        index_results = self.unstructured_agent.create_text_indexes()
        print(f"  Vector index: {index_results['vector_index']}")
        print(f"  Full-text index: {index_results['fulltext_index']}")

        return results

    def resolve_entities(
        self,
        similarity_threshold: float = 0.8
    ) -> Dict[str, Any]:
        """
        Resolve entities between subject and domain graphs.

        Args:
            similarity_threshold: Minimum similarity for matching

        Returns:
            Dictionary with resolution results
        """
        print(f"\n🔗 Resolving Entities (threshold: {similarity_threshold})...")

        # Perform entity resolution
        results = self.resolution_agent.resolve_all_entities(
            similarity_threshold=similarity_threshold
        )

        print("\n✅ Entity Resolution Complete")
        print(f"  Total relationships created: {results['total_relationships']}")

        if results.get('entities_resolved'):
            print("\n📈 Resolution by Type:")
            for entity_type, count in results['entities_resolved'].items():
                print(f"    {entity_type}: {count} correspondences")

        if results.get('errors'):
            print("\n⚠️  Errors:")
            for error in results['errors'][:5]:  # Show first 5 errors
                print(f"    - {error}")

        # Get detailed statistics
        stats = self.resolution_agent.get_resolution_statistics()
        if stats.get('unresolved_by_type'):
            print("\n❓ Unresolved Entities:")
            for entity_type, count in stats['unresolved_by_type'].items():
                print(f"    {entity_type}: {count} unresolved")

        return results

    def initialize_rag(self) -> None:
        """Initialize the RAG system for Q&A."""
        if self.rag_initialized:
            print("ℹ️  RAG system already initialized")
            return

        print("\n🤖 Initializing RAG System...")

        # Set up vector store
        self.rag_agent.setup_vector_store()

        # Set up Cypher chain
        self.rag_agent.setup_cypher_chain()

        # Refresh graph schema
        self.rag_agent.graph.refresh_schema()

        self.rag_initialized = True
        print("✅ RAG System Ready")

    async def build_complete_graph(
        self,
        reset: bool = False,
        limit_markdown_files: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Build the complete knowledge graph (domain + subject + resolution).

        Args:
            reset: Whether to reset the graph first
            limit_markdown_files: Optional limit on markdown files to process

        Returns:
            Dictionary with complete build results
        """
        results = {}

        # Reset if requested
        if reset:
            results['reset'] = self.reset_graph(confirm=True)

        # Build domain graph
        print("\n" + "="*60)
        print("PHASE 1: Domain Graph Construction")
        print("="*60)
        results['domain'] = self.build_domain_graph()

        # Build subject graph
        print("\n" + "="*60)
        print("PHASE 2: Subject Graph Construction")
        print("="*60)
        results['subject'] = await self.build_subject_graph(limit=limit_markdown_files)

        # Resolve entities
        print("\n" + "="*60)
        print("PHASE 3: Entity Resolution")
        print("="*60)
        results['resolution'] = self.resolve_entities()

        # Initialize RAG
        print("\n" + "="*60)
        print("PHASE 4: RAG System Initialization")
        print("="*60)
        self.initialize_rag()

        self.graph_built = True

        # Final statistics
        print("\n" + "="*60)
        print("KNOWLEDGE GRAPH CONSTRUCTION COMPLETE")
        print("="*60)
        self._print_final_statistics()

        return results

    def _print_final_statistics(self) -> None:
        """Print final graph statistics."""
        stats_query = """
        MATCH (n)
        WITH labels(n) as node_labels, count(n) as count
        UNWIND node_labels as label
        WITH label, sum(count) as total
        RETURN label, total
        ORDER BY total DESC
        """

        result = graphdb.send_query(stats_query)

        if result['status'] == 'success':
            print("\n📊 Final Graph Statistics:")
            total_nodes = 0
            for row in result['query_result']:
                print(f"    {row['label']:20} {row['total']:8,} nodes")
                total_nodes += row['total']
            print(f"    {'TOTAL':20} {total_nodes:8,} nodes")

    def ask_question(
        self,
        question: str,
        use_workflow: bool = False
    ) -> str:
        """
        Ask a question using the Q&A system.

        Args:
            question: The question to answer
            use_workflow: Whether to use LangGraph workflow

        Returns:
            Answer string
        """
        if not self.graph_built:
            return "❌ Knowledge graph not built. Run build_complete_graph() first."

        if not self.rag_initialized:
            self.initialize_rag()

        print(f"\n💭 Question: {question}")

        if use_workflow:
            # Use LangGraph workflow
            workflow = self.rag_agent.create_langgraph_workflow()
            result = workflow.invoke({"question": question})
            answer = result.get('answer', 'No answer generated')
        else:
            # Use direct Q&A
            answer = self.rag_agent.answer_question(question)

        return answer

    def interactive_qa(self) -> None:
        """Run an interactive Q&A session."""
        if not self.graph_built:
            print("❌ Knowledge graph not built. Run build_complete_graph() first.")
            return

        if not self.rag_initialized:
            self.initialize_rag()

        print("\n" + "="*60)
        print("SUPPLY CHAIN KNOWLEDGE GRAPH Q&A")
        print("="*60)
        print("\nCommands:")
        print("  'quit' - Exit")
        print("  'help' - Show example queries")
        print("  'workflow' - Toggle workflow mode")
        print("\n")

        use_workflow = False
        sample_queries = self.rag_agent.get_sample_queries()

        while True:
            try:
                question = input(f"\n{'[Workflow Mode] ' if use_workflow else ''}Question: ").strip()

                if question.lower() == 'quit':
                    print("👋 Goodbye!")
                    break

                if question.lower() == 'help':
                    print("\n📝 Example queries:")
                    for i, q in enumerate(sample_queries[:5], 1):
                        print(f"  {i}. {q}")
                    continue

                if question.lower() == 'workflow':
                    use_workflow = not use_workflow
                    mode = "enabled" if use_workflow else "disabled"
                    print(f"🔄 Workflow mode {mode}")
                    continue

                if not question:
                    continue

                # Get answer
                answer = self.ask_question(question, use_workflow=use_workflow)

                print("\n" + "-"*40)
                print("Answer:")
                print("-"*40)
                print(answer)

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")

    def test_system(self) -> None:
        """Run a test of the complete system with sample queries."""
        if not self.graph_built:
            print("❌ Knowledge graph not built. Run build_complete_graph() first.")
            return

        if not self.rag_initialized:
            self.initialize_rag()

        print("\n" + "="*60)
        print("SYSTEM TEST - Sample Queries")
        print("="*60)

        test_queries = [
            "Which suppliers provide parts for the Uppsala Sofa?",
            "What quality issues are mentioned in product reviews?",
            "List all products and their prices",
            "Find suppliers located in Sweden"
        ]

        for i, question in enumerate(test_queries, 1):
            print(f"\n📌 Test {i}: {question}")
            answer = self.ask_question(question)
            print(f"\n{answer[:300]}..." if len(answer) > 300 else f"\n{answer}")
            print("-" * 60)


# Convenience function for quick setup
async def create_and_build_system(
    reset: bool = True,
    limit_markdown_files: int = 3
) -> SupplyChainQASystem:
    """
    Convenience function to create and build the complete system.

    Args:
        reset: Whether to reset the graph first
        limit_markdown_files: Number of markdown files to process (for demo)

    Returns:
        Initialized SupplyChainQASystem instance
    """
    system = SupplyChainQASystem()
    await system.build_complete_graph(
        reset=reset,
        limit_markdown_files=limit_markdown_files
    )
    return system