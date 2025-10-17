# PhD Candidate Technical Exercise: Adaptive Supply Chain Intelligence System

## Case Study

You've been hired as the lead architect for **GlobalTech Industries**, a Fortune 500 company that has recently acquired three smaller companies. The company is struggling with a critical problem: they have massive amounts of data across different systems, but no way to get intelligent answers to complex business questions.

The CEO recently asked: *"Which suppliers are causing the most customer complaints about our premium products?"*
It took the analytics team **3 weeks** of manual work across spreadsheets and documents to find the answer.

Your mission is to build an **Adaptive Intelligence System** that can automatically understand diverse data sources and answer such complex questions in seconds, not weeks.

## The Challenge

### Current Situation
GlobalTech has:
- **15+ CSV files** with structured business data (products, suppliers, assemblies, parts, etc.)
- **100+ text documents** including customer reviews, quality reports, and supplier assessments
- **New data arriving weekly** from acquisitions and partnerships
- **No standardized schema** - each acquisition brought their own data formats

### The Problem
Current approaches have failed:
1. **Traditional databases** can't handle the unstructured text documents
2. **Search engines** find documents but can't answer relationship questions
3. **Data warehouses** require manual ETL for each new data source
4. **BI tools** need predefined queries and can't adapt to new data

### Your Task
Build a system that can:
1. **Automatically understand** what data is available (CSVs and text files)
2. **Intelligently connect** information across different sources
3. **Answer complex questions** that span multiple data types
4. **Adapt to new data** without manual reconfiguration

## Technical Requirements

### Core Capabilities

1. **Data Understanding**
   - Analyze any CSV file to understand its structure and content
   - Process text documents to extract meaningful information
   - Identify relationships between different data sources
   - Work with data you've never seen before

2. **Intelligent Connections**
   - Connect entities across different files (e.g., "Product X" in reviews with product_id in CSV)
   - Understand implicit relationships (e.g., suppliers → parts → products → reviews)
   - Handle variations in naming (e.g., "ACME Corp", "Acme Corporation", "ACME")

3. **Question Answering**
   - Answer questions that require combining multiple data sources
   - Provide evidence/sources for answers
   - Handle both factual and analytical questions

4. **Adaptability**
   - Add new data sources without changing code
   - Learn the structure of new datasets automatically
   - Scale from 10 files to 1000 files

### Example Questions Your System Must Answer

1. **Simple Factual**: "What products does supplier ACME Corp provide parts for?"
2. **Cross-Source**: "Which products with negative reviews use parts from unreliable suppliers?"
3. **Analytical**: "What quality issues are mentioned most frequently for products over $500?"
4. **Relationship**: "Find all suppliers connected to products that have assembly issues"
5. **Temporal**: "How have supplier relationships changed after customer complaints?"

## Provided Data

You'll work with data from the `data/` directory:

### Structured Data (CSV files)
- `products.csv` - Product catalog with IDs, names, prices
- `suppliers.csv` - Supplier information
- `parts.csv` - Component parts details
- `assemblies.csv` - Product assembly information
- `part_supplier_mapping.csv` - Which supplier provides which parts
- `assembly_parts.csv` - Parts used in each assembly
- Additional relationship files...

### Unstructured Data (Text files)
- `product_reviews/*.txt` - Customer reviews for products
- `quality_reports/*.md` - Quality assessment reports
- `supplier_assessments/*.txt` - Supplier evaluation documents

## Constraints & Considerations

1. **No Manual Schema Definition**: Your system must figure out the data structure automatically
2. **Mixed Data Types**: Must handle both structured (CSV) and unstructured (text) data
3. **Scalability**: Design should work for 10x or 100x more files
4. **Explainability**: Users need to understand how answers were derived
5. **Performance**: Complex questions should be answered in < 30 seconds

## Deliverables

### 1. System Architecture (40%)
- Design document explaining your approach
- How does your system understand new data?
- How does it connect information across sources?
- How does it answer complex questions?

### 2. Implementation (40%)
- Working Python code that demonstrates core capabilities
- Must work with the provided data files
- Should be extensible to new data sources
- Include clear documentation

### 3. Demonstration (20%)
- Answer the 5 example questions using your system
- Add a new CSV file and show the system adapts
- Add a new text document and show it's incorporated
- Answer a complex question that you define

## Evaluation Criteria

Your solution will be evaluated on:

1. **Intelligence** (30%)
   - How well does it understand data without manual configuration?
   - Can it discover non-obvious relationships?
   - Does it handle ambiguity and variations?

2. **Adaptability** (25%)
   - How easily can new data sources be added?
   - Does it require code changes for new data?
   - Can it handle different data formats?

3. **Accuracy** (25%)
   - Are the answers correct?
   - Is the evidence/reasoning sound?
   - Does it handle edge cases?

4. **Architecture** (20%)
   - Is the design scalable?
   - Is it maintainable?
   - Are the components well-separated?

## Hints & Guidance

Consider these questions as you design your solution:

1. **Data Understanding**: What if the system could "learn" what each file contains and how it relates to others?

2. **Relationship Discovery**: How do humans understand that "supplier_id" in one file relates to "id" in suppliers.csv?

3. **Entity Recognition**: How can you identify that "Uppsala Sofa" in a review refers to product_id "P003"?

4. **Information Storage**: What structure would let you efficiently store and query both facts and relationships?

5. **Question Decomposition**: How would you break down "Which suppliers are causing quality issues?" into answerable sub-questions?

6. **Flexibility vs Structure**: How can you balance structured data processing with flexible text understanding?

## Bonus Challenges (Optional)

For candidates who finish early:

1. **Multi-hop Reasoning**: Answer questions requiring 4+ connected data sources
2. **Confidence Scoring**: Provide confidence levels for answers
3. **Contradiction Detection**: Identify conflicting information across sources
4. **Trend Analysis**: Identify patterns over time or across categories
5. **Recommendation Engine**: Suggest suppliers to replace based on quality metrics

## Getting Started

1. Examine the data files to understand their structure
2. Think about how different pieces of information connect
3. Design a system that can learn these connections automatically
4. Implement core components incrementally
5. Test with simple questions first, then complex ones

## Submission

Submit your solution as a Git repository containing:
- `README.md` - Setup instructions and architecture overview
- `src/` - Your implementation code
- `docs/` - Design documents and approach explanation
- `demo.ipynb` or `demo.py` - Demonstration of capabilities
- `results.md` - Answers to the example questions with explanations

## Time Limit

You have **1 week** to complete this exercise. Focus on demonstrating the core concepts rather than building a production-ready system.

## Tips for Success

- Start by understanding the data and relationships
- Build incrementally - get simple questions working first
- Focus on adaptability over hard-coded solutions
- Think about how the system learns vs what you program
- Consider how different technologies might work together
- Document your thought process and design decisions

## Questions?

This exercise is intentionally open-ended to assess your problem-solving approach. Make reasonable assumptions and document them. The goal is to see how you tackle complex, ambiguous problems that require innovative solutions.

Good luck! We're excited to see your approach to this challenging problem.

---

*Note: This exercise simulates real-world challenges in enterprise data integration and intelligence. The best solutions will demonstrate deep understanding of both the business problem and technical possibilities.*