"""
Knowledge Graph Service
Provides graph-like queries on JSON data with explicit dimensional relationships

Treats the JSON structure as a knowledge graph with:
- Nodes: Projects, Unit Types, Quarterly Summaries, L0 Dimensions
- Edges: Dimensional relationships (IS, NUMERATOR, DENOMINATOR, INVERSE_OF)
"""
from typing import Dict, List, Optional, Set, Tuple
from app.services.data_service import data_service


class KnowledgeGraphService:
    """Query service for knowledge graph structure in JSON"""

    def __init__(self):
        self.data_service = data_service
        self.l0_dimensions = self._initialize_l0_dimensions()

    def _initialize_l0_dimensions(self) -> Dict:
        """
        Initialize L0 dimension definitions (conceptual center of knowledge graph)

        Returns:
            Dict of L0 dimensions with metadata
        """
        return {
            "U": {
                "name": "Units",
                "description": "Count of housing units (1BHK, 2BHK, 3BHK) and sales units",
                "unit": "count",
                "analogy": "Mass",
                "layer": "L0"
            },
            "L²": {
                "name": "Space",
                "description": "Area in sqft/sqm (carpet, saleable, built-up)",
                "unit": "sqft",
                "analogy": "Length²",
                "layer": "L0"
            },
            "T": {
                "name": "Time",
                "description": "Months/years for sales cycle, project duration, possession",
                "unit": "months",
                "analogy": "Time",
                "layer": "L0"
            },
            "C": {
                "name": "Cash Flow",
                "description": "INR revenue, cost, investment, pricing",
                "unit": "INR",
                "analogy": "Current",
                "layer": "L0"
            }
        }

    # ==================================================================
    # LAYER QUERIES (Concentric Circles: L0 → L1 → L2 → L3)
    # ==================================================================

    def get_layer_0_dimensions(self) -> Dict:
        """
        Get L0 dimensions (center of knowledge graph)

        Returns:
            Dict of L0 dimensions with metadata
        """
        return self.l0_dimensions

    def get_layer_1_nodes(self) -> Dict:
        """
        Get all L1 nodes (raw data from PDF)

        Returns:
            {
                "projects": [...],
                "unit_types": [...],
                "quarterly_summaries": [...]
            }
        """
        return {
            "projects": self.data_service.projects,
            "unit_types": self.data_service.unit_types,
            "quarterly_summaries": self.data_service.quarterly_summaries
        }

    # ==================================================================
    # DIMENSIONAL RELATIONSHIP QUERIES
    # ==================================================================

    def find_by_relationship(self, rel_type: str, dimension: str) -> List[Dict]:
        """
        Find all attributes with specific relationship to a dimension

        Args:
            rel_type: "IS", "NUMERATOR", "DENOMINATOR", "INVERSE_OF"
            dimension: "U", "L²", "T", "C"

        Returns:
            List of attributes with that relationship

        Example:
            >>> kg.find_by_relationship("NUMERATOR", "C")
            # Returns all attributes with C as numerator (prices: C/L², C/T, etc.)
        """
        return self.data_service.find_attributes_by_relationship(rel_type, dimension)

    def get_dependencies(self, project_name: str, attribute: str) -> Dict[str, str]:
        """
        Get dimensional dependencies for an attribute

        Args:
            project_name: Name of project
            attribute: Attribute name (e.g., "currentPricePSF")

        Returns:
            Dict mapping dimension to relationship type
            e.g., {"C": "NUMERATOR", "L²": "DENOMINATOR"}
        """
        project = self.data_service.get_project_by_name(project_name)
        if not project or attribute not in project:
            return {}

        attr_data = project[attribute]
        relationships = self.data_service.get_relationships(attr_data)

        return {rel['target']: rel['type'] for rel in relationships}

    def get_all_relationships_for_dimension(self, dimension: str) -> Dict:
        """
        Get all relationships involving a dimension

        Args:
            dimension: "U", "L²", "T", "C"

        Returns:
            {
                "IS": [list of attributes with IS relationship],
                "NUMERATOR": [list of attributes with dimension as numerator],
                "DENOMINATOR": [list of attributes with dimension as denominator],
                "INVERSE_OF": [list of attributes with inverse relationship]
            }
        """
        results = {
            "IS": [],
            "NUMERATOR": [],
            "DENOMINATOR": [],
            "INVERSE_OF": []
        }

        for rel_type in results.keys():
            results[rel_type] = self.find_by_relationship(rel_type, dimension)

        return results

    # ==================================================================
    # DIMENSIONAL ANALYSIS
    # ==================================================================

    def get_dimensional_profile(self, project_name: str) -> Dict:
        """
        Get complete dimensional profile of a project

        Returns:
            {
                "U": [list of U attributes],
                "L²": [list of L² attributes],
                "T": [list of T attributes],
                "C": [list of C attributes],
                "Composite": [list of composite attributes],
                "Dimensionless": [list of dimensionless attributes]
            }
        """
        project = self.data_service.get_project_by_name(project_name)
        if not project:
            return {}

        profile = {
            "U": [],
            "L²": [],
            "T": [],
            "C": [],
            "Composite": [],
            "Dimensionless": []
        }

        for attr_name, attr_data in project.items():
            if not isinstance(attr_data, dict):
                continue

            dimension = self.data_service.get_dimension(attr_data)
            relationships = self.data_service.get_relationships(attr_data)

            attr_info = {
                'attribute': attr_name,
                'value': self.data_service.get_value(attr_data),
                'unit': self.data_service.get_unit(attr_data),
                'dimension': dimension,
                'relationships': relationships
            }

            # Categorize by dimension type
            if not relationships or dimension in ['None', 'Dimensionless']:
                profile['Dimensionless'].append(attr_info)
            elif len(relationships) == 1 and relationships[0]['type'] == 'IS':
                # Pure dimension
                target = relationships[0]['target']
                if target in profile:
                    profile[target].append(attr_info)
            else:
                # Composite dimension
                profile['Composite'].append(attr_info)

        return profile

    def get_dimensional_formula_breakdown(self, dimension: str) -> Dict:
        """
        Break down a composite dimension formula into its parts

        Args:
            dimension: Dimension formula (e.g., "C/L²", "1/T")

        Returns:
            {
                "formula": "C/L²",
                "components": [
                    {"type": "NUMERATOR", "dimension": "C", "name": "Cash Flow"},
                    {"type": "DENOMINATOR", "dimension": "L²", "name": "Space"}
                ],
                "description": "Cash Flow per unit Space (Price per square foot)"
            }
        """
        from scripts.dimension_parser import DimensionParser
        parser = DimensionParser()

        relationships = parser.parse_dimension(dimension)

        components = []
        for rel in relationships:
            target = rel['target']
            components.append({
                "type": rel['type'],
                "dimension": target,
                "name": self.l0_dimensions.get(target, {}).get('name', 'Unknown')
            })

        return {
            "formula": dimension,
            "components": components,
            "summary": parser.get_dimension_summary(dimension)
        }

    # ==================================================================
    # GRAPH VISUALIZATION
    # ==================================================================

    def get_graph_visualization_data(self, project_name: Optional[str] = None) -> Dict:
        """
        Get graph visualization data for UI with proper layering

        Architecture:
        - L0 (Gray): Base dimensions (U, L², T, C)
        - Projects (Blue): Core metadata nodes
        - L1 Attributes (Green): Numeric values with dimensions
        - L2 Metrics (Yellow): Calculated financial metrics

        Args:
            project_name: If provided, focus on this project. Otherwise, show all.

        Returns:
            Graph data with nodes and edges
        """
        nodes = []
        edges = []
        node_id_map = {}

        # Metadata attributes (non-numeric, goes in Project node)
        METADATA_ATTRS = ['projectId', 'projectName', 'developerName', 'location',
                          'launchDate', 'possessionDate', 'reraRegistered',
                          'layer', 'nodeType', 'extractionTimestamp', 'priorityWeight']

        # Add L0 dimension nodes (center of graph)
        for dim_key, dim_data in self.l0_dimensions.items():
            node_id = f"dim_{dim_key}"
            nodes.append({
                "id": node_id,
                "label": f"{dim_key} ({dim_data['name']})",
                "type": "L0_Dimension",
                "layer": 0,
                "group": 0,
                "size": 40,
                "color": "#9E9E9E"
            })
            node_id_map[dim_key] = node_id

        # Add project nodes with metadata
        projects = [self.data_service.get_project_by_name(project_name)] if project_name else self.data_service.projects

        for idx, project in enumerate(projects):
            if not project:
                continue

            # Build project node with full metadata
            proj_id_value = self.data_service.get_value(project.get('projectId', idx))
            proj_id = f"proj_{proj_id_value}"

            project_node = {
                "id": proj_id,
                "label": self.data_service.get_value(project.get('projectName', 'Unknown')),
                "type": "Project_L1",
                "layer": 1,
                "group": 1,
                "size": 30,
                "color": "#2196F3",
                # Add core metadata
                "projectId": str(proj_id_value),
                "projectName": self.data_service.get_value(project.get('projectName')),
                "developerName": self.data_service.get_value(project.get('developerName')),
                "location": self.data_service.get_value(project.get('location')),
                "launchDate": self.data_service.get_value(project.get('launchDate')),
                "possessionDate": self.data_service.get_value(project.get('possessionDate')),
                "reraRegistered": self.data_service.get_value(project.get('reraRegistered'))
            }
            nodes.append(project_node)

            # Add L1 attribute nodes (numeric values with dimensions)
            for attr_name, attr_data in project.items():
                if not isinstance(attr_data, dict):
                    continue

                # Skip metadata attributes (they're in project node)
                if attr_name in METADATA_ATTRS:
                    continue

                # Skip l2_metrics and l3_insights (handled separately)
                if attr_name in ['l2_metrics', 'l3_insights']:
                    continue

                dimension = self.data_service.get_dimension(attr_data)

                # Skip dimensionless attributes for cleaner graph
                if dimension in ['None', 'Dimensionless']:
                    continue

                attr_id = f"{proj_id}_attr_{attr_name}"
                nodes.append({
                    "id": attr_id,
                    "label": attr_name,
                    "type": "L1_Attribute",
                    "layer": 1,
                    "group": 1,
                    "size": 15,
                    "color": "#4CAF50",  # Green for L1
                    "value": self.data_service.get_value(attr_data),
                    "unit": self.data_service.get_unit(attr_data),
                    "dimension": dimension
                })

                # Edge from project to L1 attribute
                edges.append({
                    "source": proj_id,
                    "target": attr_id,
                    "type": "HAS_L1_ATTRIBUTE",
                    "color": "#CCCCCC"
                })

                # Edges from L1 attribute to L0 dimensions
                relationships = self.data_service.get_relationships(attr_data)
                for rel in relationships:
                    target_dim = rel['target']
                    rel_type = rel['type']

                    if target_dim in node_id_map:
                        edges.append({
                            "source": attr_id,
                            "target": node_id_map[target_dim],
                            "type": rel_type,
                            "label": rel_type,
                            "color": self._get_relationship_color(rel_type)
                        })

            # Add L2 metric nodes (calculated financial metrics)
            l2_metrics = project.get('l2_metrics', {})
            if l2_metrics and isinstance(l2_metrics, dict):
                for metric_name, metric_data in l2_metrics.items():
                    if not isinstance(metric_data, dict):
                        continue

                    metric_id = f"{proj_id}_l2_{metric_name}"
                    dimension = self.data_service.get_dimension(metric_data)

                    nodes.append({
                        "id": metric_id,
                        "label": metric_name,
                        "type": "L2_Metric",
                        "layer": 2,
                        "group": 2,
                        "size": 20,
                        "color": "#FFC107",  # Yellow for L2
                        "value": self.data_service.get_value(metric_data),
                        "unit": self.data_service.get_unit(metric_data),
                        "dimension": dimension,
                        "calculation": metric_data.get('calculation', '')
                    })

                    # Edge from project to L2 metric
                    edges.append({
                        "source": proj_id,
                        "target": metric_id,
                        "type": "HAS_L2_METRIC",
                        "color": "#FFE082"
                    })

                    # Edges from L2 metric to L0 dimensions
                    relationships = self.data_service.get_relationships(metric_data)
                    for rel in relationships:
                        target_dim = rel['target']
                        rel_type = rel['type']

                        if target_dim in node_id_map:
                            edges.append({
                                "source": metric_id,
                                "target": node_id_map[target_dim],
                                "type": rel_type,
                                "label": rel_type,
                                "color": self._get_relationship_color(rel_type)
                            })

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "l0_dimensions": len(self.l0_dimensions),
                "l1_projects": len(projects),
                "l1_attributes": len([n for n in nodes if n.get('type') == 'L1_Attribute']),
                "l2_metrics": len([n for n in nodes if n.get('type') == 'L2_Metric'])
            }
        }

    def _get_relationship_color(self, rel_type: str) -> str:
        """Get color for relationship type"""
        colors = {
            "IS": "#FF5722",        # Red-Orange
            "NUMERATOR": "#2196F3", # Blue
            "DENOMINATOR": "#FF9800", # Orange
            "INVERSE_OF": "#9C27B0"  # Purple
        }
        return colors.get(rel_type, "#999999")

    # ==================================================================
    # QUERY STATISTICS
    # ==================================================================

    def get_knowledge_graph_stats(self) -> Dict:
        """
        Get statistics about the knowledge graph

        Returns:
            {
                "l0_dimensions": 4,
                "l1_projects": 10,
                "l1_unit_types": 4,
                "l1_quarterly": 14,
                "total_attributes": 150,
                "dimensional_relationships": 300,
                "relationship_breakdown": {
                    "IS": 100,
                    "NUMERATOR": 50,
                    "DENOMINATOR": 50,
                    "INVERSE_OF": 100
                }
            }
        """
        total_attributes = 0
        total_relationships = 0
        relationship_counts = {"IS": 0, "NUMERATOR": 0, "DENOMINATOR": 0, "INVERSE_OF": 0}

        for project in self.data_service.projects:
            for attr_name, attr_data in project.items():
                if isinstance(attr_data, dict):
                    total_attributes += 1
                    relationships = self.data_service.get_relationships(attr_data)
                    total_relationships += len(relationships)

                    for rel in relationships:
                        rel_type = rel.get('type')
                        if rel_type in relationship_counts:
                            relationship_counts[rel_type] += 1

        return {
            "l0_dimensions": len(self.l0_dimensions),
            "l1_projects": len(self.data_service.projects),
            "l1_unit_types": len(self.data_service.unit_types),
            "l1_quarterly": len(self.data_service.quarterly_summaries),
            "total_attributes": total_attributes,
            "total_dimensional_relationships": total_relationships,
            "relationship_breakdown": relationship_counts
        }


# Global knowledge graph service instance
knowledge_graph_service = KnowledgeGraphService()
