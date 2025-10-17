"""
Test supply chain queries to validate the fixed pipeline
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from notebooks.neo4j_for_adk import graphdb

def test_supply_chain_queries():
    """Test critical supply chain queries"""

    print("\n" + "="*60)
    print("SUPPLY CHAIN VALIDATION TESTS")
    print("="*60)

    # Test 1: Verify SUPPLIES relationships exist
    query1 = """
    MATCH ()-[r:SUPPLIES]->()
    RETURN count(r) as supplies_count
    """
    result1 = graphdb.send_query(query1)
    if result1['status'] == 'success' and result1['query_result']:
        count = result1['query_result'][0]['supplies_count']
        print(f"\n✅ Test 1: SUPPLIES relationships exist")
        print(f"   Found {count} SUPPLIES relationships")
    else:
        print(f"\n❌ Test 1: No SUPPLIES relationships found!")

    # Test 2: Which suppliers provide parts for a specific product?
    query2 = """
    MATCH (p:Product {product_name: 'Stockholm Chair'})
          -[:CONTAINS]-(a:Assembly)
          -[:IS_PART_OF]-(part:Part)
          -[:SUPPLIES]-(s:Supplier)
    RETURN DISTINCT s.name as supplier,
           collect(DISTINCT part.part_name) as parts_supplied
    LIMIT 5
    """
    result2 = graphdb.send_query(query2)
    if result2['status'] == 'success' and result2['query_result']:
        print(f"\n✅ Test 2: Supply chain traceability works")
        print(f"   Suppliers for Stockholm Chair:")
        for row in result2['query_result']:
            print(f"   - {row['supplier']}: {', '.join(row['parts_supplied'][:3])}")
    else:
        print(f"\n⚠️ Test 2: Could not trace suppliers for Stockholm Chair")

    # Test 3: Find parts with multiple supplier options
    query3 = """
    MATCH (part:Part)-[:SUPPLIES]-(s:Supplier)
    WITH part, count(DISTINCT s) as supplier_count
    WHERE supplier_count > 1
    RETURN part.part_name as part_name, supplier_count
    ORDER BY supplier_count DESC
    LIMIT 5
    """
    result3 = graphdb.send_query(query3)
    if result3['status'] == 'success' and result3['query_result']:
        print(f"\n✅ Test 3: Multiple supplier analysis works")
        print(f"   Parts with multiple suppliers:")
        for row in result3['query_result']:
            print(f"   - {row['part_name']}: {row['supplier_count']} suppliers")
    else:
        print(f"\n⚠️ Test 3: No parts with multiple suppliers found")

    # Test 4: Find single points of failure (parts with only one supplier)
    query4 = """
    MATCH (part:Part)-[:SUPPLIES]-(s:Supplier)
    WITH part, count(DISTINCT s) as supplier_count
    WHERE supplier_count = 1
    MATCH (part)-[:SUPPLIES]-(supplier:Supplier)
    RETURN part.part_name as part_name, supplier.name as sole_supplier
    LIMIT 5
    """
    result4 = graphdb.send_query(query4)
    if result4['status'] == 'success' and result4['query_result']:
        print(f"\n✅ Test 4: Single point of failure analysis works")
        print(f"   Parts with only one supplier (risk points):")
        for row in result4['query_result']:
            print(f"   - {row['part_name']}: only from {row['sole_supplier']}")
    else:
        print(f"\n⚠️ Test 4: No single supplier parts found")

    # Test 5: Verify all three relationship types work together
    query5 = """
    MATCH path = (p:Product)-[:CONTAINS]->(a:Assembly)
                           -[:IS_PART_OF]->(part:Part)
                           -[:SUPPLIES]->(s:Supplier)
    RETURN count(path) as complete_paths
    """
    result5 = graphdb.send_query(query5)
    if result5['status'] == 'success' and result5['query_result']:
        count = result5['query_result'][0]['complete_paths']
        if count > 0:
            print(f"\n✅ Test 5: Complete supply chain paths exist")
            print(f"   Found {count} complete Product->Assembly->Part->Supplier paths")
        else:
            print(f"\n❌ Test 5: No complete supply chain paths found!")
    else:
        print(f"\n❌ Test 5: Query failed!")

    print("\n" + "="*60)
    print("VALIDATION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_supply_chain_queries()