"""
Script to index quarterly market data into ChromaDB for semantic search
Creates a dedicated collection for time-series market data
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from app.services.quarterly_market_service import quarterly_market_service


def index_quarterly_data():
    """
    Index quarterly sales and supply data into ChromaDB

    Creates semantic search over:
    - Individual quarters
    - YoY growth periods
    - QoQ growth periods
    - Market trends and patterns
    """

    # Initialize ChromaDB client
    persist_directory = "data/chroma_quarterly_db"
    Path(persist_directory).mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(
        path=persist_directory,
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True
        )
    )

    # Create or reset collection
    try:
        client.delete_collection("quarterly_market_data")
        print("✓ Deleted existing quarterly_market_data collection")
    except:
        pass

    # Get quarterly data and metadata first
    all_quarters = quarterly_market_service.get_all_quarters()
    metadata_info = quarterly_market_service.get_metadata()

    # Build location string dynamically from metadata
    location_info = metadata_info.get('location', {})
    region = location_info.get('region', 'Region')
    city = location_info.get('city', '')
    state = location_info.get('state', '')
    country = location_info.get('country', '')

    location_parts = [region]
    if city:
        location_parts.append(city)
    if state:
        location_parts.append(state)
    if country:
        location_parts.append(country)
    location_str = ', '.join(location_parts)

    collection = client.create_collection(
        name="quarterly_market_data",
        metadata={
            "description": f"Quarterly sales and marketable supply data for {location_str} ({metadata_info.get('date_range', {}).get('start')} to {metadata_info.get('date_range', {}).get('end')})",
            "source": metadata_info.get('source', 'Liases Foras Pillar 1 - Market Intelligence'),
            "layer": "Layer 0 - Raw Dimensions (U, L², T)",
            "location": location_str
        }
    )

    # Load embedding model
    embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    print(f"\n📊 Indexing {len(all_quarters)} quarterly data points...")

    documents = []
    embeddings = []
    ids = []
    metadatas = []

    for i, quarter in enumerate(all_quarters):
        # Create rich text representation for semantic search
        # location_str already built above

        quarter_text = f"""
Location: {location_str}
Quarter: {quarter['quarter']} ({quarter['quarter_id']})
Year: {quarter['year']}, Quarter Number: {quarter['quarter_num']}

Sales Performance in {region}:
- Units Sold: {quarter['sales_units']:,} units
- Total Sales Area: {quarter['sales_area_mn_sqft']:.2f} million sq ft
- Average Unit Size: {(quarter['sales_area_mn_sqft'] * 1_000_000) / quarter['sales_units'] if quarter['sales_units'] > 0 else 0:.0f} sq ft

Marketable Supply in {region}:
- Available Units: {quarter['supply_units']:,} units
- Total Supply Area: {quarter['supply_area_mn_sqft']:.2f} million sq ft
- Average Unit Size: {(quarter['supply_area_mn_sqft'] * 1_000_000) / quarter['supply_units'] if quarter['supply_units'] > 0 else 0:.0f} sq ft

Market Dynamics - {region} Market:
- Absorption Rate: {(quarter['sales_units'] / quarter['supply_units'] * 100) if quarter['supply_units'] > 0 else 0:.2f}%
- Sales to Supply Ratio: 1:{quarter['supply_units'] / quarter['sales_units'] if quarter['sales_units'] > 0 else 0:.1f}

Layer 0 Dimensions:
- U (Units): Sales={quarter['sales_units']}, Supply={quarter['supply_units']}
- L² (Area): Sales={quarter['sales_area_mn_sqft']:.2f}M sq ft, Supply={quarter['supply_area_mn_sqft']:.2f}M sq ft
- T (Time): {quarter['quarter']}

