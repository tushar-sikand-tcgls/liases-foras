"""
Insight Agent - VectorDB + GraphRAG Synthesis

Performs semantic search in VectorDB for market intelligence
"""

from typing import Dict, Any, List, Optional
from app.services.graph_state import GraphState
from app.services.vector_db_service import VectorDBService


def build_search_query(
    query: str,
    region: Optional[str],
    intent: Optional[str],
    layer1_metrics: Optional[Dict[str, Any]]
) -> str:
    """
    Build enhanced search query for VectorDB

    Args:
        query: Original user query
        region: Region context
        intent: Classified intent
        layer1_metrics: Calculated metrics (for context)

    Returns:
        Enhanced search query
    """
    query_parts = [query]

    if region:
        query_parts.append(f"{region} market")

    if intent == "INSIGHT":
        # For insight queries, focus on causal factors
        if "why" in query.lower() or "how" in query.lower():
            query_parts.append("factors driving trends infrastructure demographics")

    if intent == "STRATEGIC":
        # For strategic queries, focus on opportunities
        query_parts.append("investment opportunity growth projections")

    # Add metric context if available
    if layer1_metrics and layer1_metrics.get("aggregates"):
        aggregates = layer1_metrics["aggregates"]
        if "avg_psf" in aggregates:
            query_parts.append("pricing trends")
        if "avg_absorption_rate" in aggregates:
            query_parts.append("absorption demand")

    return " ".join(query_parts)


def insight_agent_node(state: GraphState) -> GraphState:
    """
    Insight Agent Node - LangGraph node function

    Performs semantic search in VectorDB for market intelligence

    Args:
        state: Current graph state

    Returns:
        Updated state with vector_insights and increased confidence
    """

    query = state["query"]
    region = state.get("region")
    intent = state.get("intent")
    layer1_metrics = state.get("layer1_metrics")

    errors = []
    warnings = []
    vector_insights = None

    try:
        # Initialize VectorDB service
        vector_db = VectorDBService()

        # Build enhanced search query
        search_query = build_search_query(query, region, intent, layer1_metrics)

        # Perform semantic search
        results = vector_db.search(
            query=search_query,
            n_results=5,
            where_filter={"city": region} if region else None
        )

        if results and results.get("documents"):
            # Format insights
            vector_insights = []

            documents = results["documents"][0] if isinstance(results["documents"], list) else results["documents"]
            metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []
            distances = results.get("distances", [[]])[0] if results.get("distances") else []

            for i, doc in enumerate(documents):
                insight = {
                    "text": doc,
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                    "similarity_score": 1 - distances[i] if i < len(distances) else 0.0,
                    "rank": i + 1
                }
                vector_insights.append(insight)

            # Increase confidence if we found insights
            confidence = state.get("confidence", 0.0)
            confidence = min(confidence + 0.4, 1.0)  # Cap at 1.0

        else:
            warnings.append("VectorDB search returned no results")
            vector_insights = []
            confidence = state.get("confidence", 0.0)

    except Exception as e:
        errors.append(f"Error searching VectorDB: {str(e)}")
        vector_insights = []
        confidence = state.get("confidence", 0.0)

    # Update state
    updated_state = {
        **state,
        "vector_insights": vector_insights,
        "confidence": confidence,
        "iteration": state["iteration"] + 1
    }

    # Add errors and warnings
    if errors:
        updated_state["errors"] = errors
    if warnings:
        updated_state["warnings"] = warnings

    # Log tool call
    tool_call = {
        "tool": "search_vector_insights",
        "args": {"query": search_query, "region": region},
        "result_summary": f"{len(vector_insights) if vector_insights else 0} insights retrieved",
        "top_similarity": vector_insights[0]["similarity_score"] if vector_insights else 0.0
    }
    updated_state["tool_calls"] = [tool_call]

    return updated_state
