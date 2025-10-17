"""
Check relationship directions in the graph
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from notebooks.neo4j_for_adk import graphdb

# Check relationship patterns
queries = [
    ("Product->Assembly (CONTAINS)", "MATCH (p:Product)-[:CONTAINS]->(a:Assembly) RETURN count(*) as count"),
    ("Assembly->Product (CONTAINS)", "MATCH (a:Assembly)-[:CONTAINS]->(p:Product) RETURN count(*) as count"),
    ("Part->Assembly (IS_PART_OF)", "MATCH (p:Part)-[:IS_PART_OF]->(a:Assembly) RETURN count(*) as count"),
    ("Assembly->Part (IS_PART_OF)", "MATCH (a:Assembly)-[:IS_PART_OF]->(p:Part) RETURN count(*) as count"),
    ("Supplier->Part (SUPPLIES)", "MATCH (s:Supplier)-[:SUPPLIES]->(p:Part) RETURN count(*) as count"),
    ("Part->Supplier (SUPPLIES)", "MATCH (p:Part)-[:SUPPLIES]->(s:Supplier) RETURN count(*) as count"),
]

print("\nRelationship Direction Analysis:")
print("="*50)

for label, query in queries:
    result = graphdb.send_query(query)
    if result['status'] == 'success' and result['query_result']:
        count = result['query_result'][0]['count']
        if count > 0:
            print(f"✅ {label}: {count}")
        else:
            print(f"   {label}: 0")

# Check what relationships actually exist
print("\nAll relationship types:")
result = graphdb.send_query("MATCH ()-[r]->() RETURN DISTINCT type(r) as rel_type, count(r) as count ORDER BY count DESC")
if result['status'] == 'success':
    for row in result['query_result']:
        print(f"  {row['rel_type']}: {row['count']}")