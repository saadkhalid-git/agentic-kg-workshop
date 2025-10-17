#!/usr/bin/env python3
"""
Entry point for running the Automated Knowledge Graph Pipeline
Run this script to build the complete knowledge graph without human intervention
"""

import sys
import os
import asyncio
import argparse
from datetime import datetime
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import pipeline components
from automated_pipeline.pipeline.builder import KnowledgeGraphBuilder, create_and_run_pipeline
from automated_pipeline.pipeline.config import PipelineConfig

# Import environment loading
from dotenv import load_dotenv


def setup_environment():
    """Load environment variables and validate setup."""
    # Load .env file
    load_dotenv()

    # Validate environment
    validation = PipelineConfig.validate_environment()

    missing = [key for key, is_set in validation.items() if not is_set and key != "NEO4J_IMPORT_DIR"]

    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"  - {var}")
        print("\nPlease set these in your .env file or environment")
        return False

    return True


async def run_pipeline(args):
    """Run the knowledge graph pipeline with given arguments."""

    print("\n" + "🚀 "*20)
    print("AUTOMATED KNOWLEDGE GRAPH PIPELINE")
    print("🚀 "*20 + "\n")

    # Setup environment
    if not setup_environment():
        return 1

    # Create builder
    builder = KnowledgeGraphBuilder()

    # Override config if needed
    if args.no_reset:
        builder.config.RESET_GRAPH_BEFORE_RUN = False
    if args.limit:
        builder.config.LIMIT_FILES = args.limit
    if args.quiet:
        builder.config.VERBOSE_OUTPUT = False

    try:
        # Run the pipeline
        results = await builder.build_complete_graph(
            reset=not args.no_reset,
            limit_files=args.limit
        )

        # Save results if requested
        if args.output:
            output_file = args.output
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n📁 Results saved to: {output_file}")

        # Run test queries if requested
        if args.test:
            builder.test_with_sample_queries()

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
    """Run a quick demo with limited data."""
    print("\n" + "🎭 "*20)
    print("RUNNING DEMO MODE")
    print("🎭 "*20 + "\n")

    print("This will:")
    print("1. Reset the graph")
    print("2. Process all CSV files")
    print("3. Process 3 review files (for speed)")
    print("4. Resolve entities")
    print("5. Run test queries\n")

    # Setup environment
    if not setup_environment():
        return 1

    # Run with limited files
    builder = await create_and_run_pipeline(
        reset=True,
        limit_files=3,
        test_queries=True
    )

    print("\n✅ Demo completed!")
    print("\nTo run the full pipeline, use: python run_pipeline.py")

    return 0


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Automated Knowledge Graph Pipeline - Build KG from CSV and text data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline with reset
  python run_pipeline.py

  # Run without resetting existing graph
  python run_pipeline.py --no-reset

  # Run with limited files for testing
  python run_pipeline.py --limit 3

  # Run demo mode
  python run_pipeline.py --demo

  # Save results to file
  python run_pipeline.py --output results.json

  # Run with test queries
  python run_pipeline.py --test
        """
    )

    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run demo mode with limited data'
    )

    parser.add_argument(
        '--no-reset',
        action='store_true',
        help='Do not reset the graph before building'
    )

    parser.add_argument(
        '--limit',
        type=int,
        metavar='N',
        help='Limit number of markdown files to process'
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='Run test queries after building'
    )

    parser.add_argument(
        '--output',
        type=str,
        metavar='FILE',
        help='Save results to JSON file'
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Reduce output verbosity'
    )

    parser.add_argument(
        '--config',
        action='store_true',
        help='Show configuration and exit'
    )

    args = parser.parse_args()

    # Show config and exit if requested
    if args.config:
        PipelineConfig.print_config()
        return 0

    # Run demo if requested
    if args.demo:
        return asyncio.run(run_demo())

    # Run the pipeline
    return asyncio.run(run_pipeline(args))


if __name__ == "__main__":
    sys.exit(main())