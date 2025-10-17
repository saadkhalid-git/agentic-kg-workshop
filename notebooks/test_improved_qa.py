#!/usr/bin/env python
"""
Test improved Q&A system with Cypher integration
"""

import asyncio
import warnings
warnings.filterwarnings('ignore')
from dotenv import load_dotenv
load_dotenv()

from supply_chain_qa_system import SupplyChainQASystem


async def test_improved_qa():
    """Test the improved Q&A system."""

    # Initialize system
    system = SupplyChainQASystem()

    # Build graph quickly with 2 files
    print("Building knowledge graph (quick mode)...")
    await system.build_complete_graph(
        reset=True,
        limit_markdown_files=2
    )

    print("\n" + "="*60)
    print("TESTING IMPROVED Q&A SYSTEM")
    print("="*60)

    test_questions = [
        ('Products Query', 'What products are available and their prices?'),
        ('Supplier Location', 'List all suppliers located in Sweden'),
        ('Supply Chain Trace', 'Which suppliers provide parts for the Uppsala Sofa?'),
        ('Quality Issues', 'What quality issues are mentioned in reviews?'),
        ('Assembly Query', 'Which assemblies are used in the Gothenburg Table?'),
    ]

    for title, question in test_questions:
        print(f"\n📌 {title}:")
        print(f"Q: {question}")

        answer = system.ask_question(question)

        # Format answer for display
        if len(answer) > 400:
            display = answer[:400] + "..."
        else:
            display = answer

        print(f"A: {display}")
        print("-"*60)


if __name__ == "__main__":
    asyncio.run(test_improved_qa())