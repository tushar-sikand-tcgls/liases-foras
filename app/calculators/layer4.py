"""
Layer 4: Market Insights & Contextual Intelligence

Uses RAG (Retrieval-Augmented Generation) to enrich financial calculations
with market context from city reports vector database.
"""

from typing import Dict, Any, List, Optional
from app.services.vector_db_service import get_vector_db


class Layer4Calculator:
    """
    Layer 4: Market Intelligence Layer

    Enriches quantitative analysis with qualitative market insights
    using semantic search over city reports.
    """

    def __init__(self):
        """Initialize with vector DB service"""
        self.vector_db = get_vector_db()

    def get_market_insights(
        self,
        city: str,
        locality: str,
        price_psf: Optional[float] = None,
        project_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive market insights for a location

        Args:
            city: City name (Mumbai, Pune, etc.)
            locality: Locality/micro-market name
            price_psf: Price per square foot (optional, for context)
            project_type: Project type (luxury, mid-segment, affordable)

        Returns:
            Dictionary with market context, trends, infrastructure
        """
        insights = {
            "city": city,
            "locality": locality,
            "price_psf": price_psf,
            "project_type": project_type
        }

        # 1. Get city overview
        insights["city_overview"] = self._get_city_overview(city)

        # 2. Get locality-specific insights
        insights["locality_insights"] = self._get_locality_insights(city, locality)

        # 3. Get price context and benchmarks
        if price_psf:
            insights["price_context"] = self._get_price_context(city, locality, price_psf)

        # 4. Get infrastructure and amenities
        insights["infrastructure"] = self._get_infrastructure_insights(city, locality)

        # 5. Get future outlook and trends
        insights["future_outlook"] = self._get_future_outlook(city, locality)

        # 6. Generate positioning statement
        insights["positioning"] = self._generate_positioning(insights)

        return insights

    def _get_city_overview(self, city: str) -> Dict[str, Any]:
        """Get executive summary for the city"""
        results = self.vector_db.semantic_search(
            query=f"{city} real estate market overview executive summary key trends",
            city=city,
            section_type="executive_summary",
            n_results=1
        )

        if results:
            return {
                "text": results[0]["text"],
                "source": results[0]["metadata"]["section"],
                "similarity": results[0]["similarity_score"]
            }
        return {"text": f"No overview available for {city}", "source": None, "similarity": 0}

    def _get_locality_insights(self, city: str, locality: str) -> Dict[str, Any]:
        """Get detailed insights for specific locality"""
        results = self.vector_db.semantic_search(
            query=f"{locality} {city} price density liveability demographics trends",
            city=city,
            n_results=3
        )

        # Filter for locality mentions
        relevant = [r for r in results if locality.lower() in r["text"].lower()]

        if not relevant:
            relevant = results[:1]  # Fallback to top result

        insights = {
            "primary": relevant[0] if relevant else None,
            "related": relevant[1:] if len(relevant) > 1 else [],
            "micro_markets_mentioned": []
        }

        if relevant:
            # Extract mentioned micro-markets
            for result in relevant:
                markets = result["metadata"].get("micro_markets", "").split(",")
                insights["micro_markets_mentioned"].extend([m for m in markets if m])

        return insights

    def _get_price_context(self, city: str, locality: str, price_psf: float) -> Dict[str, Any]:
        """Get price benchmarking and context"""
        query = f"{locality} {city} price per square foot ₹{int(price_psf)} rates comparison market"

        results = self.vector_db.semantic_search(
            query=query,
            city=city,
            n_results=2
        )

        context = {
            "query_price": price_psf,
            "market_data": results[0] if results else None,
            "comparables": results[1] if len(results) > 1 else None
        }

        # Try to extract price range from text if available
        if results and results[0]:
            text = results[0]["text"]
            # Look for price patterns like "₹25k-40k"
            import re
            price_patterns = re.findall(r'₹(\d+)k?(?:-₹?(\d+)k?)?', text)
            if price_patterns:
                context["market_price_ranges"] = price_patterns

        return context

    def _get_infrastructure_insights(self, city: str, locality: str) -> Dict[str, Any]:
        """Get infrastructure and amenities information"""
        results = self.vector_db.semantic_search(
            query=f"{locality} {city} schools hospitals malls metro connectivity infrastructure amenities",
            city=city,
            section_type="social_infrastructure",
            n_results=2
        )

        infrastructure = {
            "amenities": results[0] if results else None,
            "connectivity": None
        }

        # Search for connectivity/transport
        transport_results = self.vector_db.semantic_search(
            query=f"{locality} {city} metro road highway connectivity transport commute",
            city=city,
            n_results=1
        )

        if transport_results:
            infrastructure["connectivity"] = transport_results[0]

        return infrastructure

    def _get_future_outlook(self, city: str, locality: str) -> Dict[str, Any]:
        """Get future trends and outlook"""
        results = self.vector_db.semantic_search(
            query=f"{locality} {city} future outlook investment forecast development next 5 years appreciation",
            city=city,
            section_type="future_outlook",
            n_results=2
        )

        outlook = {
            "trends": results[0] if results else None,
            "projections": results[1] if len(results) > 1 else None
        }

        return outlook

    def _generate_positioning(self, insights: Dict[str, Any]) -> str:
        """Generate a positioning statement based on all insights"""
        city = insights["city"]
        locality = insights["locality"]
        price_psf = insights.get("price_psf")

        positioning_parts = [f"**{locality}, {city}**"]

        # Add price positioning if available
        if price_psf:
            positioning_parts.append(f"at ₹{price_psf:,.0f}/sqft")

        # Add locality characteristic
        locality_info = insights.get("locality_insights", {}).get("primary")
        if locality_info:
            # Extract key characteristics from text snippet
            snippet = locality_info["text"][:200]
            positioning_parts.append(f"- {snippet}...")

        return " ".join(positioning_parts)

    def enrich_irr_calculation(
        self,
        irr_result: Dict[str, Any],
        city: str,
        locality: str
    ) -> Dict[str, Any]:
        """
        Enrich IRR calculation with market context

        Args:
            irr_result: Result from Layer 2 IRR calculation
            city: City name
            locality: Locality name

        Returns:
            Enriched result with market insights
        """
        irr_value = irr_result.get("value", 0)

        # Get market insights
        insights = self.get_market_insights(city, locality)

        # Add market context to result
        enriched = {
            **irr_result,
            "market_insights": {
                "city_context": insights["city_overview"],
                "locality_context": insights["locality_insights"].get("primary"),
                "comparable_projects": self._find_comparable_projects(city, locality, irr_value),
                "market_positioning": self._position_irr(irr_value, city, locality)
            }
        }

        return enriched

    def _find_comparable_projects(self, city: str, locality: str, irr: float) -> List[Dict]:
        """Find comparable projects mentioned in reports"""
        query = f"{locality} {city} projects IRR {irr:.0f}% returns profitability investment"

        results = self.vector_db.semantic_search(
            query=query,
            city=city,
            n_results=2
        )

        return results

    def _position_irr(self, irr: float, city: str, locality: str) -> str:
        """Position IRR value against market benchmarks"""
        # Search for IRR/return benchmarks in the city
        query = f"{city} IRR returns typical target real estate {irr:.0f}%"

        results = self.vector_db.semantic_search(
            query=query,
            city=city,
            n_results=1
        )

        if irr >= 0.25:
            return f"Exceptional return ({irr:.1%}) - significantly above market targets for {city}"
        elif irr >= 0.20:
            return f"Strong return ({irr:.1%}) - meets typical {city} real estate targets (20-28%)"
        elif irr >= 0.15:
            return f"Moderate return ({irr:.1%}) - below typical {city} targets but acceptable"
        else:
            return f"Below-market return ({irr:.1%}) - consider optimization for {locality}"

    def get_region_insights(self, region: str, city: str) -> Dict[str, Any]:
        """
        Get comprehensive insights for an entire region/catchment area

        Args:
            region: Region name (e.g., "Chakan", "Hinjewadi")
            city: City name

        Returns:
            Dictionary with aggregated regional insights
        """
        insights = {
            "region": region,
            "city": city,
            "level": "region"
        }

        # 1. Get regional overview
        regional_query = f"{region} {city} region overview development infrastructure projects"
        regional_results = self.vector_db.semantic_search(
            query=regional_query,
            city=city,
            n_results=5
        )

        insights["regional_overview"] = {
            "primary": regional_results[0] if regional_results else None,
            "related": regional_results[1:3] if len(regional_results) > 1 else []
        }

        # 2. Get micro-markets within region
        micro_markets_query = f"{region} micro markets localities neighborhoods areas zones"
        micro_markets = self.vector_db.semantic_search(
            query=micro_markets_query,
            city=city,
            n_results=3
        )

        insights["micro_markets"] = micro_markets

        # 3. Get regional infrastructure
        infra_query = f"{region} {city} infrastructure connectivity metro roads schools hospitals malls"
        infra_results = self.vector_db.semantic_search(
            query=infra_query,
            city=city,
            section_type="social_infrastructure",
            n_results=3
        )

        insights["infrastructure"] = infra_results

        # 4. Get development trends
        trends_query = f"{region} {city} development trends future projects investment growth"
        trends_results = self.vector_db.semantic_search(
            query=trends_query,
            city=city,
            section_type="future_outlook",
            n_results=3
        )

        insights["trends"] = trends_results

        # 5. Get price trends for region
        price_query = f"{region} {city} price rates per square foot market comparison trends"
        price_results = self.vector_db.semantic_search(
            query=price_query,
            city=city,
            n_results=3
        )

        insights["price_trends"] = price_results

        # 6. Generate regional summary
        insights["summary"] = self._generate_regional_summary(insights)

        return insights

    def _generate_regional_summary(self, insights: Dict[str, Any]) -> str:
        """Generate a summary for regional insights"""
        region = insights["region"]
        city = insights["city"]

        summary_parts = [f"**{region}, {city}** - Regional Analysis"]

        # Add overview snippet if available
        if insights.get("regional_overview", {}).get("primary"):
            overview = insights["regional_overview"]["primary"]["text"][:200]
            summary_parts.append(f"\n{overview}...")

        # Add infrastructure highlight
        if insights.get("infrastructure"):
            summary_parts.append(f"\n✓ Infrastructure: {len(insights['infrastructure'])} key facilities identified")

        # Add micro-markets count
        if insights.get("micro_markets"):
            summary_parts.append(f"✓ Micro-markets: {len(insights['micro_markets'])} localities analyzed")

        return " ".join(summary_parts)

    def get_catchment_area_insights(
        self,
        catchment_area: str,
        city: str,
        radius_km: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Get insights for a catchment area (broader than region)

        Args:
            catchment_area: Catchment area description (e.g., "Western Pune", "South Mumbai")
            city: City name
            radius_km: Optional radius in km for catchment definition

        Returns:
            Dictionary with catchment area insights
        """
        insights = {
            "catchment_area": catchment_area,
            "city": city,
            "radius_km": radius_km,
            "level": "catchment"
        }

        # Get broader area insights
        catchment_query = f"{catchment_area} {city} market overview suburbs regions localities"
        catchment_results = self.vector_db.semantic_search(
            query=catchment_query,
            city=city,
            n_results=7
        )

        insights["area_overview"] = catchment_results[:3]
        insights["regional_breakdown"] = catchment_results[3:7]

        # Get demographic and economic indicators
        demo_query = f"{catchment_area} {city} demographics population density affluence economic"
        demo_results = self.vector_db.semantic_search(
            query=demo_query,
            city=city,
            n_results=3
        )

        insights["demographics"] = demo_results

        # Get major projects and developments
        projects_query = f"{catchment_area} {city} major projects developments townships infrastructure"
        projects_results = self.vector_db.semantic_search(
            query=projects_query,
            city=city,
            n_results=5
        )

        insights["major_projects"] = projects_results

        return insights
