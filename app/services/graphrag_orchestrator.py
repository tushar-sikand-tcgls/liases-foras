"""
GraphRAG Orchestrator - Hybrid LLM + Knowledge Graph Query System

Architecture:
┌─────────────┐
│ User Query  │
└──────┬──────┘
       ↓
┌─────────────────────────────────┐
│ UltraThink Agent (LLM)          │
│ - Understands intent            │
│ - Matches entities (lenient)    │
│ - Decides what to fetch         │
│ - Designs response template     │
└──────┬──────────────────────────┘
       ↓
  {action, attribute, project, template, fields_needed}
       ↓
┌─────────────────────────────────┐
│ Knowledge Graph (Source of Truth)│
│ - Fetches ACTUAL values         │
│ - No hallucinations             │
│ - Structured & reliable         │
└──────┬──────────────────────────┘
       ↓
  {attribute_value, project_data, enrichment}
       ↓
┌─────────────────────────────────┐
│ Template Filler                 │
│ - Replaces {VALUE}              │
│ - Fills {project}, {location}   │
│ - Natural language output       │
└──────┬──────────────────────────┘
       ↓
┌─────────────┐
│ Final Answer│
└─────────────┘

Key Innovation: LLM provides INTELLIGENCE, KG provides TRUTH
"""

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import re

from app.services.ultrathink_agent import UltraThinkAgent, UltraThinkDecision
from app.services.data_service import data_service


@dataclass
class GraphRAGResponse:
    """Complete response from GraphRAG system"""
    answer: str
    confidence: float
    attribute_used: Optional[str]
    project_used: Optional[str]
    kg_data: Dict
    llm_reasoning: str
    template_used: str


