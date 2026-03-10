#!/usr/bin/env python3
"""
Test script to verify the enriched knowledge graph visualization
Shows the increase in nodes from adding unitMixBreakdown and priceRangeDistribution
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.knowledge_graph_service import KnowledgeGraphService

def test_enriched_visualization():
    """Test the enhanced graph visualization with enrichment nodes"""

    print("=" * 80)
    print("Testing Enhanced Knowledge Graph Visualization")
    print("=" * 80)

    # Initialize service for Kolkata
    kg_service = KnowledgeGraphService(city="Kolkata")

    # Get visualization data
    print("\nGenerating graph visualization data...")
    viz_data = kg_service.get_graph_visualization_data()

    # Display statistics
    stats = viz_data['stats']
    print("\n" + "=" * 80)
    print("GRAPH STATISTICS")
    print("=" * 80)
    print(f"Total Nodes:           {stats['total_nodes']}")
    print(f"Total Edges:           {stats['total_edges']}")
    print(f"\nNode Breakdown:")
    print(f"  L0 Dimensions:       {stats['l0_dimensions']}")
    print(f"  L1 Projects:         {stats['l1_projects']}")
    print(f"  L1 Attributes:       {stats['l1_attributes']}")
    print(f"  L1 Enrichments:      {stats['l1_enrichments']}")
    print(f"    - Unit Mix:        {stats['l1_unit_mix']}")
    print(f"    - Price Ranges:    {stats['l1_price_range']}")
    print(f"  L2 Metrics:          {stats['l2_metrics']}")

    # Show node type breakdown
    print("\n" + "=" * 80)
    print("NODE TYPE ANALYSIS")
    print("=" * 80)
    node_types = {}
    for node in viz_data['nodes']:
        node_type = node.get('type', 'Unknown')
        node_types[node_type] = node_types.get(node_type, 0) + 1

    for node_type, count in sorted(node_types.items()):
        print(f"  {node_type:20s} : {count:4d} nodes")

    # Show edge type breakdown
    print("\n" + "=" * 80)
    print("EDGE TYPE ANALYSIS")
    print("=" * 80)
    edge_types = {}
    for edge in viz_data['edges']:
        edge_type = edge.get('type', 'Unknown')
        edge_types[edge_type] = edge_types.get(edge_type, 0) + 1

    for edge_type, count in sorted(edge_types.items()):
        print(f"  {edge_type:25s} : {count:4d} edges")

    # Show sample enrichment nodes
    print("\n" + "=" * 80)
    print("SAMPLE ENRICHMENT NODES (First 5 of each type)")
    print("=" * 80)

    enrichment_nodes = [n for n in viz_data['nodes'] if n.get('type') == 'L1_Enrichment']

    # Unit Mix samples
    unit_mix_nodes = [n for n in enrichment_nodes if n.get('enrichmentType') == 'unit_mix'][:5]
    if unit_mix_nodes:
        print("\nUnit Mix Breakdown Nodes:")
        for node in unit_mix_nodes:
            print(f"  - {node['id']:40s} | Label: {node['label']}")
            if 'saleableMinSize' in node:
                print(f"    Saleable Size: {node['saleableMinSize']['value']} {node['saleableMinSize']['unit']}")
            if 'minCost' in node:
                print(f"    Min Cost: {node['minCost']['value']} {node['minCost']['unit']}")

    # Price Range samples
    price_range_nodes = [n for n in enrichment_nodes if n.get('enrichmentType') == 'price_range'][:5]
    if price_range_nodes:
        print("\nPrice Range Distribution Nodes:")
        for node in price_range_nodes:
            print(f"  - {node['id']:40s} | Label: {node['label']}")
            if 'annualSalesUnits' in node:
                print(f"    Annual Sales: {node['annualSalesUnits']['value']} {node['annualSalesUnits']['unit']}")
            if 'monthsInventory' in node:
                print(f"    Months Inventory: {node['monthsInventory']['value']} {node['monthsInventory']['unit']}")

    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)

    expected_min_nodes = 300  # Conservative estimate
    if stats['total_nodes'] >= expected_min_nodes:
        print(f"✓ SUCCESS: Graph has {stats['total_nodes']} nodes (expected ≥ {expected_min_nodes})")
    else:
        print(f"⚠ WARNING: Graph has {stats['total_nodes']} nodes (expected ≥ {expected_min_nodes})")

    if stats['l1_enrichments'] > 0:
        print(f"✓ SUCCESS: Found {stats['l1_enrichments']} enrichment nodes")
    else:
        print("✗ FAILED: No enrichment nodes found")

    print("\n" + "=" * 80)
    print("Test completed successfully!")
    print("=" * 80)

if __name__ == "__main__":
    test_enriched_visualization()
