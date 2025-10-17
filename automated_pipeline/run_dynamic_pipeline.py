#!/usr/bin/env python3
"""
Entry point for running the Dynamic Knowledge Graph Pipeline
This pipeline generates plans dynamically based on data analysis
"""

import sys
import os
import asyncio
import argparse
from datetime import datetime
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import dynamic pipeline components
from automated_pipeline.pipeline.dynamic_builder import DynamicKnowledgeGraphBuilder, create_and_run_dynamic_pipeline

# Import environment loading
from dotenv import load_dotenv


def setup_environment():
    """Load environment variables and validate setup."""
    # Load .env file
    load_dotenv()

    # Check required environment variables
    required_vars = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "NEO4J_URI": os.getenv("NEO4J_URI"),
        "NEO4J_USERNAME": os.getenv("NEO4J_USERNAME"),
        "NEO4J_PASSWORD": os.getenv("NEO4J_PASSWORD")
    }

    missing = [var for var, value in required_vars.items() if not value]

    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"  - {var}")
        print("\nPlease set these in your .env file or environment")
        return False

    return True


def print_generated_plans(plans_file: str = "generated_plans/all_generated_plans.json"):
    """Print a summary of the generated plans."""
    if not os.path.exists(plans_file):
        print("No plans file found")
        return

    with open(plans_file, 'r') as f:
        plans = json.load(f)

    print("\n" + "="*60)
    print("📋 GENERATED PLANS SUMMARY")
    print("="*60)

    # Goal
    if "goal" in plans:
        goal = plans["goal"]
        print(f"\n🎯 Goal: {goal.get('kind_of_graph', 'Unknown')}")
        print(f"   {goal.get('description', '')[:100]}...")

    # File Selection
    if "file_selection" in plans:
        selection = plans["file_selection"]
        print(f"\n📂 Files Selected:")
        print(f"   CSV: {len(selection.get('approved_csv_files', []))} files")
        print(f"   Text: {len(selection.get('approved_text_files', []))} files")

    # Construction Plan
    if "construction_plan" in plans:
        construction = plans["construction_plan"]
        nodes = [k for k, v in construction.items() if v.get('construction_type') == 'node']
        rels = [k for k, v in construction.items() if v.get('construction_type') == 'relationship']
        print(f"\n🏗️ Construction Plan:")
        print(f"   Nodes: {', '.join(nodes)}")
        print(f"   Relationships: {', '.join(rels)}")

    # Extraction Plan
    if "extraction_plan" in plans:
        extraction = plans["extraction_plan"]
        print(f"\n📝 Extraction Plan:")
        print(f"   Entity Types: {', '.join(extraction.get('entity_types', []))}")
        print(f"   Fact Types: {', '.join(extraction.get('fact_types', {}).keys())}")

    print("="*60 + "\n")


async def run_pipeline(args):
    """Run the dynamic knowledge graph pipeline with given arguments."""

    print("\n" + "🤖 "*20)
    print("DYNAMIC KNOWLEDGE GRAPH PIPELINE")
    print("🤖 "*20 + "\n")

    # Setup environment
    if not setup_environment():
        return 1

    # Set data directory if provided
    data_dir = args.data_dir if args.data_dir else None

    # Create builder
    builder = DynamicKnowledgeGraphBuilder(data_dir=data_dir)

    try:
        # Run the pipeline
        results = await builder.build_complete_graph(
            reset=not args.no_reset,
            force_regenerate_plans=args.regenerate,
            limit_text_files=args.limit
        )

        # Save results if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n📁 Results saved to: {args.output}")

        # Print generated plans if requested
        if args.show_plans:
            print_generated_plans()

        # Print summary
        if results['status'] == 'success':
            print("\n" + "="*60)
            print("✅ PIPELINE COMPLETED SUCCESSFULLY")
            print("="*60)
            print(f"\nExecution Time: {results['execution_time_seconds']:.2f} seconds")

            if 'final_statistics' in results:
                stats = results['final_statistics']
                print(f"Total Nodes: {stats['total_nodes']:,}")
                print(f"Total Relationships: {stats['total_relationships']:,}")

            print("\n📁 Generated plans saved in: generated_plans/")
            print("   - approved_user_goal.json")
            print("   - approved_files.json")
            print("   - construction_plan.json")
            print("   - extraction_plan.json")
            print("   - all_generated_plans.json")

            return 0
        else:
            print("\n❌ Pipeline failed:")
            print(results.get('error', 'Unknown error'))
            return 1

    except KeyboardInterrupt:
        print("\n\n⚠️ Pipeline interrupted by user")
        return 2

    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 3


