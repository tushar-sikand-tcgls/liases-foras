"""
Widget Templates for Dynamic Rendering

Provides template classes for rendering different types of data structures
as Streamlit widgets.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import streamlit as st
from components.schema_analyzer import StructureMetadata
from components.formatters import auto_format_value, format_key_name


class WidgetTemplate(ABC):
    """Abstract base class for widget templates"""
    
    @abstractmethod
    def can_render(self, data: Dict, metadata: StructureMetadata) -> bool:
        """Check if this template can handle the data"""
        pass
    
    @abstractmethod
    def render(self, data: Dict, config: Optional[Dict] = None) -> None:
        """Render the widget using Streamlit"""
        pass


class SingleMetricTemplate(WidgetTemplate):
    """Renders single metric with st.metric()"""
    
    def can_render(self, data: Dict, metadata: StructureMetadata) -> bool:
        """Can render if has metric, value, unit structure"""
        required_keys = {"metric", "value", "unit"}
        return required_keys.issubset(set(data.keys()))
    
    def render(self, data: Dict, config: Optional[Dict] = None) -> None:
        """Render single metric"""
        config = config or {}
        
        metric_name = data.get("metric", "Metric")
        value = data.get("value")
        unit = data.get("unit", "")
        
        # Format value
        if value is not None:
            formatted_value = auto_format_value("value", value, unit)
            
            # Show metric with optional target range
            target_range = config.get("target_range")
            if target_range and isinstance(value, (int, float)):
                min_target, max_target = target_range

                # Special handling for IRR with 3-tier interpretation
                if metric_name == "💎 Internal Rate of Return (IRR)":
                    if value >= min_target:
                        st.metric(metric_name, formatted_value)
                        st.success(f"🎯 Exceeds target range ({min_target}-{max_target}{unit})")
                    elif value >= 15:
                        st.metric(metric_name, formatted_value)
                        st.info(f"📊 Acceptable range (15-{min_target}{unit}) - below optimal but viable")
                    else:
                        st.metric(metric_name, formatted_value)
                        st.warning(f"⚠️ Below acceptable range (target: {min_target}-{max_target}{unit})")
                else:
                    # Standard target range handling for other metrics
                    if value >= min_target:
                        delta = f"Target: {min_target}-{max_target}{unit}"
                        st.metric(metric_name, formatted_value, delta=delta)
                    else:
                        st.metric(metric_name, formatted_value)
                        st.warning(f"⚠️ Below target range ({min_target}-{max_target}{unit})")
            else:
                st.metric(metric_name, formatted_value)
        else:
            st.error(f"⚠️ {metric_name} calculation failed")
            st.info("Value returned as null - check input parameters")


class KeyValuePanelTemplate(WidgetTemplate):
    """Renders dictionary as styled key-value panel"""
    
    def can_render(self, data: Dict, metadata: StructureMetadata) -> bool:
        """Can render any dictionary"""
        return isinstance(data, dict) and len(data) > 0
    
    def render(self, data: Dict, config: Optional[Dict] = None) -> None:
        """Render key-value panel"""
        st.markdown('<div class="info-panel">', unsafe_allow_html=True)
        
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                continue  # Skip nested structures in main panel
            
            formatted_key = format_key_name(key)
            formatted_value = auto_format_value(key, value)
            
            st.markdown(f"""
            <div class="kv-row">
                <div class="kv-key">{formatted_key}</div>
                <div class="kv-value">{formatted_value}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)


