"""
Structured Data Agent for Domain Graph Construction

This agent handles the construction of the domain graph from structured CSV files.
It creates nodes for Products, Assemblies, Parts, and Suppliers, along with their relationships.
"""

from typing import Dict, Any, List, Optional
from neo4j_for_adk import graphdb, tool_success, tool_error


class StructuredDataAgent:
    """Agent for constructing domain graph from structured CSV data."""

    def __init__(self):
        self.name = "StructuredDataAgent"
        self.description = "Constructs domain graph from CSV files with products, suppliers, parts, and assemblies"

    def create_uniqueness_constraint(self, label: str, unique_property_key: str) -> Dict[str, Any]:
        """
        Creates a uniqueness constraint for a node label and property key.

        Args:
            label: The label of the node to create a constraint for
            unique_property_key: The property key that should have unique values

        Returns:
            Dictionary with status and optional error message
        """
        constraint_name = f"{label}_{unique_property_key}_constraint"
        query = f"""CREATE CONSTRAINT `{constraint_name}` IF NOT EXISTS
        FOR (n:`{label}`)
        REQUIRE n.`{unique_property_key}` IS UNIQUE"""

        return graphdb.send_query(query)

    def load_nodes_from_csv(
        self,
        source_file: str,
        label: str,
        unique_column_name: str,
        properties: List[str]
    ) -> Dict[str, Any]:
        """
        Batch load nodes from a CSV file.

        Args:
            source_file: Name of the CSV file in Neo4j import directory
            label: Node label to assign
            unique_column_name: Column to use as unique identifier
            properties: List of properties to import from CSV

        Returns:
            Dictionary with status and optional error message
        """
        query = f"""
        LOAD CSV WITH HEADERS FROM "file:///" + $source_file AS row
        CALL (row) {{
            MERGE (n:$($label) {{ {unique_column_name} : row[$unique_column_name] }})
            FOREACH (k IN $properties | SET n[k] = row[k])
        }} IN TRANSACTIONS OF 1000 ROWS
        """

        return graphdb.send_query(query, {
            "source_file": source_file,
            "label": label,
            "unique_column_name": unique_column_name,
            "properties": properties
        })

    def import_nodes(self, node_construction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Import nodes according to a node construction rule.

        Args:
            node_construction: Dictionary containing:
                - label: Node label
                - source_file: CSV file name
                - unique_column_name: Unique identifier column
                - properties: List of properties to import

        Returns:
            Dictionary with status and optional error message
        """
        # Create uniqueness constraint
        uniqueness_result = self.create_uniqueness_constraint(
            node_construction["label"],
            node_construction["unique_column_name"]
        )

        if uniqueness_result["status"] == "error":
            return uniqueness_result

        # Import nodes from CSV
        return self.load_nodes_from_csv(
            node_construction["source_file"],
            node_construction["label"],
            node_construction["unique_column_name"],
            node_construction["properties"]
        )

    def import_relationships(self, relationship_construction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Import relationships according to a relationship construction rule.

        Args:
            relationship_construction: Dictionary containing:
                - source_file: CSV file name
                - relationship_type: Type of relationship
                - from_node_label: Label of source nodes
                - from_node_column: Column identifying source nodes
                - to_node_label: Label of target nodes
                - to_node_column: Column identifying target nodes
                - properties: List of relationship properties

        Returns:
            Dictionary with status and optional error message
        """
        from_node_column = relationship_construction["from_node_column"]
        to_node_column = relationship_construction["to_node_column"]

        query = f"""
        LOAD CSV WITH HEADERS FROM "file:///" + $source_file AS row
        CALL (row) {{
            MATCH (from_node:$($from_node_label) {{ {from_node_column} : row[$from_node_column] }}),
                  (to_node:$($to_node_label) {{ {to_node_column} : row[$to_node_column] }})
            MERGE (from_node)-[r:$($relationship_type)]->(to_node)
            FOREACH (k IN $properties | SET r[k] = row[k])
        }} IN TRANSACTIONS OF 1000 ROWS
        """

        return graphdb.send_query(query, {
            "source_file": relationship_construction["source_file"],
            "from_node_label": relationship_construction["from_node_label"],
            "from_node_column": relationship_construction["from_node_column"],
            "to_node_label": relationship_construction["to_node_label"],
            "to_node_column": relationship_construction["to_node_column"],
            "relationship_type": relationship_construction["relationship_type"],
            "properties": relationship_construction["properties"]
        })

    def construct_domain_graph(self, construction_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Construct the complete domain graph from a construction plan.

        Args:
            construction_plan: Dictionary mapping entity names to construction rules

        Returns:
            Dictionary with construction statistics and any errors
        """
        results = {
            "nodes_created": [],
            "relationships_created": [],
            "errors": []
        }

        # First, import all nodes
        node_constructions = [
            (key, value) for key, value in construction_plan.items()
            if value['construction_type'] == 'node'
        ]

        for name, node_construction in node_constructions:
            print(f"  Importing {node_construction['label']} nodes...")
            result = self.import_nodes(node_construction)

            if result['status'] == 'error':
                error_msg = f"Failed to import {name}: {result.get('error_message', 'Unknown error')}"
                results['errors'].append(error_msg)
                print(f"    ❌ {error_msg}")
            else:
                results['nodes_created'].append(name)
                print(f"    ✅ Successfully imported {name}")

        # Second, import all relationships
        relationship_constructions = [
            (key, value) for key, value in construction_plan.items()
            if value['construction_type'] == 'relationship'
        ]

        for name, relationship_construction in relationship_constructions:
            print(f"  Creating {relationship_construction['relationship_type']} relationships...")
            result = self.import_relationships(relationship_construction)

            if result['status'] == 'error':
                error_msg = f"Failed to create {name}: {result.get('error_message', 'Unknown error')}"
                results['errors'].append(error_msg)
                print(f"    ❌ {error_msg}")
            else:
                results['relationships_created'].append(name)
                print(f"    ✅ Successfully created {name}")

        # Get statistics
        stats = self.get_graph_statistics()
        results['statistics'] = stats

        return results

    def get_graph_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the constructed domain graph.

        Returns:
            Dictionary with node and relationship counts
        """
        node_stats = graphdb.send_query("""
            MATCH (n)
            WHERE NOT n:`__Entity__`
            WITH labels(n) as labels, count(n) as count
            RETURN labels[0] as label, count
            ORDER BY label
        """)

        rel_stats = graphdb.send_query("""
            MATCH ()-[r]->()
            WHERE NOT type(r) IN ['MENTIONED_IN', 'CORRESPONDS_TO', 'HAS_CHUNK', 'NEXT_CHUNK']
            RETURN type(r) as type, count(r) as count
            ORDER BY count DESC
        """)

        stats = {
            "nodes": {},
            "relationships": {}
        }

        if node_stats['status'] == 'success':
            for row in node_stats['query_result']:
                stats['nodes'][row['label']] = row['count']

        if rel_stats['status'] == 'success':
            for row in rel_stats['query_result']:
                stats['relationships'][row['type']] = row['count']

        return stats

    def validate_construction_plan(self, construction_plan: Dict[str, Any]) -> List[str]:
        """
        Validate a construction plan for potential issues.

        Args:
            construction_plan: Dictionary mapping entity names to construction rules

        Returns:
            List of validation warnings/errors
        """
        warnings = []

        # Check for required fields in node constructions
        for name, rule in construction_plan.items():
            if rule['construction_type'] == 'node':
                required = ['label', 'source_file', 'unique_column_name', 'properties']
                for field in required:
                    if field not in rule:
                        warnings.append(f"Node {name} missing required field: {field}")

            elif rule['construction_type'] == 'relationship':
                required = ['source_file', 'relationship_type', 'from_node_label',
                           'from_node_column', 'to_node_label', 'to_node_column']
                for field in required:
                    if field not in rule:
                        warnings.append(f"Relationship {name} missing required field: {field}")

        # Check that all referenced node labels exist
        node_labels = set()
        for name, rule in construction_plan.items():
            if rule['construction_type'] == 'node':
                node_labels.add(rule['label'])

        for name, rule in construction_plan.items():
            if rule['construction_type'] == 'relationship':
                if rule.get('from_node_label') not in node_labels:
                    warnings.append(f"Relationship {name} references unknown node label: {rule.get('from_node_label')}")
                if rule.get('to_node_label') not in node_labels:
                    warnings.append(f"Relationship {name} references unknown node label: {rule.get('to_node_label')}")

        return warnings


# Default construction plan for supply chain domain
DEFAULT_SUPPLY_CHAIN_PLAN = {
    "Assembly": {
        "construction_type": "node",
        "source_file": "assemblies.csv",
        "label": "Assembly",
        "unique_column_name": "assembly_id",
        "properties": ["assembly_name", "quantity", "product_id"]
    },
    "Part": {
        "construction_type": "node",
        "source_file": "parts.csv",
        "label": "Part",
        "unique_column_name": "part_id",
        "properties": ["part_name", "quantity", "assembly_id"]
    },
    "Product": {
        "construction_type": "node",
        "source_file": "products.csv",
        "label": "Product",
        "unique_column_name": "product_id",
        "properties": ["product_name", "price", "description"]
    },
    "Supplier": {
        "construction_type": "node",
        "source_file": "suppliers.csv",
        "label": "Supplier",
        "unique_column_name": "supplier_id",
        "properties": ["name", "specialty", "city", "country", "website", "contact_email"]
    },
    "Contains": {
        "construction_type": "relationship",
        "source_file": "assemblies.csv",
        "relationship_type": "Contains",
        "from_node_label": "Product",
        "from_node_column": "product_id",
        "to_node_label": "Assembly",
        "to_node_column": "assembly_id",
        "properties": ["quantity"]
    },
    "Is_Part_Of": {
        "construction_type": "relationship",
        "source_file": "parts.csv",
        "relationship_type": "Is_Part_Of",
        "from_node_label": "Part",
        "from_node_column": "part_id",
        "to_node_label": "Assembly",
        "to_node_column": "assembly_id",
        "properties": ["quantity"]
    },
    "Supplied_By": {
        "construction_type": "relationship",
        "source_file": "part_supplier_mapping.csv",
        "relationship_type": "Supplied_By",
        "from_node_label": "Part",
        "from_node_column": "part_id",
        "to_node_label": "Supplier",
        "to_node_column": "supplier_id",
        "properties": ["supplier_name", "lead_time_days", "unit_cost",
                      "minimum_order_quantity", "preferred_supplier"]
    }
}