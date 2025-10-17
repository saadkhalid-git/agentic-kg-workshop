"""
Main Orchestrator for Automated Knowledge Graph Pipeline
Coordinates all agents to build the complete knowledge graph without human intervention
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

# Import pipeline configuration
from automated_pipeline.pipeline.config import PipelineConfig

# Import agents
from automated_pipeline.agents.structured_agent import AutomatedStructuredAgent
from automated_pipeline.agents.unstructured_agent import AutomatedUnstructuredAgent
from automated_pipeline.agents.linkage_agent import AutomatedLinkageAgent

# Import Neo4j utilities
from notebooks.neo4j_for_adk import graphdb
from notebooks.tools import drop_neo4j_indexes, clear_neo4j_data


class KnowledgeGraphBuilder:
    """
    Main orchestrator for building the complete knowledge graph.
    Coordinates all phases of construction without human intervention.
    """

    def __init__(self, config: PipelineConfig = None):
        """Initialize the builder with configuration."""
        self.config = config or PipelineConfig
        self.structured_agent = AutomatedStructuredAgent()
        self.unstructured_agent = AutomatedUnstructuredAgent(
            llm_model=self.config.LLM_MODEL,
            embedding_model=self.config.EMBEDDING_MODEL
        )
        self.linkage_agent = AutomatedLinkageAgent(
            similarity_threshold=self.config.SIMILARITY_THRESHOLD
        )

        # Track execution state
        self.execution_log = []
        self.start_time = None
        self.end_time = None

    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.execution_log.append(log_entry)
        if self.config.VERBOSE_OUTPUT:
            print(message)

    def reset_graph(self, confirm: bool = False) -> Dict[str, Any]:
        """Reset the Neo4j graph database."""
        if not confirm:
            return {
                "status": "error",
                "message": "Reset requires confirmation. Set confirm=True to proceed."
            }

        self.log("🔄 Resetting Neo4j graph...")

        # Drop indexes
        drop_result = drop_neo4j_indexes()
        self.log(f"  Indexes dropped: {drop_result['status']}")

        # Clear data
        clear_result = clear_neo4j_data()
        self.log(f"  Data cleared: {clear_result['status']}")

        return {
            "status": "success",
            "indexes_dropped": drop_result['status'],
            "data_cleared": clear_result['status']
        }

    def build_domain_graph(self) -> Dict[str, Any]:
        """Phase 1: Build the domain graph from CSV files."""
        self.log("\n" + "="*60)
        self.log("PHASE 1: DOMAIN GRAPH CONSTRUCTION")
        self.log("="*60)

        construction_plan = self.config.CONSTRUCTION_PLAN

        # Build the graph
        results = self.structured_agent.construct_domain_graph(construction_plan)

        # Log results
        if results['nodes_created']:
            self.log(f"✅ Nodes created: {', '.join(results['nodes_created'])}")
        if results['relationships_created']:
            self.log(f"✅ Relationships created: {', '.join(results['relationships_created'])}")
        if results['errors']:
            self.log(f"⚠️ Errors: {len(results['errors'])}", "WARNING")
            for error in results['errors'][:3]:  # Show first 3 errors
                self.log(f"  - {error}", "ERROR")

        # Log statistics
        if results.get('statistics'):
            self.log("\n📊 Domain Graph Statistics:")
            for label, count in results['statistics'].get('nodes', {}).items():
                self.log(f"  {label}: {count} nodes")
            for rel_type, count in results['statistics'].get('relationships', {}).items():
                self.log(f"  {rel_type}: {count} relationships")

        return results

    async def build_subject_graph(self) -> Dict[str, Any]:
        """Phase 2: Build the subject graph from markdown files."""
        self.log("\n" + "="*60)
        self.log("PHASE 2: SUBJECT GRAPH CONSTRUCTION")
        self.log("="*60)

        # Get file list
        markdown_files = self.config.MARKDOWN_FILES
        if self.config.LIMIT_FILES:
            markdown_files = markdown_files[:self.config.LIMIT_FILES]
            self.log(f"ℹ️ Limiting to {self.config.LIMIT_FILES} files for testing")

        # Use local data directory
        data_dir = self.config.get_data_directory()

        # Build the graph
        results = await self.unstructured_agent.construct_subject_graph(
            file_paths=markdown_files,
            entity_types=self.config.ENTITY_TYPES,
            fact_types=self.config.FACT_TYPES,
            import_dir=data_dir
        )

        # Log results
        self.log(f"✅ Files processed: {len(results['files_processed'])}")
        if results['files_failed']:
            self.log(f"⚠️ Files failed: {len(results['files_failed'])}", "WARNING")

        if results.get('entities_by_type'):
            self.log("\n📊 Entity Statistics:")
            for entity_type, count in results['entities_by_type'].items():
                self.log(f"  {entity_type}: {count} entities")

        self.log(f"  Chunks created: {results.get('chunk_count', 0)}")
        self.log(f"  Documents created: {results.get('document_count', 0)}")

        return results

    def resolve_entities(self) -> Dict[str, Any]:
        """Phase 3: Resolve entities between graphs."""
        self.log("\n" + "="*60)
        self.log("PHASE 3: ENTITY RESOLUTION")
        self.log("="*60)

        # Remove existing correspondences
        self.linkage_agent.remove_existing_correspondences()

        # Perform resolution
        results = self.linkage_agent.resolve_all_entities(
            entity_types=self.config.ENTITY_TYPES_TO_RESOLVE
        )

        # Log results
        self.log(f"✅ Total relationships created: {results['total_relationships']}")

        if results.get('entities_resolved'):
            self.log("\n📊 Resolution by Type:")
            for entity_type, count in results['entities_resolved'].items():
                self.log(f"  {entity_type}: {count} correspondences")

        if results.get('entities_unresolved'):
            self.log("\n❓ Unresolved Entities:")
            for entity_type, count in results['entities_unresolved'].items():
                if count > 0:
                    self.log(f"  {entity_type}: {count} unresolved")

        # Get detailed statistics
        stats = self.linkage_agent.get_resolution_statistics()
        if stats.get('correspondence_relationships') > 0:
            self.log(f"\n📈 Resolution Quality:")
            self.log(f"  Average similarity: {stats['avg_similarity']:.3f}")
            self.log(f"  Min similarity: {stats['min_similarity']:.3f}")
            self.log(f"  Max similarity: {stats['max_similarity']:.3f}")

        return results

    def get_final_statistics(self) -> Dict[str, Any]:
        """Get final statistics about the constructed graph."""
        stats_query = """
        MATCH (n)
        WITH labels(n) as node_labels, count(n) as node_count
        UNWIND node_labels as label
        WITH label, sum(node_count) as total
        RETURN label, total
        ORDER BY total DESC
        """

        result = graphdb.send_query(stats_query)

        stats = {"nodes_by_label": {}, "total_nodes": 0}

        if result['status'] == 'success':
            for row in result['query_result']:
                stats["nodes_by_label"][row['label']] = row['total']
                stats["total_nodes"] += row['total']

        # Count relationships
        rel_query = """
        MATCH ()-[r]->()
        RETURN type(r) as type, count(r) as count
        ORDER BY count DESC
        """

        rel_result = graphdb.send_query(rel_query)

        stats["relationships_by_type"] = {}
        stats["total_relationships"] = 0

        if rel_result['status'] == 'success':
            for row in rel_result['query_result']:
                stats["relationships_by_type"][row['type']] = row['count']
                stats["total_relationships"] += row['count']

        return stats

    async def build_complete_graph(
        self,
        reset: bool = None,
        limit_files: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Build the complete knowledge graph.

        Args:
            reset: Whether to reset the graph first (uses config default if not specified)
            limit_files: Limit number of files to process (overrides config)

        Returns:
            Dictionary with complete build results
        """
        self.start_time = datetime.now()
        self.execution_log = []

        # Override config if parameters provided
        if reset is not None:
            original_reset = self.config.RESET_GRAPH_BEFORE_RUN
            self.config.RESET_GRAPH_BEFORE_RUN = reset

        if limit_files is not None:
            original_limit = self.config.LIMIT_FILES
            self.config.LIMIT_FILES = limit_files

        results = {
            "start_time": self.start_time.isoformat(),
            "config": {
                "goal": self.config.USER_GOAL,
                "csv_files": len(self.config.CSV_FILES),
                "markdown_files": len(self.config.MARKDOWN_FILES),
                "limit_files": self.config.LIMIT_FILES
            }
        }

        try:
            # Print configuration
            if self.config.VERBOSE_OUTPUT:
                self.config.print_config()

            # Reset if requested
            if self.config.RESET_GRAPH_BEFORE_RUN:
                results['reset'] = self.reset_graph(confirm=True)

            # Phase 1: Domain Graph
            results['domain'] = self.build_domain_graph()

            # Phase 2: Subject Graph
            results['subject'] = await self.build_subject_graph()

            # Phase 3: Entity Resolution
            results['resolution'] = self.resolve_entities()

            # Final Statistics
            self.log("\n" + "="*60)
            self.log("KNOWLEDGE GRAPH CONSTRUCTION COMPLETE")
            self.log("="*60)

            stats = self.get_final_statistics()
            results['final_statistics'] = stats

            self.log("\n📊 Final Graph Statistics:")
            self.log(f"  Total Nodes: {stats['total_nodes']:,}")
            self.log(f"  Total Relationships: {stats['total_relationships']:,}")

            for label, count in list(stats['nodes_by_label'].items())[:10]:  # Top 10
                self.log(f"    {label:20} {count:8,} nodes")

            # Calculate execution time
            self.end_time = datetime.now()
            execution_time = (self.end_time - self.start_time).total_seconds()
            results['execution_time_seconds'] = execution_time
            results['end_time'] = self.end_time.isoformat()

            self.log(f"\n⏱️ Execution time: {execution_time:.2f} seconds")
            self.log("\n✅ Pipeline execution completed successfully!")

            results['status'] = 'success'

        except Exception as e:
            self.log(f"\n❌ Pipeline failed: {str(e)}", "ERROR")
            results['status'] = 'error'
            results['error'] = str(e)

        finally:
            # Restore original config if overridden
            if reset is not None:
                self.config.RESET_GRAPH_BEFORE_RUN = original_reset
            if limit_files is not None:
                self.config.LIMIT_FILES = original_limit

            results['execution_log'] = self.execution_log

        return results

    def test_with_sample_queries(self) -> None:
        """Test the graph with sample queries."""
        self.log("\n" + "="*60)
        self.log("TESTING WITH SAMPLE QUERIES")
        self.log("="*60)

        for i, query in enumerate(self.config.SAMPLE_QUERIES[:3], 1):
            self.log(f"\n📝 Query {i}: {query}")

            # Simple Cypher query test
            if "products" in query.lower() and "prices" in query.lower():
                cypher = """
                MATCH (p:Product)
                RETURN p.product_name as name, p.price as price
                ORDER BY p.price DESC
                LIMIT 5
                """
            elif "suppliers" in query.lower() and "sweden" in query.lower():
                cypher = """
                MATCH (s:Supplier)
                WHERE s.country = 'Sweden'
                RETURN s.name as supplier, s.city as city
                """
            elif "quality issues" in query.lower():
                cypher = """
                MATCH (p:Product)-[:HAS_ISSUE]->(i:Issue)
                RETURN p.name as product, collect(i.name) as issues
                LIMIT 5
                """
            else:
                cypher = """
                MATCH (n)
                RETURN count(n) as total_nodes
                """

            result = graphdb.send_query(cypher)

            if result['status'] == 'success' and result['query_result']:
                self.log("  ✅ Query successful")
                for row in result['query_result'][:3]:  # Show first 3 results
                    self.log(f"    {row}")
            else:
                self.log(f"  ⚠️ Query returned no results")


async def create_and_run_pipeline(
    reset: bool = True,
    limit_files: Optional[int] = None,
    test_queries: bool = False
) -> KnowledgeGraphBuilder:
    """
    Convenience function to create and run the pipeline.

    Args:
        reset: Whether to reset the graph first
        limit_files: Limit number of files to process
        test_queries: Whether to run test queries after building

    Returns:
        KnowledgeGraphBuilder instance with completed graph
    """
    builder = KnowledgeGraphBuilder()
    await builder.build_complete_graph(reset=reset, limit_files=limit_files)

    if test_queries:
        builder.test_with_sample_queries()

    return builder