class GraphRAGOrchestrator:
    """
    Hybrid LLM + Knowledge Graph orchestrator

    Philosophy:
    - LLM: Intelligent matching, reasoning, formatting decisions
    - KG: Source of truth for all factual data
    - No LLM hallucinations - all numbers come from KG
    """

    def __init__(self):
        self.ultrathink = UltraThinkAgent()
        self.kg = data_service  # Knowledge graph data service

    def query(
        self,
        user_query: str,
        available_attributes: Optional[List[str]] = None,
        available_projects: Optional[List[str]] = None
    ) -> GraphRAGResponse:
        """
        Execute a query using GraphRAG

        Steps:
        1. Let LLM think about the query (UltraThink)
        2. Fetch from KG based on LLM's decision
        3. Fill template with KG data
        4. Return natural language answer

        Args:
            user_query: User's natural language question
            available_attributes: List of queryable attributes (auto-loaded if None)
            available_projects: List of projects (auto-loaded if None)

        Returns:
            GraphRAGResponse with answer and metadata
        """

        # Step 1: Prepare context for LLM
        if available_attributes is None:
            available_attributes = self._get_all_attributes()
        if available_projects is None:
            available_projects = self._get_all_projects()

        # Optional: Sample KG data to help LLM understand structure
        sample_project = None
        if available_projects:
            sample_project = self.kg.get_project_by_name(available_projects[0])

        # Step 2: Let UltraThink LLM decide what to do
        decision = self.ultrathink.think(
            user_query,
            available_attributes,
            available_projects,
            kg_sample_data=sample_project
        )

        # Step 3: Execute LLM's decision
        if decision.action == "fetch_and_answer":
            return self._execute_fetch_and_answer(decision)

        elif decision.action == "need_clarification":
            return self._handle_clarification_needed(decision)

        elif decision.action == "error":
            return self._handle_error(decision)

        else:
            # Unknown action - fallback
            return GraphRAGResponse(
                answer=f"Unknown action: {decision.action}",
                confidence=0.0,
                attribute_used=None,
                project_used=None,
                kg_data={},
                llm_reasoning=decision.reasoning,
                template_used=""
            )

    def _execute_fetch_and_answer(self, decision: UltraThinkDecision) -> GraphRAGResponse:
        """
        Execute fetch from KG and fill template

        This is where KG becomes the source of truth.
        LLM has decided WHAT to fetch, KG provides the ACTUAL value.
        """

        # Fetch project data from KG
        project_data = None
        if decision.project:
            project_data = self.kg.get_project_by_name(decision.project)

        if not project_data and decision.project:
            # LLM thought there was a project but KG doesn't have it
            return GraphRAGResponse(
                answer=f"Project '{decision.project}' not found in knowledge graph.",
                confidence=0.0,
                attribute_used=decision.attribute,
                project_used=decision.project,
                kg_data={},
                llm_reasoning=decision.reasoning,
                template_used=decision.response_template
            )

        # Fetch attribute value from KG
        attribute_value = None
        if decision.attribute and project_data:
            attribute_value = self._fetch_attribute_from_kg(
                project_data,
                decision.attribute
            )

        # Gather enrichment data from KG
        enrichment_data = {}
        if project_data:
            enrichment_data = self._gather_enrichment_data(
                project_data,
                decision.kg_fields_needed
            )

        # Fill template with KG data
        final_answer = self._fill_template(
            decision.response_template,
            value=attribute_value,
            attribute=decision.attribute,
            project=decision.project,
            enrichment=enrichment_data
        )

        return GraphRAGResponse(
            answer=final_answer,
            confidence=decision.confidence,
            attribute_used=decision.attribute,
            project_used=decision.project,
            kg_data={
                "attribute_value": attribute_value,
                "project_data": project_data,
                "enrichment": enrichment_data
            },
            llm_reasoning=decision.reasoning,
            template_used=decision.response_template
        )

    def _handle_clarification_needed(self, decision: UltraThinkDecision) -> GraphRAGResponse:
        """Handle case where LLM needs clarification"""

        # LLM has designed a clarification template
        # We might need to fetch list of projects for example
        enrichment = {}
        if "all_projects" in decision.kg_fields_needed:
            all_projects = self._get_all_projects()
            enrichment["project_list"] = all_projects[:10]  # Top 10
            enrichment["count"] = len(all_projects)

        answer = self._fill_template(
            decision.response_template,
            enrichment=enrichment
        )

        return GraphRAGResponse(
            answer=answer,
            confidence=decision.confidence,
            attribute_used=None,
            project_used=None,
            kg_data=enrichment,
            llm_reasoning=decision.reasoning,
            template_used=decision.response_template
        )

    def _handle_error(self, decision: UltraThinkDecision) -> GraphRAGResponse:
        """Handle error cases"""
        return GraphRAGResponse(
            answer=decision.response_template,
            confidence=0.0,
            attribute_used=decision.attribute,
            project_used=decision.project,
            kg_data={},
            llm_reasoning=decision.reasoning,
            template_used=decision.response_template
        )

    def _fetch_attribute_from_kg(
        self,
        project_data: Dict,
        attribute_name: str
    ) -> Any:
        """
        Fetch attribute value from KG project data

        This is the SOURCE OF TRUTH - no LLM involved here.
        """

        # Try direct field access
        if attribute_name in project_data:
            return self.kg.get_value(project_data[attribute_name])

        # Try normalized field access (camelCase, lowercase, etc.)
        normalized_attr = attribute_name.lower().replace(' ', '').replace('(', '').replace(')', '')

        for key in project_data.keys():
            key_normalized = key.lower().replace('_', '').replace('-', '')
            if key_normalized == normalized_attr or normalized_attr in key_normalized:
                return self.kg.get_value(project_data[key])

        # Not found
        return None

    def _gather_enrichment_data(
        self,
        project_data: Dict,
        fields_needed: List[str]
    ) -> Dict:
        """Gather enrichment fields from KG"""
        enrichment = {}

        for field in fields_needed:
            # Handle dot notation: "project.location"
            if '.' in field:
                _, field_name = field.split('.', 1)
            else:
                field_name = field

            # Try to fetch from project data
            if field_name in project_data:
                enrichment[field_name] = self.kg.get_value(project_data[field_name])
            else:
                # Try normalized access
                for key in project_data.keys():
                    if field_name.lower() in key.lower():
                        enrichment[field_name] = self.kg.get_value(project_data[key])
                        break

        return enrichment

    def _fill_template(
        self,
        template: str,
        value: Any = None,
        attribute: Optional[str] = None,
        project: Optional[str] = None,
        enrichment: Optional[Dict] = None
    ) -> str:
        """
        Fill template with KG data

        Replaces placeholders:
        - {VALUE} → attribute value from KG
        - {attribute} → attribute name
        - {project} → project name
        - {location}, {developer}, etc. → enrichment data
        """

        filled = template

        # Replace main placeholders
        if value is not None:
            filled = filled.replace("{VALUE}", str(value))
        if attribute:
            filled = filled.replace("{attribute}", attribute)
        if project:
            filled = filled.replace("{project}", project)

        # Replace enrichment placeholders
        if enrichment:
            for key, val in enrichment.items():
                placeholder = f"{{{key}}}"
                filled = filled.replace(placeholder, str(val))

        return filled

    def _get_all_attributes(self) -> List[str]:
        """Get list of all queryable attributes"""
        # This would come from your attribute Excel or service
        # For now, return a sample
        from app.services.dynamic_formula_service import DynamicFormulaService

        try:
            formula_service = DynamicFormulaService()
            return list(formula_service.attributes.keys())
        except Exception:
            return [
                "Project Size", "Total Supply", "Sold %", "Unsold %",
                "Annual Sales", "Saleable Price"
            ]

    def _get_all_projects(self) -> List[str]:
        """Get list of all projects from KG"""
        all_projects = self.kg.get_all_projects()
        return [
            self.kg.get_value(proj.get('projectName'))
            for proj in all_projects
            if proj.get('projectName')
        ]


# Global instance
_graphrag_orchestrator = None

def get_graphrag_orchestrator() -> GraphRAGOrchestrator:
    """Get or create global GraphRAG orchestrator"""
    global _graphrag_orchestrator
    if _graphrag_orchestrator is None:
        _graphrag_orchestrator = GraphRAGOrchestrator()
    return _graphrag_orchestrator


# Convenience function for quick queries
def ask_graphrag(query: str) -> str:
    """
    Quick GraphRAG query

    Usage:
        answer = ask_graphrag("What is the Project Size of Sara City?")
        print(answer)
    """
    orchestrator = get_graphrag_orchestrator()
    response = orchestrator.query(query)
    return response.answer