async def run_demo():
    """Run a quick demo with dynamic plan generation."""
    print("\n" + "🎭 "*20)
    print("DYNAMIC DEMO MODE")
    print("🎭 "*20 + "\n")

    print("This will:")
    print("1. Analyze available data files")
    print("2. Automatically determine the goal")
    print("3. Select relevant files")
    print("4. Generate schema dynamically")
    print("5. Build the knowledge graph")
    print("6. Save all plans as JSON\n")

    # Setup environment
    if not setup_environment():
        return 1

    # Run with limited files
    builder = await create_and_run_dynamic_pipeline(
        reset=True,
        force_regenerate_plans=True,  # Always regenerate in demo
        limit_text_files=3
    )

    print("\n✅ Demo completed!")
    print("\n📋 Check the generated_plans/ directory to see:")
    print("  - How the goal was determined")
    print("  - Which files were selected and why")
    print("  - The schema that was generated")
    print("  - Entity and fact types for extraction")

    # Print plans summary
    print_generated_plans()

    return 0


def view_plans():
    """View existing generated plans."""
    plans_dir = "generated_plans"

    if not os.path.exists(plans_dir):
        print("❌ No generated plans found. Run the pipeline first.")
        return 1

    print("\n📂 Generated Plans:")
    print("="*60)

    plan_files = [
        ("Goal", "approved_user_goal.json"),
        ("File Selection", "approved_files.json"),
        ("Construction Plan", "construction_plan.json"),
        ("Extraction Plan", "extraction_plan.json")
    ]

    for title, filename in plan_files:
        filepath = os.path.join(plans_dir, filename)
        if os.path.exists(filepath):
            print(f"\n📋 {title} ({filename}):")
            with open(filepath, 'r') as f:
                data = json.load(f)
                # Print summary based on file type
                if "goal" in filename:
                    print(f"  Graph Type: {data.get('kind_of_graph', 'N/A')}")
                    print(f"  Description: {data.get('description', '')[:150]}...")
                elif "files" in filename:
                    print(f"  CSV Files: {len(data.get('approved_csv_files', []))}")
                    print(f"  Text Files: {len(data.get('approved_text_files', []))}")
                elif "construction" in filename:
                    nodes = [k for k, v in data.items() if v.get('construction_type') == 'node']
                    rels = [k for k, v in data.items() if v.get('construction_type') == 'relationship']
                    print(f"  Nodes: {', '.join(nodes[:5])}")
                    print(f"  Relationships: {', '.join(rels[:5])}")
                elif "extraction" in filename:
                    print(f"  Entity Types: {', '.join(data.get('entity_types', [])[:8])}")
                    print(f"  Fact Types: {len(data.get('fact_types', {}))}")

    print("\n" + "="*60)
    return 0


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Dynamic Knowledge Graph Pipeline - Generates plans based on data analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This pipeline dynamically analyzes your data to:
  1. Determine the appropriate knowledge graph goal
  2. Select relevant files based on content
  3. Generate schema from file structure
  4. Build the complete knowledge graph

Examples:
  # Run full dynamic pipeline
  python run_dynamic_pipeline.py

  # Run demo with plan generation
  python run_dynamic_pipeline.py --demo

  # Force regeneration of all plans
  python run_dynamic_pipeline.py --regenerate

  # View existing plans
  python run_dynamic_pipeline.py --view-plans

  # Use custom data directory
  python run_dynamic_pipeline.py --data-dir /path/to/data

  # Save detailed results
  python run_dynamic_pipeline.py --output results.json --show-plans
        """
    )

    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run demo mode with dynamic plan generation'
    )

    parser.add_argument(
        '--no-reset',
        action='store_true',
        help='Do not reset the graph before building'
    )

    parser.add_argument(
        '--regenerate',
        action='store_true',
        help='Force regeneration of all plans (ignore existing)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        metavar='N',
        help='Limit number of text files to process'
    )

    parser.add_argument(
        '--data-dir',
        type=str,
        metavar='DIR',
        help='Directory containing data files'
    )

    parser.add_argument(
        '--output',
        type=str,
        metavar='FILE',
        help='Save results to JSON file'
    )

    parser.add_argument(
        '--show-plans',
        action='store_true',
        help='Show generated plans summary after execution'
    )

    parser.add_argument(
        '--view-plans',
        action='store_true',
        help='View existing generated plans and exit'
    )

    args = parser.parse_args()

    # View plans and exit if requested
    if args.view_plans:
        return view_plans()

    # Run demo if requested
    if args.demo:
        return asyncio.run(run_demo())

    # Run the pipeline
    return asyncio.run(run_pipeline(args))


if __name__ == "__main__":
    sys.exit(main())