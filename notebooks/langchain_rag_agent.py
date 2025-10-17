"""
LangChain RAG Agent for GraphRAG Retrieval

This agent implements multiple retrieval strategies using LangChain
for question answering over the knowledge graph.
"""

from typing import Dict, Any, List, Optional
from langchain_neo4j import Neo4jGraph, Neo4jVector
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import GraphCypherQAChain
from langchain.prompts import PromptTemplate
from langchain_core.documents import Document
from langgraph.graph import StateGraph, END
from typing import TypedDict


class RAGState(TypedDict):
    """State for the RAG workflow."""
    question: str
    query_type: str
    vector_results: List[str]
    cypher_results: str
    trace_results: str
    final_context: str
    answer: str


class LangChainRAGAgent:
    """Agent for GraphRAG retrieval using LangChain."""

    def __init__(
        self,
        neo4j_uri: str,
        neo4j_username: str,
        neo4j_password: str,
        openai_model: str = "gpt-4o",
        embedding_model: str = "text-embedding-3-large",
        temperature: float = 0
    ):
        """
        Initialize the RAG agent.

        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_username: Neo4j username
            neo4j_password: Neo4j password
            openai_model: OpenAI model for generation
            embedding_model: OpenAI model for embeddings
            temperature: Temperature for generation
        """
        self.name = "LangChainRAGAgent"
        self.description = "Multi-strategy retrieval and Q&A using LangChain GraphRAG"

        # Initialize Neo4j Graph
        self.graph = Neo4jGraph(
            url=neo4j_uri,
            username=neo4j_username,
            password=neo4j_password,
            database="neo4j"
        )

        # Initialize LLM and embeddings
        self.llm = ChatOpenAI(model=openai_model, temperature=temperature)
        self.embeddings = OpenAIEmbeddings(model=embedding_model)

        # Initialize vector store (will be set up later)
        self.vector_store = None

        # Initialize Cypher chain
        self.cypher_chain = None

        # Connection details for vector store
        self.neo4j_uri = neo4j_uri
        self.neo4j_username = neo4j_username
        self.neo4j_password = neo4j_password

    def setup_vector_store(
        self,
        index_name: str = "chunk_embedding_index",
        node_label: str = "Chunk",
        text_property: str = "text",
        embedding_property: str = "embedding"
    ) -> None:
        """
        Set up the vector store for hybrid search.

        Args:
            index_name: Name of the vector index
            node_label: Label of nodes to search
            text_property: Property containing text
            embedding_property: Property containing embeddings
        """
        # Custom retrieval query with graph traversal
        retrieval_query = """
        // node is the chunk found by vector/hybrid search
        // score is the similarity score

        // Get parent document for broader context
        OPTIONAL MATCH (doc:Document)-[:HAS_CHUNK]->(node)

        // Get entities mentioned in this chunk
        OPTIONAL MATCH (entity:`__Entity__`)-[:MENTIONED_IN]->(node)

        // Get corresponding domain nodes
        OPTIONAL MATCH (entity)-[:CORRESPONDS_TO]->(product:Product)

        // Get supply chain info for products
        OPTIONAL MATCH (product)-[:Contains]->(assembly:Assembly)
        OPTIONAL MATCH (assembly)<-[:Is_Part_Of]-(part:Part)
        OPTIONAL MATCH (part)-[:Supplied_By]->(supplier:Supplier)

        WITH node, score, doc,
             collect(DISTINCT entity.name) AS entities,
             collect(DISTINCT product.product_name) AS products,
             collect(DISTINCT assembly.assembly_name)[..3] AS assemblies,
             collect(DISTINCT part.part_name)[..5] AS parts,
             collect(DISTINCT supplier.name)[..3] AS suppliers

        RETURN
            node.text AS text,
            score,
            CASE WHEN doc.path IS NOT NULL THEN doc.path ELSE 'Unknown' END AS source_document,
            entities,
            products,
            assemblies,
            parts,
            suppliers
        """

        try:
            self.vector_store = Neo4jVector.from_existing_index(
                embedding=self.embeddings,
                url=self.neo4j_uri,
                username=self.neo4j_username,
                password=self.neo4j_password,
                index_name=index_name,
                node_label=node_label,
                text_node_property=text_property,
                embedding_node_property=embedding_property,
                search_type="hybrid",
                retrieval_query=retrieval_query
            )
            print(f"✅ Vector store initialized with index: {index_name}")
        except Exception as e:
            print(f"⚠️  Vector store initialization failed: {str(e)}")
            print("   Falling back to basic configuration...")

            # Fallback to simpler configuration
            self.vector_store = Neo4jVector.from_existing_index(
                embedding=self.embeddings,
                url=self.neo4j_uri,
                username=self.neo4j_username,
                password=self.neo4j_password,
                index_name=index_name
            )

    def setup_cypher_chain(self) -> None:
        """Set up the Cypher QA chain for structured queries."""
        # For now, we'll use direct Cypher queries instead of the chain
        # due to compatibility issues with newer langchain versions
        self.cypher_chain = None
        print("  Note: Using direct Cypher queries instead of GraphCypherQAChain")

    def hybrid_search(self, question: str, k: int = 5) -> List[Document]:
        """
        Perform hybrid vector + full-text search.

        Args:
            question: Query string
            k: Number of results to return

        Returns:
            List of relevant documents with metadata
        """
        if not self.vector_store:
            return []

        try:
            return self.vector_store.similarity_search(question, k=k)
        except Exception as e:
            print(f"Hybrid search error: {str(e)}")
            return []

    def cypher_query(self, question: str) -> str:
        """
        Generate and execute a Cypher query from natural language.

        Args:
            question: Natural language question

        Returns:
            Query results as string
        """
        # Generate Cypher query using LLM
        cypher_prompt = f"""
        Convert this question into a Neo4j Cypher query:

        Question: {question}

        The graph contains:
        - Product nodes with properties: product_id, product_name, price, description
        - Assembly nodes with properties: assembly_id, assembly_name, quantity
        - Part nodes with properties: part_id, part_name, quantity
        - Supplier nodes with properties: supplier_id, name, city, country, specialty
        - Relationships: (Product)-[:Contains]->(Assembly), (Part)-[:Is_Part_Of]->(Assembly), (Part)-[:Supplied_By]->(Supplier)

        Return ONLY the Cypher query, no explanation.
        """

        try:
            # Generate Cypher query
            response = self.llm.invoke(cypher_prompt)
            cypher = response.content.strip()

            # Remove markdown code block syntax if present
            if cypher.startswith("```"):
                lines = cypher.split("\n")
                cypher = "\n".join(lines[1:-1])  # Remove first and last line
                cypher = cypher.replace("```cypher", "").replace("```", "").strip()

            # Execute query
            results = self.graph.query(cypher)

            if results:
                return str(results)
            else:
                return "No results found"
        except Exception as e:
            return f"Cypher query error: {str(e)}"

    def trace_issue_to_supplier(
        self,
        product_name: Optional[str] = None,
        issue_keyword: Optional[str] = None
    ) -> str:
        """
        Trace quality issues to suppliers through the supply chain.

        Args:
            product_name: Name of the product (optional)
            issue_keyword: Issue keyword to search for (optional)

        Returns:
            Formatted tracing results
        """
        # Build dynamic query based on inputs
        where_clauses = []
        params = {}

        if product_name:
            where_clauses.append("p.product_name CONTAINS $product_name")
            params["product_name"] = product_name

        if issue_keyword:
            params["issue_keyword"] = issue_keyword

        where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        # Main tracing query
        cypher = f"""
        MATCH (p:Product){where_clause}
        OPTIONAL MATCH (p)-[:Contains]->(a:Assembly)
        OPTIONAL MATCH (part:Part)-[:Is_Part_Of]->(a)
        OPTIONAL MATCH (part)-[:Supplied_By]->(s:Supplier)

        // Find related issues if keyword provided
        {"OPTIONAL MATCH (issue:Issue) WHERE issue.name CONTAINS $issue_keyword" if issue_keyword else ""}

        WITH p, a, part, s
        {"  , issue" if issue_keyword else ""}

        RETURN DISTINCT
            p.product_name AS product,
            collect(DISTINCT a.assembly_name)[..5] AS assemblies,
            collect(DISTINCT part.part_name)[..10] AS parts,
            collect(DISTINCT s.name)[..5] AS suppliers,
            collect(DISTINCT s.city + ', ' + s.country)[..5] AS supplier_locations
            {"  , collect(DISTINCT issue.name)[..5] AS related_issues" if issue_keyword else ""}
        LIMIT 10
        """

        try:
            results = self.graph.query(cypher, params)
            return self._format_trace_results(results, issue_keyword is not None)
        except Exception as e:
            return f"Tracing error: {str(e)}"

    def _format_trace_results(self, results: List[Dict], include_issues: bool = False) -> str:
        """
        Format tracing results into readable text.

        Args:
            results: Query results
            include_issues: Whether to include issue information

        Returns:
            Formatted string
        """
        if not results:
            return "No supply chain information found."

        output = []
        for r in results:
            output.append(f"📦 Product: {r.get('product', 'Unknown')}")

            if r.get('assemblies'):
                output.append(f"   🔧 Assemblies: {', '.join(r['assemblies'])}")

            if r.get('parts'):
                output.append(f"   🔩 Parts: {', '.join(r['parts'])}")

            if r.get('suppliers'):
                output.append(f"   🏭 Suppliers: {', '.join(r['suppliers'])}")

            if r.get('supplier_locations'):
                output.append(f"   📍 Locations: {', '.join(r['supplier_locations'])}")

            if include_issues and r.get('related_issues'):
                output.append(f"   ⚠️  Issues: {', '.join(r['related_issues'])}")

            output.append("---")

        return "\n".join(output)

    def answer_question(
        self,
        question: str,
        use_vector: bool = True,
        use_cypher: bool = True,
        use_trace: bool = False
    ) -> str:
        """
        Answer a question using multiple retrieval strategies.

        Args:
            question: User's question
            use_vector: Whether to use vector search
            use_cypher: Whether to use Cypher queries
            use_trace: Whether to use supply chain tracing

        Returns:
            Generated answer
        """
        context_parts = []

        # Vector search for semantic similarity
        if use_vector and self.vector_store:
            docs = self.hybrid_search(question, k=3)
            if docs:
                vector_context = "\n\n".join([doc.page_content for doc in docs])
                context_parts.append(f"From reviews and documentation:\n{vector_context}")

        # Cypher query for structured data
        if use_cypher:
            # Always try Cypher first for structured data questions
            cypher_result = self.cypher_query(question)
            if cypher_result and "error" not in cypher_result.lower() and cypher_result != "No results found":
                context_parts.append(f"From structured data:\n{cypher_result}")

        # Supply chain tracing if relevant
        if use_trace:
            # Extract product name from question if present
            product_keywords = ["sofa", "chair", "table", "desk", "lamp", "bed", "dresser", "bookshelf", "nightstand"]
            product_name = None
            for keyword in product_keywords:
                if keyword.lower() in question.lower():
                    product_name = keyword
                    break

            if product_name:
                trace_result = self.trace_issue_to_supplier(product_name=product_name)
                context_parts.append(f"Supply chain trace:\n{trace_result}")

        # Generate final answer
        if not context_parts:
            return "I couldn't find relevant information to answer your question."

        context = "\n\n".join(context_parts)

        prompt = f"""
        Answer the following question based on the provided context.
        Be specific and cite relevant information from the context.

        Context:
        {context}

        Question: {question}

        Answer:
        """

        response = self.llm.invoke(prompt)
        return response.content

    def create_langgraph_workflow(self) -> StateGraph:
        """
        Create a LangGraph workflow for intelligent query routing.

        Returns:
            Compiled LangGraph workflow
        """
        # Define workflow functions
        def classify_query(state: RAGState) -> RAGState:
            """Classify the query type."""
            question = state["question"].lower()

            if any(word in question for word in ["supplier", "part", "assembly", "manufacture"]):
                state["query_type"] = "structured"
            elif any(word in question for word in ["issue", "problem", "quality", "review", "complaint"]):
                state["query_type"] = "unstructured"
            elif any(word in question for word in ["trace", "root cause", "responsible", "why"]):
                state["query_type"] = "trace"
            else:
                state["query_type"] = "both"

            return state

        def vector_search(state: RAGState) -> RAGState:
            """Perform vector search."""
            if self.vector_store:
                docs = self.hybrid_search(state["question"], k=3)
                state["vector_results"] = [doc.page_content for doc in docs]
            else:
                state["vector_results"] = []
            return state

        def cypher_search(state: RAGState) -> RAGState:
            """Execute Cypher search."""
            state["cypher_results"] = self.cypher_query(state["question"])
            return state

        def trace_search(state: RAGState) -> RAGState:
            """Perform supply chain tracing."""
            state["trace_results"] = self.trace_issue_to_supplier()
            return state

        def aggregate_results(state: RAGState) -> RAGState:
            """Combine results from multiple sources."""
            context_parts = []

            if state.get("vector_results"):
                context_parts.append("From reviews:\n" + "\n".join(state["vector_results"]))

            if state.get("cypher_results"):
                context_parts.append(f"From structured data:\n{state['cypher_results']}")

            if state.get("trace_results"):
                context_parts.append(f"Supply chain trace:\n{state['trace_results']}")

            state["final_context"] = "\n\n".join(context_parts)
            return state

        def generate_answer(state: RAGState) -> RAGState:
            """Generate final answer."""
            prompt = f"""
            Answer this question based on the context:

            Context:
            {state['final_context']}

            Question: {state['question']}

            Answer:
            """

            response = self.llm.invoke(prompt)
            state["answer"] = response.content
            return state

        # Build the workflow
        workflow = StateGraph(RAGState)

        # Add nodes
        workflow.add_node("classify", classify_query)
        workflow.add_node("vector", vector_search)
        workflow.add_node("cypher", cypher_search)
        workflow.add_node("trace", trace_search)
        workflow.add_node("aggregate", aggregate_results)
        workflow.add_node("generate", generate_answer)

        # Add edges
        workflow.set_entry_point("classify")

        # Conditional routing based on query type
        def route_query(state):
            return state["query_type"]

        workflow.add_conditional_edges(
            "classify",
            route_query,
            {
                "structured": "cypher",
                "unstructured": "vector",
                "trace": "trace",
                "both": "vector"
            }
        )

        # Connect remaining nodes
        workflow.add_edge("vector", "cypher")
        workflow.add_edge("cypher", "aggregate")
        workflow.add_edge("trace", "aggregate")
        workflow.add_edge("aggregate", "generate")
        workflow.add_edge("generate", END)

        return workflow.compile()

    def get_sample_queries(self) -> List[str]:
        """
        Get sample queries for testing.

        Returns:
            List of sample queries
        """
        return [
            "Which suppliers are responsible for quality issues in the Uppsala Sofa?",
            "What are the most common problems across all furniture products?",
            "Find all products that use parts from suppliers in Sweden",
            "Which assembly has the most customer complaints?",
            "What quality issues are mentioned in the Stockholm Chair reviews?",
            "List all suppliers and their specialties",
            "How many parts does the Gothenburg Table have?",
            "What features do customers like about the Malmo Desk?",
            "Which products have durability issues?",
            "Trace the supply chain for the Linkoping Bed"
        ]