class ScenarioComparisonTemplate(WidgetTemplate):
    """Renders scenario comparison (base/optimistic/stress)"""
    
    def can_render(self, data: Dict, metadata: StructureMetadata) -> bool:
        """Can render if has scenario keys"""
        scenario_keys = {"baseCase", "optimisticCase", "stressCase"}
        return len(set(data.keys()) & scenario_keys) >= 2
    
    def render(self, data: Dict, config: Optional[Dict] = None) -> None:
        """Render scenario comparison"""
        st.markdown("### 📈 Scenario Comparison")
        
        col1, col2, col3 = st.columns(3)
        
        # Base case
        with col1:
            if "baseCase" in data:
                self._render_scenario(data["baseCase"], "Base Case", "neutral")
        
        # Optimistic case
        with col2:
            if "optimisticCase" in data:
                base_data = data.get("baseCase", {})
                self._render_scenario(data["optimisticCase"], "Optimistic", "success", base_data)
        
        # Stress case
        with col3:
            if "stressCase" in data:
                base_data = data.get("baseCase", {})
                self._render_scenario(data["stressCase"], "Stress", "warning", base_data)
    
    def _render_scenario(self, scenario: Dict, name: str, style: str, base: Optional[Dict] = None):
        """Render single scenario panel"""
        bg_colors = {
            "neutral": "#f8f9fa",
            "success": "#d4edda",
            "warning": "#fff3cd"
        }
        
        st.markdown(f'<div class="nested-panel" style="background-color: {bg_colors[style]};">', 
                   unsafe_allow_html=True)
        st.markdown(f"#### {name}")
        
        # Show key metrics
        if "irr_percent" in scenario:
            irr = scenario["irr_percent"]
            if base and "irr_percent" in base:
                delta = irr - base["irr_percent"]
                st.metric("IRR", f"{irr:.2f}%", delta=f"{delta:+.2f}%")
            else:
                st.metric("IRR", f"{irr:.2f}%")
        
        if "npv_inr" in scenario:
            npv = scenario["npv_inr"] / 10000000  # Convert to Crores
            if base and "npv_inr" in base:
                delta_npv = (scenario["npv_inr"] - base["npv_inr"]) / 10000000
                st.metric("NPV", f"₹{npv:.2f} Cr", delta=f"₹{delta_npv:+.2f} Cr")
            else:
                st.metric("NPV", f"₹{npv:.2f} Cr")
        
        st.markdown('</div>', unsafe_allow_html=True)


class OptimizationResultTemplate(WidgetTemplate):
    """Renders optimization result with unit mix"""
    
    def can_render(self, data: Dict, metadata: StructureMetadata) -> bool:
        """Can render if has optimal_mix and scenarios"""
        return "optimal_mix" in data or "scenarios" in data
    
    def render(self, data: Dict, config: Optional[Dict] = None) -> None:
        """Render optimization result"""
        st.markdown("### 🎯 Optimal Product Mix")
        
        # Show optimal mix
        if "optimal_mix" in data and "units_breakdown" in data:
            mix = data["optimal_mix"]
            units = data["units_breakdown"]
            
            col1, col2, col3 = st.columns(3)
            for i, (unit_type, percentage) in enumerate(mix.items()):
                with [col1, col2, col3][i % 3]:
                    unit_count = units.get(unit_type, 0)
                    st.metric(unit_type, f"{percentage*100:.1f}%", delta=f"{unit_count} units")
        
        # Show scenarios
        if "scenarios" in data:
            st.markdown("---")
            st.markdown("### 📊 Financial Scenarios")
            
            for scenario in data["scenarios"]:
                icon = {"Base Case": "📊", "Optimistic": "🚀", "Conservative": "🛡️"}.get(
                    scenario.get("scenarioName", ""), "📋"
                )
                
                with st.expander(f"{icon} {scenario['scenarioName']} - IRR: {scenario.get('irr_percent', 0):.2f}%"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("NPV", f"₹{scenario.get('npv_crore', 0):.2f} Cr")
                        st.metric("Revenue", f"₹{scenario.get('revenue_crore', 0):.2f} Cr")
                    with col2:
                        st.metric("IRR", f"{scenario.get('irr_percent', 0):.2f}%")
                        st.metric("Duration", f"{scenario.get('duration_months', 0)} months")


class MarketScoringTemplate(WidgetTemplate):
    """Renders market opportunity scoring"""
    
    def can_render(self, data: Dict, metadata: StructureMetadata) -> bool:
        """Can render if has oppsScore"""
        return "oppsScore" in data
    
    def render(self, data: Dict, config: Optional[Dict] = None) -> None:
        """Render market scoring"""
        st.markdown("### 🎯 Market Opportunity Score")
        
        opps = data.get("oppsScore", 0)
        demand = data.get("demandTrend", "unknown")
        
        st.metric("OPPS Score", f"{opps}/100", delta=f"{demand.upper()} demand")
        
        if "opportunity" in data:
            st.info(f"💡 {data['opportunity']}")
        
        # Recommended mix
        if "recommendedMix" in data:
            st.markdown("### 📊 Recommended Unit Mix")
            mix = data["recommendedMix"]
            
            col1, col2, col3 = st.columns(3)
            unit_types = list(mix.keys())
            for i, unit_type in enumerate(unit_types):
                with [col1, col2, col3][i % 3]:
                    st.metric(unit_type, f"{mix[unit_type]*100:.0f}%")


class FallbackTemplate(WidgetTemplate):
    """Fallback template for unknown structures"""
    
    def can_render(self, data: Dict, metadata: StructureMetadata) -> bool:
        """Can always render as fallback"""
        return True
    
    def render(self, data: Dict, config: Optional[Dict] = None) -> None:
        """Render as expandable JSON"""
        st.info("📋 Displaying raw data structure")
        
        with st.expander("View Data"):
            st.json(data)
