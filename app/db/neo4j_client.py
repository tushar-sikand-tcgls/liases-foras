"""
Neo4j Database Client
"""

from neo4j import GraphDatabase
from app.config import settings
from functools import lru_cache


@lru_cache()
def get_neo4j_driver():
    """
    Get Neo4j driver instance (cached)

    Returns cached driver to avoid creating multiple connections
    """
    try:
        driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        # Test connection
        driver.verify_connectivity()
        return driver
    except Exception as e:
        print(f"Warning: Neo4j connection failed: {e}")
        # Return None if Neo4j not available
        return None
