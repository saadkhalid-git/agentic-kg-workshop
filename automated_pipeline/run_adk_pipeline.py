#!/usr/bin/env python3
"""
Run the ADK-Enhanced Dynamic Knowledge Graph Pipeline
This version uses LLM-based decision making with validation loops
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import argparse
import json
from datetime import datetime

# Import the ADK-enhanced builder
from automated_pipeline.pipeline.adk_dynamic_builder import (
    ADKDynamicKnowledgeGraphBuilder,
    create_and_run_adk_dynamic_pipeline
)


def print_banner():
    """Print a banner for the ADK pipeline."""
    print("\n" + "🤖 "*30)
    print("ADK-ENHANCED KNOWLEDGE GRAPH PIPELINE")
    print("Powered by LLM Intelligence & Validation")
    print("🤖 "*30 + "\n")


def print_results(results: dict):
    """Print formatted results."""
    print("\n" + "="*60)
    print("PIPELINE RESULTS")
    print("="*60)

    # Status
    status_emoji = "✅" if results.get('status') == 'success' else "❌"
    print(f"\n{status_emoji} Status: {results.get('status', 'unknown').upper()}")

    # Execution time
    if 'execution_time_seconds' in results:
        print(f"⏱️  Execution Time: {results['execution_time_seconds']:.2f} seconds")

    # Files discovered
    if 'discovered_files' in results:
        files = results['discovered_files']
        print(f"\n📁 Files Discovered:")
        print(f"   CSV: {files.get('csv_count', 0)}")
        print(f"   Text: {files.get('text_count', 0)}")

    # Goal
    if 'goal' in results:
        goal = results['goal']
        print(f"\n🎯 Goal: {goal.get('kind_of_graph', 'Unknown')}")
        desc = goal.get('description', '')[:150]
        if desc:
            print(f"   {desc}...")

    # File selection
    if 'file_selection' in results:
        selection = results['file_selection']
        print(f"\n📂 Files Selected:")
        print(f"   CSV: {selection.get('selected_csv', 0)}")
        print(f"   Text: {selection.get('selected_text', 0)}")

    # Schema generation
    if 'schema_generation' in results:
        schema = results['schema_generation']
        print(f"\n🏗️  Schema Generated:")
        print(f"   Nodes: {schema.get('nodes_planned', 0)}")
        print(f"   Relationships: {schema.get('relationships_planned', 0)}")
        print(f"   Entity Types: {schema.get('entity_types', 0)}")
        print(f"   Fact Types: {schema.get('fact_types', 0)}")

    # Final statistics
    if 'final_statistics' in results:
        stats = results['final_statistics']
        print(f"\n📊 Final Graph Statistics:")
        print(f"   Total Nodes: {stats.get('total_nodes', 0):,}")
        print(f"   Total Relationships: {stats.get('total_relationships', 0):,}")

        # Top node types
        if 'nodes_by_label' in stats:
            print(f"\n   Top Node Types:")
            for label, count in list(stats['nodes_by_label'].items())[:5]:
                print(f"     {label:20} {count:8,}")

    # Quality metrics
    if 'quality_metrics' in results:
        quality = results['quality_metrics']
        score = quality.get('quality_score', 0)
        score_emoji = "🏆" if score >= 80 else "⚠️" if score >= 60 else "❌"
        print(f"\n{score_emoji} Graph Quality Score: {score}/100")

        if 'orphan_nodes' in quality:
            print(f"   Orphan Nodes: {quality['orphan_nodes']}")
        if 'connectivity_ratio' in quality:
            print(f"   Connectivity: {quality['connectivity_ratio']:.1%}")
        if 'relationship_types' in quality:
            print(f"   Relationship Types: {quality['relationship_types']}")

    # Validation results
    if 'validation_results' in results:
        print(f"\n🔍 Validation Scores:")
        for val_name, val_result in results['validation_results'].items():
            if isinstance(val_result, dict) and 'score' in val_result:
                score = val_result['score']
                emoji = "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"
                clean_name = val_name.replace('_', ' ').title()
                print(f"   {emoji} {clean_name}: {score}/100")

    # Error information
    if results.get('status') == 'error':
        print(f"\n❌ Error: {results.get('error', 'Unknown error')}")


async def main():
    """Main entry point for the ADK pipeline."""
    parser = argparse.ArgumentParser(
        description="Run the ADK-Enhanced Dynamic Knowledge Graph Pipeline"
    )

    # Pipeline options
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run in demo mode with limited files"
    )
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Don't reset the graph before building"
    )
    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="Force regeneration of all plans (ignore cached)"
    )
    parser.add_argument(
        "--limit-files",
        type=int,
        help="Limit number of text files to process"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        help="Custom data directory path"
    )
    parser.add_argument(
        "--llm-model",
        type=str,
        default="gpt-4o-mini",
        choices=["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
        help="LLM model to use (default: gpt-4o-mini)"
    )
    parser.add_argument(
        "--no-validation",
        action="store_true",
        help="Skip quality validation"
    )

    # Output options
    parser.add_argument(
        "--output",
        type=str,
        help="Save detailed results to JSON file"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Minimal output"
    )
    parser.add_argument(
        "--view-plans",
        action="store_true",
        help="View generated plans"
    )

    args = parser.parse_args()

    # Print banner unless quiet mode
    if not args.quiet:
        print_banner()

    # Demo mode settings
    if args.demo:
        if not args.quiet:
            print("🎭 "*20)
            print("DEMO MODE ACTIVATED")
            print("🎭 "*20)
            print("\nThis will:")
            print("1. Use LLM to analyze your data")
            print("2. Generate intelligent plans")
            print("3. Build a small graph (limited files)")
            print("4. Validate quality at each step")
            print("5. Save all results\n")

        limit_files = 3
    else:
        limit_files = args.limit_files

    # View plans if requested
    if args.view_plans:
        plans_dir = "generated_plans"
        adk_results_file = os.path.join(plans_dir, "adk_pipeline_results.json")

        if os.path.exists(adk_results_file):
            with open(adk_results_file, 'r') as f:
                adk_results = json.load(f)

            print("\n" + "="*60)
            print("ADK PIPELINE RESULTS")
            print("="*60)

            # Show generated plans
            if 'generated_plans' in adk_results:
                plans = adk_results['generated_plans']

                if 'goal' in plans:
                    print("\n🎯 Generated Goal:")
                    print(json.dumps(plans['goal'], indent=2))

                if 'file_selection' in plans:
                    selection = plans['file_selection']
                    print(f"\n📂 File Selection:")
                    print(f"  CSV files: {len(selection.get('approved_csv_files', []))}")
                    print(f"  Text files: {len(selection.get('approved_text_files', []))}")

                if 'construction_plan' in plans:
                    const_plan = plans['construction_plan']
                    print(f"\n🏗️  Construction Plan:")
                    nodes = [k for k, v in const_plan.items() if v.get('construction_type') == 'node']
                    rels = [k for k, v in const_plan.items() if v.get('construction_type') == 'relationship']
                    print(f"  Nodes: {', '.join(nodes[:5])}")
                    print(f"  Relationships: {', '.join(rels[:5])}")

            # Show validation results
            if 'validation_results' in adk_results:
                print("\n🔍 Validation Results:")
                for val_name, val_result in adk_results['validation_results'].items():
                    if isinstance(val_result, dict) and 'score' in val_result:
                        print(f"  {val_name}: {val_result['score']}/100")
                        if 'suggestions' in val_result:
                            print(f"    Suggestions: {', '.join(val_result['suggestions'][:2])}")
        else:
            print("❌ No ADK pipeline results found. Run the pipeline first.")

        return

    # Run the pipeline
    try:
        # Create and run the pipeline
        builder = await create_and_run_adk_dynamic_pipeline(
            reset=not args.no_reset,
            force_regenerate_plans=args.regenerate,
            limit_text_files=limit_files,
            data_dir=args.data_dir,
            llm_model=args.llm_model,
            validate_quality=not args.no_validation
        )

        # Get results
        results = {
            "status": "success",
            "discovered_files": builder.generated_plans.get("discovered_files", {}),
            "goal": builder.generated_plans.get("goal", {}),
            "file_selection": builder.generated_plans.get("file_selection", {}),
            "schema_generation": {
                "nodes_planned": 0,
                "relationships_planned": 0,
                "entity_types": 0,
                "fact_types": 0
            },
            "final_statistics": {},
            "quality_metrics": {},
            "validation_results": builder.validation_results,
            "execution_time_seconds": 0
        }

        # Extract schema info if available
        if "construction_plan" in builder.generated_plans:
            const_plan = builder.generated_plans["construction_plan"]
            results["schema_generation"]["nodes_planned"] = len(
                [v for v in const_plan.values() if v.get('construction_type') == 'node']
            )
            results["schema_generation"]["relationships_planned"] = len(
                [v for v in const_plan.values() if v.get('construction_type') == 'relationship']
            )

        if "extraction_plan" in builder.generated_plans:
            ext_plan = builder.generated_plans["extraction_plan"]
            results["schema_generation"]["entity_types"] = len(ext_plan.get('entity_types', []))
            results["schema_generation"]["fact_types"] = len(ext_plan.get('fact_types', {}))

        # Get final statistics
        stats = builder.get_final_statistics()
        results["final_statistics"] = stats

        # Display results unless quiet
        if not args.quiet:
            print_results(results)

        # Save detailed results if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump({
                    "results": results,
                    "generated_plans": builder.generated_plans,
                    "validation_results": builder.validation_results,
                    "execution_log": builder.execution_log
                }, f, indent=2, default=str)
            print(f"\n💾 Detailed results saved to: {args.output}")

        # Demo mode summary
        if args.demo and not args.quiet:
            print("\n" + "✨ "*20)
            print("DEMO COMPLETE!")
            print("✨ "*20)
            print("\n📋 Check the generated_plans/ directory for:")
            print("  - adk_pipeline_results.json (all results)")
            print("  - Individual plan files")
            print("\n🚀 To run the full pipeline:")
            print("  python run_adk_pipeline.py")
            print("\n🔄 To force new plans:")
            print("  python run_adk_pipeline.py --regenerate")
            print("\n📊 To view plans:")
            print("  python run_adk_pipeline.py --view-plans")

    except Exception as e:
        print(f"\n❌ Pipeline failed: {str(e)}")
        if not args.quiet:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())