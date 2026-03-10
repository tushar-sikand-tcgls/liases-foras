"""
Ports (Interfaces) for Hexagonal Architecture

Ports define the boundaries of the hexagon - what the core domain needs
from the outside world, and what it provides to the outside world.
"""

# Legacy ports (existing)
from app.ports.input_ports import (
    QueryAttributePort,
    CalculateFormulaPort,
    ProjectQueryPort,
    StatisticalAnalysisPort,
    DimensionValidationPort,
)

from app.ports.output_ports import (
    ProjectRepositoryPort,
    FormulaRepositoryPort,
    VectorSearchPort,
    ExternalDataSourcePort,
)

# New LangGraph orchestrator ports
from app.ports.vector_db_port import VectorDBPort
from app.ports.knowledge_graph_port import KnowledgeGraphPort
from app.ports.llm_port import LLMPort

__all__ = [
    # Input Ports (Driving) - Legacy
    'QueryAttributePort',
    'CalculateFormulaPort',
    'ProjectQueryPort',
    'StatisticalAnalysisPort',
    'DimensionValidationPort',

    # Output Ports (Driven) - Legacy
    'ProjectRepositoryPort',
    'FormulaRepositoryPort',
    'VectorSearchPort',
    'ExternalDataSourcePort',

    # LangGraph Orchestrator Ports - New
    'VectorDBPort',
    'KnowledgeGraphPort',
    'LLMPort',
]
