"""
Value Formatting Utilities for Dynamic Widget System

Provides auto-formatting functions for various data types commonly used in
real estate analytics (currency, percentages, units, time, area, etc.)
"""

from typing import Any, Optional, Dict
import re


# =============================================================================
# FORMATTER FUNCTIONS
# =============================================================================

def format_currency_inr(value: float, as_crore: bool = False) -> str:
    """
    Format currency in INR
    
    Args:
        value: Numeric value
        as_crore: If True, convert to Crores; otherwise use comma-separated INR
    
    Returns:
        Formatted string (e.g., "₹11.05 Cr" or "₹125,000,000")
    """
    if value is None:
        return "N/A"
    
    if as_crore:
        crore_value = value / 10000000
        return f"₹{crore_value:.2f} Cr"
    else:
        return f"₹{value:,.2f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format as percentage
    
    Args:
        value: Numeric value (already in percent, e.g., 19.71)
        decimals: Number of decimal places
    
    Returns:
        Formatted string (e.g., "19.71%")
    """
    if value is None:
        return "N/A"
    
    return f"{value:.{decimals}f}%"


def format_fraction_as_percentage(value: float, decimals: int = 1) -> str:
    """
    Format fraction (0-1 range) as percentage
    
    Args:
        value: Fraction (e.g., 0.25)
        decimals: Number of decimal places
    
    Returns:
        Formatted string (e.g., "25.0%")
    """
    if value is None:
        return "N/A"
    
    return f"{value * 100:.{decimals}f}%"


def format_time_years(value: float) -> str:
    """Format time in years"""
    if value is None:
        return "N/A"
    
    return f"{value:.1f} years"


def format_time_months(value: float) -> str:
    """Format time in months"""
    if value is None:
        return "N/A"
    
    return f"{int(value)} months"


def format_units(value: int) -> str:
    """Format unit count"""
    if value is None:
        return "N/A"
    
    return f"{int(value):,} units"


def format_area_sqft(value: float) -> str:
    """Format area in square feet"""
    if value is None:
        return "N/A"
    
    return f"{value:,.0f} sqft"


def format_boolean(value: bool) -> str:
    """Format boolean value"""
    if value is None:
        return "N/A"
    
    return "✓ Yes" if value else "✗ No"


def format_number(value: float, decimals: int = 4) -> str:
    """Format generic number"""
    if value is None:
        return "N/A"
    
    if isinstance(value, int):
        return f"{value:,}"
    else:
        return f"{value:.{decimals}f}"


# =============================================================================
# AUTO-DETECTION FORMATTER
# =============================================================================

def auto_format_value(key: str, value: Any, unit: Optional[str] = None) -> str:
    """
    Automatically detect and format value based on key name and unit
    
    Args:
        key: Field name (used for detection)
        value: Value to format
        unit: Optional unit string from API response
    
    Returns:
        Formatted string
    """
    if value is None:
        return "N/A"
    
    # Handle non-numeric types
    if isinstance(value, bool):
        return format_boolean(value)
    
    if isinstance(value, str):
        return str(value)
    
    if isinstance(value, (dict, list)):
        return "See nested data"
    
    # Numeric formatting based on unit
    if unit:
        unit_lower = unit.lower()
        
        if "%" in unit or "percent" in unit_lower:
            return format_percentage(value)
        
        if "inr" in unit_lower:
            if "cr" in unit_lower or "crore" in unit_lower:
                return format_currency_inr(value, as_crore=True)
            else:
                return format_currency_inr(value, as_crore=False)
        
        if "year" in unit_lower:
            return format_time_years(value)
        
        if "month" in unit_lower:
            return format_time_months(value)
        
        if "sqft" in unit_lower or "sq ft" in unit_lower:
            return format_area_sqft(value)
        
        if "unit" in unit_lower:
            return format_units(value)
    
    # Key-based detection (fallback if no unit provided)
    key_lower = key.lower()
    
    # Percentages
    if any(keyword in key_lower for keyword in ["percent", "irr", "roi", "rate", "_pct"]):
        return format_percentage(value)
    
    # Currency
    if any(keyword in key_lower for keyword in ["crore", "cr_"]):
        return format_currency_inr(value, as_crore=True)
    
    if any(keyword in key_lower for keyword in ["inr", "revenue", "cost", "price", "value", "npv", "investment"]):
        # Large values (> 10M) shown as Crores
        if abs(value) > 10000000:
            return format_currency_inr(value, as_crore=True)
        else:
            return format_currency_inr(value, as_crore=False)
    
    # Time
    if "year" in key_lower and "duration" not in key_lower:
        return format_time_years(value)
    
    if "month" in key_lower:
        return format_time_months(value)
    
    # Area
    if any(keyword in key_lower for keyword in ["sqft", "area"]):
        return format_area_sqft(value)
    
    # Units
    if "units" in key_lower or "count" in key_lower:
        return format_units(value)
    
    # Fractions (0-1 range that should be percentages)
    if "mix" in key_lower or "multiplier" in key_lower:
        if 0 <= value <= 1:
            return format_fraction_as_percentage(value)
    
    # Default: generic number formatting
    return format_number(value)


# =============================================================================
# KEY NAME FORMATTER
# =============================================================================

def format_key_name(key: str) -> str:
    """
    Convert key names to human-readable format
    
    Examples:
        "npv_inr" -> "NPV (INR)"
        "irr_percent" -> "IRR (%)"
        "totalUnits" -> "Total Units"
        "absorption_rate" -> "Absorption Rate"
    
    Args:
        key: Raw key name
    
    Returns:
        Formatted key name
    """
    # Replace underscores with spaces
    formatted = key.replace('_', ' ')
    
    # Handle camelCase: insert space before capitals
    formatted = re.sub(r'([a-z])([A-Z])', r'\1 \2', formatted)
    
    # Uppercase specific acronyms
    acronyms = {
        'inr': 'INR',
        'npv': 'NPV',
        'irr': 'IRR',
        'roi': 'ROI',
        'psf': 'PSF',
        'asp': 'ASP',
        'opps': 'OPPS',
        'bhk': 'BHK',
        'cf': 'CF',
        'noi': 'NOI',
        'apr': 'APR'
    }
    
    words = formatted.split()
    formatted_words = []
    
    for word in words:
        word_lower = word.lower()
        if word_lower in acronyms:
            formatted_words.append(acronyms[word_lower])
        else:
            formatted_words.append(word.title())
    
    result = ' '.join(formatted_words)
    
    # Add units in parentheses if detected in original key
    if '_inr' in key.lower() and '(INR)' not in result:
        result = result.replace(' INR', ' (INR)')
    
    if '_percent' in key.lower() and '(%)' not in result:
        result = result.replace(' Percent', ' (%)')
    
    if '_crore' in key.lower() and '(Cr)' not in result:
        result = result.replace(' Crore', ' (Cr)')
    
    return result


# =============================================================================
# FORMATTING PRESETS
# =============================================================================

FORMATTERS: Dict[str, callable] = {
    "percent": format_percentage,
    "fraction_to_percent": format_fraction_as_percentage,
    "inr": lambda v: format_currency_inr(v, as_crore=False),
    "inr_crore": lambda v: format_currency_inr(v, as_crore=True),
    "years": format_time_years,
    "months": format_time_months,
    "units": format_units,
    "sqft": format_area_sqft,
    "boolean": format_boolean,
    "number": format_number
}


def get_formatter(formatter_name: str) -> callable:
    """
    Get formatter function by name
    
    Args:
        formatter_name: Name from FORMATTERS dict
    
    Returns:
        Formatter function
    """
    return FORMATTERS.get(formatter_name, format_number)