Data Source: {metadata_info.get('source', 'Liases Foras')}
Pillar: {metadata_info.get('pillar', 'Pillar 1: Market Intelligence')}
Region: Chakan, Pune
"""

        # Generate embedding
        embedding = embedding_model.encode(quarter_text).tolist()

        # Add to batch
        documents.append(quarter_text)
        embeddings.append(embedding)
        ids.append(quarter['quarter_id'])
        metadatas.append({
            'quarter': quarter['quarter'],
            'quarter_id': quarter['quarter_id'],
            'year': str(quarter['year']),
            'quarter_num': str(quarter['quarter_num']),
            'sales_units': str(quarter['sales_units']),
            'supply_units': str(quarter['supply_units']),
            'layer': 'Layer 0',
            'dimension_type': 'U, L², T',
            'data_type': 'quarterly_market',
            'region': 'Chakan',
            'city': 'Pune',
            'state': 'Maharashtra'
        })

    # Add all documents to collection
    collection.add(
        documents=documents,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas
    )

    print(f"✓ Indexed {len(documents)} quarterly data points")

    # Add aggregated trend summaries
    print("\n📈 Adding market trend summaries...")

    # YoY growth summary
    yoy_sales = quarterly_market_service.calculate_yoy_growth('sales_units')
    recent_yoy = yoy_sales[-8:] if len(yoy_sales) >= 8 else yoy_sales  # Last 2 years

    yoy_text = f"Year-over-Year Sales Growth Trends for {region} (Recent 2 Years):\n\n"
    yoy_text += f"Location: {location_str}\n\n"
    for item in recent_yoy:
        if item['yoy_growth_pct'] is not None:
            yoy_text += f"{item['quarter']}: {item['yoy_growth_pct']:+.1f}% YoY ({item['current_value']} units vs {item['yoy_value']} units previous year)\n"

    yoy_embedding = embedding_model.encode(yoy_text).tolist()
    collection.add(
        documents=[yoy_text],
        embeddings=[yoy_embedding],
        ids=['yoy_sales_trend_recent'],
        metadatas=[{
            'data_type': 'yoy_trend',
            'metric': 'sales_units',
            'layer': 'Layer 1',
            'period': 'recent_2_years'
        }]
    )

    # QoQ growth summary
    qoq_sales = quarterly_market_service.calculate_qoq_growth('sales_units')
    recent_qoq = qoq_sales[-8:] if len(qoq_sales) >= 8 else qoq_sales

    qoq_text = "Quarter-over-Quarter Sales Momentum (Recent 2 Years):\n\n"
    for item in recent_qoq:
        if item['qoq_growth_pct'] is not None:
            qoq_text += f"{item['quarter']}: {item['qoq_growth_pct']:+.1f}% QoQ ({item['current_value']} units vs {item['prev_value']} units previous quarter)\n"

    qoq_embedding = embedding_model.encode(qoq_text).tolist()
    collection.add(
        documents=[qoq_text],
        embeddings=[qoq_embedding],
        ids=['qoq_sales_trend_recent'],
        metadatas=[{
            'data_type': 'qoq_trend',
            'metric': 'sales_units',
            'layer': 'Layer 1',
            'period': 'recent_2_years'
        }]
    )

    # Summary statistics
    sales_stats = quarterly_market_service.get_summary_statistics('sales_units')
    supply_stats = quarterly_market_service.get_summary_statistics('supply_units')

    stats_text = f"""
Market Summary Statistics (All Time):

Sales Performance:
- Peak Quarter: {sales_stats['max']:,} units
- Lowest Quarter: {sales_stats['min']:,} units
- Average Per Quarter: {sales_stats['mean']:.0f} units
- Median: {sales_stats['median']:.0f} units
- Total Sales (All Quarters): {sales_stats['total']:,} units

Supply Dynamics:
- Peak Supply: {supply_stats['max']:,} units
- Lowest Supply: {supply_stats['min']:,} units
- Average Supply: {supply_stats['mean']:.0f} units
- Median Supply: {supply_stats['median']:.0f} units

Data Coverage:
- Total Quarters: {sales_stats['count']}
- Date Range: {metadata_info.get('date_range', {}).get('start')} to {metadata_info.get('date_range', {}).get('end')}
- Source: {metadata_info.get('source', 'Liases Foras')}
- Last Updated: {metadata_info.get('last_updated', 'N/A')}
"""

    stats_embedding = embedding_model.encode(stats_text).tolist()
    collection.add(
        documents=[stats_text],
        embeddings=[stats_embedding],
        ids=['market_summary_statistics'],
        metadatas=[{
            'data_type': 'summary_statistics',
            'layer': 'Layer 1',
            'period': 'all_time'
        }]
    )

    print(f"✓ Added 3 market trend summaries")

    # Verify indexing
    final_count = collection.count()
    print(f"\n✅ Indexing complete!")
    print(f"   Total documents in collection: {final_count}")
    print(f"   Collection: quarterly_market_data")
    print(f"   Location: {persist_directory}")

    # Test semantic search
    print("\n🔍 Testing semantic search...")
    test_query = "What was the sales performance in 2023?"
    test_embedding = embedding_model.encode(test_query).tolist()

    results = collection.query(
        query_embeddings=[test_embedding],
        n_results=3
    )

    print(f"   Query: '{test_query}'")
    print(f"   Found {len(results['ids'][0])} relevant documents:")
    for i, doc_id in enumerate(results['ids'][0]):
        print(f"   {i+1}. {doc_id}")

    return final_count


if __name__ == "__main__":
    print("=" * 70)
    print("Quarterly Market Data → ChromaDB Indexer")
    print("=" * 70)

    try:
        count = index_quarterly_data()
        print(f"\n✅ Success! Indexed {count} documents.")
        print("\nNext steps:")
        print("1. Use semantic search via VectorDBService")
        print("2. Query via Gemini function calling")
        print("3. Visualize in Streamlit frontend")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
