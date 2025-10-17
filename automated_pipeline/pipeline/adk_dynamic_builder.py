"""
ADK-Enhanced Dynamic Pipeline Builder
Orchestrates ADK agents with LLM decision making to build knowledge graphs
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import asyncio
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Import ADK agents
from automated_pipeline.agents.adk_intent_agent import ADKIntentAgent, GoalValidationAgent
from automated_pipeline.agents.adk_file_selection_agent import ADKFileSelectionAgent, FileSelectionValidationAgent
from automated_pipeline.agents.adk_schema_agent import ADKSchemaAgent, SchemaValidationAgent

# Import execution agents (these will be improved next)
from automated_pipeline.agents.structured_agent import AutomatedStructuredAgent
from automated_pipeline.agents.unstructured_agent import AutomatedUnstructuredAgent
from automated_pipeline.agents.linkage_agent import AutomatedLinkageAgent

# Import Neo4j utilities
from notebooks.neo4j_for_adk import graphdb
from notebooks.tools import drop_neo4j_indexes, clear_neo4j_data


class ADKDynamicKnowledgeGraphBuilder:
    """
    Enhanced orchestrator using ADK agents with LLM-based decision making.
    Includes validation and critic loops for quality assurance.
    """

    def __init__(self, data_dir: str = None, llm_model: str = "gpt-4o-mini"):
        """
        Initialize the ADK-enhanced dynamic builder.

        Args:
            data_dir: Directory containing data files (uses default if not provided)
            llm_model: LLM model to use for agents
        """
        # ADK Planning agents
        self.intent_agent = ADKIntentAgent(llm_model=llm_model)
        self.intent_validator = GoalValidationAgent(llm_model=llm_model)

        self.file_selection_agent = ADKFileSelectionAgent(llm_model=llm_model)
        self.file_selection_validator = FileSelectionValidationAgent(llm_model=llm_model)

        self.schema_agent = ADKSchemaAgent(llm_model=llm_model)
        self.schema_validator = SchemaValidationAgent(llm_model=llm_model)

        # Execution agents (to be upgraded next)
        self.structured_agent = AutomatedStructuredAgent()
        self.unstructured_agent = AutomatedUnstructuredAgent(llm_model=llm_model)
        self.linkage_agent = AutomatedLinkageAgent()

        # Data directory
        if data_dir:
            self.data_dir = data_dir
        else:
            # Default to project data directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            self.data_dir = os.path.join(project_root, "data")

        # Execution tracking
        self.execution_log = []
        self.generated_plans = {}
        self.validation_results = {}

    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.execution_log.append(log_entry)
        print(message)

    def discover_files(self) -> Tuple[List[str], List[str]]:
        """Discover available CSV and text files in the data directory."""
        self.log("🔍 Discovering available files...")

        csv_files = []
        text_files = []

        # Walk through data directory
        for root, dirs, files in os.walk(self.data_dir):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.data_dir)

                if file.lower().endswith('.csv'):
                    csv_files.append(file_path)
                elif file.lower().endswith(('.md', '.txt')):
                    text_files.append(file_path)

        self.log(f"  Found {len(csv_files)} CSV files and {len(text_files)} text files")
        return csv_files, text_files

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

    async def phase1_determine_goal_with_validation(
        self,
        csv_files: List[str],
        text_files: List[str],
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """Phase 1: Determine goal using ADK agent with validation."""
        self.log("\n" + "="*60)
        self.log("PHASE 1: INTELLIGENT GOAL DETERMINATION (ADK)")
        self.log("="*60)

        # Generate goal using ADK agent
        goal = await self.intent_agent.load_or_generate_goal(
            csv_files,
            text_files,
            force_regenerate=force_regenerate
        )

        # Validate the generated goal
        self.log("  🔍 Validating generated goal...")
        validation = await self.intent_validator.validate_goal(goal, csv_files, text_files)

        # Store validation result
        self.validation_results["goal_validation"] = validation

        # If validation score is low, log warning
        if validation.get("score", 0) < 70:
            self.log(f"  ⚠️ Goal validation score is low: {validation['score']}/100", "WARNING")
            self.log(f"  💡 Suggestions: {', '.join(validation.get('suggestions', []))}", "WARNING")

        self.generated_plans["goal"] = goal
        return goal

    async def phase2_select_files_with_validation(
        self,
        csv_files: List[str],
        text_files: List[str],
        goal: Dict[str, Any],
        force_reselect: bool = False
    ) -> Dict[str, Any]:
        """Phase 2: Select files using ADK agent with validation."""
        self.log("\n" + "="*60)
        self.log("PHASE 2: INTELLIGENT FILE SELECTION (ADK)")
        self.log("="*60)

        # Select files using ADK agent
        selection = await self.file_selection_agent.load_or_select_files(
            csv_files,
            text_files,
            goal,
            force_reselect=force_reselect
        )

        # Validate the file selection
        self.log("  🔍 Validating file selection...")
        validation = await self.file_selection_validator.validate_selection(selection, goal)

        # Store validation result
        self.validation_results["file_selection_validation"] = validation

        # Log validation results
        if validation.get("score", 0) < 70:
            self.log(f"  ⚠️ Selection validation score is low: {validation['score']}/100", "WARNING")
            if validation.get("missing_entities"):
                self.log(f"  ❌ Missing entities: {', '.join(validation['missing_entities'])}", "WARNING")
            if validation.get("recommendations"):
                self.log(f"  💡 Recommendations: {', '.join(validation['recommendations'])}", "WARNING")

        self.generated_plans["file_selection"] = selection
        return selection

    async def phase3_generate_schema_with_validation(
        self,
        csv_files: List[str],
        text_files: List[str],
        goal: Dict[str, Any],
        force_regenerate: bool = False
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Phase 3: Generate schema using ADK agent with validation."""
        self.log("\n" + "="*60)
        self.log("PHASE 3: INTELLIGENT SCHEMA GENERATION (ADK)")
        self.log("="*60)

        # Generate schema using ADK agent
        construction_plan, extraction_plan = await self.schema_agent.load_or_generate_plans(
            csv_files,
            text_files,
            goal,
            force_regenerate=force_regenerate
        )

        # Validate the generated schema
        self.log("  🔍 Validating generated schema...")
        validation = await self.schema_validator.validate_schema(
            construction_plan,
            extraction_plan,
            goal
        )

        # Store validation result
        self.validation_results["schema_validation"] = validation

        # Log validation results
        if validation.get("score", 0) < 70:
            self.log(f"  ⚠️ Schema validation score is low: {validation['score']}/100", "WARNING")
            if validation.get("issues"):
                for issue in validation['issues'][:3]:
                    self.log(f"  ❌ Issue: {issue}", "WARNING")
            if validation.get("improvements"):
                self.log(f"  💡 Improvements: {', '.join(validation['improvements'][:3])}", "WARNING")

        self.generated_plans["construction_plan"] = construction_plan
        self.generated_plans["extraction_plan"] = extraction_plan

        return construction_plan, extraction_plan

    def phase4_build_domain_graph(self, construction_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 4: Build the domain graph from CSV files."""
        self.log("\n" + "="*60)
        self.log("PHASE 4: DOMAIN GRAPH CONSTRUCTION")
        self.log("="*60)

        results = self.structured_agent.construct_domain_graph(construction_plan)

        # Log results
        if results['nodes_created']:
            self.log(f"✅ Nodes created: {', '.join(results['nodes_created'])}")
        if results['relationships_created']:
            self.log(f"✅ Relationships created: {', '.join(results['relationships_created'])}")

        if results.get('statistics'):
            self.log("\n📊 Domain Graph Statistics:")
            for label, count in results['statistics'].get('nodes', {}).items():
                self.log(f"  {label}: {count} nodes")
            for rel_type, count in results['statistics'].get('relationships', {}).items():
                self.log(f"  {rel_type}: {count} relationships")

        return results

    async def phase5_build_subject_graph(
        self,
        text_files: List[str],
        extraction_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Phase 5: Build the subject graph from text files."""
        self.log("\n" + "="*60)
        self.log("PHASE 5: SUBJECT GRAPH CONSTRUCTION")
        self.log("="*60)

        # Extract entity types and fact types from plan
        entity_types = extraction_plan.get("entity_types", ["Product", "Issue", "Feature", "User"])
        fact_types = extraction_plan.get("fact_types", {})

        # Build the graph
        results = await self.unstructured_agent.construct_subject_graph(
            file_paths=text_files,
            entity_types=entity_types,
            fact_types=fact_types,
            import_dir=None  # Files already have full paths
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

    def phase6_resolve_entities(self, entity_types: List[str] = None) -> Dict[str, Any]:
        """Phase 6: Resolve entities between graphs with enhanced similarity."""
        self.log("\n" + "="*60)
        self.log("PHASE 6: ENHANCED ENTITY RESOLUTION")
        self.log("="*60)

        # Remove existing correspondences
        self.linkage_agent.remove_existing_correspondences()

        # Use entity types from extraction plan if available
        if entity_types is None and "extraction_plan" in self.generated_plans:
            # Get domain entities that might appear in both graphs
            entity_types = ["Product", "Supplier", "Part", "Assembly"]

        # Perform resolution
        results = self.linkage_agent.resolve_all_entities(
            entity_types=entity_types
        )

        # Log results
        self.log(f"✅ Total relationships created: {results['total_relationships']}")

        if results.get('entities_resolved'):
            self.log("\n📊 Resolution by Type:")
            for entity_type, count in results['entities_resolved'].items():
                self.log(f"  {entity_type}: {count} correspondences")

        # Get detailed statistics
        stats = self.linkage_agent.get_resolution_statistics()
        if stats.get('correspondence_relationships', 0) > 0:
            self.log(f"\n📈 Resolution Quality:")
            self.log(f"  Average similarity: {stats.get('avg_similarity', 0):.3f}")
            self.log(f"  Min similarity: {stats.get('min_similarity', 0):.3f}")
            self.log(f"  Max similarity: {stats.get('max_similarity', 0):.3f}")

        return results

    def validate_graph_quality(self) -> Dict[str, Any]:
        """Validate the quality of the constructed graph."""
        self.log("\n" + "="*60)
        self.log("GRAPH QUALITY VALIDATION")
        self.log("="*60)

        quality_metrics = {}

        # Check for orphan nodes
        orphan_query = """
        MATCH (n)
        WHERE NOT (n)--()
        RETURN labels(n)[0] as label, count(n) as count
        """
        result = graphdb.send_query(orphan_query)

        orphan_nodes = 0
        if result['status'] == 'success':
            for row in result['query_result']:
                orphan_nodes += row['count']

        quality_metrics['orphan_nodes'] = orphan_nodes

        # Check graph connectivity
        connectivity_query = """
        MATCH (n)
        WITH count(n) as total_nodes
        MATCH (n)--()
        WITH total_nodes, count(DISTINCT n) as connected_nodes
        RETURN total_nodes, connected_nodes,
               toFloat(connected_nodes) / total_nodes as connectivity_ratio
        """
        result = graphdb.send_query(connectivity_query)

        if result['status'] == 'success' and result['query_result']:
            row = result['query_result'][0]
            quality_metrics['connectivity_ratio'] = row.get('connectivity_ratio', 0)
            quality_metrics['total_nodes'] = row.get('total_nodes', 0)
            quality_metrics['connected_nodes'] = row.get('connected_nodes', 0)

        # Check relationship diversity
        rel_diversity_query = """
        MATCH ()-[r]->()
        RETURN type(r) as type, count(r) as count
        ORDER BY count DESC
        """
        result = graphdb.send_query(rel_diversity_query)

        if result['status'] == 'success':
            quality_metrics['relationship_types'] = len(result['query_result'])
            quality_metrics['relationship_distribution'] = {
                row['type']: row['count'] for row in result['query_result'][:5]
            }

        # Calculate quality score
        quality_score = 100

        # Penalize orphan nodes
        if quality_metrics.get('orphan_nodes', 0) > 0:
            penalty = min(quality_metrics['orphan_nodes'] * 2, 30)
            quality_score -= penalty
            self.log(f"  ⚠️ Found {quality_metrics['orphan_nodes']} orphan nodes (-{penalty} points)")

        # Reward high connectivity
        connectivity = quality_metrics.get('connectivity_ratio', 0)
        if connectivity > 0.8:
            self.log(f"  ✅ High graph connectivity: {connectivity:.1%}")
        elif connectivity < 0.5:
            penalty = 20
            quality_score -= penalty
            self.log(f"  ⚠️ Low graph connectivity: {connectivity:.1%} (-{penalty} points)")

        # Reward relationship diversity
        rel_types = quality_metrics.get('relationship_types', 0)
        if rel_types > 5:
            self.log(f"  ✅ Good relationship diversity: {rel_types} types")
        elif rel_types < 3:
            penalty = 10
            quality_score -= penalty
            self.log(f"  ⚠️ Low relationship diversity: {rel_types} types (-{penalty} points)")

        quality_metrics['quality_score'] = max(quality_score, 0)
        self.log(f"\n📊 Overall Graph Quality Score: {quality_metrics['quality_score']}/100")

        return quality_metrics

    def save_all_results(self, output_dir: str = "generated_plans") -> str:
        """Save all generated plans and validation results."""
        os.makedirs(output_dir, exist_ok=True)

        # Combine all results
        all_results = {
            "generated_plans": self.generated_plans,
            "validation_results": self.validation_results,
            "timestamp": datetime.now().isoformat()
        }

        output_file = os.path.join(output_dir, "adk_pipeline_results.json")

        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)

        self.log(f"💾 All results saved to: {output_file}")
        return output_file

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
        reset: bool = True,
        force_regenerate_plans: bool = False,
        limit_text_files: Optional[int] = None,
        validate_quality: bool = True
    ) -> Dict[str, Any]:
        """
        Build the complete knowledge graph with ADK agents and validation.

        Args:
            reset: Whether to reset the graph first
            force_regenerate_plans: Force regeneration of all plans
            limit_text_files: Limit number of text files to process
            validate_quality: Whether to perform quality validation

        Returns:
            Dictionary with complete build results
        """
        start_time = datetime.now()
        self.execution_log = []
        self.generated_plans = {}
        self.validation_results = {}

        results = {
            "start_time": start_time.isoformat(),
            "data_directory": self.data_dir,
            "pipeline_type": "ADK-Enhanced with LLM"
        }

        try:
            self.log("\n" + "🤖 "*20)
            self.log("ADK-ENHANCED DYNAMIC KNOWLEDGE GRAPH PIPELINE")
            self.log("🤖 "*20 + "\n")
            self.log("Using LLM-based decision making with validation loops")

            # Reset if requested
            if reset:
                results['reset'] = self.reset_graph(confirm=True)

            # Discover files
            csv_files, text_files = self.discover_files()
            results['discovered_files'] = {
                "csv_count": len(csv_files),
                "text_count": len(text_files)
            }

            # Phase 1: Determine goal with validation
            goal = await self.phase1_determine_goal_with_validation(
                csv_files,
                text_files,
                force_regenerate=force_regenerate_plans
            )
            results['goal'] = goal

            # Phase 2: Select files with validation
            file_selection = await self.phase2_select_files_with_validation(
                csv_files,
                text_files,
                goal,
                force_reselect=force_regenerate_plans
            )
            results['file_selection'] = {
                "selected_csv": len(file_selection['approved_csv_files']),
                "selected_text": len(file_selection['approved_text_files'])
            }

            # Get selected files
            selected_csv = file_selection['approved_csv_files']
            selected_text = file_selection['approved_text_files']

            # Apply text file limit if specified
            if limit_text_files and len(selected_text) > limit_text_files:
                selected_text = selected_text[:limit_text_files]
                self.log(f"ℹ️ Limiting to {limit_text_files} text files")

            # Phase 3: Generate schema with validation
            construction_plan, extraction_plan = await self.phase3_generate_schema_with_validation(
                selected_csv,
                selected_text,
                goal,
                force_regenerate=force_regenerate_plans
            )
            results['schema_generation'] = {
                "nodes_planned": len([v for v in construction_plan.values() if v.get('construction_type') == 'node']),
                "relationships_planned": len([v for v in construction_plan.values() if v.get('construction_type') == 'relationship']),
                "entity_types": len(extraction_plan.get('entity_types', [])),
                "fact_types": len(extraction_plan.get('fact_types', {}))
            }

            # Phase 4: Build domain graph
            results['domain'] = self.phase4_build_domain_graph(construction_plan)

            # Phase 5: Build subject graph
            if selected_text:
                results['subject'] = await self.phase5_build_subject_graph(
                    selected_text,
                    extraction_plan
                )

            # Phase 6: Entity resolution with enhanced similarity
            results['resolution'] = self.phase6_resolve_entities()

            # Validate graph quality if requested
            if validate_quality:
                quality_metrics = self.validate_graph_quality()
                results['quality_metrics'] = quality_metrics

            # Save all results
            self.save_all_results()

            # Final Statistics
            self.log("\n" + "="*60)
            self.log("KNOWLEDGE GRAPH CONSTRUCTION COMPLETE")
            self.log("="*60)

            stats = self.get_final_statistics()
            results['final_statistics'] = stats

            self.log("\n📊 Final Graph Statistics:")
            self.log(f"  Total Nodes: {stats['total_nodes']:,}")
            self.log(f"  Total Relationships: {stats['total_relationships']:,}")

            for label, count in list(stats['nodes_by_label'].items())[:10]:
                self.log(f"    {label:20} {count:8,} nodes")

            # Display validation summary
            self.log("\n🔍 Validation Summary:")
            for val_name, val_result in self.validation_results.items():
                score = val_result.get('score', 0)
                emoji = "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"
                self.log(f"  {emoji} {val_name}: {score}/100")

            # Calculate execution time
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            results['execution_time_seconds'] = execution_time
            results['end_time'] = end_time.isoformat()

            self.log(f"\n⏱️ Execution time: {execution_time:.2f} seconds")
            self.log("\n✅ ADK-Enhanced pipeline execution completed successfully!")

            results['status'] = 'success'

        except Exception as e:
            self.log(f"\n❌ Pipeline failed: {str(e)}", "ERROR")
            results['status'] = 'error'
            results['error'] = str(e)
            import traceback
            results['traceback'] = traceback.format_exc()

        finally:
            results['execution_log'] = self.execution_log
            results['generated_plans'] = self.generated_plans
            results['validation_results'] = self.validation_results

        return results


async def create_and_run_adk_dynamic_pipeline(
    reset: bool = True,
    force_regenerate_plans: bool = False,
    limit_text_files: Optional[int] = None,
    data_dir: Optional[str] = None,
    llm_model: str = "gpt-4o-mini",
    validate_quality: bool = True
) -> ADKDynamicKnowledgeGraphBuilder:
    """
    Convenience function to create and run the ADK-enhanced dynamic pipeline.

    Args:
        reset: Whether to reset the graph first
        force_regenerate_plans: Force regeneration of all plans
        limit_text_files: Limit number of text files to process
        data_dir: Data directory (uses default if not provided)
        llm_model: LLM model to use for agents
        validate_quality: Whether to perform quality validation

    Returns:
        ADKDynamicKnowledgeGraphBuilder instance with completed graph
    """
    builder = ADKDynamicKnowledgeGraphBuilder(data_dir=data_dir, llm_model=llm_model)
    await builder.build_complete_graph(
        reset=reset,
        force_regenerate_plans=force_regenerate_plans,
        limit_text_files=limit_text_files,
        validate_quality=validate_quality
    )
    return builder