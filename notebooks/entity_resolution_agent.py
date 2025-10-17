"""
Entity Resolution Agent for Graph Connection

This agent handles entity resolution between the subject graph (extracted entities)
and the domain graph (structured data), creating CORRESPONDS_TO relationships.
"""

from typing import Dict, Any, List, Tuple, Optional
from neo4j_for_adk import graphdb
import re


class EntityResolutionAgent:
    """Agent for resolving and connecting entities across different graphs."""

    def __init__(self):
        self.name = "EntityResolutionAgent"
        self.description = "Resolves entities between subject and domain graphs using similarity matching"

    def find_unique_entity_labels(self) -> List[str]:
        """
        Find all unique entity labels in the subject graph.

        Returns:
            List of unique entity labels (excluding system labels starting with __)
        """
        result = graphdb.send_query("""
            MATCH (n)
            WHERE n:`__Entity__`
            WITH DISTINCT labels(n) AS entity_labels
            UNWIND entity_labels AS entity_label
            WITH entity_label
            WHERE NOT entity_label STARTS WITH "__"
            RETURN collect(DISTINCT entity_label) as unique_entity_labels
        """)

        if result['status'] == 'error':
            raise Exception(f"Failed to get entity labels: {result.get('error_message', 'Unknown error')}")

        return result['query_result'][0]['unique_entity_labels'] if result['query_result'] else []

    def find_unique_entity_keys(self, entity_label: str) -> List[str]:
        """
        Find unique property keys for entities with a given label.

        Args:
            entity_label: Label of entities to inspect

        Returns:
            List of unique property keys
        """
        result = graphdb.send_query("""
            MATCH (n:$($entityLabel))
            WHERE n:`__Entity__`
            WITH DISTINCT keys(n) as entityKeys
            UNWIND entityKeys as entityKey
            RETURN collect(DISTINCT entityKey) as unique_entity_keys
        """, {
            "entityLabel": entity_label
        })

        if result['status'] == 'error':
            raise Exception(f"Failed to get entity keys: {result.get('error_message', 'Unknown error')}")

        return result['query_result'][0]['unique_entity_keys'] if result['query_result'] else []

    def find_unique_domain_keys(self, domain_label: str) -> List[str]:
        """
        Find unique property keys for domain nodes with a given label.

        Args:
            domain_label: Label of domain nodes to inspect

        Returns:
            List of unique property keys
        """
        result = graphdb.send_query("""
            MATCH (n:$($domainLabel))
            WHERE NOT n:`__Entity__`  // Exclude entities, only domain nodes
            WITH DISTINCT keys(n) as domainKeys
            UNWIND domainKeys as domainKey
            RETURN collect(DISTINCT domainKey) as unique_domain_keys
        """, {
            "domainLabel": domain_label
        })

        if result['status'] == 'error':
            raise Exception(f"Failed to get domain keys: {result.get('error_message', 'Unknown error')}")

        return result['query_result'][0]['unique_domain_keys'] if result['query_result'] else []

    def normalize_key(self, label: str, key: str) -> str:
        """
        Normalize a property key for comparison.

        Keys are normalized by:
        - Converting to lowercase
        - Removing label prefix
        - Replacing spaces with underscores

        Args:
            label: The node label
            key: The property key to normalize

        Returns:
            Normalized key string
        """
        # Convert to lowercase
        normalized = key.lower()

        # Remove label prefix (e.g., "Product_name" -> "name")
        label_pattern = f"^{label.lower()}[_ ]*"
        normalized = re.sub(label_pattern, "", normalized)

        # Replace spaces with underscores
        normalized = re.sub(" ", "_", normalized)

        return normalized

    def correlate_keys(
        self,
        label: str,
        entity_keys: List[str],
        domain_keys: List[str],
        similarity_threshold: float = 0.8
    ) -> List[Tuple[str, str, float]]:
        """
        Find correlating keys between entity and domain nodes.

        Args:
            label: The node label
            entity_keys: List of entity property keys
            domain_keys: List of domain property keys
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            List of tuples (entity_key, domain_key, similarity_score)
        """
        correlated = []

        for entity_key in entity_keys:
            normalized_entity = self.normalize_key(label, entity_key)

            for domain_key in domain_keys:
                normalized_domain = self.normalize_key(label, domain_key)

                # Simple similarity: exact match after normalization
                if normalized_entity == normalized_domain:
                    correlated.append((entity_key, domain_key, 1.0))
                # Partial match (one contains the other)
                elif normalized_entity in normalized_domain or normalized_domain in normalized_entity:
                    # Calculate simple similarity based on length ratio
                    similarity = min(len(normalized_entity), len(normalized_domain)) / max(len(normalized_entity), len(normalized_domain))
                    if similarity >= similarity_threshold:
                        correlated.append((entity_key, domain_key, similarity))

        # Sort by similarity score (highest first)
        correlated.sort(key=lambda x: x[2], reverse=True)

        return correlated

    def create_correspondence_relationships(
        self,
        label: str,
        entity_key: str,
        domain_key: str,
        similarity_threshold: float = 0.9
    ) -> Dict[str, Any]:
        """
        Create CORRESPONDS_TO relationships between matching entities and domain nodes.

        Uses Jaro-Winkler distance for string similarity matching.

        Args:
            label: Node label to match
            entity_key: Property key in entity nodes
            domain_key: Property key in domain nodes
            similarity_threshold: Minimum similarity (0-1) for matching

        Returns:
            Dictionary with number of relationships created
        """
        # Convert similarity threshold to distance threshold
        distance_threshold = 1.0 - similarity_threshold

        query = """
        MATCH (entity:$($entityLabel):`__Entity__`), (domain:$($entityLabel))
        WHERE apoc.text.jaroWinklerDistance(
            toLower(toString(entity[$entityKey])),
            toLower(toString(domain[$domainKey]))
        ) < $distance
        MERGE (entity)-[r:CORRESPONDS_TO]->(domain)
        ON CREATE SET
            r.created_at = datetime(),
            r.entity_key = $entityKey,
            r.domain_key = $domainKey,
            r.similarity = 1.0 - apoc.text.jaroWinklerDistance(
                toLower(toString(entity[$entityKey])),
                toLower(toString(domain[$domainKey]))
            )
        ON MATCH SET
            r.updated_at = datetime()
        RETURN count(r) as relationships_created
        """

        result = graphdb.send_query(query, {
            "entityLabel": label,
            "entityKey": entity_key,
            "domainKey": domain_key,
            "distance": distance_threshold
        })

        if result['status'] == 'error':
            return {
                "status": "error",
                "error": result.get('error_message', 'Unknown error'),
                "relationships_created": 0
            }

        count = result['query_result'][0]['relationships_created'] if result['query_result'] else 0

        return {
            "status": "success",
            "label": label,
            "entity_key": entity_key,
            "domain_key": domain_key,
            "relationships_created": count
        }

    def resolve_all_entities(
        self,
        similarity_threshold: float = 0.8,
        key_correlation_threshold: float = 0.8
    ) -> Dict[str, Any]:
        """
        Automatically resolve all entities in the graph.

        Args:
            similarity_threshold: Minimum similarity for entity matching
            key_correlation_threshold: Minimum similarity for key correlation

        Returns:
            Dictionary with resolution statistics
        """
        results = {
            "entities_resolved": {},
            "total_relationships": 0,
            "errors": []
        }

        print("Starting entity resolution...")

        # Get all entity labels
        entity_labels = self.find_unique_entity_labels()

        for entity_label in entity_labels:
            print(f"\nResolving {entity_label} entities...")

            # Get keys for this entity type
            entity_keys = self.find_unique_entity_keys(entity_label)
            domain_keys = self.find_unique_domain_keys(entity_label)

            if not entity_keys or not domain_keys:
                msg = f"  ⚠️  No keys found for {entity_label} (entity keys: {len(entity_keys)}, domain keys: {len(domain_keys)})"
                print(msg)
                results['errors'].append(msg)
                continue

            # Find correlated keys
            correlated_keys = self.correlate_keys(
                entity_label,
                entity_keys,
                domain_keys,
                key_correlation_threshold
            )

            if not correlated_keys:
                msg = f"  ⚠️  No correlating keys found for {entity_label}"
                print(msg)
                results['errors'].append(msg)
                continue

            # Use the best correlated key pair
            best_match = correlated_keys[0]
            entity_key, domain_key, correlation_score = best_match

            print(f"  Using key correlation: {entity_key} <-> {domain_key} (score: {correlation_score:.2f})")

            # Create correspondence relationships
            resolution_result = self.create_correspondence_relationships(
                entity_label,
                entity_key,
                domain_key,
                similarity_threshold
            )

            if resolution_result['status'] == 'success':
                count = resolution_result['relationships_created']
                results['entities_resolved'][entity_label] = count
                results['total_relationships'] += count
                print(f"  ✅ Created {count} correspondence relationships")
            else:
                error_msg = f"Failed to resolve {entity_label}: {resolution_result['error']}"
                results['errors'].append(error_msg)
                print(f"  ❌ {error_msg}")

        return results

    def get_resolution_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about entity resolution in the graph.

        Returns:
            Dictionary with resolution statistics
        """
        # Count correspondence relationships by entity type
        stats_query = """
        MATCH (e:`__Entity__`)-[r:CORRESPONDS_TO]->(d)
        WITH labels(e) as entity_labels, labels(d) as domain_labels, r
        UNWIND entity_labels as entity_label
        WITH entity_label, domain_labels, r
        WHERE NOT entity_label STARTS WITH "__"
        RETURN
            entity_label,
            count(DISTINCT r) as correspondence_count,
            avg(r.similarity) as avg_similarity,
            min(r.similarity) as min_similarity,
            max(r.similarity) as max_similarity
        ORDER BY entity_label
        """

        result = graphdb.send_query(stats_query)

        if result['status'] == 'error':
            return {"error": result.get('error_message', 'Unknown error')}

        stats = {
            "resolution_by_type": {},
            "total_correspondences": 0
        }

        for row in result.get('query_result', []):
            type_stats = {
                "count": row['correspondence_count'],
                "avg_similarity": round(row['avg_similarity'], 3) if row['avg_similarity'] else 0,
                "min_similarity": round(row['min_similarity'], 3) if row['min_similarity'] else 0,
                "max_similarity": round(row['max_similarity'], 3) if row['max_similarity'] else 0
            }
            stats["resolution_by_type"][row['entity_label']] = type_stats
            stats["total_correspondences"] += row['correspondence_count']

        # Count unresolved entities
        unresolved_query = """
        MATCH (e:`__Entity__`)
        WHERE NOT (e)-[:CORRESPONDS_TO]->()
        WITH labels(e) as entity_labels
        UNWIND entity_labels as entity_label
        WITH entity_label
        WHERE NOT entity_label STARTS WITH "__"
        RETURN entity_label, count(*) as unresolved_count
        """

        unresolved_result = graphdb.send_query(unresolved_query)

        if unresolved_result['status'] == 'success':
            stats["unresolved_by_type"] = {}
            for row in unresolved_result.get('query_result', []):
                stats["unresolved_by_type"][row['entity_label']] = row['unresolved_count']

        return stats

    def validate_resolutions(self) -> List[Dict[str, Any]]:
        """
        Validate entity resolutions for potential issues.

        Returns:
            List of validation warnings/issues
        """
        issues = []

        # Check for entities with multiple correspondences
        multi_correspondence_query = """
        MATCH (e:`__Entity__`)-[r:CORRESPONDS_TO]->(d)
        WITH e, count(r) as correspondence_count
        WHERE correspondence_count > 1
        RETURN id(e) as entity_id, labels(e) as labels, correspondence_count
        LIMIT 10
        """

        result = graphdb.send_query(multi_correspondence_query)

        if result['status'] == 'success':
            for row in result.get('query_result', []):
                issues.append({
                    "type": "multiple_correspondences",
                    "entity_id": row['entity_id'],
                    "labels": row['labels'],
                    "count": row['correspondence_count'],
                    "message": f"Entity has {row['correspondence_count']} correspondences"
                })

        # Check for low similarity correspondences
        low_similarity_query = """
        MATCH (e:`__Entity__`)-[r:CORRESPONDS_TO]->(d)
        WHERE r.similarity < 0.7
        RETURN
            id(e) as entity_id,
            labels(e) as entity_labels,
            id(d) as domain_id,
            labels(d) as domain_labels,
            r.similarity as similarity
        LIMIT 10
        """

        result = graphdb.send_query(low_similarity_query)

        if result['status'] == 'success':
            for row in result.get('query_result', []):
                issues.append({
                    "type": "low_similarity",
                    "entity_id": row['entity_id'],
                    "domain_id": row['domain_id'],
                    "similarity": row['similarity'],
                    "message": f"Low similarity correspondence: {row['similarity']:.2f}"
                })

        return issues

    def remove_correspondence_relationships(self, label: Optional[str] = None) -> Dict[str, Any]:
        """
        Remove correspondence relationships, optionally filtered by label.

        Args:
            label: Optional label to filter which correspondences to remove

        Returns:
            Dictionary with deletion statistics
        """
        if label:
            query = """
            MATCH (e:$($label):`__Entity__`)-[r:CORRESPONDS_TO]->()
            WITH r
            DELETE r
            RETURN count(*) as deleted_count
            """
            params = {"label": label}
        else:
            query = """
            MATCH (e:`__Entity__`)-[r:CORRESPONDS_TO]->()
            WITH r
            DELETE r
            RETURN count(*) as deleted_count
            """
            params = {}

        result = graphdb.send_query(query, params)

        if result['status'] == 'error':
            return {
                "status": "error",
                "error": result.get('error_message', 'Unknown error')
            }

        count = result['query_result'][0]['deleted_count'] if result['query_result'] else 0

        return {
            "status": "success",
            "deleted_count": count,
            "label": label if label else "all"
        }