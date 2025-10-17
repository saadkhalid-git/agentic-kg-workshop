#!/usr/bin/env python
"""
Supply Chain Knowledge Graph Pipeline Demo

This script demonstrates the complete pipeline for building and querying
a knowledge graph from supply chain data and product reviews.
"""

import asyncio
import warnings
import sys

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Add current directory to path
sys.path.append('.')

from supply_chain_qa_system import SupplyChainQASystem


async def main():
    """Run the complete demo."""

    print("\n" + "="*70)
    print(" SUPPLY CHAIN KNOWLEDGE GRAPH PIPELINE DEMO")
    print("="*70)
    print("\nThis demo will:")
    print("1. Build a domain graph from CSV supply chain data")
    print("2. Extract entities from product review markdown files")
    print("3. Resolve entities between the two graphs")
    print("4. Answer questions using GraphRAG retrieval")
    print("\n" + "="*70)

    # Initialize the system
    print("\n🔧 Initializing system...")
    system = SupplyChainQASystem()

    # Build the complete knowledge graph
    print("\n📊 Building knowledge graph...")
    print("   (Processing 3 review files for demo speed)\n")

    results = await system.build_complete_graph(
        reset=True,  # Reset graph to start fresh
        limit_markdown_files=3  # Process only 3 files for demo
    )

    # Demonstration queries
    print("\n" + "="*70)
    print(" Q&A DEMONSTRATION")
    print("="*70)

    test_queries = [
        "What products are available and their prices?",
        "List all suppliers located in Sweden",
        "Which suppliers provide parts for the Uppsala Sofa?",
        "What quality issues are mentioned in product reviews?",
        "Which assemblies are used in the Gothenburg Table?",
        "Find suppliers that specialize in wood products"
    ]

    for i, question in enumerate(test_queries, 1):
        print(f"\n📌 Query {i}:")
        print(f"Q: {question}")

        answer = system.ask_question(question)

        # Truncate long answers for display
        if len(answer) > 300:
            display_answer = answer[:300] + "..."
        else:
            display_answer = answer

        print(f"A: {display_answer}")
        print("-" * 70)

    # Interactive mode option
    print("\n" + "="*70)
    print(" DEMO COMPLETE")
    print("="*70)
    print("\nThe knowledge graph is now ready for queries!")
    print("\nTo run interactive Q&A, uncomment the line below:")
    print("# system.interactive_qa()")

    # Uncomment for interactive mode:
    # system.interactive_qa()

    return results


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())